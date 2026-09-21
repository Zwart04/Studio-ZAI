# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Studio ZAI desktop (Windows/Linux).

Build from the repository root:
    pyinstaller desktop/packaging/studiozai.spec --noconfirm

Set STUDIOZAI_FFMPEG_DIR to the folder holding ffmpeg(.exe)/ffprobe(.exe) to
ship them inside the package (recommended for a self-contained build).
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = next(
    (
        candidate
        for candidate in [Path(SPECPATH).resolve(), *Path(SPECPATH).resolve().parents]
        if (candidate / "core" / "studiozai").is_dir() and (candidate / "ui").is_dir()
    ),
    Path(SPECPATH).resolve().parent,
)
CORE = ROOT / "core"
UI = ROOT / "ui"

datas = [
    (str(CORE / "studiozai" / "models" / "registry.json"), "studiozai/models"),
    (str(UI), "ui"),
]
binaries = []

ff_dir = os.environ.get("STUDIOZAI_FFMPEG_DIR")
if ff_dir:
    for name in ("ffmpeg.exe", "ffprobe.exe", "ffmpeg", "ffprobe"):
        candidate = Path(ff_dir) / name
        if candidate.exists():
            binaries.append((str(candidate), "bin"))

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "studiozai.pipeline.download",
    "studiozai.pipeline.transcribe",
    "studiozai.pipeline.voice",
    "engineio.async_drivers.threading",
]

# Binary-heavy packages that PyInstaller cannot infer on its own.
for package in ("ctranslate2", "faster_whisper", "av", "tokenizers", "onnxruntime", "piper", "yt_dlp"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    except Exception:  # package not installed in this build environment
        continue
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

a = Analysis(
    [str(ROOT / "desktop" / "launcher.py")],
    pathex=[str(CORE)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "torch",
        "torchaudio",
        "chatterbox",
        "mediapipe",
        "cv2",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="StudioZAI",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="StudioZAI",
)
