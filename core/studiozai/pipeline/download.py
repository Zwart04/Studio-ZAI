"""Download media from YouTube / TikTok / Instagram using yt-dlp."""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import ytnet

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
    from ..execution_policy import check_network
    check_network("https://media.invalid")
    try:
        import yt_dlp  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "yt-dlp belum terpasang. Jalankan: pip install -e \"core[media]\""
        ) from exc
    return yt_dlp


def is_supported_host(url: str) -> bool:
    from urllib.parse import urlparse
    host = (urlparse(url).hostname or "").lower()
    return any(host == allowed or host.endswith("." + allowed) for allowed in SUPPORTED_HOSTS)


def fetch_info(
    url: str,
    cookies: str | Path | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Ambil metadata + daftar format tanpa mengunduh. Timeout agar UI tidak macet.

    Otomatis mempindah keluarga alamat IP (IPv4/IPv6) bila YouTube
    menantang salah satunya — lihat ``ytnet``.
    """
    if not is_url(url):
        raise ValueError("bukan URL yang valid")
    yt_dlp = _yt_dlp()

    def attempt(family: str) -> dict[str, Any]:
        options: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": timeout,
            "retries": 2,
            **ytnet.js_runtime_options(),
            **ytnet.family_options(family),
        }
        if cookies:
            options["cookiefile"] = str(cookies)
        with yt_dlp.YoutubeDL(options) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        info, family = ytnet.try_families(attempt)
    except Exception as exc:
        raise RuntimeError(ytnet.friendly_error("membaca link", exc)) from exc
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
        "family": family,
        "formats": formats,
        "audio_tracks": audio_tracks(info),
        "heatmap": extract_heatmap(info),
    }


def extract_heatmap(info: dict[str, Any], limit: int = 300) -> list[dict[str, float]]:
    """Retensi penonton YouTube (heatmap) dari metadata yt-dlp, tanpa unduh.

    Format yt-dlp: [{"start_time":..,"end_time":..,"value":..}]. Nilai
    dinormalisasi 0..1 dan dibatasi jumlahnya agar JSON proyek tetap kecil.
    Tidak semua video menyediakannya — kosong berarti "tidak ada data",
    bukan error.
    """
    raw = info.get("heatmap") or []
    points: list[dict[str, float]] = []
    peak = 0.0
    for row in raw:
        try:
            start = float(row.get("start_time", row.get("start", 0.0)))
            end = float(row.get("end_time", row.get("end", start)))
            value = float(row.get("value", 0.0))
        except (AttributeError, TypeError, ValueError):
            continue
        if end <= start or value < 0:
            continue
        peak = max(peak, value)
        points.append({"start": start, "end": end, "value": value})
    if not points:
        return []
    if peak > 0:
        for point in points:
            point["value"] = round(point["value"] / peak, 4)
    points.sort(key=lambda p: p["start"])
    if len(points) > limit:
        step = len(points) / limit
        points = [points[int(i * step)] for i in range(limit)]
    return points


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


# --------------------------------------------------------------------------- http


# CDN YouTube membatasi client yang tidak menyerupai browser
# (yt-dlp/ffmpeg turun sampai ~30 KB/s). Header browser membuat
# urllib mencapai kecepatan penuh (~20 MB/s pada pengujian).
_BROWSER_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.7,en;q=0.3",
}


def _extract(
    url: str,
    format_selector: str | None,
    cookies: str | Path | None = None,
) -> dict[str, Any]:
    """Baca metadata + format tanpa mengunduh (download=False).

    Otomatis pindah keluarga alamat IP bila salah satunya diblokir (lihat
    ``ytnet``) sehingga unduh audio/rentang tidak ikut macet.
    """
    yt_dlp = _yt_dlp()

    def attempt(family: str) -> dict[str, Any]:
        options: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 60,
            "retries": 2,
            **ytnet.js_runtime_options(),
            **ytnet.family_options(family),
        }
        if format_selector:
            options["format"] = format_selector
        if cookies:
            options["cookiefile"] = str(cookies)
        with yt_dlp.YoutubeDL(options) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        info, _family = ytnet.try_families(attempt)
    except Exception as exc:
        raise RuntimeError(ytnet.friendly_error("membaca link", exc)) from exc
    return info


def _http_open(url: str, byte_range: str | None = None, family: str | None = None):  # type: ignore[return-value]
    """Buka URL CDN dengan header browser, tertambat ke keluarga IP.

    Tanpa tambatan ini yt-dlp bisa lolos lewat satu keluarga alamat
    sementara unduhan byte tetap mencoba keluarga lain yang diblokir.
    ``family=None`` memakai keluarga terakhir yang terbukti baik.
    """
    headers = dict(_BROWSER_HEADERS)
    if byte_range:
        headers["Range"] = byte_range
    request = urllib.request.Request(url, headers=headers)
    return ytnet.opener_for(family).open(request, timeout=120)


# CDN YouTube membatasi tiap koneksi setelah ~2 MB (turun ke
# ~30 KB/s). Unduhan dipotong per 2 MB dengan koneksi baru per
# potongan sehingga kecepatan penuh (~20 MB/s) terjaga.
_CHUNK_BYTES = 2 * 1024 * 1024


def _content_length(url: str, family: str | None = None) -> int:
    """Total byte stream; 0 bila tidak diketahui."""
    with _http_open(url, "bytes=0-0", family) as response:
        content_range = response.headers.get("Content-Range") or ""
        if "/" in content_range:
            return int(content_range.split("/")[-1])
        return int(response.headers.get("Content-Length") or 0)


def _http_copy(
    url: str,
    handle,
    progress_cb: ProgressCb | None = None,
    total: int = 0,
    family: str | None = None,
) -> int:
    """Salin isi URL ke file handle yang terbuka, per potongan 2 MB."""
    done = 0
    position = 0
    whole_file = False
    while not whole_file:
        end = position + _CHUNK_BYTES - 1
        if total:
            end = min(end, total - 1)
        chunk: bytes | None = None
        for _attempt in range(3):
            try:
                with _http_open(url, f"bytes={position}-{end}", family) as response:
                    chunk = response.read()
                    if response.status != 206:
                        # Server mengabaikan Range: isi sudah utuh.
                        whole_file = True
                if chunk is not None:
                    break
            except (urllib.error.URLError, OSError, TimeoutError):
                chunk = None
        if not chunk:
            raise RuntimeError("koneksi unduhan gagal berulang kali")
        handle.write(chunk)
        done += len(chunk)
        position += len(chunk)
        if progress_cb:
            label = f"{done / 1048576:.0f} MB"
            if total:
                label = f"{done / 1048576:.0f}/{total / 1048576:.0f} MB"
            progress_cb(min(99.0, done / total * 100) if total else 99.0, label)
        if total and position >= total:
            break
    return done


def _http_download(
    url: str,
    target: Path,
    progress_cb: ProgressCb | None = None,
    family: str | None = None,
) -> int:
    """Unduh URL ke berkas dengan header browser; kembalikan byte yang ditulis."""
    total = 0
    try:
        total = _content_length(url, family)
    except Exception:  # noqa: BLE001, S110 - missing Content-Length permits streamed download
        pass
    done = 0
    with open(target, "wb") as handle:
        done = _http_copy(url, handle, progress_cb, total, family)
    return done


def _safe_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value or "tanpa-judul").strip()
    return (cleaned or "tanpa-judul")[:80]


def _pick_audio_format(
    info: dict[str, Any],
    audio_lang: str | None = None,
) -> dict[str, Any]:
    """Format audio murni terbaik (m4a lebih dulu), opsional per bahasa."""
    formats = [
        fmt for fmt in info.get("formats") or []
        if fmt.get("acodec") not in (None, "none")
        and fmt.get("vcodec") in (None, "none")
        and fmt.get("url")
    ]
    if not formats:
        raise RuntimeError("tidak ada track audio yang tersedia")
    if audio_lang:
        wanted = audio_lang.lower().replace("_", "-")
        matches = [
            fmt for fmt in formats
            if str(fmt.get("language") or "").lower().replace("_", "-") == wanted
            or str(fmt.get("language") or "").lower().replace("_", "-").startswith(wanted + "-")
        ]
        if not matches:
            raise RuntimeError(f"Track audio bahasa {audio_lang} tidak tersedia. Pilih bahasa lain.")
        formats = matches
    formats.sort(
        key=lambda fmt: (
            str(fmt.get("ext") or "") != "m4a",
            -_audio_bitrate(fmt),
        )
    )
    return formats[0]


def _pick_hls_format(info: dict[str, Any], max_height: int) -> dict[str, Any] | None:
    """Varian HLS (m3u8) muxed video+audio dengan tinggi <= max_height.

    HLS dipakai untuk unduhan rentang:playlist-nya berisi daftar
    segmen ber-durasi, jadi rentang waktu bisa dipilih tanpa
    mengunduh stream dari awal.
    """
    hls = [
        fmt for fmt in info.get("formats") or []
        if fmt.get("protocol") in {"m3u8", "m3u8_native"}
        and fmt.get("vcodec") not in (None, "none")
        and fmt.get("url")
    ]
    if not hls:
        return None
    fitting = [fmt for fmt in hls if (fmt.get("height") or 0) <= max_height]
    pool = fitting or hls
    pool.sort(key=lambda fmt: -(fmt.get("height") or 0))
    return pool[0]


def _hls_parse(playlist: str) -> tuple[str | None, list[tuple[float, str]]]:
    """urai playlist HLS -> (init_segment_url, [(durasi, url_segmen)])."""
    init_url: str | None = None
    entries: list[tuple[float, str]] = []
    lines = playlist.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("#EXT-X-MAP:"):
            match = re.search(r'URI="([^"]+)"', line)
            if match:
                init_url = match.group(1)
        elif line.startswith("#EXTINF:"):
            try:
                duration = float(line.split(":", 1)[1].rstrip(","))
            except ValueError:
                duration = 0.0
            following = index + 1
            while following < len(lines) and (
                not lines[following].strip() or lines[following].startswith("#")
            ):
                following += 1
            if following < len(lines):
                entries.append((duration, lines[following].strip()))
            index = following
        index += 1
    return init_url, entries


def _hls_section(
    playlist_url: str,
    start: float,
    end: float,
    out_dir: Path,
    progress_cb: ProgressCb,
    family: str | None = None,
) -> tuple[Path, float, float]:
    """Unduh segmen HLS yang menutupi [start, end] jadi satu berkas fMP4 mentah.

    Mengembalikan (path, seg_start, seg_end) — batas waktu ACTUAL
    dari isi berkas (boleh sedikit lebih lebar dari [start, end]
    karena menyertakan segmen tetangga sebagai cadangan).
    """
    with _http_open(playlist_url, None, family) as response:
        playlist = response.read().decode("utf-8", "replace")
    init_url, entries = _hls_parse(playlist)
    if not entries:
        raise RuntimeError("playlist HLS kosong")

    # Pilih segmen yang overlap [start, end] plus satu segmen
    # sebelum dan sesudahnya sebagai cadangan batas potongan.
    cursor = 0.0
    spans: list[tuple[float, float, str]] = []
    for duration, seg_url in entries:
        seg_end = cursor + duration
        spans.append((cursor, seg_end, seg_url))
        cursor = seg_end

    chosen: list[tuple[float, float, str]] = []
    for position, (seg_start, seg_end, seg_url) in enumerate(spans):
        if seg_end > start and seg_start < end:
            if position > 0 and not chosen:
                chosen.append(spans[position - 1])
            chosen.append((seg_start, seg_end, seg_url))
            if position + 1 < len(spans):
                chosen.append(spans[position + 1])
    if not chosen:
        # Rentang di luar durasi: pakai segmen terakhir.
        chosen = [spans[-1]]
    # Dedup (segmen tumpang tindih antar iterasi) dan urutkan waktu.
    seen: dict[str, tuple[float, float, str]] = {}
    for span in chosen:
        seen.setdefault(span[2], span)
    chosen = [seen[url] for url in sorted(seen, key=lambda u: seen[u][0])]
    seg_start = chosen[0][0]
    seg_end = chosen[-1][1]

    raw = out_dir / f".section-{start:.0f}-{end:.0f}.raw.mp4"
    written = 0
    with open(raw, "wb") as handle:
        if init_url:
            with _http_open(init_url, None, family) as response:
                init_data = response.read()
            handle.write(init_data)
            written += len(init_data)
        for index, (_s, _e, seg_url) in enumerate(chosen):
            # Segmen bisa beberapa MB: unduh chunked supaya
            # tidak kena batas throttle per koneksi.
            written += _http_copy(seg_url, handle, family=family)
            progress_cb(
                10.0 + 75.0 * (index + 1) / len(chosen),
                f"segmen {index + 1}/{len(chosen)} · {written / 1048576:.0f} MB",
            )
    return raw, seg_start, seg_end


def pick_format_id(formats: list[dict[str, Any]], quality: str) -> str:
    """Pilih format_id yt-dlp dari pilihan kualitas UI."""
    if quality == "audio":
        return "bestaudio[ext=m4a]/bestaudio/best"
    if quality == "best":
        return "bv*+ba/b"
    match = re.search(r"(\d{3,4})p", quality)
    height = int(match.group(1)) if match else 1080
    return f"bv*[height<={height}]+ba/b[height<={height}]/b"


def _make_hook(progress_cb: ProgressCb | None) -> Callable[[dict[str, Any]], None]:
    """Progress hook yt-dlp -> callback; emit maksimal 5x/detik supaya SSE tidak banjir."""
    state: dict[str, Any] = {"last_emit": 0.0}

    def hook(payload: dict[str, Any]) -> None:
        if not progress_cb:
            return
        status = payload.get("status")
        if status == "downloading":
            total = payload.get("total_bytes") or payload.get("total_bytes_estimate") or 0
            done = payload.get("downloaded_bytes") or 0
            percent = (done / total * 100) if total else 0.0
            speed = payload.get("speed") or 0
            eta = payload.get("eta") or 0
            if time.time() - state["last_emit"] < 0.2:
                return
            state["last_emit"] = time.time()
            speed_txt = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "…"
            detail = f"{done / 1024 / 1024:.0f}/{total / 1024 / 1024:.0f} MB · {speed_txt}"
            if eta:
                detail += f" · sisa {int(eta // 60)}:{int(eta % 60):02d}"
            progress_cb(min(99.0, percent), detail)
        elif status == "finished":
            progress_cb(99.0, "menyimpan berkas")
        elif status == "error":
            progress_cb(0.0, "gagal mengunduh")

    return hook


def _base_options(
    out_dir: Path,
    cookies: str | Path | None,
    progress_cb: ProgressCb | None,
    outtmpl: str | None = None,
    family: str | None = None,
) -> dict[str, Any]:
    options: dict[str, Any] = {
        "outtmpl": outtmpl or str(out_dir / "%(title).80s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "progress_hooks": [_make_hook(progress_cb)],
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "continuedl": True,
    }
    options.update(ytnet.js_runtime_options())
    if family:
        options.update(ytnet.family_options(family))
    if cookies:
        options["cookiefile"] = str(cookies)
    return options


def _install_language_selector(ydl: Any, fmt: str, audio_lang: str) -> None:
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


def _resolve_output(path: Path, out_dir: Path) -> Path:
    if path.exists():
        return path
    candidates = sorted(out_dir.glob(f"{path.stem}.*"), key=lambda p: p.stat().st_size)
    if candidates:
        return candidates[-1]
    return path


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

    fmt = format_id or f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b"

    def attempt(family: str) -> dict[str, Any]:
        options = _base_options(out_dir, cookies, progress_cb, family=family)
        options["format"] = fmt
        options["merge_output_format"] = "mp4"
        with yt_dlp.YoutubeDL(options) as ydl:
            if audio_lang:
                _install_language_selector(ydl, fmt, audio_lang)
            info = ydl.extract_info(url, download=True)
            return {"path": _resolve_output(Path(ydl.prepare_filename(info)), out_dir), "info": info}

    try:
        outcome, _family = ytnet.try_families(attempt)
    except Exception as exc:
        raise RuntimeError(ytnet.friendly_error("mengunduh", exc)) from exc
    path = Path(outcome["path"])
    info = outcome["info"]
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
        "heatmap": extract_heatmap(info),
    }


def download_audio(
    url: str,
    out_dir: str | Path,
    cookies: str | Path | None = None,
    progress_cb: ProgressCb | None = None,
    audio_lang: str | None = None,
) -> dict[str, Any]:
    """Download the audio track only — enough for transcript & clip picking.

    Memakai track audio murni (m4a/opus) sehingga transkripsi dan
    analisis momen bisa jalan tanpa mengunduh video yang besar.

    Unduhan lewat urllib dengan header browser: CDN YouTube
    membatasi client non-browser (yt-dlp/ffmpeg) ke ~30 KB/s,
    sementara urllib dengan User-Agent browser mencapai ~20 MB/s.
    """
    if not is_url(url):
        raise ValueError("bukan URL yang valid")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        info = _extract(url, pick_format_id([], "audio"), cookies)
        if info.get("is_live"):
            raise RuntimeError("Live yang masih berjalan perlu rekaman berkas lokal")
        chosen = _pick_audio_format(info, audio_lang)
        target = out_dir / _safe_name(info.get("title") or "audio")
        target = target.with_suffix("." + (chosen.get("ext") or "m4a"))
        # Unduhan byte CDN juga bisa ditolak per keluarga IP — coba
        # bergantian seperti jalur metadata/caption.
        ytnet.try_families(
            lambda family: _http_download(chosen["url"], target, progress_cb, family)
        )
    except Exception as exc:
        raise RuntimeError(ytnet.friendly_error("mengunduh audio", exc)) from exc
    if not target.exists():
        raise RuntimeError("unduhan audio selesai tetapi berkas tidak ditemukan")
    if progress_cb:
        progress_cb(100.0, "audio selesai")
    return {
        "path": str(target),
        "title": info.get("title") or target.stem,
        "duration": float(info.get("duration") or 0.0),
        "webpage_url": info.get("webpage_url") or url,
        "uploader": info.get("uploader") or "",
        "heatmap": extract_heatmap(info),
    }


def _cut_audio_range(audio_path: str | Path, start: float, end: float,
                     out_path: Path) -> Path | None:
    """Potong rentang audio dari berkas lokal (cepat, tanpa jaringan).

    Dipakai untuk memberi suara pada segmen video HLS yang selalu video-only.
    """
    from ..utils import ffmpeg as ffmpeg_utils

    duration = max(0.5, end - start)
    result = ffmpeg_utils.run_ffmpeg(
        ["-ss", f"{max(0.0, start):.3f}", "-i", str(audio_path),
         "-t", f"{duration:.3f}", "-vn", "-c:a", "aac", "-b:a", "128k",
         str(out_path)],
        None,
        None,
        timeout=600,
    )
    if result.ok and out_path.exists() and out_path.stat().st_size > 1024:
        return out_path
    out_path.unlink(missing_ok=True)
    return None


def download_range(
    url: str,
    start: float,
    end: float,
    out_dir: str | Path,
    cookies: str | Path | None = None,
    max_height: int = 720,
    progress_cb: ProgressCb | None = None,
    format_id: str | None = None,
    audio_lang: str | None = None,
    audio_path: str | Path | None = None,
) -> dict[str, Any]:
    """Download ONLY the [start, end] section of a URL.

    Cara kerja (pure-Python, lihat catatan di ``_http_download``):
    membaca playlist HLS (m3u8) dari yt-dlp, memilih segmen fMP4
    yang menutupi rentang waktu, mengunduh init + segmen terpilih
    lewat urllib dengan header browser, lalu meremux-nya jadi MP4
    dengan ffmpeg (lokal, tanpa jaringan). Untuk klip 60 detik dari
    video 80 menit hanya beberapa MB yang ditransfer.

    Potongan presisi: render klip memotong ulang dengan -ss di dalam
    berkas segmen (re-encode), jadi batas segmen 5–7 detik tidak
    memengaruhi ketepatan klip.
    """
    if not is_url(url):
        raise ValueError("bukan URL yang valid")
    if end <= start:
        raise ValueError("rentang tidak valid")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    target = out_dir / f"clip-{start:.0f}-{end:.0f}.mp4"
    try:
        info = _extract(url, None, cookies)
        hls = _pick_hls_format(info, max_height)
        if hls is None:
            raise RuntimeError(
                "format HLS tidak tersedia untuk unduhan rentang; "
                "unduh video penuh dulu sebagai alternatif"
            )
        _report = progress_cb or (lambda _p, _m: None)
        _report(5.0, "membaca daftar segmen")
        # Playlist + segmen juga menempel pada keluarga IP — bila salah
        # satu keluarga ditolak, ulangi dengan keluarga lain otomatis.
        raw, actual_start, actual_end = ytnet.try_families(
            lambda family: _hls_section(hls["url"], start, end, out_dir, _report, family)
        )[0]
        # Segmen video HLS selalu video-only. Bila berkas audio lengkap sudah
        # ada di lokal (mode online selalu mengunduhnya untuk transkrip),
        # potong rentang yang sama dari situ lalu gabungkan — tanpa unduh lagi.
        audio_cut: Path | None = None
        if audio_path:
            candidate = Path(audio_path)
            if candidate.exists():
                _report(80.0, "menyiapkan audio rentang")
                audio_cut = _cut_audio_range(
                    candidate, actual_start, actual_end,
                    out_dir / f"clip-{start:.0f}-{end:.0f}.m4a")
        _report(90.0, "menyimpan berkas")
        from ..utils import ffmpeg as ffmpeg_utils

        if audio_cut is not None:
            result = ffmpeg_utils.run_ffmpeg(
                ["-i", str(raw), "-i", str(audio_cut),
                 "-map", "0:v:0", "-map", "1:a:0",
                 "-c", "copy", "-movflags", "+faststart", str(target)],
                None,
                None,
                timeout=900,
            )
        else:
            result = ffmpeg_utils.run_ffmpeg(
                ["-i", str(raw), "-c", "copy", "-movflags", "+faststart", str(target)],
                None,
                None,
                timeout=900,
            )
        if not result.ok:
            raise RuntimeError(f"remux segmen gagal: {result.stderr[-300:]}")
        raw.unlink(missing_ok=True)
        if audio_cut is not None:
            audio_cut.unlink(missing_ok=True)
    except Exception as exc:
        raise RuntimeError(
            ytnet.friendly_error(f"mengunduh rentang {start:.0f}-{end:.0f}", exc)
        ) from exc
    if not target.exists():
        raise RuntimeError("rentang terunduh tetapi berkas tidak ditemukan")
    duration = 0.0
    try:
        from ..utils import ffmpeg as ffmpeg_utils

        duration = float(
            ffmpeg_utils.ffprobe_json(target).get("format", {}).get("duration") or 0.0
        )
    except Exception as exc:
        raise RuntimeError("Segmen terunduh tidak dapat divalidasi") from exc
    if progress_cb:
        progress_cb(100.0, "selesai")
    return {
        "path": str(target),
        # Batas isi berkas (bisa lebih lebar dari permintaan
        # karena menyertakan segmen tetangga).
        "start": float(actual_start),
        "end": float(actual_end),
        "duration": duration or float(actual_end - actual_start),
        "title": info.get("title") or target.stem,
        "webpage_url": info.get("webpage_url") or url,
    }
