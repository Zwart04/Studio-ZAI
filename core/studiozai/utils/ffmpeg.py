"""Thin wrappers around the system FFmpeg/FFprobe binaries."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from . import proc

TIME_RE = re.compile(r"time=(\d+):(\d{2}):(\d{2})(?:\.(\d+))?")

ProgressCb = Callable[[float], None]


class FFmpegNotFound(RuntimeError):
    pass


def bundled_bin_dir() -> Path | None:
    """Directory holding the ffmpeg/ffprobe shipped with the packaged app."""
    env = os.environ.get("STUDIOZAI_BIN")
    if env and Path(env).is_dir():
        return Path(env)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        for candidate in (Path(meipass) / "bin", Path(meipass)):
            if (candidate / "ffmpeg.exe").exists() or (candidate / "ffmpeg").exists():
                return candidate
    exe_dir = Path(sys.executable).resolve().parent
    for candidate in (exe_dir / "bin", exe_dir):
        if (candidate / "ffmpeg.exe").exists() or (candidate / "ffmpeg").exists():
            return candidate
    return None


def _find_tool(name: str) -> str | None:
    bundled = bundled_bin_dir()
    if bundled:
        for candidate in (bundled / f"{name}.exe", bundled / name):
            if candidate.exists():
                return str(candidate)
    return shutil.which(name)


def ffmpeg_path() -> str:
    path = _find_tool("ffmpeg")
    if not path:
        raise FFmpegNotFound(
            "ffmpeg tidak ditemukan (versi bundel maupun di PATH). "
            "Instal ffmpeg lalu jalankan 'studiozai doctor'."
        )
    return path


def ffprobe_path() -> str:
    path = _find_tool("ffprobe")
    if not path:
        raise FFmpegNotFound("ffprobe tidak ditemukan (biasanya satu paket dengan ffmpeg).")
    return path


def ffmpeg_available() -> bool:
    return _find_tool("ffmpeg") is not None and _find_tool("ffprobe") is not None


def detect_h264_encoder() -> str:
    """Prefer NVENC only when an NVIDIA GPU is actually present, otherwise x264."""
    if not shutil.which("nvidia-smi"):
        return "libx264"
    try:
        code, out, _ = proc.run(["nvidia-smi", "-L"], timeout=15)
    except (OSError, subprocess.SubprocessError):
        return "libx264"
    if code != 0 or "GPU" not in out:
        return "libx264"
    try:
        _, encoders, _ = proc.run([ffmpeg_path(), "-hide_banner", "-encoders"], timeout=20)
    except (OSError, subprocess.SubprocessError):
        return "libx264"
    return "h264_nvenc" if "h264_nvenc" in encoders else "libx264"


@dataclass
class RunResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    command: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _creation_flags() -> int:
    """On Windows, prevent child process consoles from flashing on screen."""
    if sys.platform == "win32":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return 0


def run_ffmpeg(
    args: Sequence[str],
    total_duration: float | None = None,
    progress_cb: ProgressCb | None = None,
    timeout: int | None = None,
) -> RunResult:
    """Run ffmpeg with array args (never shell) and optional progress parsing."""
    cmd = [ffmpeg_path(), "-hide_banner", "-nostdin", "-y", *args]
    proc_handle = proc.spawn(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stderr_lines: list[str] = []
    assert proc_handle.stderr is not None
    try:
        for line in proc_handle.stderr:
            stderr_lines.append(line)
            if progress_cb and total_duration:
                match = TIME_RE.search(line)
                if match:
                    h, m, s, frac = match.groups()
                    seconds = int(h) * 3600 + int(m) * 60 + int(s) + float(f"0.{frac or 0}")
                    progress_cb(min(99.0, max(0.0, seconds / total_duration * 100)))
        try:
            proc_handle.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc_handle.kill()
            proc_handle.wait()
    except BaseException:
        # Cancellation raised by a progress callback must also stop the encoder.
        proc_handle.kill()
        proc_handle.wait()
        raise
    finally:
        proc.forget(proc_handle)
        proc_handle.stderr.close()
        if proc_handle.stdout:
            proc_handle.stdout.close()
    if progress_cb and proc_handle.returncode == 0:
        progress_cb(100.0)
    return RunResult(proc_handle.returncode, "", "".join(stderr_lines[-200:]), cmd)


def run_command(args: Sequence[str], timeout: int | None = None) -> RunResult:
    code, out, err = proc.run(list(args), timeout=timeout)
    return RunResult(code, out, err, list(args))


def ffprobe_json(path: str | Path) -> dict:
    res = run_command(
        [
            ffprobe_path(),
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        timeout=60,
    )
    if not res.ok:
        raise RuntimeError(f"ffprobe gagal untuk {path}: {res.stderr[:300]}")
    return json.loads(res.stdout or "{}")
