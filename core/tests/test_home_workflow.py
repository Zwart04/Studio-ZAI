from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from studiozai import config, projects, server, service
from studiozai.execution_policy import check_network, processing
from studiozai.pipeline import transcribe


@pytest.mark.parametrize("value,expected", [("en-US", "en"), ("id_ID", "id"), ("zh-Hant-TW", "zh"), ("pt-BR", "pt"), ("auto", None), ("und", None), ("iw-IL", "he")])
def test_whisper_accepts_audio_track_language(monkeypatch, tmp_path, value, expected):
    seen = {}
    def decode(audio, **kwargs):
        seen.update(kwargs)
        return iter([SimpleNamespace(start=0, end=1, text="hello", words=[])]), SimpleNamespace(duration=1, language=expected or "en")
    monkeypatch.setattr(transcribe, "load_model", lambda _: SimpleNamespace(transcribe=decode))
    monkeypatch.setattr(transcribe, "_decode_audio_array", lambda _: [0])
    transcribe._transcribe_single(tmp_path / "fixture.wav", lang=value)
    assert seen["language"] == expected


def test_transcript_only_preserves_clips_and_never_ranks_or_renders(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    project = projects.Project.create("Transcript fixture")
    project.transcript = {"language": "en-US", "segments": [{"start": 1, "end": 2, "text": "Hello."}]}
    project.clips = [projects.Clip(0, 1, 2, title="Keep my edit")]
    project.save()
    def forbidden(*args, **kwargs):
        pytest.fail("Transcript-only must not rank, transcribe existing captions or render")
    monkeypatch.setattr(service, "generate_clips", forbidden)
    monkeypatch.setattr(service, "render_clip", forbidden)
    monkeypatch.setattr(transcribe, "transcribe", forbidden)
    result = server._process_task(project.id, server.ProcessRequest(source="", task="transcript", processing_mode="local"))(SimpleNamespace(report=lambda *a: None))
    assert result["project"]["execution"]["task"] == "transcript"
    assert result["project"]["clips"][0]["title"] == "Keep my edit"
    response = TestClient(server.app).get(f"/api/projects/{project.id}/transcript.srt")
    assert response.status_code == 200
    assert "00:00:01,000 --> 00:00:02,000" in response.text
    assert "Hello." in response.text


def test_local_model_cannot_call_cloud_but_can_fetch_video():
    with processing("local"):
        check_network("https://youtube.com")
        check_network("http://localhost:1235/v1", inference=True)
        with pytest.raises(ValueError):
            check_network("https://api.openai.com/v1", inference=True)
