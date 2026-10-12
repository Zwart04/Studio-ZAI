"""Verifikasi alur online end-to-end dengan URL nyata (tanpa mock).

Mengukur jalur yang persis dipakai produksi:
  1. /api/link-info      -> metadata (mengungkap pilihan keluarga IP).
  2. /process online     -> audio-only + caption YouTube + analisis momen.
  3. Ringkasan transkrip -> jumlah segmen/kata, adakah duplikat rolling.

Alat ini juga memverifikasi jalur anti-error (auto pindah IPv4/IPv6):
bila bot-block masih mengenai satu keluarga alamat, keluarga lain
harus dijalankan otomatis dan proses tetap selesai.

Contoh:
  python tools/verify_online_e2e.py "https://youtu.be/oPZY7nKtUTc"
  python tools/verify_online_e2e.py "https://youtu.be/oPZY7nKtUTc" --exe

``--exe`` menjalankan EXE hasil packaging (dist/StudioZAI/StudioZAI.exe)
supaya jalur caption ikut teruji di lingkungan beku — di sana subproses
``python -m yt_dlp`` mustahil berjalan, jadi verifikasi in-process saja
tidak cukup.

Tidak pernah mengunduh media penuh; hasil proyek ditulis ke tools/.e2e-tmp.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = next((arg for arg in sys.argv[1:] if not arg.startswith("-")),
           "https://youtu.be/oPZY7nKtUTc")
USE_EXE = "--exe" in sys.argv[1:]
PORT = "8746"
BASE = f"http://127.0.0.1:{PORT}/api"

# Judul klip boleh memuat emoji — paksa stdout UTF-8 (Windows: cp1252).
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]


def request(route: str, payload: dict | None = None, method: str | None = None):
    req = urllib.request.Request(
        BASE + route, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def wait(job_id: str, label: str) -> dict:
    """Polling job sampai selesai; cetak tiap perubahan tahap."""
    started = time.perf_counter()
    last = ""
    while True:
        data = request("/jobs/" + job_id)
        note = f"{data.get('stage') or ''} {data.get('message') or ''}".strip()
        if note and note != last:
            print(f"   [{time.perf_counter() - started:5.1f}s] "
                  f"{data.get('progress', 0):5.1f}% {note}", flush=True)
            last = note
        if data["status"] in ("done", "error", "cancelled"):
            print(f"   -> {label} {data['status']} "
                  f"{time.perf_counter() - started:.1f}s",
                  str(data.get("error") or "")[:300], flush=True)
            return data
        time.sleep(0.4)


def run() -> int:
    print("== 1. link-info ==", flush=True)
    mark = time.perf_counter()
    try:
        info = request("/link-info", {"url": URL}, method="POST")
    except urllib.error.HTTPError as exc:
        print("  ", exc.code, exc.read().decode(errors="replace")[:300], flush=True)
        return 1
    print("  ", f"{time.perf_counter() - mark:.1f}s",
          {"title": info["title"][:50], "duration": info["duration"],
           "formats": len(info["formats"]), "family": info.get("family")},
          flush=True)

    print("== 2. buat proyek (kosong, seperti UI) ==", flush=True)
    project = request("/projects", {"title": "verifikasi online", "source": "",
                                    "lang": "id"}, method="POST")
    print("   id", project["id"], flush=True)

    print("== 3. proses (analisis + klip) ==", flush=True)
    mark = time.perf_counter()
    accepted = request(f"/projects/{project['id']}/process", {
        "source": URL, "online": True, "count": 4, "min_len": 20, "max_len": 60,
        "use_transcript": True, "review_first": True, "analysis_mode": "auto",
        "subtitle_position": "bottom", "canvas": "portrait", "audio_mode": "original",
        "formats": [], "quality": "720p"}, method="POST")
    if "id" in accepted:
        result = wait(accepted["id"], "process")
    else:
        result = {"status": "error", "error": str(accepted)[:400]}
        print("   -> proses ditolak:", result["error"], flush=True)
    total = time.perf_counter() - mark

    detail = request(f"/projects/{project['id']}")
    transcript = detail.get("transcript") or {}
    segments = transcript.get("segments") or []
    words = sum(len(seg.get("words") or []) for seg in segments)
    clips = detail.get("clips") or []

    print(f"\n=== RINGKASAN === total proses {total:.1f}s | status {result.get('status')}")
    print("transkrip:", len(segments), "segmen,", words, "kata, bahasa",
          transcript.get("language"), "source", transcript.get("source"))
    print("klip:", len(clips))
    for clip in clips[:5]:
        print("  -", f"{clip['start']:.0f}-{clip['end']:.0f}s",
              round(clip.get("score") or 0, 2), (clip.get("title") or "")[:60])
    print("cek duplikat berurutan:",
          sum(1 for a, b in zip(segments, segments[1:]) if a["text"] == b["text"]))
    print("cuplikan:", " ".join(seg["text"] for seg in segments)[:220])
    return 0 if result.get("status") == "done" and clips else 1


if not USE_EXE:
    sys.path.insert(0, str(ROOT / "core"))
    from fastapi.testclient import TestClient  # noqa: E402

    from studiozai import config, server  # noqa: E402

    TMP = Path(__file__).resolve().parent / ".e2e-tmp"
    TMP.mkdir(parents=True, exist_ok=True)
    config._base_dir = lambda: TMP  # type: ignore[attr-defined]

    client = TestClient(server.app)
    request = lambda route, payload=None, method=None: (  # noqa: E731
        client.post(BASE + route, json=payload).json()
        if method == "POST" else client.get(BASE + route).json())
    code = run()
    raise SystemExit(code)

# --- jalur EXE beku: jalankan server terpaket lalu tembak API HTTP biasa.
process = subprocess.Popen(
    [str(ROOT / "dist" / "StudioZAI" / "StudioZAI.exe"), "serve",
     "--port", PORT, "--no-browser"],
    env=dict(os.environ), creationflags=subprocess.CREATE_NO_WINDOW)
try:
    for _ in range(120):
        try:
            request("/health")
            break
        except OSError:
            if process.poll() is not None:
                raise SystemExit("server EXE berhenti sebelum siap")
            time.sleep(0.5)
    else:
        raise SystemExit("server EXE tidak pernah siap")
    print("EXE:", json.dumps(request("/health")), flush=True)
    code = run()
finally:
    process.terminate()
raise SystemExit(code)
