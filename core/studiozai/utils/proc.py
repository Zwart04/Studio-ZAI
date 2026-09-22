"""Pelacakan dan pembersihan proses anak (ffmpeg/ffprobe).

Masalah yang diperbaiki: kalau aplikasi ditutup paksa (End task) saat ffmpeg
masih jalan, proses ffmpeg itu tetap hidup dan mengunci file klip — folder
aplikasi jadi tidak bisa dihapus. Dua lapis perlindungan:

1. Job Object Windows dengan KILL_ON_JOB_CLOSE -> anak mati otomatis ketika
   proses induk hilang, bahkan bila dibunuh paksa.
2. atexit -> semua anak yang masih hidup dihentikan saat keluar normal.
"""

from __future__ import annotations

import atexit
import subprocess
import sys
import threading
from collections.abc import Sequence
from typing import IO, Any

_LOCK = threading.Lock()
_CHILDREN: set[subprocess.Popen[Any]] = set()
_JOB: int | None = None
_JOB_READY = False

_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000


def _creation_flags() -> int:
    """Sembunyikan jendela konsol anak di Windows."""
    if sys.platform == "win32":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return 0


def _get_job() -> int | None:
    """Buat Job Object sekali (Windows saja)."""
    global _JOB, _JOB_READY
    if _JOB_READY:
        return _JOB
    _JOB_READY = True
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class _IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class _BASIC_LIMIT(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
                ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class _EXTENDED_LIMIT(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", _BASIC_LIMIT),
                ("IoInfo", _IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None
        info = _EXTENDED_LIMIT()
        info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        ok = kernel32.SetInformationJobObject(
            wintypes.HANDLE(job),
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not ok:
            kernel32.CloseHandle(wintypes.HANDLE(job))
            return None
        _JOB = int(job)
    except Exception:  # noqa: BLE001 - ctypes/Windows bisa gagal dengan cara apa pun
        _JOB = None
    return _JOB


def _assign_to_job(proc: subprocess.Popen[Any]) -> None:
    job = _get_job()
    if not job or sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x0200 | 0x1000, False, proc.pid)  # SET_QUOTA|QUERY_LIMITED
        if not handle:
            return
        try:
            kernel32.AssignProcessToJobObject(wintypes.HANDLE(job), wintypes.HANDLE(handle))
        finally:
            kernel32.CloseHandle(wintypes.HANDLE(handle))
    except Exception:  # noqa: BLE001, S110 - job object bersifat opsional
        pass


def spawn(
    cmd: Sequence[str],
    *,
    stdout: int | IO[Any] | None = None,
    stderr: int | IO[Any] | None = None,
    text: bool = False,
) -> subprocess.Popen[Any]:
    """subprocess.Popen yang otomatis dilacak dan dibersihkan."""
    proc = subprocess.Popen(
        list(cmd),
        stdout=stdout,
        stderr=stderr,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
        creationflags=_creation_flags(),
    )
    with _LOCK:
        _CHILDREN.add(proc)
    _assign_to_job(proc)
    return proc


def run(cmd: Sequence[str], timeout: int | None = None) -> tuple[int, str, str]:
    """Jalankan perintah sampai selesai, kembalikan (kode, stdout, stderr)."""
    proc = spawn(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    finally:
        with _LOCK:
            _CHILDREN.discard(proc)
    return proc.returncode or 0, out or "", err or ""


def run_bytes(cmd: Sequence[str], timeout: int | None = None) -> tuple[int, bytes, str]:
    """Seperti run(), tapi stdout dikembalikan sebagai bytes (mis. PCM audio)."""
    proc_handle = spawn(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
    try:
        out, err = proc_handle.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc_handle.kill()
        out, err = proc_handle.communicate()
    finally:
        forget(proc_handle)
    return proc_handle.returncode or 0, out or b"", (err or b"").decode("utf-8", "replace")


def forget(process: subprocess.Popen[Any]) -> None:
    """Berhenti melacak proses yang sudah selesai."""
    with _LOCK:
        _CHILDREN.discard(process)


def terminate_all() -> int:
    """Hentikan semua proses anak yang masih hidup. Kembalikan jumlahnya."""
    with _LOCK:
        children = list(_CHILDREN)
        _CHILDREN.clear()
    killed = 0
    for proc in children:
        if proc.poll() is not None:
            continue
        try:
            proc.kill()
            killed += 1
        except OSError:
            pass
    return killed


def active_count() -> int:
    with _LOCK:
        return sum(1 for proc in _CHILDREN if proc.poll() is None)


atexit.register(terminate_all)
