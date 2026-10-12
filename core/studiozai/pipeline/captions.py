"""Transkrip instan dari caption YouTube (tanpa mengunduh media).

Pola cheat-clip-pro: caption adalah teks ber-timing yang sudah disediakan
YouTube (KB, detik) — jauh lebih cepat daripada mentranskrip audio lokal
(menit). Dipakai sebagai sumber utama saat mode online; Whisper lokal tetap
jadi cadangan bila video tidak punya caption.

Dua lapis pengambilan, keduanya auto-pindah keluarga alamat IP (lihat
``ytnet``) sehingga tantangan bot YouTube pada satu keluarga tidak
menggugurkan seluruh analisis:

1. yt-dlp CLI subtitle — timing per kata (karaoke), butuh pemutar video.
2. youtube-transcript-api (InnerTube) — tanpa word-timing tetapi lolos
   saat jalur pemutar diblokir.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import ytnet


class _CaptionUnavailable(RuntimeError):
    """Caption memang tidak tersedia (bukan masalah jaringan)."""


def video_id_of(url: str) -> str:
    """Ekstrak ID video YouTube dari URL apa pun (watch/shorts/embed/live/youtu.be)."""
    match = re.search(r"(?:v=|/shorts/|/embed/|/live/|/v/|youtu\.be/)([\w-]{11})", url)
    if match:
        return match.group(1)
    match = re.search(r"([\w-]{11})", url)
    return match.group(1) if match else ""


def fetch_captions(
    url: str,
    out_dir: str | Path,
    lang: str | None = None,
    cookies: str | Path | None = None,
    progress_cb: Any | None = None,
) -> dict[str, Any]:
    """Unduh HANYA subtitle (vtt/srt) lalu parse jadi segmen.

    Mencoba (1) API yt-dlp in-process per keluarga IP lalu (2) InnerTube
    API per keluarga IP. Tanpa mengunduh media apa pun.

    Mengembalikan {"language": ..., "source": "youtube",
    "segments": [{"start","end","text","words": [...]}]}.
    Melempar RuntimeError bila tidak ada caption yang bisa dipakai.
    """
    errors: list[str] = []

    for family in ytnet.get_family_order():
        try:
            return _fetch_via_ytdlp(url, out_dir, lang, cookies, progress_cb, family)
        except Exception as exc:
            errors.append(_note("yt-dlp", family, exc))
            if not ytnet.is_family_retryable(exc) and not isinstance(exc, _CaptionUnavailable):
                raise RuntimeError(ytnet.friendly_error("mengambil caption", exc)) from exc

    for family in ytnet.get_family_order():
        try:
            return _fetch_via_api(url, lang, progress_cb, family)
        except Exception as exc:
            errors.append(_note("innerTube", family, exc))
            if not ytnet.is_family_retryable(exc) and not isinstance(exc, _CaptionUnavailable):
                raise RuntimeError(ytnet.friendly_error("mengambil caption", exc)) from exc

    detail = "; ".join(dict.fromkeys(errors))[:400]
    if any("tidak memiliki caption" in note or "no transcript" in note.lower() for note in errors):
        raise RuntimeError("video ini tidak memiliki caption")
    raise RuntimeError(ytnet.friendly_error("mengambil caption", RuntimeError(detail)))


def _note(tier: str, family: str, exc: Exception) -> str:
    first = (str(exc).splitlines()[0] if str(exc) else type(exc).__name__)[:150]
    return f"{tier}/{family}: {first}"


def _fetch_via_ytdlp(
    url: str,
    out_dir: str | Path,
    lang: str | None,
    cookies: str | Path | None,
    progress_cb: Any | None,
    family: str,
) -> dict[str, Any]:
    """Unduh subtitle lewat API yt-dlp dalam proses (skip_download + sub).

    Dipakai API in-process, BUKAN ``sys.executable -m yt_dlp``: pada build
    PyInstaller ``sys.executable`` adalah StudioZAI.exe sehingga subproses
    itu tidak akan pernah berjalan. ``ignoreerrors`` dipasang agar satu
    track gagal (mis. HTTP 429 pada bahasa kedua) tidak membatalkan track
    lain yang sudah berhasil.
    """
    try:
        import yt_dlp  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "yt-dlp belum terpasang. Jalankan: pip install -e \"core[media]\""
        ) from exc

    out_dir = Path(out_dir)
    target = out_dir / "captions"
    target.mkdir(parents=True, exist_ok=True)
    for stale in (*target.glob("*.vtt"), *target.glob("*.srt")):
        stale.unlink(missing_ok=True)

    want = (lang or "auto").lower().split("-", 1)[0]
    langs = [w for w in dict.fromkeys([want, "id", "en"]) if w and w != "auto"]
    options: dict[str, Any] = {
        "outtmpl": str(target / "%(title).80B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": langs or ["en"],
        "subtitlesformat": "vtt/best",
        "ignoreerrors": True,
        "socket_timeout": 60,
        "retries": 2,
        **ytnet.js_runtime_options(),
        **ytnet.family_options(family),
    }
    if cookies:
        options["cookiefile"] = str(cookies)
    if progress_cb:
        progress_cb(10.0, "mengambil subtitle YouTube")
    with yt_dlp.YoutubeDL(options) as ydl:
        result = ydl.extract_info(url, download=True)

    files = sorted(target.glob("*.vtt")) + sorted(target.glob("*.srt"))
    if not files:
        if result is None:
            # ignoreerrors menelan alasannya; umumkan sebagai hambatan
            # jaringan supaya keluarga IP berikutnya dicoba.
            raise RuntimeError("subtitle gagal diunduh (kemungkinan diblokir)")
        raise _CaptionUnavailable("video ini tidak memiliki caption")
    picked = _pick_caption_file(files, lang)
    language = _language_of(picked, lang)
    segments = parse_subtitle_file(picked)
    for path in files:
        path.unlink(missing_ok=True)
    if not segments:
        raise _CaptionUnavailable("caption kosong")
    ytnet.mark_family_working(family)
    if progress_cb:
        progress_cb(100.0, f"{len(segments)} baris caption")
    return {
        "language": language,
        "source": "youtube",
        "segments": segments,
        "text": " ".join(s["text"] for s in segments).strip(),
    }


def _fetch_via_api(
    url: str,
    lang: str | None,
    progress_cb: Any | None,
    family: str,
) -> dict[str, Any]:
    """InnerTube API (youtube-transcript-api) — cadangan saat jalur pemutar diblokir."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import NoTranscriptFound
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise _CaptionUnavailable("youtube-transcript-api belum terpasang") from exc

    video_id = video_id_of(url)
    if not video_id:
        raise _CaptionUnavailable("bukan URL video YouTube")

    want = (lang or "auto").lower().split("-", 1)[0]
    languages = [code for code in dict.fromkeys([want, "id", "en"]) if code and code != "auto"]

    session = ytnet.family_session(family, timeout=20.0)
    api = YouTubeTranscriptApi(http_client=session) if session is not None else YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=languages)
    except NoTranscriptFound:
        # Bahasa pilihan tidak tersedia: pakai track mana pun yang ada
        # (prioritas id/en). Error jaringan sengaja dibiarkan merambat
        # agar pencarian keluarga IP di lapisan atas tetap jalan.
        found = None
        for track in api.list(video_id):
            found = track
            if str(getattr(track, "language_code", "")).lower().split("-")[0] in {"id", "en"}:
                break
        if found is None:
            raise _CaptionUnavailable("video ini tidak memiliki caption")
        fetched = found.fetch()

    segments: list[dict[str, Any]] = []
    for snippet in fetched.snippets:
        text = _clean_cue_text(str(snippet.text or ""))
        if not text:
            continue
        start = float(snippet.start or 0.0)
        end = start + max(0.1, float(snippet.duration or 0.0))
        segments.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "text": text,
            "words": [],
        })
    if not segments:
        raise _CaptionUnavailable("caption kosong")
    ytnet.mark_family_working(family)
    if progress_cb:
        progress_cb(100.0, f"{len(segments)} baris caption (InnerTube)")
    return {
        "language": (getattr(fetched, "language_code", "") or want or "auto"),
        "source": "youtube",
        "segments": segments,
        "text": " ".join(s["text"] for s in segments).strip(),
    }


