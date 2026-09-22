import json
import subprocess
import time
import urllib.request

p = subprocess.Popen(
    ["dist\\StudioZAI\\StudioZAI.exe", "serve", "--port", "8743", "--no-browser"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.STDOUT,
)
time.sleep(18)
try:
    body = {"url": "https://youtu.be/gTKS8SAwUzE"}
    req = urllib.request.Request(
        "http://127.0.0.1:8743/api/link-info",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    info = json.loads(urllib.request.urlopen(req, timeout=90).read())
    print("LINK-INFO OK:", info["title"][:60], "|", round(info.get("duration", 0)), "s |", len(info.get("formats", [])), "format")
    voices = json.loads(urllib.request.urlopen("http://127.0.0.1:8743/api/voices", timeout=15).read())
    print("VOICES (installed):", voices)
except Exception as e:  # noqa: BLE001
    print("GAGAL:", e)
finally:
    p.terminate()
