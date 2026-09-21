"""Download media from YouTube / TikTok / Instagram using yt-dlp."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

URL_RE = re.compile(r"^https?://", re.IGNORECASE)
ProgressCb = Callable[[float, str], None]

SUPPORTED_HOSTS = (
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "vimeo.com",
)


def is_url(value: str) -> bool:
    return bool(URL_RE.match(value.strip()))


def _yt_dlp():
    try:
        import yt_dlp  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "yt-dlp belum terpasang. Jalankan: pip install -e \"core[media]\""
        ) from exc
    return yt_dlp


def is_supported_host(url: str) -> bool:
    lowered = url.lower()
    return any(host in lowered for host in SUPPORTED_HOSTS)


def download(
    url: str,
    out_dir: str | Path,
    cookies: str | Path | None = None,
    max_height: int = 1080,
    progress_cb: ProgressCb | None = None,
) -> dict[str, Any]:
    """Download a video and return {path, title, duration, webpage_url}."""
    if not is_url(url):
        raise ValueError("bukan URL yang valid")
    yt_dlp = _yt_dlp()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def hook(payload: dict[str, Any]) -> None:
        if not progress_cb:
            return
        status = payload.get("status")
        if status == "downloading":
            total = payload.get("total_bytes") or payload.get("total_bytes_estimate") or 0
            done = payload.get("downloaded_bytes") or 0
            percent = (done / total * 100) if total else 0.0
            progress_cb(min(99.0, percent), "mengunduh video")
        elif status == "finished":
            progress_cb(99.0, "menyimpan berkas")
        elif status == "error":
            progress_cb(0.0, "gagal mengunduh")

    options: dict[str, Any] = {
        "outtmpl": str(out_dir / "%(title).80s.%(ext)s"),
        "format": f"bv*[height<={max_height}][ext=mp4]+ba[ext=m4a]/b[height<={max_height}]/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "progress_hooks": [hook],
    }
    if cookies:
        options["cookiefile"] = str(cookies)

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        path = Path(ydl.prepare_filename(info))
        if not path.exists():
            candidates = sorted(out_dir.glob(f"{path.stem}.*"), key=lambda p: p.stat().st_size)
            if candidates:
                path = candidates[-1]
    if not path.exists():
        raise RuntimeError("unduhan selesai tetapi berkas tidak ditemukan")
    if progress_cb:
        progress_cb(100.0, "selesai")
    return {
        "path": str(path),
        "title": info.get("title") or path.stem,
        "duration": float(info.get("duration") or 0.0),
        "webpage_url": info.get("webpage_url") or url,
        "uploader": info.get("uploader") or "",
    }
