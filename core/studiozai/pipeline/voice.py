"""Voice: Piper TTS (ID/EN, ultra light) and Chatterbox zero-shot cloning."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .. import models
from ..utils import ffmpeg

ProgressCb = Callable[[float, str], None]

LANG_DEFAULT_VOICE = {
    "id": "piper-id_ID-news_tts-medium",
    "en": "piper-en_US-lessac-medium",
}

_CHATTERBOX_CACHE: dict[str, Any] = {}


def tts_models() -> list[dict[str, Any]]:
    return models.manager.models_by_kind("tts")


def clone_models() -> list[dict[str, Any]]:
    return models.manager.models_by_kind("clone")


def default_voice(lang: str = "id") -> str:
    return LANG_DEFAULT_VOICE.get(lang, LANG_DEFAULT_VOICE["id"])


def piper_available() -> bool:
    try:
        from piper.voice import PiperVoice  # noqa: F401
    except ImportError:
        return False
    return True


def voice_files(voice_id: str) -> tuple[Path, Path | None]:
    directory = models.manager.model_dir(voice_id)
    onnx = next(iter(sorted(directory.glob("*.onnx"))), None)
    if onnx is None:
        raise FileNotFoundError(
            f"model suara {voice_id} belum terpasang. Unduh dari halaman Model."
        )
    config = onnx.with_suffix(onnx.suffix + ".json")
    return onnx, (config if config.exists() else None)


def synthesize(
    text: str,
    out_path: str | Path,
    voice_id: str | None = None,
    lang: str = "id",
    progress_cb: ProgressCb | None = None,
) -> Path:
    """Piper text-to-speech. Fast on CPU, no cloning."""
    if not text.strip():
        raise ValueError("teks kosong")
    voice_id = voice_id or default_voice(lang)
    if not piper_available():
        raise RuntimeError("piper-tts belum terpasang. Jalankan: pip install -e \"core[tts]\"")
    from piper.voice import PiperVoice  # type: ignore

    onnx, config = voice_files(voice_id)
    if progress_cb:
        progress_cb(10.0, f"memuat suara {onnx.stem}")
    voice = PiperVoice.load(str(onnx), config_path=str(config) if config else None)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if progress_cb:
        progress_cb(40.0, "membuat suara")
    _write_piper(voice, text, out_path)
    if progress_cb:
        progress_cb(100.0, "suara selesai")
    return out_path


def _write_piper(voice: Any, text: str, out_path: Path) -> None:
    import wave

    with wave.open(str(out_path), "wb") as wav_file:
        if hasattr(voice, "synthesize_wav"):
            voice.synthesize_wav(text, wav_file)
        else:  # older piper releases
            for chunk in voice.synthesize(text):
                wav_file.writeframes(chunk.audio_int16_bytes)


def chatterbox_available() -> bool:
    try:
        from chatterbox.tts import ChatterboxTTS  # noqa: F401
    except ImportError:
        return False
    return True


def _load_chatterbox(model_id: str = "chatterbox-base", language: str = "id") -> Any:
    if not chatterbox_available():
        raise RuntimeError(
            "chatterbox-tts belum terpasang. Jalankan: pip install -e \"core[clone]\""
        )
    device = "cpu"
    try:
        import torch

        if torch.cuda.is_available():
            device = "cuda"
    except ImportError:
        pass
    key = f"{model_id}:{language}:{device}"
    if key in _CHATTERBOX_CACHE:
        return _CHATTERBOX_CACHE[key]
    from chatterbox.tts import ChatterboxTTS  # type: ignore

    model = ChatterboxTTS.from_pretrained(device=device)
    if language == "id" and models.manager.is_installed("chatterbox-id-finetune") and device == "cpu":
        model = _apply_indonesian_checkpoint(model)
    _CHATTERBOX_CACHE[key] = (model, device)
    return _CHATTERBOX_CACHE[key]


def _apply_indonesian_checkpoint(model: Any) -> Any:
    try:
        from safetensors.torch import load_file
    except ImportError:
        return model
    checkpoint = models.manager.model_dir("chatterbox-id-finetune") / "t3_cfg.safetensors"
    if not checkpoint.exists():
        return model
    try:
        model.t3.load_state_dict(load_file(str(checkpoint), device="cpu"))
    except (RuntimeError, KeyError, OSError):
        pass
    return model


def clone_speak(
    text: str,
    out_path: str | Path,
    sample: str | Path | None = None,
    language: str = "id",
    model_id: str = "chatterbox-base",
    progress_cb: ProgressCb | None = None,
) -> Path:
    """Zero-shot cloning: reference sample (>= 6s) plus text -> wav (PerTh watermarked)."""
    if not text.strip():
        raise ValueError("teks kosong")
    if not sample:
        raise ValueError("butuh contoh suara (sample) untuk kloning")
    model, device = _load_chatterbox(model_id, language)
    if progress_cb:
        progress_cb(20.0, f"mengkloning suara ({device})")
    wav = model.generate(text, audio_prompt_path=str(sample))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import torchaudio

        torchaudio.save(str(out_path), wav, model.sr)
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("torchaudio dibutuhkan untuk menyimpan hasil kloning") from exc
    if progress_cb:
        progress_cb(100.0, "suara hasil kloning selesai")
    return out_path


def duration_of(path: str | Path) -> float:
    from . import probe

    return probe.probe(path).duration


def atempo_chain(ratio: float) -> str:
    """Build a chain of atempo filters supporting ratios outside 0.5-2.0."""
    ratio = max(0.25, min(4.0, ratio))
    parts: list[str] = []
    while ratio > 2.0:
        parts.append("atempo=2.0")
        ratio /= 2.0
    while ratio < 0.5:
        parts.append("atempo=0.5")
        ratio /= 0.5
    parts.append(f"atempo={ratio:.4f}")
    return ",".join(parts)


def fit_duration(src: str | Path, target_seconds: float, out: str | Path) -> Path:
    """Time-stretch a voice track so it fits the clip duration."""
    current = duration_of(src)
    if current <= 0 or target_seconds <= 0:
        raise ValueError("durasi tidak valid")
    ratio = current / target_seconds
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if abs(ratio - 1.0) < 0.02:
        result = ffmpeg.run_ffmpeg(["-i", str(src), "-c", "copy", str(out)], timeout=300)
        if result.ok:
            return out
    chain = atempo_chain(ratio)
    result = ffmpeg.run_ffmpeg(["-i", str(src), "-filter:a", chain, str(out)], timeout=900)
    if not result.ok:
        raise RuntimeError(f"gagal menyesuaikan durasi suara: {result.stderr[-300:]}")
    return out


def mix_tracks(
    original: str | Path,
    voice: str | Path,
    out: str | Path,
    original_volume: float = 0.25,
    voice_volume: float = 1.0,
) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    result = ffmpeg.run_ffmpeg(
        [
            "-i",
            str(original),
            "-i",
            str(voice),
            "-filter_complex",
            (
                f"[0:a]volume={original_volume:.3f}[oa];"
                f"[1:a]volume={voice_volume:.3f}[va];"
                f"[oa][va]amix=inputs=2:duration=first:normalize=0[a]"
            ),
            "-map",
            "[a]",
            str(out),
        ],
        timeout=900,
    )
    if not result.ok:
        raise RuntimeError(f"gagal mencampur audio: {result.stderr[-300:]}")
    return out
