"""Regression checks for audio choice, editor captions, and source geometry."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yt_dlp
from fastapi.testclient import TestClient

from studiozai import config, projects, server, service
from studiozai.pipeline import crop, download, highlight, timeline
from studiozai.utils import ffmpeg


@pytest.mark.parametrize("quality", ["480p", "720p", "best", "audio"])
def test_requested_audio_survives_quality_selection(monkeypatch, tmp_path, quality):
    selections = []

    class FakeYDL(yt_dlp.YoutubeDL):
        def extract_info(self, url, download=True):
            formats = [
                {"format_id": "v480", "height": 480, "width": 854, "vcodec": "avc1", "acodec": "none", "ext": "mp4", "url": "https://example.com/v480"},
                {"format_id": "v1080", "height": 1080, "width": 1920, "vcodec": "avc1", "acodec": "none", "ext": "mp4", "url": "https://example.com/v1080"},
                {"format_id": "id-low", "vcodec": "none", "acodec": "mp4a", "language": "id-ID", "ext": "m4a", "abr": 48, "url": "https://example.com/id-low"},
                {"format_id": "id-high", "vcodec": "none", "acodec": "mp4a", "language": "id-ID", "ext": "m4a", "abr": 160, "url": "https://example.com/id-high"},
                {"format_id": "en", "vcodec": "none", "acodec": "mp4a", "language": "en", "ext": "m4a", "url": "https://example.com/en"},
            ]
            result = list(self.format_selector({"formats": formats, "has_merged_format": False, "incomplete_formats": False}))
            selections.extend(result)
            return {"title": "sample"}

        def prepare_filename(self, info):
            target = tmp_path / "sample.mp4"
            target.touch()
            return str(target)

    monkeypatch.setattr(download, "_yt_dlp", lambda: SimpleNamespace(YoutubeDL=FakeYDL))
    download.download("https://example.com/video", tmp_path, format_id=download.pick_format_id([], quality), audio_lang="id")
    assert selections
    streams = selections[0].get("requested_formats", selections)
    assert [f["format_id"] for f in streams if f["acodec"] != "none"] == ["id-high"]
    if quality == "480p":
        assert next(f for f in streams if f["vcodec"] != "none")["height"] == 480
    with pytest.raises(RuntimeError, match="tidak tersedia"):
        download.download("https://example.com/video", tmp_path, audio_lang="ja")


@pytest.mark.skipif(not ffmpeg.ffmpeg_available(), reason="FFmpeg required")
def test_caption_action_transcribes_only_selected_clip(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    source = tmp_path / "source.wav"
    assert ffmpeg.run_ffmpeg([
        "-f", "lavfi", "-i", "sine=frequency=440:duration=20",
        "-c:a", "pcm_s16le", str(source),
    ]).ok
    project = projects.Project.create("Captions", source=str(source), language="id")
    project.clips = [projects.Clip(index=0, start=10, end=14)]
    project.save()

    def transcribe(audio, **kwargs):
        duration = float(ffmpeg.ffprobe_json(audio)["format"]["duration"])
        assert 3.9 < duration < 4.1  # editor must not transcribe all 20 seconds
        assert kwargs["lang"] == "id"
        return {"segments": [{"start": 0.5, "end": 2, "text": "Halo Indonesia"}]}

    monkeypatch.setattr(service.transcribe, "transcribe", transcribe)
    def submit(kind, title, run):
        return SimpleNamespace(as_dict=lambda: run(None))
    monkeypatch.setattr(server.jobs.MANAGER, "submit", submit)
    result = server.generate_clip_captions(project.id, 0)
    assert result["captions"][0]["start"] == 0.5
    assert projects.load_project(project.id).clip(0).captions[0]["text"] == "Halo Indonesia"
    assert not list(project.root.glob("caption-*"))


def test_caption_action_reuses_project_ai_transcript(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    project = projects.Project.create("Captions", language="id")
    project.clips = [projects.Clip(index=0, start=10, end=14)]
    project.transcript = {"model": "whisper-small-int8", "segments": [
        {"start": 10.5, "end": 12, "text": "Halo Indonesia"},
    ]}
    project.save()
    monkeypatch.setattr(service.transcribe, "transcribe", lambda *_args, **_kwargs: pytest.fail("ASR repeated"))
    assert service.generate_captions_for_clip(project, project.clip(0))[0]["start"] == 0.5


def test_cached_transcript_guides_clips_when_asr_model_is_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    source = tmp_path / "source.mp4"
    source.touch()
    project = projects.Project.create("Speaker", source=str(source), language="id")
    project.duration = 120
    project.transcript = {"segments": [{"start": 10, "end": 30, "text": "Speaker pertama ini bagus"}]}
    project.save()
    monkeypatch.setattr(service.transcribe, "asr_available", lambda: False)
    seen = []

    def analyze(*args, **kwargs):
        seen.append(kwargs.get("transcript"))
        return [highlight.ClipCandidate(10, 30, 1.0, "awal topik")]

    monkeypatch.setattr(highlight, "analyze_media", analyze)
    clips = service.generate_clips(project, count=1)
    assert seen == [project.transcript]
    assert clips[0].captions[0]["text"] == "Speaker pertama ini bagus"


@pytest.mark.skipif(not ffmpeg.ffmpeg_available(), reason="FFmpeg required")
@pytest.mark.parametrize("shape", ["original", "square", "landscape"])
def test_canvas_keeps_square_geometry(tmp_path: Path, shape):
    import subprocess
    source = tmp_path / "source.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
        "color=c=black:s=640x360:r=10,drawbox=x=270:y=130:w=100:h=100:color=white:t=fill",
        "-t", "0.4", "-c:v", "libx264", str(source)], check=True)
    out = tmp_path / "out.mp4"
    size = crop.canvas_size(shape, 640, 360)
    tl = timeline.default_timeline(0, 0.4, str(source), canvas=shape)
    timeline.render_timeline(source, out, tl, src_size=(640, 360), encoder="libx264")
    result = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"], check=True, capture_output=True)
    frame = np.frombuffer(result.stdout, dtype=np.uint8).reshape(size[1], size[0])
    yy, xx = np.where(frame > 220)
    assert abs((xx.max() - xx.min()) / (yy.max() - yy.min()) - 1) < 0.04


def test_preview_preserves_selected_aspect(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    source = tmp_path / "source.mp4"
    source.touch()
    project = projects.Project.create("Preview", source=str(source))
    project.width, project.height = 1280, 720
    clip = projects.Clip(index=0, start=0, end=3, canvas="original")
    seen = {}
    monkeypatch.setattr(timeline, "render_timeline", lambda *args, **kwargs: seen.update(kwargs))
    service.render_preview(project, clip)
    assert seen["scale_to"] == (960, 540)
def test_editor_drop_upload_streams_into_project(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    project = projects.Project.create("Drop")
    with TestClient(server.app) as client:
        result = client.post(
            f"/api/projects/{project.id}/assets/upload",
            content=b"video bytes",
            headers={"X-Filename": "speaker%20review.mp4"},
        )
        assert result.status_code == 200
        path = Path(result.json()["path"])
        assert path.parent == project.root / "assets"
        assert path.read_bytes() == b"video bytes"
        invalid = client.post(
            f"/api/projects/{project.id}/assets/upload",
            content=b"invalid",
            headers={"X-Filename": "script.exe"},
        )
        assert invalid.status_code == 400


@pytest.mark.skipif(not ffmpeg.ffmpeg_available(), reason="FFmpeg required")
def test_voice_sample_accepts_decodable_non_wav_file(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    sample = tmp_path / "input.flac"
    assert ffmpeg.run_ffmpeg([
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:a", "flac", str(sample),
    ]).ok
    with TestClient(server.app) as client:
        result = client.post("/api/voice-sample", content=sample.read_bytes())
    assert result.status_code == 200
    output = Path(result.json()["path"])
    assert output.exists()
    assert output.suffix == ".wav"
    stream = ffmpeg.ffprobe_json(output)["streams"][0]
    assert stream["sample_rate"] == "24000"
    assert stream["channels"] == 1


def test_clone_model_choice_reaches_synthesis(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    selected = []

    def fake_clone(*args, **kwargs):
        selected.append(kwargs["model_id"])
        return Path(args[1])

    monkeypatch.setattr(server.voice, "clone_speak", fake_clone)
    payload = server.CloneRequest(text="Halo", sample="sample.wav", model_id="chatterbox-id-finetune")
    result = server._quick_clone_task(payload)(SimpleNamespace(report=lambda *_args: None))
    assert result["path"].endswith(".wav")
    assert selected == ["chatterbox-id-finetune"]
