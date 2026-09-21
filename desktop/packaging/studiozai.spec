# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Studio ZAI desktop (Windows/Linux).

Build from the repository root:
    pyinstaller desktop/packaging/studiozai.spec --noconfirm
"""

import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parents[2]
CORE = ROOT / "core"
UI = ROOT / "ui"

datas = [
    (str(CORE / "studiozai" / "models" / "registry.json"), "studiozai/models"),
    (str(UI), "ui"),
]

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "studiozai.pipeline.download",
    "studiozai.pipeline.transcribe",
    "studiozai.pipeline.voice",
]

a = Analysis(
    [str(ROOT / "desktop" / "launcher.py")],
    pathex=[str(CORE)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PyQt5", "PySide6"],
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
    icon=str(ROOT / "desktop" / "packaging" / "icons" / "studiozai.ico")
    if (ROOT / "desktop" / "packaging" / "icons" / "studiozai.ico").exists()
    else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="StudioZAI",
)