def _pick_caption_file(files: list[Path], lang: str | None) -> Path:
    """Manual sesuai bahasa > Inggris > auto > apa pun yang ada."""
    want = (lang or "auto").lower().split("-", 1)[0]
    scored: list[tuple[int, Path]] = []
    for path in files:
        name = path.stem.lower()
        language = _language_of(path, "unknown").split("-", 1)[0]
        is_auto = "auto" in name or "automatic" in name
        if want and want != "auto" and want == language and not is_auto:
            rank = 0
        elif language == "en" and not is_auto:
            rank = 1
        elif not is_auto:
            rank = 2
        elif want == language or (want == "auto"):
            rank = 3
        else:
            rank = 4
        scored.append((rank, path))
    scored.sort(key=lambda row: (row[0], row[1].name))
    return scored[0][1]


def _language_of(path: Path, fallback: str | None) -> str:
    name = path.stem
    match = re.search(r"\.([a-zA-Z]{2,3}(?:-[a-zA-Z]{2,4})?)$", name)
    if match:
        return match.group(1).lower()
    return (fallback or "auto").lower().split("-", 1)[0] or "unknown"


VTT_TIME = re.compile(
    r"(?:(?P<sh>\d+):)?(?P<sm>\d{1,2}):(?P<ss>\d\d)[.,](?P<sms>\d+)"
    r"\s*-->\s*"
    r"(?:(?P<eh>\d+):)?(?P<em>\d{1,2}):(?P<es>\d\d)[.,](?P<ems>\d+)"
)
SRT_TIME = re.compile(
    r"(?P<sh>\d+):(?P<sm>\d\d):(?P<ss>\d\d),(?P<sms>\d+)"
    r"\s*-->\s*"
    r"(?P<eh>\d+):(?P<em>\d\d):(?P<es>\d\d),(?P<ems>\d+)"
)
WORD_TIME = re.compile(r"<(?:(\d+):)?(\d{1,2}):(\d\d)[.,](\d+)>")
TAG_RE = re.compile(r"</?[^>]+>")


