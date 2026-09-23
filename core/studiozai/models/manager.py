"""Model registry and hardware-aware model manager."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

REGISTRY_FILE = Path(__file__).with_name("registry.json")
CHUNK = 1024 * 256
ProgressCb = Callable[[float, str], None]

DownloadSpec = dict[str, Any]


def load_registry() -> list[dict[str, Any]]:
    data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return list(data.get("models", []))


def get_model(model_id: str) -> dict[str, Any]:
    for model in load_registry():
        if model["id"] == model_id:
            return model
    raise KeyError(f"model tidak dikenal: {model_id}")


def models_by_kind(kind: str) -> list[dict[str, Any]]:
    return [m for m in load_registry() if m.get("kind") == kind]


# --------------------------------------------------------------------------- hardware


def _ram_gb() -> float | None:
    try:
        if sys.platform == "win32":
            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):  # type: ignore[attr-defined]
                return round(status.ullTotalPhys / 1024**3, 1)
        elif sys.platform == "darwin":
            out = subprocess.run(
                ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=False
            ).stdout.strip()
            return round(int(out) / 1024**3, 1)
        else:
            with open("/proc/meminfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("MemTotal:"):
                        return round(int(line.split()[1]) / 1024**2, 1)
    except (OSError, ValueError, subprocess.SubprocessError, AttributeError):
        return None
    return None


def _gpu_info() -> dict[str, Any]:
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            name, _, mem = out.stdout.strip().splitlines()[0].partition(",")
            return {"vendor": "nvidia", "name": name.strip(), "vram_gb": round(int(mem) / 1024, 1)}
    except (OSError, ValueError, subprocess.SubprocessError, IndexError):
        pass
    return {}


def detect_hardware() -> dict[str, Any]:
    free = shutil.disk_usage(models_dir()).free
    return {
        "os": platform.system().lower() or "unknown",
        "arch": platform.machine(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count() or 1,
        "ram_gb": _ram_gb(),
        "gpu": _gpu_info(),
        "disk_free_gb": round(free / 1024**3, 1),
        "android": False,
    }


def resolve_tier(hw: dict[str, Any], lang: str = "id") -> dict[str, Any]:
    """Pick the lightest model set that comfortably fits the detected device."""
    ram = hw.get("ram_gb") or 0
    reasons: list[str] = []

    if hw.get("android"):
        if ram and ram < 6:
            asr, reasons = "whisper-tiny-int8", ["RAM Android < 6GB -> Whisper tiny"]
        else:
            asr, reasons = "whisper-base-int8", ["Android arm64 -> Whisper base int8"]
        clone = "zipvoice-zh-en" if (ram or 0) >= 6 else None
        if clone:
            reasons.append("RAM >= 6GB -> ZipVoice (cloning EN)")
        else:
            reasons.append("RAM < 6GB -> cloning dimatikan")
    else:
        if ram and ram < 8:
            asr = "whisper-base-int8"
            reasons.append("RAM < 8GB -> Whisper base")
        else:
            asr = "whisper-small-int8"
            reasons.append("RAM >= 8GB -> Whisper small (akurasi ID lebih baik)")
        clone = "zipvoice-zh-en" if (ram or 0) >= 6 else None
        if clone:
            reasons.append("ZipVoice CPU opsional (English / Mandarin, bukan Indonesia)")

    tts = "piper-id_ID-news_tts-medium" if lang == "id" else "piper-en_US-lessac-medium"
    return {"asr": asr, "tts": tts, "clone": clone, "reasons": reasons}


# --------------------------------------------------------------------------- storage


def model_dir(model_id: str) -> Path:
    d = models_dir() / model_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def models_dir() -> Path:
    from ..config import models_dir as _models_dir

    return _models_dir()


def marker_path(model_id: str) -> Path:
    return model_dir(model_id) / ".installed"


def is_installed(model_id: str) -> bool:
    if model_id == "supertonic-3-int8":
        directory = model_dir(model_id)
        required = (
            "duration_predictor.int8.onnx", "text_encoder.int8.onnx",
            "vector_estimator.int8.onnx", "vocoder.int8.onnx",
            "tts.json", "unicode_indexer.bin", "voice.bin",
        )
        return marker_path(model_id).exists() and any(
            all((candidate / name).is_file() for name in required)
            for candidate in (directory, *directory.iterdir()) if candidate.is_dir()
        )
    if model_id == "sdxs-512":
        checkpoint = model_dir(model_id) / "sdxs-512-tinySDdistilled_Q8_0.gguf"
        return (marker_path(model_id).exists() and checkpoint.is_file()
                and checkpoint.stat().st_size == 682847200)
    if model_id == "zipvoice-zh-en":
        directory = model_dir(model_id)
        return marker_path(model_id).exists() and (directory / "vocos_24khz.onnx").is_file() and any(directory.rglob("encoder.int8.onnx"))
    if model_id.startswith("whisper-"):
        directory = model_dir(model_id)
        return (marker_path(model_id).exists()
                and (directory / "model.bin").is_file()
                and (directory / "model.bin").stat().st_size > 1024 * 1024
                and all((directory / name).is_file() for name in ("config.json", "tokenizer.json")))
    return marker_path(model_id).exists()


def installed_size_mb(model_id: str) -> float:
    total = 0
    for path in model_dir(model_id).rglob("*"):
        if path.is_file():
            total += path.stat().st_size
    return round(total / 1024**2, 1)


def status() -> list[dict[str, Any]]:
    rows = []
    for model in load_registry():
        if model.get("experimental") and not is_installed(model["id"]):
            continue
        rows.append(
            {
                **{k: model.get(k) for k in ("id", "kind", "langs", "platforms", "tier", "size_mb", "license", "note", "homepage")},
                "installed": is_installed(model["id"]),
                "installed_mb": installed_size_mb(model["id"]) if is_installed(model["id"]) else 0,
                "requires_pip": model.get("download", {}).get("type") == "lib",
            }
        )
    return rows


# --------------------------------------------------------------------------- download


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def _open_with_resume(
    url: str,
    target: Path,
    existing: int,
) -> tuple[Any, int, str]:
    """Buka koneksi unduhan, tangani resume dengan aman.

    Kembalikan (response, existing_baru, mode). Bila server menolak Range dengan
    HTTP 416 (file lokal sudah lengkap atau lebih besar dari sumbernya), unduhan
    dimulai ulang dari nol. Tanpa ini, resume yang "sudah selesai" akan selalu
    gagal dengan 'HTTP Error 416: Range Not Satisfiable'.
    """
    headers = {"User-Agent": "StudioZAI/1.3"}
    if existing:
        headers["Range"] = f"bytes={existing}-"
    request = urllib.request.Request(url, headers=headers)
    try:
        return urllib.request.urlopen(request, timeout=60), existing, "ab"
    except urllib.error.HTTPError as exc:
        if exc.code != 416 or not existing:
            raise
        target.unlink(missing_ok=True)
        fresh = urllib.request.Request(url, headers={"User-Agent": "StudioZAI/1.3"})
        return urllib.request.urlopen(fresh, timeout=60), 0, "wb"


def _download_file(url: str, target: Path, progress_cb: ProgressCb | None, base: float, span: float) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.stat().st_size if target.exists() else 0
    last_emit = 0.0
    try:
        response, existing, _mode = _open_with_resume(url, target, existing)
        with response:
            mode = "ab" if existing and response.status == 206 else "wb"
            if mode == "wb":
                existing = 0
            total = int(response.headers.get("Content-Length") or 0) + existing
            with target.open(mode) as fh:
                done = existing
                while True:
                    block = response.read(CHUNK)
                    if not block:
                        break
                    fh.write(block)
                    done += len(block)
                    if progress_cb and total and time.time() - last_emit >= 0.25:
                        last_emit = time.time()
                        mb = f"{done / 1024 / 1024:.0f}/{total / 1024 / 1024:.0f} MB"
                        progress_cb(base + span * done / total, f"mengunduh {target.name} · {mb}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"gagal mengunduh {target.name}: {exc}") from exc


def _validate_members(dest: Path, names: list[str]) -> None:
    """Tolak nama anggota arsip yang keluar dari folder tujuan.

    Arsip model diunduh dari internet (HuggingFace/GitHub) sehingga namanya
    tidak boleh dipercaya: path absolut, `..`, atau keluar dari `dest`
    akan dibatalkan sebelum apa pun ditulis ke disk.
    """
    base = dest.resolve()
    for name in names:
        normalized = name.replace("\\", "/")
        if normalized.startswith("/") or (len(normalized) > 1 and normalized[1] == ":") or ".." in normalized.split("/"):
            raise RuntimeError(f"Arsip berisi path tidak aman: {name!r} - unduhan dibatalkan.")
        candidate = (base / normalized).resolve()
        if candidate != base and base not in candidate.parents:
            raise RuntimeError(f"Arsip keluar dari folder tujuan: {name!r} - unduhan dibatalkan.")


def _extract_archive(path: Path, dest: Path) -> None:
    """Ekstrak arsip model dengan penjagaan path traversal."""
    dest = Path(dest)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            _validate_members(dest, [info.filename for info in archive.infolist()])
            archive.extractall(dest)
    elif path.name.endswith((".tar.bz2", ".tar.gz", ".tgz")):
        with tarfile.open(path) as archive:
            members = archive.getmembers()
            _validate_members(dest, [member.name for member in members])
            for member in members:
                if member.issym() or member.islnk():
                    raise RuntimeError("Arsip berisi tautan simbolik - unduhan dibatalkan.")
            # filter='data' (Python 3.12+) menolak path/permission berbahaya.
            if sys.version_info >= (3, 12):
                archive.extractall(dest, members=members, filter="data")
            else:
                archive.extractall(dest, members=members)


def download(model_id: str, progress_cb: ProgressCb | None = None) -> Path:
    """Download all files of a model, verify checksums, then write the install marker."""
    model = get_model(model_id)
    spec: DownloadSpec = model.get("download", {})
    target_dir = model_dir(model_id)
    kind = spec.get("type")

    if kind == "lib":
        if spec.get("provider") == "faster-whisper":
            from faster_whisper.utils import download_model
            if progress_cb:
                progress_cb(5, "mengunduh bobot Whisper; tunggu sampai verifikasi selesai")
            download_model(spec["repo"], output_dir=str(target_dir))
            if not (target_dir / "model.bin").exists():
                raise RuntimeError("Bobot Whisper belum lengkap. Ulangi unduhan.")
        else:
            raise RuntimeError(
                "Model ini memerlukan runtime tambahan dan setup manual. "
                + spec.get("note", "Lihat panduan Model untuk instalasi.")
            )
    elif kind == "files":
        files = spec.get("files", [])
        for index, item in enumerate(files):
            base = index / max(1, len(files)) * 100
            span = 100 / max(1, len(files))
            dest = target_dir / item["name"]
            if dest.exists() and item.get("sha256") and _sha256(dest) == item["sha256"]:
                if progress_cb:
                    progress_cb(base + span, f"{dest.name} sudah ada")
                continue
            _download_file(item["url"], dest, progress_cb, base, span)
            if item.get("sha256"):
                actual = _sha256(dest)
                if actual != item["sha256"]:
                    dest.unlink(missing_ok=True)
                    raise RuntimeError(f"checksum tidak cocok untuk {dest.name}")
    elif kind == "archive":
        archive = target_dir / spec["name"]
        _download_file(spec["url"], archive, progress_cb, 0, 95)
        if spec.get("sha256") and _sha256(archive) != spec["sha256"]:
            archive.unlink(missing_ok=True)
            raise RuntimeError(f"checksum tidak cocok untuk {spec['name']}")
        if progress_cb:
            progress_cb(96, "mengekstrak arsip")
        try:
            _extract_archive(archive, target_dir)
        except (zipfile.BadZipFile, tarfile.TarError, OSError, EOFError) as exc:
            archive.unlink(missing_ok=True)
            raise RuntimeError(f"arsip rusak, unduh ulang: {exc}") from exc
        archive.unlink(missing_ok=True)
    else:
        raise RuntimeError(f"spesifikasi unduhan tidak dikenal untuk {model_id}")

    for item in spec.get("extra_files", []):
        _download_file(item["url"], target_dir / item["name"], progress_cb, 97, 2)
    marker_path(model_id).write_text(
        json.dumps({"id": model_id, "source": spec.get("provider") or spec.get("url", "")}),
        encoding="utf-8",
    )
    if progress_cb:
        progress_cb(100, "terpasang")
    return target_dir


def remove(model_id: str) -> None:
    directory = models_dir() / model_id
    if directory.exists():
        shutil.rmtree(directory, ignore_errors=True)


def verify_all() -> list[str]:
    """Return model ids whose marker exists but whose files are gone/broken."""
    broken: list[str] = []
    for model in load_registry():
        if is_installed(model["id"]) and installed_size_mb(model["id"]) <= 0:
            broken.append(model["id"])
    return broken
