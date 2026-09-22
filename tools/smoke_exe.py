import subprocess
import time
import urllib.request

p = subprocess.Popen(
    ["dist\\StudioZAI\\StudioZAI.exe", "serve", "--port", "8740", "--no-browser"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)
time.sleep(16)
try:
    health = urllib.request.urlopen("http://127.0.0.1:8740/api/health", timeout=10).read().decode()
    print("HEALTH:", health)
    page = urllib.request.urlopen("http://127.0.0.1:8740/", timeout=10).read().decode("utf-8", "replace")
    print("logo:", "/assets/logo.png" in page, "| favicon:", "favicon" in page, "| brand:", "brand-logo" in page)
    print("EXE OK")
except Exception as e:  # noqa: BLE001
    print("GAGAL:", e)
finally:
    p.terminate()
