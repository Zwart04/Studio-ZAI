"""Guard real voice/language choices and file-format handling."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from studiozai.models import manager
from studiozai.pipeline import voice


def test_commercial_voice_recommendations_do_not_include_restricted_models():
    entries = {item["id"]: item for item in manager.load_registry() if item["kind"] in {"tts", "clone"}}
    assert entries["piper-en_US-ryan-medium"]["commercial_use"] == "restricted"
    assert entries["piper-en_US-lessac-medium"]["commercial_use"] == "restricted"
    assert entries["piper-en_US-ljspeech-medium"]["commercial_use"] == "allowed"
    assert entries["supertonic-3-int8"]["commercial_use"] == "allowed"
    assert entries["chatterbox-id-finetune"]["size_mb"] >= 2000
    assert all(not item.get("recommended") for item in entries.values()
               if item["commercial_use"] != "allowed")
    assert "piper-en_US-lessac-medium" not in {item["id"] for item in voice.tts_models()}
    assert "piper-en_US-ryan-medium" not in {item["id"] for item in voice.tts_models()}
    assert {item["id"] for item in voice.clone_models()} == {
        "chatterbox-id-finetune", "zipvoice-zh-en",
    }


def test_zipvoice_cannot_be_used_for_indonesian(tmp_path):
    sample = tmp_path / "saya.mp3"
    sample.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="English/Mandarin"):
        voice.clone_speak("Halo", tmp_path / "out.wav", sample=sample,
                          language="id", model_id="zipvoice-zh-en")


def test_chatterbox_converts_non_wav_sample_before_clone(monkeypatch, tmp_path):
    sample = tmp_path / "suara.m4a"
    sample.write_bytes(b"fixture")
    target = tmp_path / "clone.wav"
    seen = {}

    class FakeModel:
        sr = 24000

        def generate(self, text, audio_prompt_path):
            seen["text"] = text
            seen["sample"] = audio_prompt_path
            assert audio_prompt_path.endswith(".reference.wav")
            assert (tmp_path / "clone.reference.wav").exists()
            return b"wav"

    def convert(args, timeout):
        assert args[1] == str(sample)
        assert args[-1] == str(target.with_suffix(".reference.wav"))
        (tmp_path / "clone.reference.wav").write_bytes(b"normalized")
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(voice, "_load_chatterbox", lambda model_id, language: (FakeModel(), "cpu"))
    monkeypatch.setattr(voice.ffmpeg, "run_ffmpeg", convert)
    monkeypatch.setattr(voice, "duration_of", lambda _path: 8.0)
    monkeypatch.setitem(sys.modules, "torchaudio", SimpleNamespace(
        save=lambda path, wav, rate: target.write_bytes(wav)))

    assert voice.clone_speak("Selamat pagi", target, sample=sample,
                             language="id", model_id="chatterbox-id-finetune") == target
    assert seen["text"] == "Selamat pagi"
    assert target.read_bytes() == b"wav"
    assert not (tmp_path / "clone.reference.wav").exists()
