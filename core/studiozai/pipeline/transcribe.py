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
        ModelCache[key] = WhisperModel(size, device=device, compute_type=compute_type)
    return ModelCache[key]


def transcribe(
    media_path: str | Path,
    model_id: str = "whisper-small-int8",
    lang: str | None = None,
    progress_cb: ProgressCb | None = None,
) -> dict[str, Any]:
    model = load_model(model_id)
    if progress_cb:
        progress_cb(5.0, "memuat model ASR")
    segments_iter, info = model.transcribe(
        str(media_path),
        language=None if lang in (None, "auto") else lang,
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
    )
    total = float(getattr(info, "duration", 0.0) or 0.0)
    segments: list[dict[str, Any]] = []
    for segment in segments_iter:
        words = [
            {"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
            for w in (segment.words or [])
            if w.word.strip()
        ]
        segments.append(
            {
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": segment.text.strip(),
                "words": words,
            }
        )
        if progress_cb and total:
            progress_cb(min(95.0, segment.end / total * 100), "menranskripsi audio")

    transcript = {
        "language": getattr(info, "language", lang) or lang or "unknown",
        "language_probability": round(float(getattr(info, "language_probability", 0.0) or 0), 3),
        "duration": round(total, 3),
        "model": model_id,
        "segments": segments,
        "text": " ".join(s["text"] for s in segments).strip(),
    }
    if progress_cb:
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
