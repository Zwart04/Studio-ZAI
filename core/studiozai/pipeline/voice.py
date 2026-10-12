"""Local voice synthesis: Piper, Supertonic 3, and zero-shot cloning."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import RLock
from typing import Any

from .. import models
from ..jobs import bounded_inference
from ..utils import ffmpeg

ProgressCb = Callable[[float, str], None]

LANG_DEFAULT_VOICE = {
    "id": "supertonic-3-int8",
    "en": "piper-en_US-ljspeech-medium",
}

_CHATTERBOX_CACHE: dict[str, Any] = {}
_SUPERTONIC_ENGINE: Any = None
_SUPERTONIC_LOCK = RLock()
SUPERTONIC_ID = "supertonic-3-int8"
SUPERTONIC_FILES = (
    "duration_predictor.int8.onnx", "text_encoder.int8.onnx",
    "vector_estimator.int8.onnx", "vocoder.int8.onnx",
    "tts.json", "unicode_indexer.bin", "voice.bin",
)


def tts_models() -> list[dict[str, Any]]:
    return [m for m in models.manager.models_by_kind("tts") if not m.get("deprecated")]


def clone_models() -> list[dict[str, Any]]:
    return [m for m in models.manager.models_by_kind("clone") if not m.get("deprecated")]


def zipvoice_available() -> bool:
    try:
        import sherpa_onnx  # noqa: F401
        return True
    except ImportError:
        return False


def _zipvoice(text: str, sample: str | Path, reference_text: str, out_path: Path,
              progress_cb: ProgressCb | None) -> Path:
    import wave

    import numpy as np
    import sherpa_onnx

    directory = models.manager.model_dir("zipvoice-zh-en")
    def find(name: str) -> str:
        path = next(directory.rglob(name), None)
        if path is None:
            raise ValueError("Model ZipVoice belum lengkap. Unduh ulang di halaman Model.")
        return str(path)
    if not reference_text.strip():
        raise ValueError("Isi teks yang persis diucapkan di rekaman contoh.")
    if progress_cb:
        progress_cb(10, "memuat ZipVoice CPU")
    tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        zipvoice=sherpa_onnx.OfflineTtsZipvoiceModelConfig(
            tokens=find("tokens.txt"), encoder=find("encoder.int8.onnx"), decoder=find("decoder.int8.onnx"),
            data_dir=find("espeak-ng-data"), lexicon=find("lexicon.txt"), vocoder=find("vocos_24khz.onnx")),
        num_threads=2, provider="cpu")))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = out_path.with_suffix(".reference.wav")
    try:
        converted = ffmpeg.run_ffmpeg(["-i", str(sample), "-t", "30", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(temporary)])
        if not converted.ok:
            raise ValueError("Rekaman contoh tidak dapat dibaca.")
        with wave.open(str(temporary), "rb") as wav:
            samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if len(samples) < 16000:
            raise ValueError("Rekaman contoh terlalu pendek; gunakan 6–30 detik.")
        generation = sherpa_onnx.GenerationConfig()
        generation.reference_audio = samples
        generation.reference_sample_rate = 16000
        generation.reference_text = reference_text
        generation.num_steps = 4
        if progress_cb:
            progress_cb(30, "meniru karakter suara; tunggu sampai audio selesai")
        audio = tts.generate(text, generation)
        if not len(audio.samples):
            raise RuntimeError("Model tidak menghasilkan suara.")
        with wave.open(str(out_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(audio.sample_rate)
            wav.writeframes((np.clip(audio.samples, -1, 1) * 32767).astype(np.int16).tobytes())
    finally:
        temporary.unlink(missing_ok=True)
    if progress_cb:
        progress_cb(100, "suara selesai")
    return out_path


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


def _supertonic_sid(voice_id: str) -> int:
    if voice_id == SUPERTONIC_ID:
        return 0
    try:
        sid = int(voice_id.removeprefix(SUPERTONIC_ID + ":"))
    except ValueError as exc:
        raise ValueError("Pilihan suara Supertonic tidak dikenal.") from exc
    if not 0 <= sid <= 9:
        raise ValueError("Suara Supertonic harus bernomor 0–9.")
    return sid


def _supertonic_directory() -> Path:
    if not models.manager.is_installed(SUPERTONIC_ID):
        raise FileNotFoundError("Unduh Supertonic 3 di halaman Model sebelum membuat suara.")
    root = models.manager.model_dir(SUPERTONIC_ID)
    for directory in (root, *root.iterdir()):
        if directory.is_dir() and all((directory / name).is_file() for name in SUPERTONIC_FILES):
            return directory
    raise FileNotFoundError("Berkas Supertonic 3 belum lengkap. Unduh ulang di halaman Model.")


def _load_supertonic() -> Any:
    global _SUPERTONIC_ENGINE
    if _SUPERTONIC_ENGINE is not None:
        return _SUPERTONIC_ENGINE
    try:
        import sherpa_onnx
    except ImportError as exc:
        raise RuntimeError("sherpa-onnx diperlukan untuk Supertonic 3.") from exc
    directory = _supertonic_directory()
    config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
                duration_predictor=str(directory / "duration_predictor.int8.onnx"),
                text_encoder=str(directory / "text_encoder.int8.onnx"),
                vector_estimator=str(directory / "vector_estimator.int8.onnx"),
                vocoder=str(directory / "vocoder.int8.onnx"),
                tts_json=str(directory / "tts.json"),
                unicode_indexer=str(directory / "unicode_indexer.bin"),
                voice_style=str(directory / "voice.bin"),
            ),
            num_threads=2,
            provider="cpu",
        )
    )
    if not config.validate():
        raise RuntimeError("Konfigurasi Supertonic 3 tidak valid. Coba unduh ulang model.")
    _SUPERTONIC_ENGINE = sherpa_onnx.OfflineTts(config)
    return _SUPERTONIC_ENGINE


def _synthesize_supertonic(
    text: str, out_path: Path, voice_id: str, lang: str,
    progress_cb: ProgressCb | None,
) -> Path:
    # Validate cheaply BEFORE importing the heavy optional sherpa_onnx so
    # invalid voice presets fail fast with ValueError even when the
    # engine is not installed.
    sid = _supertonic_sid(voice_id)
    language = lang.lower().split("-", 1)[0].split("_", 1)[0]
    if language not in {"id", "en"}:
        raise ValueError("Supertonic 3 di Studio ZAI tersedia untuk Indonesia dan English.")
    import wave

    import numpy as np
    import sherpa_onnx

    if progress_cb:
        progress_cb(10.0, "memuat Supertonic 3 lokal")
    with _SUPERTONIC_LOCK:
        engine = _load_supertonic()
        settings = sherpa_onnx.GenerationConfig()
        settings.sid = sid
        settings.num_steps = 8
        settings.speed = 1.0
        settings.extra["lang"] = language
        if progress_cb:
            progress_cb(45.0, "membuat suara lokal")
        audio = engine.generate(text, settings)
    samples = np.asarray(audio.samples, dtype=np.float32)
    if samples.size == 0 or audio.sample_rate <= 0:
        raise RuntimeError("Supertonic 3 tidak menghasilkan audio.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(int(audio.sample_rate))
        wav.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())
    if progress_cb:
        progress_cb(100.0, "suara selesai")
    return out_path


@bounded_inference
def synthesize(
    text: str,
    out_path: str | Path,
    voice_id: str | None = None,
    lang: str = "id",
    progress_cb: ProgressCb | None = None,
) -> Path:
    """Synthesize locally with the selected lightweight Piper/Supertonic voice."""
    if not text.strip():
        raise ValueError("teks kosong")
    voice_id = voice_id or default_voice(lang)
    if voice_id == SUPERTONIC_ID or voice_id.startswith(SUPERTONIC_ID + ":"):
        return _synthesize_supertonic(text, Path(out_path), voice_id, lang, progress_cb)
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


def _load_chatterbox(model_id: str = "chatterbox-id-finetune", language: str = "id") -> Any:
    if model_id not in {"chatterbox-base", "chatterbox-id-finetune"}:
        raise ValueError("Model kloning tidak dikenal.")
    if model_id == "chatterbox-base" and language != "en":
        raise ValueError("Chatterbox dasar hanya mendukung English; pilih model Indonesia untuk Bahasa Indonesia.")
    if model_id == "chatterbox-id-finetune":
        if language != "id":
            raise ValueError("Chatterbox Indonesia hanya mendukung Bahasa Indonesia.")
        if not models.manager.is_installed(model_id):
            raise FileNotFoundError("Unduh checkpoint Chatterbox Indonesia dari halaman Model dahulu.")
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
    if model_id == "chatterbox-id-finetune":
        model = _apply_indonesian_checkpoint(model)
    _CHATTERBOX_CACHE[key] = (model, device)
    return _CHATTERBOX_CACHE[key]


def _apply_indonesian_checkpoint(model: Any) -> Any:
    try:
        from safetensors.torch import load_file
    except ImportError as exc:
        raise RuntimeError("safetensors diperlukan untuk checkpoint Chatterbox Indonesia.") from exc
    checkpoint = models.manager.model_dir("chatterbox-id-finetune") / "t3_cfg.safetensors"
    if not checkpoint.exists():
        raise FileNotFoundError("Checkpoint Chatterbox Indonesia belum lengkap. Unduh ulang model.")
    # Gagal memuat bobot harus menjadi error, bukan diam-diam memakai suara English.
    model.t3.load_state_dict(load_file(str(checkpoint), device="cpu"))
    return model


@bounded_inference
def clone_speak(
    text: str,
    out_path: str | Path,
    sample: str | Path | None = None,
    language: str = "id",
    model_id: str = "zipvoice-zh-en",
    progress_cb: ProgressCb | None = None,
    reference_text: str = "",
) -> Path:
    """Zero-shot cloning from a local recording; ffmpeg accepts common formats."""
    if not text.strip():
        raise ValueError("teks kosong")
    if not sample:
        raise ValueError("butuh contoh suara (sample) untuk kloning")
    sample = Path(sample).expanduser()
    if not sample.is_file():
        raise FileNotFoundError("Rekaman contoh tidak ditemukan. Pilih berkas audio yang masih ada.")
    if model_id == "zipvoice-zh-en":
        if language not in {"en", "zh"}:
            raise ValueError("ZipVoice mendukung English/Mandarin. Gunakan Piper atau suara online untuk Indonesia.")
        return _zipvoice(text, sample, reference_text, Path(out_path), progress_cb)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = out_path.with_suffix(".reference.wav")
    try:
        converted = ffmpeg.run_ffmpeg([
            "-i", str(sample), "-t", "30", "-vn", "-ac", "1", "-ar", "24000",
            "-c:a", "pcm_s16le", str(temporary),
        ], timeout=120)
        if not converted.ok:
            raise ValueError("Rekaman contoh tidak dapat dibaca; coba berkas audio lain.")
        if duration_of(temporary) < 6:
            raise ValueError("Rekaman contoh terlalu pendek; gunakan suara jelas selama 6–30 detik.")
        model, device = _load_chatterbox(model_id, language)
        if progress_cb:
            progress_cb(20.0, f"mengkloning suara ({device})")
        wav = model.generate(text, audio_prompt_path=str(temporary))
    finally:
        temporary.unlink(missing_ok=True)
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
