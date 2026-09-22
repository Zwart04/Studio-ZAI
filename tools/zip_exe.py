import os
import shutil

root = os.getcwd()
base = os.path.join(root, "dist", "StudioZAI-1.2.0-windows-x64")
zp = base + ".zip"
if os.path.exists(zp):
    os.remove(zp)
shutil.make_archive(base, "zip", os.path.join(root, "dist", "StudioZAI"))
print("zip:", round(os.path.getsize(zp) / 1024 / 1024), "MB")
