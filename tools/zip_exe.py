import os
import re
import shutil
import sys
from pathlib import Path


def default_version() -> str:
    """Ambil versi dari satu sumber kebenaran (core/studiozai/__init__.py)."""
    init = Path(__file__).resolve().parents[1] / "core" / "studiozai" / "__init__.py"
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init.read_text(encoding="utf-8"))
    return match.group(1) if match else "0.0.0"


version = sys.argv[1] if len(sys.argv) > 1 else default_version()
root = os.getcwd()
base = os.path.join(root, "dist", f"StudioZAI-{version}-windows-x64")
zp = base + ".zip"
if os.path.exists(zp):
    os.remove(zp)
shutil.make_archive(base, "zip", os.path.join(root, "dist", "StudioZAI"))
print("zip:", round(os.path.getsize(zp) / 1024 / 1024), "MB")
