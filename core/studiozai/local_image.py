"""Offline, one-step SDXS image generation on desktop.

The executable is an official, pinned stable-diffusion.cpp CPU release. Its
weights are downloaded on demand, verified by the ordinary model manager, and
never bundled with Studio ZAI. No local HTTP server or cloud key is required.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import threading
import uuid
import zipfile
from pathlib import Path

from . import config
from .models import manager

MODEL_ID = "sdxs-512"
MODEL_FILE = "sdxs-512-tinySDdistilled_Q8_0.gguf"
MODEL_BYTES = 682847200
ENGINE_ZIP = "sd-cpp-win-cpu-28b454b.zip"
ENGINE_SHA256 = "cb55af2f5f112f5ef6a8b2785e25d44b5427714b89acae3f7c6fcf4ba7a72eb0"
_install_lock = threading.Lock()


def _bundled_zip() -> Path | None:
    root = Path(getattr(sys, "_MEIPASS", ""))
    candidates = [root / "vendor" / ENGINE_ZIP,
                  Path(__file__).resolve().parents[2] / "vendor" / ENGINE_ZIP]
    return next((p for p in candidates if p.is_file()), None)


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _engine() -> Path:
    override = os.environ.get("STUDIOZAI_SD_CLI", "").strip()
    if override:
        cli = Path(override)
        if not cli.is_file():
            raise RuntimeError("STUDIOZAI_SD_CLI menunjuk berkas yang tidak ada.")
        return cli
    if sys.platform != "win32":
        installed = shutil.which("sd-cli")
        if installed:
            return Path(installed)
        raise RuntimeError("Pasang stable-diffusion.cpp sd-cli untuk gambar lokal di sistem ini.")

    destination = config.data_dir() / "runtime" / "sd-cpp-28b454b"
    cli = destination / "sd-cli.exe"
    with _install_lock:
        if cli.is_file() and (destination / ".ready").is_file():
            return cli
        archive = _bundled_zip()
        if archive is None:
            raise RuntimeError("Mesin gambar lokal tidak ada dalam paket aplikasi.")
        if _checksum(archive) != ENGINE_SHA256:
            raise RuntimeError("Paket mesin gambar lokal rusak (checksum salah).")
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            if any(Path(name).name != name or name.startswith(("/", "\\")) for name in names):
                raise RuntimeError("Paket mesin gambar lokal berisi path tidak aman.")
            for name in names:
                if name.lower().endswith((".exe", ".dll", ".txt")):
                    with bundle.open(name) as source, (destination / name).open("wb") as target:
                        shutil.copyfileobj(source, target)
        if not cli.is_file():
            raise RuntimeError("Paket mesin gambar lokal tidak lengkap.")
        (destination / ".ready").write_text(ENGINE_SHA256, encoding="ascii")
    return cli


def generate(prompt: str) -> Path:
    clean = prompt.strip()
    if not clean or len(clean) > 2000:
        raise ValueError("Tulis deskripsi gambar (maksimum 2.000 karakter).")
    if not manager.is_installed(MODEL_ID):
        raise RuntimeError("Unduh model SDXS-512 pada halaman Model sebelum membuat gambar lokal.")
    model = manager.model_dir(MODEL_ID) / MODEL_FILE
    if model.stat().st_size != MODEL_BYTES:
        raise RuntimeError("Model gambar tidak lengkap. Unduh ulang SDXS-512.")
    cli = _engine()
    output = config.data_dir() / "images"
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"image-{uuid.uuid4().hex[:12]}.png"
    # The image stays local. List arguments avoid shell expansion of prompts.
    command = [str(cli), "-m", str(model), "-p", clean,
               "--cfg-scale", "1", "--steps", "1", "--sampling-method", "euler_a",
               "-W", "512", "-H", "512", "--vae-tiling", "--diffusion-fa",
               "-t", str(max(1, min(os.cpu_count() or 1, 4))), "-o", str(target)]
    try:
        completed = subprocess.run(command, cwd=cli.parent, capture_output=True,
                                   text=True, errors="replace", timeout=480, check=False)
        if completed.returncode != 0 or not target.is_file():
            detail = (completed.stderr or completed.stdout).strip()[-500:]
            raise RuntimeError(f"Mesin gambar lokal gagal: {detail or 'tidak ada keluaran'}")
        with target.open("rb") as source:
            if source.read(8) != b"\x89PNG\r\n\x1a\n":
                raise RuntimeError("Mesin gambar lokal tidak menghasilkan PNG yang valid.")
        return target
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Pembuatan gambar melebihi 8 menit. Coba perangkat dengan RAM lebih besar.") from exc
    except Exception:
        target.unlink(missing_ok=True)
        raise