def _to_seconds(h: str | None, m: str, s: str, ms: str) -> float:
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms[:3].ljust(3, "0")) / 1000.0


def _clean_cue_text(raw: str) -> str:
    text = WORD_TIME.sub(" ", raw)
    text = TAG_RE.sub("", text)
    return re.sub(r"\s+", " ", text.replace("\n", " ").strip())


def _cue_words(raw: str, start: float, end: float) -> list[dict[str, Any]]:
    """Timing per kata dari timestamp inline <00:00.000> bila ada."""
    marks = [(m.start(), _to_seconds(*m.groups())) for m in WORD_TIME.finditer(raw)]
    if not marks:
        return []
    words: list[dict[str, Any]] = []
    boundaries = [(0, start), *[(match.end(), _to_seconds(*match.groups())) for match in WORD_TIME.finditer(raw)], (len(raw), end)]
    for index, (position, timestamp) in enumerate(boundaries[:-1]):
        next_position, next_time = boundaries[index + 1]
        chunk = WORD_TIME.sub("", raw[position:next_position])
        tokens = _clean_cue_text(chunk).split()
        if not tokens:
            continue
        if len(tokens) != 1 or not start <= timestamp < next_time <= end:
            return []
        words.append({"word": tokens[0], "start": round(timestamp, 3), "end": round(next_time, 3)})
    return words


def parse_subtitle_file(path: str | Path) -> list[dict[str, Any]]:
    """Parse VTT/SRT jadi segmen {start,end,text,words} (word timing bila ada).

    Caption otomatis YouTube memakai rolling window: tiap cue mengulang
    baris terakhir window sebelumnya (plus cue 10 ms berisi ulangan polos)
    lalu menambah baris baru ber-timing. Tanpa pembuangan ulangan itu,
    transkrip membengkak ~50% dan timing per kata meleset. Karena itu
    baris pembuka cue hanya dipertahankan bila bukan salinan akhir baris
    yang sudah diterima (pencocokan lokal — ucapan berulang yang asli di
    bagian lain video tetap dipertahankan).
    """
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    pattern = VTT_TIME if Path(path).suffix.lower() == ".vtt" else SRT_TIME
    segments: list[dict[str, Any]] = []
    history: list[str] = []  # baris teks yang sudah diterima, berurutan
    for match in pattern.finditer(text):
        start = _to_seconds(match.group("sh"), match.group("sm"),
                            match.group("ss"), match.group("sms"))
        end = _to_seconds(match.group("eh"), match.group("em"),
                          match.group("es"), match.group("ems"))
        if end <= start:
            continue
        tail = text[match.end():]
        # Pengaturan cue VTT (align/position) menempel di baris timestamp —
        # buang sampai newline pertama, lalu ambil satu blok cue.
        first_break = tail.find("\n")
        body = tail[first_break + 1:] if first_break != -1 else ""
        body = body.split("\n\n", 1)[0]
        # Baris nomor urut SRT (mis. "12\n00:00...") bukan bagian teks.
        pairs: list[tuple[str, str]] = []
        for line in body.splitlines():
            if not line.strip() or re.fullmatch(r"\d+", line.strip()):
                continue
            cleaned = _clean_cue_text(line)
            if cleaned:
                pairs.append((line, cleaned))
        if not pairs:
            continue
        texts = [cleaned for _line, cleaned in pairs]
        # Buang prefiks yang hanya mengulang akhir riwayat (rolling window).
        drop = 0
        for size in range(min(len(texts), len(history)), 0, -1):
            if history[-size:] == texts[:size]:
                drop = size
                break
        kept = pairs[drop:]
        if not kept:
            continue
        raw = "\n".join(line for line, _cleaned in kept)
        history.extend(cleaned for _line, cleaned in kept)
        segments.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "text": " ".join(cleaned for _line, cleaned in kept),
            "words": _cue_words(raw, start, end),
        })
    return segments
