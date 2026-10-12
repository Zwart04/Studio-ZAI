"""Regresi mode online: tanpa video penuh, fitur tetap jalan via audio/segmen.

- Caption per klip memakai audio yang sudah diunduh (bukan FileNotFoundError).
- Batch-render mengizinkan proyek online (segmen diunduh per klip saat render).
- Track-face online mengunduh hanya rentang yang dilacak + menggeser waktu.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from studiozai import config, projects, server, service


def _online_project(monkeypatch, tmp_path, **kwargs):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    project = projects.Project.create("Online", language="id")
    project.online = True
    project.source_url = "https://www.youtube.com/watch?v=abcdefghijk"
    project.duration = 120.0
    audio = project.root / "audio.m4a"
    audio.touch()
    project.audio_path = str(audio)
    for key, value in kwargs.items():
        setattr(project, key, value)
    project.clips = [projects.Clip(index=0, start=10, end=14)]
    project.save()
    return project


def test_captions_for_clip_uses_online_audio(monkeypatch, tmp_path):
    project = _online_project(monkeypatch, tmp_path)

    def fake_ffmpeg(cmd, timeout=None):
        Path(cmd[-1]).touch()
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(service.ffmpeg, "run_ffmpeg", fake_ffmpeg)
    monkeypatch.setattr(
        service.transcribe, "transcribe",
        lambda audio, **kwargs: {"language": "id", "segments": [
            {"start": 0.5, "end": 2.0, "text": "Halo online"}]},
    )
    captions = service.generate_captions_for_clip(project, project.clip(0))
    assert captions and captions[0]["text"] == "Halo online"


def test_captions_for_clip_still_fails_without_any_media(monkeypatch, tmp_path):
    project = _online_project(monkeypatch, tmp_path)
    Path(project.audio_path).unlink()
    project.audio_path = ""
    project.save()
    try:
        service.generate_captions_for_clip(project, project.clip(0))
    except FileNotFoundError:
        return
    raise AssertionError("harusnya FileNotFoundError tanpa media apa pun")


def test_batch_render_allows_online_project(monkeypatch, tmp_path):
    project = _online_project(monkeypatch, tmp_path)
    monkeypatch.setattr(
        server.jobs.MANAGER, "submit",
        lambda kind, title, run: SimpleNamespace(
            as_dict=lambda: {"id": "queued", "status": "queued"}),
    )
    with TestClient(server.app) as client:
        response = client.post(
            f"/api/projects/{project.id}/batch-render",
            json={"clips": [0], "formats": ["portrait"]},
        )
        assert response.status_code == 200, response.text


def test_batch_render_still_rejects_missing_offline_media(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    project = projects.Project.create("Offline", language="id")
    project.clips = [projects.Clip(index=0, start=1, end=3)]
    project.save()
    with TestClient(server.app) as client:
        response = client.post(
            f"/api/projects/{project.id}/batch-render",
            json={"clips": [0], "formats": ["portrait"]},
        )
        assert response.status_code == 400


def test_track_face_online_downloads_only_range(monkeypatch, tmp_path):
    project = _online_project(monkeypatch, tmp_path)
    seen = {}

    def fake_range(url, start, end, out_dir, cookies=None, **kwargs):
        seen.update(url=url, start=start, end=end)
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        target = out / "clip-range.mp4"
        target.touch()
        return {"path": str(target), "start": 8.0, "end": 20.0}

    def fake_follow(path, start, end, x, progress=None, y=0.4):
        seen.update(path=path, fstart=start, fend=end)
        return {"ok": True}

    monkeypatch.setattr(server.download_pipeline, "download_range", fake_range)
    from studiozai.pipeline import framing
    monkeypatch.setattr(framing, "follow_face", fake_follow)
    monkeypatch.setattr(
        server.jobs.MANAGER, "submit",
        lambda kind, title, run: SimpleNamespace(as_dict=lambda: run(
            SimpleNamespace(report=lambda *a, **k: None,
                            check_cancel=lambda: None))),
    )
    with TestClient(server.app) as client:
        response = client.post(
            f"/api/projects/{project.id}/track-face",
            json={"start": 10.0, "end": 14.0, "x": 0.5, "y": 0.4},
        )
        assert response.status_code == 200, response.text
    # Rentang unduhan hanya sekitar [10, 14] + padding, bukan video penuh.
    assert seen["start"] <= 10.0 and seen["end"] >= 14.0
    assert seen["end"] - seen["start"] < 30.0
    # Waktu digeser karena berkas segmen mulai di detik 8.
    assert seen["fstart"] == 2.0 and seen["fend"] == 6.0


def test_track_face_still_rejects_missing_offline_media(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    project = projects.Project.create("Offline", language="id")
    project.duration = 60.0
    project.save()
    with TestClient(server.app) as client:
        response = client.post(
            f"/api/projects/{project.id}/track-face",
            json={"start": 1.0, "end": 3.0, "x": 0.5, "y": 0.4},
        )
        assert response.status_code == 400


def test_transcribe_decodes_without_pyav(monkeypatch, tmp_path):
    """Regresi TypeError metadata_errors (av 19+): model harus menerima array."""
    import subprocess

    import numpy as np

    from studiozai.pipeline import transcribe as transcribe_mod
    from studiozai.utils import ffmpeg as ffmpeg_utils

    if not ffmpeg_utils.ffmpeg_available():
        pytest.skip("FFmpeg required")
    tone = tmp_path / "tone.wav"
    subprocess.run(
        [ffmpeg_utils.ffmpeg_path(), "-y", "-v", "error",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
         "-ar", "16000", "-ac", "1", str(tone)],
        check=True,
    )
    audio = transcribe_mod._decode_audio_array(tone)
    assert isinstance(audio, np.ndarray)
    assert audio.dtype == np.float32
    assert audio.shape == (16000,)
    import sys
    assert "av" not in sys.modules


def test_transcribe_single_passes_array_to_model(monkeypatch, tmp_path):
    import subprocess

    import numpy as np

    from studiozai.pipeline import transcribe as transcribe_mod
    from studiozai.utils import ffmpeg as ffmpeg_utils

    if not ffmpeg_utils.ffmpeg_available():
        pytest.skip("FFmpeg required")
    tone = tmp_path / "tone.wav"
    subprocess.run(
        [ffmpeg_utils.ffmpeg_path(), "-y", "-v", "error",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
         "-ar", "16000", "-ac", "1", str(tone)],
        check=True,
    )
    seen = {}

    class FakeModel:
        def transcribe(self, audio, **kwargs):
            seen["audio"] = audio
            seen["kwargs"] = kwargs
            word = SimpleNamespace(word="halo", start=0.0, end=0.5)
            seg = SimpleNamespace(start=0.0, end=0.5, text="halo", words=[word])
            info = SimpleNamespace(duration=1.0, language="id", language_probability=0.9)
            return iter([seg]), info

    monkeypatch.setattr(transcribe_mod, "load_model", lambda model_id="x": FakeModel())
    result = transcribe_mod._transcribe_single(
        tone, model_id="whisper-tiny-int8", lang="id", offset=10.0)
    assert isinstance(seen["audio"], np.ndarray)
    assert seen["kwargs"]["word_timestamps"] is True
    assert result["segments"][0]["start"] == 10.0
    assert result["segments"][0]["words"][0]["word"] == "halo"


def test_process_request_accepts_model_overrides():
    payload = server.ProcessRequest(
        source="https://www.youtube.com/watch?v=abcdefghijk",
        asr_model="whisper-tiny-int8",
        model="gpt-4o-mini",
    )
    assert payload.asr_model == "whisper-tiny-int8"
    assert payload.model == "gpt-4o-mini"


def test_generate_clips_forwards_asr_model(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    source = tmp_path / "source.mp4"
    source.touch()
    project = projects.Project.create("ASR", source=str(source), language="id")
    project.duration = 120.0
    project.save()
    seen = {}

    def fake_ensure(proj, model_id=None, lang=None, job=None):
        seen["model_id"] = model_id
        return {"segments": []}

    monkeypatch.setattr(service, "ensure_transcript", fake_ensure)
    monkeypatch.setattr(service.transcribe, "asr_available", lambda: True)
    monkeypatch.setattr(service.highlight, "analyze_media", lambda *a, **k: [])
    service.generate_clips(project, count=1, asr_model="whisper-tiny-int8")
    assert seen.get("model_id") == "whisper-tiny-int8"


def test_generate_clips_forwards_llm_model(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    source = tmp_path / "source.mp4"
    source.touch()
    project = projects.Project.create("LLM", source=str(source), language="id")
    project.duration = 120.0
    project.transcript = {"segments": [{"start": 1.0, "end": 5.0, "text": "halo dunia"}]}
    project.save()
    seen = {}
    monkeypatch.setattr(service.highlight, "analyze_media", lambda *a, **k: [])
    monkeypatch.setattr(
        service.highlight, "rank_with_llm",
        lambda transcript, **kwargs: seen.update(kwargs) or [],
    )
    service.generate_clips(project, count=1, use_llm=True, model="gpt-4o-mini")
    assert seen.get("model") == "gpt-4o-mini"


def _make_test_video(tmp_path, name="source.mp4", duration=4):
    import subprocess

    from studiozai.utils import ffmpeg as ffmpeg_utils

    if not ffmpeg_utils.ffmpeg_available():
        pytest.skip("FFmpeg required")
    out = tmp_path / name
    subprocess.run(
        [ffmpeg_utils.ffmpeg_path(), "-y", "-v", "error",
         "-f", "lavfi", "-i", f"testsrc2=size=320x240:rate=10:duration={duration}",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
         "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
         "-shortest", str(out)],
        check=True,
    )
    return out


def _preview_clip():
    return projects.Clip(
        index=1,
        start=0.0,
        end=3.0,
        title="Uji",
        captions=[{"start": 0.0, "end": 1.0, "text": "halo", "words": []}],
    )


def test_render_preview_offline_produces_mp4(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    video = _make_test_video(tmp_path)
    project = projects.Project.create("Prev", source=str(video), language="id")
    project.duration = 4.0
    project.width, project.height = 320, 240
    clip = _preview_clip()
    project.clips = [clip]
    project.save()
    result = service.render_preview(project, clip)
    assert Path(result["mp4"]).stat().st_size > 1000


def test_render_preview_online_uses_only_segment(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    video = _make_test_video(tmp_path)
    project = projects.Project.create("PrevOnline", language="id")
    project.audio_path = str(video)
    project.online = True
    project.source_url = "https://www.youtube.com/watch?v=abcdefghijk"
    project.source = ""
    project.duration = 120.0
    project.width, project.height = 320, 240
    clip = _preview_clip()
    project.clips = [clip]
    project.save()
    seen = {}

    def fake_range(url, start, end, out_dir, cookies=None, **kwargs):
        seen.update(url=url, start=start, end=end)
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        target = out / "clip-range.mp4"
        target.write_bytes(video.read_bytes())
        return {"path": str(target), "start": float(start), "end": float(end)}

    monkeypatch.setattr(service.download, "download_range", fake_range)
    result = service.render_preview(project, clip)
    assert Path(result["mp4"]).stat().st_size > 1000
    # Hanya rentang klip (+padding kecil) yang diminta, bukan video penuh.
    assert seen["start"] <= clip.start and seen["end"] >= clip.end
    assert seen["end"] - seen["start"] < 30.0


def test_typography_load_tolerates_corrupt_file(monkeypatch, tmp_path):
    from studiozai import typography

    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    config.data_dir().mkdir(parents=True, exist_ok=True)
    (config.data_dir() / "typography.json").write_text("{rusak", encoding="utf-8")
    assert typography.load() == {}


def test_hook_score_and_heat_average():
    from studiozai.pipeline import highlight as highlight_mod

    assert highlight_mod.hook_score("") == 0.0
    assert highlight_mod.hook_score("hari ini cerah sekali") == 0.0
    assert highlight_mod.hook_score("Jangan lakukan ini!") > 0.4
    assert highlight_mod.hook_score("3 cara gratis") >= 0.6
    heat = [{"start": 0.0, "end": 10.0, "value": 0.2},
            {"start": 10.0, "end": 20.0, "value": 1.0}]
    assert highlight_mod.heat_average(heat, 10.0, 20.0) == 1.0
    assert highlight_mod.heat_average(heat, 0.0, 20.0) == 0.6
    assert highlight_mod.heat_average([], 0.0, 5.0) == 0.0


def test_caption_parser_vtt_with_word_times(tmp_path):
    from studiozai.pipeline import captions as captions_mod

    vtt = tmp_path / "a.en.vtt"
    vtt.write_text(
        "WEBVTT\nKind: captions\n\n"
        "00:00.000 --> 00:02.500 align:start position:0%\n"
        "<00:00.000>hello <00:00.500>world\n\n"
        "00:03.000 --> 00:05.000 align:start position:0%\n"
        "<c>second line</c>\n",
        encoding="utf-8",
    )
    segs = captions_mod.parse_subtitle_file(vtt)
    assert len(segs) == 2
    assert segs[0]["text"] == "hello world"
    assert [w["word"] for w in segs[0]["words"]] == ["hello", "world"]
    assert segs[0]["words"][0]["start"] == 0.0
    assert segs[1]["text"] == "second line"
    assert segs[1]["words"] == []


def test_caption_file_rank_prefers_manual_language(tmp_path):
    from studiozai.pipeline import captions as captions_mod

    auto = tmp_path / "v [vid].id.vtt"
    manual = tmp_path / "v [vid].en.vtt"
    auto.touch()
    manual.touch()
    assert captions_mod._pick_caption_file([auto, manual], "en") == manual
    assert captions_mod._pick_caption_file([auto], "id") == auto


def test_generate_clips_prefers_youtube_captions(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    project = projects.Project.create("Cap", language="id")
    project.online = True
    project.source_url = "https://www.youtube.com/watch?v=abcdefghijk"
    audio = tmp_path / "audio.m4a"
    audio.touch()
    project.audio_path = str(audio)
    project.duration = 120.0
    project.save()
    seen = {}

    def fake_captions(proj, lang=None, job=None):
        seen["called"] = True
        proj.transcript = {"language": "id", "source": "youtube",
                           "segments": [{"start": 10.0, "end": 12.0, "text": "halo",
                                         "words": []}]}
        return proj.transcript

    monkeypatch.setattr(service, "ensure_transcript_from_captions", fake_captions)
    monkeypatch.setattr(
        service, "ensure_transcript",
        lambda *a, **k: pytest.fail("Whisper tidak boleh jalan bila caption ada"))
    monkeypatch.setattr(service.highlight, "analyze_media", lambda *a, **k: [])
    service.generate_clips(project, count=1)
    assert seen.get("called") is True
    assert project.transcript.get("source") == "youtube"


def test_generate_clips_falls_back_to_whisper(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    source = tmp_path / "source.mp4"
    source.touch()
    project = projects.Project.create("W", source=str(source), language="id")
    project.online = True
    project.source_url = "https://www.youtube.com/watch?v=abcdefghijk"
    project.duration = 120.0
    project.save()
    seen = {}

    def no_captions(proj, lang=None, job=None):
        raise RuntimeError("video ini tidak memiliki caption")

    def fake_whisper(proj, model_id=None, lang=None, job=None):
        seen["model_id"] = model_id
        return {"segments": []}

    monkeypatch.setattr(service, "ensure_transcript_from_captions", no_captions)
    monkeypatch.setattr(service, "ensure_transcript", fake_whisper)
    monkeypatch.setattr(service.transcribe, "asr_available", lambda: True)
    monkeypatch.setattr(service.highlight, "analyze_media", lambda *a, **k: [])
    service.generate_clips(project, count=1)
    assert "model_id" in seen


def test_score_windows_heat_and_hook_bonus():
    from studiozai.pipeline import highlight as highlight_mod

    windows = [
        {"start": 0.0, "end": 10.0, "duration": 10.0, "text": "halo semua",
         "words": [{"word": "halo", "start": 0.0, "end": 1.0}] * 10},
        {"start": 10.0, "end": 20.0, "duration": 10.0,
         "text": "Jangan lewatkan 3 cara ini!",
         "words": [{"word": "x", "start": 10.0, "end": 11.0}] * 10},
    ]
    plain = highlight_mod.score_windows(windows, None, [])
    boosted = highlight_mod.score_windows(
        windows, None, [],
        [{"start": 10.0, "end": 20.0, "value": 1.0}])
    assert plain[1]["score"] > plain[0]["score"]  # hook saja
    assert boosted[1]["score"] > plain[1]["score"]  # + heatmap
    assert boosted[0]["score"] == plain[0]["score"]  # tanpa sinyal = sama
    assert boosted[1]["heat"] == 1.0 and boosted[1]["hook"] > 0


def test_extract_heatmap_normalizes():
    from studiozai.pipeline import download as download_mod

    info = {"heatmap": [
        {"start_time": 0, "end_time": 5, "value": 10},
        {"start_time": 5, "end_time": 10, "value": 40},
        {"start_time": 10, "end_time": 8, "value": 5},
    ]}
    heat = download_mod.extract_heatmap(info)
    assert heat == [{"start": 0.0, "end": 5.0, "value": 0.25},
                    {"start": 5.0, "end": 10.0, "value": 1.0}]
    assert download_mod.extract_heatmap({}) == []


def _make_video_only(tmp_path):
    import subprocess

    from studiozai.utils import ffmpeg as ffmpeg_utils

    out = tmp_path / "silent.mp4"
    subprocess.run(
        [ffmpeg_utils.ffmpeg_path(), "-y", "-v", "error",
         "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=10:duration=4",
         "-c:v", "libx264", "-preset", "ultrafast", "-an", str(out)],
        check=True,
    )
    return out


def _make_tone(tmp_path, name="tone.m4a"):
    import subprocess

    from studiozai.utils import ffmpeg as ffmpeg_utils

    out = tmp_path / name
    subprocess.run(
        [ffmpeg_utils.ffmpeg_path(), "-y", "-v", "error",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
         "-ar", "16000", "-ac", "1", "-c:a", "aac", str(out)],
        check=True,
    )
    return out


def _stream_kinds(path):
    from studiozai.utils import ffmpeg as ffmpeg_utils

    streams = ffmpeg_utils.ffprobe_json(path).get("streams", [])
    return sorted(s.get("codec_type", "") for s in streams)


def test_download_range_muxes_local_audio(monkeypatch, tmp_path):
    from studiozai.pipeline import download as download_mod

    video = _make_video_only(tmp_path)
    audio = _make_tone(tmp_path)
    assert _stream_kinds(video) == ["video"]

    def fake_section(playlist_url, start, end, out_dir, progress_cb, family=None):
        target = Path(out_dir) / "vraw.mp4"
        target.write_bytes(video.read_bytes())
        return target, 0.0, 4.0

    monkeypatch.setattr(download_mod, "_hls_section", fake_section)
    monkeypatch.setattr(download_mod, "_extract", lambda *a, **k: {"title": "x"})
    monkeypatch.setattr(download_mod, "_pick_hls_format",
                        lambda *a, **k: {"url": "http://example.com/v.m3u8"})
    result = download_mod.download_range(
        "https://www.youtube.com/watch?v=abcdefghijk", 0, 4,
        tmp_path / "out", audio_path=str(audio))
    assert _stream_kinds(result["path"]) == ["audio", "video"]


def test_download_range_without_audio_stays_video_only(monkeypatch, tmp_path):
    from studiozai.pipeline import download as download_mod

    video = _make_video_only(tmp_path)

    def fake_section(playlist_url, start, end, out_dir, progress_cb, family=None):
        target = Path(out_dir) / "vraw.mp4"
        target.write_bytes(video.read_bytes())
        return target, 0.0, 4.0

    monkeypatch.setattr(download_mod, "_hls_section", fake_section)
    monkeypatch.setattr(download_mod, "_extract", lambda *a, **k: {"title": "x"})
    monkeypatch.setattr(download_mod, "_pick_hls_format",
                        lambda *a, **k: {"url": "http://example.com/v.m3u8"})
    result = download_mod.download_range(
        "https://www.youtube.com/watch?v=abcdefghijk", 0, 4, tmp_path / "out")
    assert _stream_kinds(result["path"]) == ["video"]


def test_face_smoothing_stays_near_anchor():
    from studiozai.pipeline import framing

    anchor = (0.5, 0.4)
    first = framing.smooth_center(anchor, (0.9, 0.9))
    # Frame pertama tidak melompat ke wajah jauh: tetap dekat jangkar.
    assert abs(first[0] - anchor[0]) < abs(0.9 - anchor[0])
    assert abs(first[1] - anchor[1]) < abs(0.9 - anchor[1])
    assert framing.select_face([(0.9, 0.9)], anchor) is None
    assert framing.select_face([(0.55, 0.42)], anchor) == (0.55, 0.42)


def test_clean_caption_text_removes_non_speech():
    from studiozai.pipeline import subtitle as subtitle_mod

    assert subtitle_mod.clean_caption_text("[Musik] halo semua") == "halo semua"
    assert subtitle_mod.clean_caption_text("keren *cheering* banget") == "keren banget"
    assert subtitle_mod.clean_caption_text("(tertawa) lucu") == "lucu"
    assert subtitle_mod.clean_caption_text("halo! apa kabar? baik-baik saja.") == "halo! apa kabar? baik-baik saja."
    assert subtitle_mod.clean_caption_text("mantap 👍🔥") == "mantap"
    assert subtitle_mod.clean_caption_text("") == ""


def test_group_words_drops_sound_tags_but_keeps_timing():
    from studiozai.pipeline import subtitle as subtitle_mod

    words = [
        {"word": "[Musik]", "start": 0.0, "end": 0.4},
        {"word": "halo", "start": 0.5, "end": 0.9},
        {"word": "dunia!", "start": 1.0, "end": 1.5},
    ]
    captions = subtitle_mod.group_words(words)
    assert len(captions) == 1
    assert captions[0].text == "halo dunia!"
    assert captions[0].start == 0.5
    assert captions[0].end == 1.5
