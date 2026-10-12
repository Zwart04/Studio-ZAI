"""Benchmark REAL mode online vs full download (angka aktual, bukan mock).

Alur yang diukur = alur produksi sesungguhnya:
  1. fetch_info      -> metadata saja (judul/durasi/format), 0 byte media.
  2. download_audio  -> audio saja untuk transkrip + analisis momen.
  3. download_range  -> HANYA rentang klip (contoh 60 dtk) saat render.

Dibandingkan dengan estimasi ukuran video penuh 720p dari metadata
(tanpa benar-benar mengunduh ratusan MB).

Contoh:
  python tools/bench_online.py "https://www.youtube.com/watch?v=aqz-KE-bpKQ" --start 60 --end 120
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "core"))

from studiozai.pipeline import download as dl  # noqa: E402


def fmt_mb(n: float) -> str:
    return f"{n / 1024 / 1024:.1f} MB"


def estimate_full_720p(info: dict) -> float:
    """Estimasi byte video 720p + audio terbaik dari metadata (tanpa unduh)."""
    formats = info.get("formats") or []
    duration = float(info.get("duration") or 0)
    best_v = best_a = 0.0
    for f in formats:
        if f.get("vcodec") in (None, "none"):
            continue
        height = f.get("height") or 0
        if height > 720:
            continue
        br = f.get("tbr") or f.get("abr") or 0
        if br and float(br) > best_v:
            best_v = float(br)
    for f in formats:
        if f.get("vcodec") not in (None, "none"):
            continue
        br = f.get("abr") or f.get("tbr") or 0
        if br and float(br) > best_a:
            best_a = float(br)
    if not best_v:
        best_v = 2500.0
    if not best_a:
        best_a = 128.0
    return (best_v + best_a) * 1000 / 8 * duration


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--start", type=float, default=60.0)
    ap.add_argument("--end", type=float, default=120.0)
    ap.add_argument("--out", default="tools/.bench-online")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"URL   : {args.url}")
    print(f"Klip  : {args.start:.0f}s - {args.end:.0f}s ({args.end - args.start:.0f} detik)")
    print("-" * 56)

    t0 = time.perf_counter()
    info = dl.fetch_info(args.url)
    t_info = time.perf_counter() - t0
    duration = float(info.get("duration") or 0)
    print(f"1) metadata (fetch_info) : {t_info:.1f}s, 0 byte media")
    print(f"   judul    : {info.get('title')}")
    print(f"   durasi   : {duration:.0f} detik")

    full_est = estimate_full_720p(info)
    print(f"   estimasi video penuh 720p : {fmt_mb(full_est)} (TIDAK diunduh)")

    t0 = time.perf_counter()
    audio = dl.download_audio(args.url, out)
    t_audio = time.perf_counter() - t0
    audio_bytes = Path(audio["path"]).stat().st_size
    print(f"2) audio saja (transkrip)  : {t_audio:.1f}s, {fmt_mb(audio_bytes)}")

    t0 = time.perf_counter()
    seg = dl.download_range(args.url, args.start, args.end, out)
    t_seg = time.perf_counter() - t0
    seg_bytes = Path(seg["path"]).stat().st_size
    print(f"3) rentang klip (render)   : {t_seg:.1f}s, {fmt_mb(seg_bytes)}")

    total = audio_bytes + seg_bytes
    print("-" * 56)
    print(f"TOTAL online : {fmt_mb(total)} dalam {t_info + t_audio + t_seg:.1f}s")
    print(f"HEMAT vs penuh: {fmt_mb(full_est - total)} "
          f"({100.0 * (1 - total / full_est):.1f}% lebih kecil)")
    print(f"File: audio={audio['path']}")
    print(f"      segmen={seg['path']} "
          f"(isi {seg['start']:.0f}-{seg['end']:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
