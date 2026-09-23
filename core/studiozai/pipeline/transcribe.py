"""Speech-to-text with faster-whisper (word level timestamps)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .. import models

ProgressCb = Callable[[float, str], None]
ModelCache: dict[tuple[str, str], Any] = {}

MODEL_ALIASES = {
    "whisper-tiny-int8": "tiny",
    "whisper-base-int8": "base",
    "whisper-small-int8": "small",
    "whisper-medium-int8": "medium",
}


def asr_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    return True


def _device() -> tuple[str, str]:
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return "cuda", "float16"
    except ImportError:
        pass
    return "cpu", "int8"


def load_model(model_id: str = "whisper-small-int8") -> Any:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "faster-whisper belum terpasang. Jalankan: pip install -e \"core[asr]\""
        ) from exc

    size = MODEL_ALIASES.get(model_id, model_id)
    device, compute_type = _device()
    key = (size, device)
    if key not in ModelCache:
        if model_id in MODEL_ALIASES:
            if not models.manager.is_installed(model_id):
                models.manager.download(model_id)
            size = str(models.manager.model_dir(model_id))
        ModelCache[key] = WhisperModel(size, device=device, compute_type=compute_type, local_files_only=True)
    return ModelCache[key]


def transcribe(
    media_path: str | Path,
    model_id: str = "whisper-small-int8",
    lang: str | None = None,
    progress_cb: ProgressCb | None = None,
    chunk_minutes: float = 1.5,
) -> dict[str, Any]:
    """Transkrip dengan chunking agar video panjang tidak macet di tengah jalan.

    faster-whisper memproses file besar sekaligus; pada video 20+ menit proses
    bisa terlihat "menggantung" berjam-jam tanpa progres (bug yang dilaporkan:
    video MrBeast 23 menit macet di ~58%). Dengan chunk 10 menit, tiap potong
    selesai dalam hitungan menit dan progres terus bergerak. Hasil tiap chunk
    digeser waktunya lalu digabung — word timestamps tetap akurat global.
    """
    from ..utils import ffmpeg as ffmpeg_utils

    media_path = Path(media_path)
    try:
        total_duration = float(ffmpeg_utils.ffprobe_json(media_path).get("format", {}).get("duration") or 0.0)
    except Exception:  # noqa: BLE001 - durasi opsional, lanjut dengan 0
        total_duration = 0.0

    chunk_seconds = max(60.0, float(chunk_minutes) * 60.0)
    if not total_duration or total_duration <= chunk_seconds * 1.2:
        return _transcribe_single(media_path, model_id, lang, progress_cb, offset=0.0)

    import hashlib

    fingerprint = hashlib.sha1(f"{media_path.resolve()}|{total_duration:.1f}".encode()).hexdigest()[:12]
    cache_dir = media_path.parent / ".transcript-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    all_segments: list[dict[str, Any]] = []
    language = lang or "unknown"
    language_probability = 0.0
    cursor = 0.0
    index = 0
    while cursor < total_duration - 0.5:
        end = min(cursor + chunk_seconds, total_duration)
        chunk_path = cache_dir / f"{fingerprint}_{index:03d}.wav"
        if not chunk_path.exists() or chunk_path.stat().st_size == 0:
            ffmpeg_utils.run_ffmpeg(
                [
                    "-ss",
                    f"{cursor:.3f}",
                    "-t",
                    f"{end - cursor:.3f}",
                    "-i",
                    str(media_path),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-acodec",
                    "pcm_s16le",
                    str(chunk_path),
                ],
                timeout=600,
            )
        base = (cursor / total_duration * 95.0) if total_duration else 0.0
        span = ((end - cursor) / total_duration * 95.0) if total_duration else 0.0

        def _chunk_progress(
            p: float,
            m: str,
            _base: float = base,
            _span: float = span,
            _index: int = index,
        ) -> None:
            if progress_cb:
                progress_cb(
                    min(95.0, _base + p / 100.0 * _span),
                    f"Bagian {_index + 1}/{int((total_duration + chunk_seconds - 1) // chunk_seconds)} · {m}",
                )

        try:
            part = _transcribe_single(chunk_path, model_id, lang, _chunk_progress, offset=cursor)
        finally:
            chunk_path.unlink(missing_ok=True)
        if index == 0:
            language = part.get("language", language)
            language_probability = part.get("language_probability", 0.0)
        all_segments.extend(part.get("segments", []))
        index += 1
        cursor = end

    try:
        for leftover in cache_dir.glob(f"{fingerprint}_*.wav"):
            leftover.unlink(missing_ok=True)
    except OSError:
        pass

    transcript = {
        "language": language,
        "language_probability": round(float(language_probability or 0), 3),
        "duration": round(total_duration, 3),
        "model": model_id,
        "segments": all_segments,
        "text": " ".join(s["text"] for s in all_segments).strip(),
    }
    if progress_cb:
        progress_cb(100.0, "transkrip selesai")
    return transcript


def _transcribe_single(
    media_path: str | Path,
    model_id: str = "whisper-small-int8",
    lang: str | None = None,
    progress_cb: ProgressCb | None = None,
    offset: float = 0.0,
) -> dict[str, Any]:
    if progress_cb:
        progress_cb(0.0, "Memuat model ASR; pemuatan pertama dapat lebih lama")
    model = load_model(model_id)
    if progress_cb:
        progress_cb(0.0, "Menganalisis ucapan awal")
    segments_iter, info = model.transcribe(
        str(media_path),
        language=None if lang in (None, "auto") else lang,
        word_timestamps=True,
        vad_filter=True,
        beam_size=1,
        best_of=1,
        temperature=0.0,
        condition_on_previous_text=False,
    )
    total = float(getattr(info, "duration", 0.0) or 0.0)
    segments: list[dict[str, Any]] = []
    for segment in segments_iter:
        words = [
            {"word": w.word.strip(), "start": round(w.start + offset, 3), "end": round(w.end + offset, 3)}
            for w in (segment.words or [])
            if w.word.strip()
        ]
        segments.append(
            {
                "start": round(segment.start + offset, 3),
                "end": round(segment.end + offset, 3),
                "text": segment.text.strip(),
                "words": words,
            }
        )
        if progress_cb and total:
            progress_cb(min(95.0, segment.end / total * 100), f"Audio {int(offset + segment.end)} detik sudah ditranskripsi")

    transcript = {
        "language": getattr(info, "language", lang) or lang or "unknown",
        "language_probability": round(float(getattr(info, "language_probability", 0.0) or 0), 3),
        "duration": round(total, 3),
        "model": model_id,
        "segments": segments,
        "text": " ".join(s["text"] for s in segments).strip(),
    }
    if progress_cb and offset == 0.0:
        progress_cb(100.0, "transkrip selesai")
    return transcript


def write_transcript(path: str | Path, transcript: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_transcript(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def has_word_timings(transcript: dict[str, Any]) -> bool:
    return any(segment.get("words") for segment in transcript.get("segments", []))


def registry_model_ids() -> list[str]:
    return [m["id"] for m in models.manager.models_by_kind("asr")]
