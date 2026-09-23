"""Download media from YouTube / TikTok / Instagram using yt-dlp."""

from __future__ import annotations

import re
import time
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


def fetch_info(
    url: str,
    cookies: str | Path | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Ambil metadata + daftar format tanpa mengunduh. Timeout agar UI tidak macet."""
    if not is_url(url):
        raise ValueError("bukan URL yang valid")
    yt_dlp = _yt_dlp()
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": timeout,
        "retries": 2,
    }
    if cookies:
        options["cookiefile"] = str(cookies)
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        raise RuntimeError(f"gagal membaca link: {exc}") from exc
    formats: list[dict[str, Any]] = []
    for fmt in info.get("formats") or []:
        if not fmt.get("url"):
            continue
        vcodec = str(fmt.get("vcodec") or "none")
        acodec = str(fmt.get("acodec") or "none")
        if vcodec == "none" and acodec == "none":
            continue
        formats.append(
            {
                "format_id": str(fmt.get("format_id") or ""),
                "ext": fmt.get("ext") or "mp4",
                "resolution": fmt.get("resolution") or f"{fmt.get('width') or '?'}x{fmt.get('height') or '?'}",
                "height": fmt.get("height") or 0,
                "fps": fmt.get("fps") or 0,
                "vcodec": vcodec,
                "acodec": acodec,
                "filesize": fmt.get("filesize") or fmt.get("filesize_approx") or 0,
                "tbr": round(float(fmt.get("tbr") or 0), 1),
                "has_video": vcodec != "none",
                "has_audio": acodec != "none",
            }
        )
    formats.sort(key=lambda f: (f["has_video"], f["height"], f["tbr"]))
    return {
        "title": info.get("title") or url,
        "duration": float(info.get("duration") or 0.0),
        "uploader": info.get("uploader") or "",
        "webpage_url": info.get("webpage_url") or url,
        "thumbnail": info.get("thumbnail") or "",
        "formats": formats,
        "audio_tracks": audio_tracks(info),
    }


def audio_tracks(info: dict[str, Any]) -> list[dict[str, str]]:
    """Track audio yang bisa dipilih (video YouTube multi-bahasa / dub resmi).

    yt-dlp menandai track suara terpisah dengan `language` (mis. "id", "en")
    atau `format_note`. Dipakai UI untuk menampilkan pilihan bahasa audio.
    """
    tracks: list[dict[str, str]] = []
    position: dict[str, int] = {}
    best_bitrate: dict[str, float] = {}
    for fmt in info.get("formats") or []:
        if fmt.get("acodec") in (None, "none"):
            continue
        if fmt.get("vcodec") not in (None, "none"):
            continue  # hanya track audio murni
        lang = str(fmt.get("language") or "").strip()
        note = str(fmt.get("format_note") or "").strip()
        key = lang or note
        if not key:
            continue
        bitrate = _audio_bitrate(fmt)
        track = {
            "lang": lang,
            "label": (note or lang) + (f" ({lang})" if lang and note else "")
            + (f" · {bitrate:.0f} kb/s" if bitrate else ""),
            "format_id": str(fmt.get("format_id") or ""),
        }
        if key not in position:
            position[key] = len(tracks)
            best_bitrate[key] = bitrate
            tracks.append(track)
        elif bitrate > best_bitrate[key]:
            best_bitrate[key] = bitrate
            tracks[position[key]] = track
    return tracks


def _audio_bitrate(fmt: dict[str, Any]) -> float:
    """Prefer measured audio bitrate; total bitrate is a fallback for audio-only."""
    for field in ("abr", "tbr"):
        try:
            value = float(fmt.get(field) or 0)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value
    return 0.0


def pick_format_id(formats: list[dict[str, Any]], quality: str) -> str:
    """Pilih format_id yt-dlp dari pilihan kualitas UI."""
    if quality == "audio":
        return "bestaudio[ext=m4a]/bestaudio/best"
    if quality == "best":
        return "bv*+ba/b"
    match = re.search(r"(\d{3,4})p", quality)
    height = int(match.group(1)) if match else 1080
    return f"bv*[height<={height}]+ba/b[height<={height}]/b"


def download(
    url: str,
    out_dir: str | Path,
    cookies: str | Path | None = None,
    max_height: int = 1080,
    progress_cb: ProgressCb | None = None,
    format_id: str | None = None,
    audio_lang: str | None = None,
) -> dict[str, Any]:
    """Download a video and return {path, title, duration, webpage_url}."""
    if not is_url(url):
        raise ValueError("bukan URL yang valid")
    yt_dlp = _yt_dlp()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    state: dict[str, Any] = {"speed": 0.0, "eta": 0, "last_emit": 0.0}

    def hook(payload: dict[str, Any]) -> None:
        if not progress_cb:
            return
        status = payload.get("status")
        if status == "downloading":
            total = payload.get("total_bytes") or payload.get("total_bytes_estimate") or 0
            done = payload.get("downloaded_bytes") or 0
            percent = (done / total * 100) if total else 0.0
            state["speed"] = payload.get("speed") or 0
            state["eta"] = payload.get("eta") or 0
            # emit maksimal 5x/detik supaya SSE tidak banjir
            if time.time() - state["last_emit"] < 0.2:
                return
            state["last_emit"] = time.time()
            speed = state["speed"]
            eta = state["eta"]
            speed_txt = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "…"
            detail = f"{done / 1024 / 1024:.0f}/{total / 1024 / 1024:.0f} MB · {speed_txt}"
            if eta:
                detail += f" · sisa {int(eta // 60)}:{int(eta % 60):02d}"
            progress_cb(min(99.0, percent), detail)
        elif status == "finished":
            progress_cb(99.0, "menyimpan berkas")
        elif status == "error":
            progress_cb(0.0, "gagal mengunduh")

    fmt = format_id or f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b"
    options: dict[str, Any] = {
        "outtmpl": str(out_dir / "%(title).80s.%(ext)s"),
        "format": fmt,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "progress_hooks": [hook],
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "continuedl": True,
    }
    if cookies:
        options["cookiefile"] = str(cookies)

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            if audio_lang:
                selector = ydl.build_format_selector(fmt)

                def selected_language(ctx):
                    # Preserve quality filters while excluding every other audio
                    # language, including audio embedded in muxed formats.
                    wanted = audio_lang.lower().replace("_", "-")
                    allowed = [
                        f for f in ctx["formats"]
                        if f.get("acodec") == "none"
                        or str(f.get("language") or "").lower().replace("_", "-") == wanted
                        or str(f.get("language") or "").lower().replace("_", "-").startswith(wanted + "-")
                    ]
                    audio_only = [
                        f for f in allowed
                        if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none")
                    ]
                    if audio_only:
                        best_audio = max(audio_only, key=_audio_bitrate)
                        allowed = [f for f in allowed if f not in audio_only or f is best_audio]
                    if not any(f.get("acodec") not in (None, "none") for f in allowed):
                        raise ValueError(f"Track audio {audio_lang} tidak tersedia. Pilih track lain atau audio bawaan.")
                    yield from selector({**ctx, "formats": allowed})

                ydl.format_selector = selected_language
            info = ydl.extract_info(url, download=True)
            path = Path(ydl.prepare_filename(info))
            if not path.exists():
                candidates = sorted(out_dir.glob(f"{path.stem}.*"), key=lambda p: p.stat().st_size)
                if candidates:
                    path = candidates[-1]
    except Exception as exc:
        raise RuntimeError(f"gagal mengunduh: {exc}") from exc
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
