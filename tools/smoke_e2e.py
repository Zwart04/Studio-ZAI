import json
import subprocess
import sys
import time
import urllib.request

PORT = "8745"
BASE = f"http://127.0.0.1:{PORT}/api"

p = subprocess.Popen(
    ["dist\\StudioZAI\\StudioZAI.exe", "serve", "--port", PORT, "--no-browser"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.STDOUT,
)
try:
    for _ in range(45):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"{BASE}/health", timeout=3)
            break
        except Exception:
            pass
    else:
        print("E2E GAGAL: server tidak siap")
        sys.exit(1)

    def post(path, payload):
        req = urllib.request.Request(
            BASE + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
        )
        return json.loads(urllib.request.urlopen(req, timeout=180).read())

    def get(path, timeout=30):
        return json.loads(urllib.request.urlopen(BASE + path, timeout=timeout).read())

    project = post("/projects", {"title": "E2E MrBeast chunk", "source": "", "lang": "en"})
    pid = project["id"]
    print("proyek:", pid, flush=True)

    job = post(
        f"/projects/{pid}/process",
        {
            "source": "https://youtu.be/gTKS8SAwUzE",
            "count": 2,
            "min_len": 15,
            "max_len": 40,
            "use_transcript": True,
            "use_llm": False,
            "quality": "480p",
        },
    )
    jid = job["id"]
    print("job:", jid, flush=True)
    deadline = time.time() + 30 * 60
    last_pct = -1
    stall_since = time.time()
    state = {}
    while time.time() < deadline:
        time.sleep(10)
        state = get(f"/jobs/{jid}", timeout=60)
        pct = round(state.get("progress", 0))
        if pct != last_pct:
            print(f"  [{pct}%] {state['stage']} {state.get('message','')}", flush=True)
            last_pct = pct
            stall_since = time.time()
        elif time.time() - stall_since > 300:
            print("E2E GAGAL: progres macet 5 menit di", pct, "%", flush=True)
            sys.exit(1)
        if state["status"] in ("done", "error", "cancelled"):
            break
    print("STATUS:", state.get("status"), flush=True)
    if state.get("status") != "done":
        print("ERROR:", state.get("error"), flush=True)
        print("TRACE:", ((state.get("result") or {}).get("traceback") or "")[-2000:], flush=True)
        sys.exit(1)
    detail = get(f"/projects/{pid}")
    clips = detail.get("clips", [])
    print("klip:", len(clips), flush=True)
    ok = True
    for c in clips:
        dur = round(c["end"] - c["start"], 1)
        has_mp4 = bool((c.get("files") or {}).get("mp4"))
        flag = "" if (15 <= dur <= 40 and has_mp4) else "  <-- BERMASALAH"
        if flag:
            ok = False
        print(f"  klip {c['index']}: {c['start']:.1f}-{c['end']:.1f} ({dur}s) mp4={has_mp4}{flag}", flush=True)
    print("E2E:", "LOLOS" if ok and clips else "GAGAL", flush=True)
    sys.exit(0 if ok and clips else 1)
finally:
    p.terminate()
