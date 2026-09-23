"""Optional local multilingual TTS wiring; no model download during tests."""

from __future__ import annotations

import sys
import wave
from types import SimpleNamespace

import numpy as np
import pytest

from studiozai.pipeline import voice


def test_supertonic_indonesian_voice_writes_pcm_offline(monkeypatch, tmp_path):
    calls = []

    class GenerationConfig:
        def __init__(self):
            self.extra = {}

    class FakeEngine:
        def generate(self, text, settings):
            calls.append((text, settings.sid, settings.extra["lang"], settings.num_steps))
            return SimpleNamespace(samples=np.array([0, 0.5, -0.5], dtype=np.float32), sample_rate=24000)

    monkeypatch.setitem(sys.modules, "sherpa_onnx", SimpleNamespace(GenerationConfig=GenerationConfig))
    monkeypatch.setattr(voice, "_load_supertonic", lambda: FakeEngine())
    output = tmp_path / "id.wav"
    assert voice.synthesize("Halo Indonesia", output, voice_id="supertonic-3-int8:7", lang="id") == output
    assert calls == [("Halo Indonesia", 7, "id", 8)]
    with wave.open(str(output), "rb") as wav:
        assert (wav.getnchannels(), wav.getframerate(), wav.getnframes()) == (1, 24000, 3)


def test_supertonic_rejects_unknown_preset(tmp_path):
    with pytest.raises(ValueError, match="0–9"):
        voice.synthesize("Hello", tmp_path / "bad.wav", voice_id="supertonic-3-int8:10", lang="en")
