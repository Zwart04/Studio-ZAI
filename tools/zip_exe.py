import os
import shutil
import sys

version = sys.argv[1] if len(sys.argv) > 1 else "1.3.0"
root = os.getcwd()
base = os.path.join(root, "dist", f"StudioZAI-{version}-windows-x64")
zp = base + ".zip"
if os.path.exists(zp):
    os.remove(zp)
shutil.make_archive(base, "zip", os.path.join(root, "dist", "StudioZAI"))
print("zip:", round(os.path.getsize(zp) / 1024 / 1024), "MB")
