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
    *[(str(f), str(Path("ui") / f.parent.relative_to(UI))) for f in UI.rglob("*") if f.is_file() and f.suffix in {".html", ".css", ".js", ".svg", ".png", ".ico", ".woff", ".woff2", ".ttf"}],
    (str(ROOT / "LICENSE"), "."),
    (str(ROOT / "docs" / "licenses"), "licenses"),
    (str(ROOT / "vendor" / "face_detection_yunet_2023mar.onnx"), "vendor"),
    (str(ROOT / "assets" / "logo.png"), "assets"),
]
sd_cpu_bundle = ROOT / "vendor" / "sd-cpp-win-cpu-28b454b.zip"
if sd_cpu_bundle.is_file() and os.name == "nt":
    datas.append((str(sd_cpu_bundle), "vendor"))
binaries = [
    (str(ROOT / "desktop" / "packaging" / "icons" / "studiozai.ico"), "."),
]

ff_dir = os.environ.get("STUDIOZAI_FFMPEG_DIR")
if os.name == "nt" and (ROOT / "vendor" / "qjs.exe").is_file():
    binaries.append((str(ROOT / "vendor" / "qjs.exe"), "bin"))
native_runtime = ROOT / "vendor" / "llama-cpu"
if os.name == "nt" and native_runtime.is_dir():
    for candidate in native_runtime.iterdir():
        if candidate.suffix in {".dll", ".exe"}:
            binaries.append((str(candidate), "bin"))
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
# "requests" dipakai jalur cadangan InnerTube (youtube-transcript-api).
for package in ("cv2", "sentencepiece", "sacremoses", "subword_nmt", "ctranslate2", "faster_whisper", "av", "tokenizers", "onnxruntime", "piper", "yt_dlp", "yt_dlp_ejs", "youtube_transcript_api", "requests", "urllib3", "sherpa_onnx", "sherpa_onnx_core"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    except Exception:  # package not installed in this build environment
        continue
    datas += [
        entry for entry in pkg_datas
        if not entry[1].replace("\\", "/").startswith("youtube_transcript_api/test")
    ]
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
    icon=str(ROOT / "desktop" / "packaging" / "icons" / "studiozai.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="StudioZAI",
)
