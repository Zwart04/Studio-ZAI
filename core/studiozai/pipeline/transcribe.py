"""Speech-to-text with faster-whisper (word level timestamps)."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from .. import models

ProgressCb = Callable[[float, str], None]
ModelCache: dict[tuple, Any] = {}
_MODEL_LOCK = threading.RLock()
_IDLE_TIMER = None
_DEVICE_OVERRIDE = ContextVar("asr_device_override", default=None)


def _schedule_idle_release():
    global _IDLE_TIMER
    from ..jobs import HEAVY_SLOT
    def release():
        if HEAVY_SLOT.acquire(blocking=False):
            try:
                with _MODEL_LOCK:
                    ModelCache.clear()
            finally:
                HEAVY_SLOT.release()
    if _IDLE_TIMER:
        _IDLE_TIMER.cancel()
    _IDLE_TIMER = threading.Timer(60, release)
    _IDLE_TIMER.daemon = True
    _IDLE_TIMER.start()

MODEL_ALIASES = {
    "whisper-tiny-int8": "tiny",
    "whisper-base-int8": "base",
    "whisper-small-int8": "small",
    "whisper-medium-int8": "medium",
}


def normalize_language(lang: str | None) -> str | None:
    value = str(lang or "").strip().lower().replace("_", "-").split("-")[0]
    if value in {"", "auto", "unknown", "und"}:
        return None
    return {"iw": "he", "in": "id", "ji": "yi", "jv": "jw"}.get(value, value)


def asr_available() -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec("faster_whisper") is not None
    except (ImportError, ValueError):
        return False


def _device() -> tuple[str, str]:
    from .. import config
    override = _DEVICE_OVERRIDE.get() or config.load_settings().get("asr_device", "auto")
    if override == "cpu":
        return "cpu", "int8"
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0 and "float16" in ctranslate2.get_supported_compute_types("cuda"):
            return "cuda", "float16"
    except (ImportError, RuntimeError, ValueError):
        pass
    return "cpu", "int8"


def load_model(model_id: str = "whisper-small-int8") -> Any:
    from ..resources import cpu_threads
    if model_id in MODEL_ALIASES and not models.manager.is_installed(model_id):
        raise RuntimeError(f"Model {model_id} belum terpasang. Pilih model terpasang atau unduh melalui halaman Model.")
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "faster-whisper belum terpasang. Jalankan: pip install -e \"core[asr]\""
        ) from exc

    size = MODEL_ALIASES.get(model_id, model_id)
    device, compute_type = _device()
    key = (size, device, model_revision(model_id), cpu_threads())
    if key not in ModelCache:
        if model_id in MODEL_ALIASES:
            if not models.manager.is_installed(model_id):
                raise RuntimeError(f"Model {model_id} belum terpasang. Pilih model terpasang atau unduh melalui halaman Model.")
            size = str(models.manager.model_dir(model_id))
        else:
            if not Path(size).is_dir():
                from faster_whisper.utils import download_model
                size = download_model(size, local_files_only=True)
        if not all((Path(size) / filename).is_file() for filename in ("model.bin", "config.json", "tokenizer.json")):
            raise RuntimeError("Model lokal tidak lengkap; tokenizer diperlukan agar Offline tidak mengakses jaringan.")
        with _MODEL_LOCK:
            if key not in ModelCache:
                ModelCache.clear()
                try:
                    ModelCache[key] = WhisperModel(size, device=device, compute_type=compute_type, local_files_only=True,
                                                  cpu_threads=cpu_threads())
                except (RuntimeError, ValueError):
                    if device != "cuda":
                        raise
                    ModelCache[key] = WhisperModel(size, device="cpu", compute_type="int8", local_files_only=True,
                                                  cpu_threads=cpu_threads())
    return ModelCache[key]


def model_revision(model_id):
    from .. import cache
    directory = models.manager.model_dir(model_id) if model_id in MODEL_ALIASES else Path(model_id)
    return cache.key("asr-model", [cache.file_identity(directory / name) for name in
                     ("model.bin", "config.json", "tokenizer.json") if (directory / name).is_file()])


def transcribe(
    media_path: str | Path,
    model_id: str = "whisper-small-int8",
    lang: str | None = None,
    progress_cb: ProgressCb | None = None,
    chunk_minutes: float = 1.5,
) -> dict[str, Any]:
    lang = normalize_language(lang)
    from ..jobs import inference_slot
    with inference_slot((lambda: progress_cb(0, "menunggu inference")) if progress_cb else None):
        if _IDLE_TIMER:
            _IDLE_TIMER.cancel()
        try:
            try:
                result = _transcribe(media_path, model_id, lang, progress_cb, chunk_minutes)
                if result.get("audio_features") and Path(media_path).is_file():
                    from .. import cache
                    cache.write(cache.key("acoustic-features-v1", cache.file_identity(media_path)), result["audio_features"])
                return result
            except RuntimeError as exc:
                if _device()[0] != "cuda" or not any(word in str(exc).lower() for word in ("cuda", "cublas", "cudnn", "float16")):
                    raise
                ModelCache.clear()
                token = _DEVICE_OVERRIDE.set("cpu")
                try:
                    if progress_cb:
                        progress_cb(0, "CUDA gagal; mencoba CPU INT8")
                    return _transcribe(media_path, model_id, lang, progress_cb, chunk_minutes)
                finally:
                    _DEVICE_OVERRIDE.reset(token)
        finally:
            _schedule_idle_release()


def _transcribe(media_path, model_id="whisper-small-int8", lang=None, progress_cb=None, chunk_minutes=1.5):
    """Bounded audio chunks with global word timestamps and completed-chunk resume."""
    from ..utils import ffmpeg as ffmpeg_utils

    media_path = Path(media_path)
    try:
        total_duration = float(ffmpeg_utils.ffprobe_json(media_path).get("format", {}).get("duration") or 0.0)
    except Exception:  # noqa: BLE001 - durasi opsional, lanjut dengan 0
        total_duration = 0.0

    chunk_seconds = max(60.0, float(chunk_minutes) * 60.0)
    if not total_duration or total_duration <= chunk_seconds * 1.2:
        return _transcribe_single(media_path, model_id, lang, progress_cb, offset=0.0)

    from .. import cache, config
    fingerprint = cache.key("asr-chunks-v4", cache.file_identity(media_path), model_id, model_revision(model_id), lang, chunk_seconds)[:24]
    cache_dir = config.transcript_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    all_segments: list[dict[str, Any]] = []
    language = lang or "unknown"
    language_probability = 0.0
    device = "unknown"
    rms = []
    cursor = 0.0
    index = 0
    while cursor < total_duration - .001:
        end = min(cursor + chunk_seconds, total_duration)
        result_key = cache.key("asr-chunk-result", fingerprint, index, cursor, end)
        completed = cache.read(result_key)
        if completed is not None:
            if index == 0:
                language = completed.get("language", language)
                language_probability = completed.get("language_probability", 0)
            all_segments.extend(completed.get("segments", []))
            device = completed.get("device", device)
            rms.extend(completed.get("audio_features", {}).get("rms", []))
            cursor = end
            index += 1
            if progress_cb:
                progress_cb(cursor / total_duration * 95, "memakai cache transkrip selesai")
            continue
        chunk_path = cache_dir / f"{fingerprint}_{index:03d}.wav"
        if completed is None:
            chunk_path.unlink(missing_ok=True)
            extracted = ffmpeg_utils.run_ffmpeg(
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
                progress_cb=(lambda _, at=cursor: progress_cb(at / total_duration * 95, "menyiapkan audio")) if progress_cb else None,
                timeout=600,
            )
            if not extracted.ok:
                chunk_path.unlink(missing_ok=True)
                raise RuntimeError("Audio bagian ini tidak dapat dibaca; hasil parsial tidak dipakai.")
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
            cache.write(result_key, part)
        finally:
            chunk_path.unlink(missing_ok=True)
        if index == 0:
            language = part.get("language", language)
            language_probability = part.get("language_probability", 0.0)
        all_segments.extend(part.get("segments", []))
        device = part.get("device", device)
        rms.extend(part.get("audio_features", {}).get("rms", []))
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
        "device": device,
        "segments": all_segments,
        "text": " ".join(s["text"] for s in all_segments).strip(),
    }
    if not all_segments and rms and chunk_seconds % .25 == 0:
        transcript["audio_features"] = {"duration": total_duration, "rms": rms}
    if progress_cb:
        progress_cb(100.0, "transkrip selesai")
    return transcript


def _decode_audio_array(media_path: str | Path) -> Any:
    """Decode media ke mono 16 kHz float32 via ffmpeg (tanpa PyAV).

    faster-whisper memanggil ``av.open(..., metadata_errors=...)`` untuk input
    berupa path berkas; parameter itu tidak dikenal av 19+ sehingga semua
    transkrip gagal dengan ``TypeError: open() got an unexpected keyword
    argument 'metadata_errors'``. Dengan mengoper array numpy, jalur av
    dilewati total (pola yang sama dipakai referensi openai-whisper:
    decode ffmpeg -> array -> transcribe).
    """
    import subprocess

    import numpy as np

    from ..utils import ffmpeg as ffmpeg_utils

    proc = subprocess.run(
        [
            ffmpeg_utils.ffmpeg_path(), "-v", "error",
            "-i", str(media_path),
            "-vn", "-ac", "1", "-ar", "16000",
            "-f", "s16le", "-acodec", "pcm_s16le", "-",
        ],
        capture_output=True,
        check=False,
        timeout=900,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if proc.returncode != 0:
        detail = (proc.stderr or b"").decode(errors="ignore")[-300:]
        raise RuntimeError(f"Audio tidak dapat dibaca untuk transkrip: {detail}")
    audio = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    if audio.size == 0:
        raise RuntimeError("Audio kosong, tidak ada yang bisa ditranskripsi")
    return audio


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
    # Oper array (bukan path) agar faster-whisper tidak memanggil av.open
    # yang pecah di av 19+; lihat _decode_audio_array.
    audio = _decode_audio_array(media_path)
    segments_iter, info = model.transcribe(
        audio,
        language=normalize_language(lang),
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
        "device": getattr(getattr(model, "model", None), "device", "cpu"),
        "segments": segments,
        "text": " ".join(s["text"] for s in segments).strip(),
    }
    if not segments:
        import numpy as np
        rms = [float(np.sqrt(np.mean(audio[first:first + 4000] ** 2))) for first in range(0, len(audio), 4000)]
        transcript["audio_features"] = {"duration": len(audio) / 16000, "rms": rms}
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
