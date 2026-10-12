import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from studiozai import ai, cache, config, local_llm, projects, service
from studiozai.execution_policy import check_network, processing
from studiozai.pipeline import captions, download, highlight, transcribe
from studiozai.utils import ffmpeg


@pytest.mark.parametrize('rotation,expected', [(90, (360, 640)), (-90, (360, 640)), (180, (640, 360))])
def test_phone_rotation_uses_display_dimensions(monkeypatch, tmp_path, rotation, expected):
    from studiozai.pipeline.probe import probe
    monkeypatch.setattr(ffmpeg, 'ffprobe_json', lambda path: {
        'format': {'duration': '1', 'size': '1'},
        'streams': [{'codec_type': 'video', 'width': 640, 'height': 360,
                     'side_data_list': [{'rotation': rotation}]}]})
    media = probe(tmp_path / 'phone.mp4')
    assert (media.width, media.height) == expected


@pytest.fixture
def project(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    p = projects.Project.create("Fixture")
    p.duration = 60
    p.clips = [projects.Clip(0, 5, 10)]
    p.save()
    return p


def test_caption_first_needs_no_media_or_asr(project, monkeypatch):
    monkeypatch.setattr(download, "fetch_info", lambda *a, **k: {"title": "Fixture", "duration": 60})
    monkeypatch.setattr(captions, "fetch_captions", lambda *a, **k: {
        "language": "id", "source": "youtube", "segments": [{"start": 5, "end": 25, "text": "Bagaimana cara menyelesaikan masalah ini?"}]})
    def forbidden(*args, **kwargs):
        raise AssertionError("caption discovery must not download/decode/transcribe media")
    monkeypatch.setattr(download, "download_audio", forbidden)
    monkeypatch.setattr(highlight, "decode_pcm", forbidden)
    monkeypatch.setattr(transcribe, "transcribe", forbidden)
    assert service.ingest(project, "https://youtu.be/abcdefghijk", online=True, captions_first=True) is None
    assert service.generate_clips(project, count=1)
    assert project.execution["ranking"] == "heuristic-only"


def test_caption_language_uses_suffix_not_title():
    assert captions._pick_caption_file([Path("Video.en.vtt"), Path("Video.id.vtt")], "id").name == "Video.id.vtt"


def test_audio_language_missing_is_explicit():
    with pytest.raises(RuntimeError, match="tidak tersedia"):
        download._pick_audio_format({"formats": [{"acodec": "aac", "vcodec": "none", "url": "fixture", "language": "en"}]}, "id")


@pytest.mark.parametrize("mode,url,inference", [("offline", "https://youtube.com", False),
    ("offline", "http://192.168.1.2/v1", True), ("hybrid", "https://api.openai.com/v1", True)])
def test_execution_policy_blocks_unapproved_network(mode, url, inference):
    with processing(mode), pytest.raises(ValueError):
        check_network(url, inference=inference)


def test_offline_allows_same_machine_inference():
    with processing("offline"):
        check_network("http://127.0.0.1:11434/v1", inference=True)


def test_partial_cache_is_not_reused(project):
    identifier = cache.key("fixture")
    cache.write(identifier, {"value": 1})
    path = config.cache_dir() / "pipeline" / f"{identifier}.json"
    row = json.loads(path.read_text())
    row["complete"] = False
    path.write_text(json.dumps(row))
    assert cache.read(identifier) is None


def test_segment_zero_and_draft_do_not_overwrite_saved_edits(project, monkeypatch):
    audio = project.root / "audio.m4a"
    audio.touch()
    project.audio_path = str(audio)
    project.online, project.source_url = True, "https://youtu.be/abcdefghijk"
    project.save()
    draft = projects.load_project(project.id)
    draft.clip(0).title = "unsaved"
    fresh = projects.load_project(project.id)
    fresh.clip(0).title = "saved edit"
    fresh.clip(0).files["mp4_portrait"] = "previous.mp4"
    fresh.save()
    target = project.root / "segment.mp4"
    target.touch()
    monkeypatch.setattr(download, "download_range", lambda *a, **k: {"path": str(target), "start": 0, "end": 20})
    monkeypatch.setattr(service.probe, "probe", lambda *a: SimpleNamespace(width=320, height=180))
    assert service._resolve_render_media(draft, draft.clip(0))[1] == 0
    result = projects.load_project(project.id)
    assert result.clip(0).title == "saved edit"
    assert result.clip(0).files["mp4_portrait"] == "previous.mp4"


def test_local_llm_receives_shortlist_model_and_reuses_cache(project, monkeypatch):
    received = []
    def respond(base, route, key, payload, **kwargs):
        received.append(payload)
        return {"choices": [{"message": {"content": json.dumps([{"candidate_id": 0, "start": 5, "end": 20,
            "title": "Test", "reason": "Complete answer", "score": .9, "hook_assessment": "Question", "context_completeness": .8}])}}]}
    monkeypatch.setattr(ai, "request", respond)
    transcript = {"segments": [{"start": 5, "end": 20, "text": "Real fixture content"}]}
    candidates = [highlight.ClipCandidate(5, 20, .8, "candidate")]
    for _ in range(2):
        rows = local_llm.rank_shortlist(transcript, candidates, model="selected-local", base_url="http://127.0.0.1:17777/v1", min_len=10, max_len=20)
        assert rows[0]["model"] == "selected-local"
    assert len(received) == 1
    assert received[0]["model"] == "selected-local"
    assert "Real fixture content" in received[0]["messages"][0]["content"]


def test_local_llm_rejects_invalid_timestamps(project, monkeypatch):
    monkeypatch.setattr(ai, "request", lambda *a, **k: {"choices": [{"message": {"content": '[{"candidate_id":0,"start":0,"end":99,"score":0.9,"context_completeness":1}]'}}]})
    assert not local_llm.rank_shortlist({"segments": []}, [highlight.ClipCandidate(5, 20, .8, "")], model="fixture")


def test_project_merges_independent_edits_and_rejects_conflicting_edits(project):
    first, second = projects.load_project(project.id), projects.load_project(project.id)
    first.clip(0).title = "New title"
    second.clip(0).files["mp4"] = "new-output.mp4"
    first.save()
    second.save()
    saved = projects.load_project(project.id)
    assert saved.clip(0).title == "New title"
    assert saved.clip(0).files["mp4"] == "new-output.mp4"
    first, second = projects.load_project(project.id), projects.load_project(project.id)
    first.clip(0).title = "First edit"
    second.clip(0).title = "Conflicting edit"
    first.save()
    with pytest.raises(projects.ProjectConflict):
        second.save()
    assert projects.load_project(project.id).clip(0).title == "First edit"


def test_deleted_clip_cannot_be_resurrected_by_old_snapshot(project):
    old = projects.load_project(project.id)
    project.clips.clear()
    project.save()
    old.clip(0).title = "stale edit"
    with pytest.raises(projects.ProjectConflict):
        old.save()
    assert not projects.load_project(project.id).clips


def test_native_ollama_profile_limits_context_and_disables_thinking(project, monkeypatch):
    requests = []
    def response(base, route, key, payload=None, **kwargs):
        if route == "/api/version":
            return {"version": "0.13.0"}
        if route == "/api/show":
            return {"capabilities": ["completion", "thinking"]}
        requests.append(payload)
        return {"message": {"content": '[{"candidate_id":0,"start":5,"end":20,"score":0.9,"context_completeness":0.8,"title":"Fixture","reason":"Complete answer","hook_assessment":"Question"}]'}}
    local_llm._NATIVE_CAPABILITIES.clear()
    monkeypatch.setattr(ai, "request", response)
    assert local_llm.rank_shortlist({"segments": []}, [highlight.ClipCandidate(5, 20, .8, "")], model="fixture-native")
    assert requests[0]["options"]["num_ctx"] == 4096
    assert requests[0]["think"] is False
    assert requests[0]["format"] == local_llm.SCHEMA


def test_vtt_word_marks_do_not_fabricate_uniform_timing():
    assert captions._cue_words('Halo<00:00.500>dunia<00:01.000>lagi', 0, 1.5) == [
        {"word": "Halo", "start": 0, "end": .5}, {"word": "dunia", "start": .5, "end": 1}, {"word": "lagi", "start": 1, "end": 1.5}]
    assert captions._cue_words('Dua kata<00:00.500>bersama<00:01.000>lagi', 0, 1.5) == []


def test_quiet_encoder_timeout_and_cleanup(monkeypatch):
    children = []
    def spawn(*args, **kwargs):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"], **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(ffmpeg, "ffmpeg_path", lambda: "fixture")
    monkeypatch.setattr(ffmpeg.proc, "spawn", spawn)
    start = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        ffmpeg.run_ffmpeg([], timeout=.15)
    assert time.monotonic() - start < 2
    assert children[0].poll() is not None


def test_missing_asr_does_not_download(project, monkeypatch):
    transcribe.ModelCache.clear()
    monkeypatch.setattr(transcribe.models.manager, "is_installed", lambda _: False)
    monkeypatch.setattr(transcribe.models.manager, "download", lambda _: pytest.fail("unexpected model download"))
    with pytest.raises(RuntimeError, match="belum terpasang"):
        transcribe.load_model("whisper-base-int8")


def test_bad_llm_array_items_are_ignored(project, monkeypatch):
    monkeypatch.setattr(ai, "request", lambda *a, **k: {"choices":[{"message":{"content":"[null, 1, \"bad\"]"}}]})
    assert local_llm.rank_shortlist({"segments":[]},[highlight.ClipCandidate(0,20,.8,"")],
        base_url="http://127.0.0.1:17777/v1",model="invalid-items") == []


def test_corrupt_completed_cache_is_not_used(project):
    identifier=cache.key("test-tamper")
    cache.write(identifier,{"text":"original"})
    path=config.cache_dir()/"pipeline"/f"{identifier}.json"
    payload=json.loads(path.read_text())
    payload["value"]["text"]="modified"
    path.write_text(json.dumps(payload))
    assert cache.read(identifier) is None


def test_failed_output_validation_preserves_successful_file(project, monkeypatch, tmp_path):
    target=tmp_path/"video.mp4"
    target.write_bytes(b"previous-success")
    def encode(args,*a,**kw):
        Path(args[-1]).write_bytes(b"broken-new-video")
        return ffmpeg.RunResult(0)
    monkeypatch.setattr(ffmpeg,"run_ffmpeg",encode)
    monkeypatch.setattr(ffmpeg,"ffprobe_json",lambda path:{"streams":[]})
    with pytest.raises(RuntimeError,match="stream video"):
        ffmpeg.finalize_video(["-i","fixture",str(target)],target,2)
    assert target.read_bytes()==b"previous-success"
    assert not list(tmp_path.glob("*.partial.mp4"))


def test_asr_and_encoder_share_the_global_budget():
    import threading

    from studiozai.jobs import inference_slot
    entered=threading.Event()
    with inference_slot():
        thread=threading.Thread(target=lambda: (ffmpeg._ENCODER_SLOT.acquire(), entered.set(), ffmpeg._ENCODER_SLOT.release()))
        thread.start()
        assert not entered.wait(.1)
    thread.join(timeout=2)
    assert entered.is_set() and not thread.is_alive()


def test_cuda_inference_failure_retries_once_on_cpu(project, monkeypatch):
    attempts=[]
    monkeypatch.setattr(transcribe,"_device",lambda: (transcribe._DEVICE_OVERRIDE.get() or "cuda","int8"))
    def run(*args,**kwargs):
        attempts.append(transcribe._DEVICE_OVERRIDE.get())
        if len(attempts)==1:
            raise RuntimeError("CUDA failed")
        return {"device":"cpu","segments":[]}
    monkeypatch.setattr(transcribe,"_transcribe",run)
    assert transcribe.transcribe("fixture")["device"]=="cpu"
    assert attempts==[None,"cpu"]


def test_model_revision_changes_when_weights_change(project, tmp_path):
    (tmp_path/"model.bin").write_bytes(b"old")
    original=transcribe.model_revision(str(tmp_path))
    (tmp_path/"model.bin").write_bytes(b"updated weights")
    assert transcribe.model_revision(str(tmp_path)) != original


def test_completed_asr_chunks_resume_without_decode(project, monkeypatch, tmp_path):
    source=tmp_path/"input.wav"
    source.write_bytes(b"fixture")
    monkeypatch.setattr(ffmpeg,"ffprobe_json",lambda _: {"format":{"duration":180}})
    calls=[]
    def decode(path, model, lang, progress, offset):
        calls.append(offset)
        return {"device":"cpu","language":"id","segments":[{"start":offset,"end":offset+1,"text":"fixture"}]}
    def extract(args,*a,**kw):
        Path(args[-1]).write_bytes(b"wav")
        return ffmpeg.RunResult(0)
    monkeypatch.setattr(transcribe,"_transcribe_single",decode)
    monkeypatch.setattr(ffmpeg,"run_ffmpeg",extract)
    first=transcribe._transcribe(source)
    second=transcribe._transcribe(source)
    assert first==second and second['device']=='cpu'
    assert calls==[0,90]


def test_speech_free_asr_reuses_decoded_audio_features(project, tmp_path, monkeypatch):
    source=tmp_path/'input.wav'
    source.write_bytes(b'fixture')
    features={'duration':2,'rms':[.1]*8}
    monkeypatch.setattr(transcribe,'_transcribe',lambda *a,**kw:{'segments':[],'audio_features':features})
    transcribe.transcribe(source)
    assert cache.read(cache.key('acoustic-features-v1',cache.file_identity(source)))==features


def test_relink_preserves_edits_exports_and_original_file(project, tmp_path, monkeypatch):
    path=tmp_path/'moved.mp4'
    path.write_bytes(b'fixture')
    project.clip(0).title='User edit'
    project.clip(0).files={'mp4':'successful.mp4'}
    monkeypatch.setattr(service.probe,'probe',lambda _:SimpleNamespace(duration=60,width=640,height=360))
    service.relink_source(project,str(path))
    fresh=projects.load_project(project.id)
    assert fresh.source==str(path.resolve())
    assert fresh.clip(0).title=='User edit' and fresh.clip(0).files['mp4']=='successful.mp4'
    assert path.read_bytes()==b'fixture'


def test_relink_rejects_a_different_video(project, tmp_path, monkeypatch):
    path=tmp_path/'wrong.mp4'
    path.touch()
    monkeypatch.setattr(service.probe,'probe',lambda _:SimpleNamespace(duration=30,width=640,height=360))
    with pytest.raises(ValueError,match='Durasi berbeda'):
        service.relink_source(project,str(path))
    assert projects.load_project(project.id).source==''
