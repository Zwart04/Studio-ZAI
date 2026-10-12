import copy
import io
import itertools
import threading
import time
from pathlib import Path

import pytest
from fastapi import HTTPException

from studiozai import config, jobs, projects, server, service
from studiozai.pipeline import timeline
from studiozai.utils import ffmpeg


@pytest.fixture
def project(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    project = projects.Project.create("Studio test")
    project.source_dir.mkdir()
    source = project.source_dir / "source.mp4"
    source.write_bytes(b"source fixture")
    project.source = str(source)
    project.width, project.height, project.duration = 1280, 720, 20
    project.clips = [projects.Clip(0, 0, 2, title="First"), projects.Clip(1, 2, 4, title="Second")]
    project.save()
    return project


@pytest.mark.parametrize("use_timeline", [False, True])
def test_variants_keep_primary_and_editor_canvas(project, monkeypatch, use_timeline):
    clip = project.clip(0)
    clip.canvas = "original"
    clip.captions = [{"start": 0, "end": 1, "text": "Keep captions"}]
    primary = project.clip_dir(0) / "primary.mp4"
    primary.write_bytes(b"original render")
    clip.files["mp4"] = str(primary)
    if use_timeline:
        clip.timeline = timeline.default_timeline(0, 2, project.source, canvas="original")
    original_timeline = copy.deepcopy(clip.timeline)
    dimensions = []

    def fake_render(source, output, *args, **kwargs):
        if use_timeline:
            shape = timeline.track(args[0], "video")[0]["canvas"]
            dimensions.append(service.crop_mod.canvas_size(shape, 1280, 720))
        else:
            dimensions.append(kwargs["out_size"])
        Path(output).write_bytes(b"variant")

    monkeypatch.setattr(service.render, "render_clip", fake_render)
    monkeypatch.setattr(service.timeline_mod, "render_timeline", fake_render)
    monkeypatch.setattr(service.render, "thumbnail", lambda source, out, **kwargs: out)
    for shape in ("portrait", "square", "landscape"):
        files = service.render_clip(project, clip, canvas_override=shape)
        assert Path(files[f"mp4_{shape}"]).read_bytes() == b"variant"
        assert f"PlayResX: {dimensions[-1][0]}" in Path(files["ass"]).read_text(encoding="utf-8-sig")
    assert dimensions == [(1080, 1920), (1080, 1080), (1920, 1080)]
    assert clip.canvas == "original" and clip.timeline == original_timeline
    assert clip.files["mp4"] == str(primary) and primary.read_bytes() == b"original render"
    assert len({clip.files[f"mp4_{fmt}"] for fmt in ("portrait", "square", "landscape")}) == 3


@pytest.mark.parametrize("clips,formats,status", [
    ([], ["portrait"], 400), ([0], [], 400), ([0], ["../bad"], 400), ([99], ["square"], 404),
])
def test_batch_rejects_invalid_selection(project, clips, formats, status):
    with pytest.raises(HTTPException) as error:
        server.batch_render(project.id, server.BatchRenderRequest(clips=clips, formats=formats))
    assert error.value.status_code == status


def queue_batch(project, monkeypatch, clips=None, formats=None):
    pending = []
    job = jobs.Job("batch", "batch-render", "Batch")

    def submit(kind, title, fn):
        pending.append(fn)
        return job

    monkeypatch.setattr(jobs.MANAGER, "submit", submit)
    server.batch_render(project.id, server.BatchRenderRequest(
        clips=clips or [0], formats=formats or ["portrait", "square"]))
    return pending[0], job


def test_batch_deduplicates_and_keeps_concurrent_title_edit(project, monkeypatch):
    calls = []

    def fake_render(snapshot, clip, job, *, canvas_override, persist):
        assert persist is False
        calls.append((clip.storage_id, canvas_override))
        job.report(70)
        current = projects.load_project(project.id)
        current.clip(0).title = "Edited while rendering"
        current.save()
        output = project.clip_dir(clip.index) / f"{canvas_override}.mp4"
        output.write_bytes(b"render")
        job.report(100)
        return {f"mp4_{canvas_override}": str(output)}

    monkeypatch.setattr(service, "render_clip", fake_render)
    run, job = queue_batch(project, monkeypatch, [0, 0], ["portrait", "portrait", "square"])
    result = run(job)
    assert len(calls) == len(result["exports"]) == 2
    current = projects.load_project(project.id)
    assert current.clip(0).title == "Edited while rendering"
    assert "mp4_square" in current.clip(0).files
    # Progres boleh keluar dari urutan antrian (pekerja paralel), tapi harus
    # tetap naik: tidak ada laporan yang melompat mundur.
    progresses = sorted(event.progress for event in job.events)
    assert progresses == sorted(progresses) and all(
        a <= b for a, b in itertools.pairwise(progresses))


def test_queued_batch_refuses_changed_clip(project, monkeypatch):
    run, job = queue_batch(project, monkeypatch)
    project.update_clip(0, {"start": 0.5})
    project.save()
    with pytest.raises(RuntimeError, match="Semua 2 render gagal"):
        run(job)
    result = job.result
    assert result["exports"] == []
    assert result["failures"]
    assert all("berubah" in failure["error"] for failure in result["failures"])


def test_batch_limits_render_workers(project, monkeypatch):
    lock = threading.Lock()
    active = {"now": 0, "peak": 0}

    def fake_render(snapshot, clip, job, *, canvas_override, persist):
        with lock:
            active["now"] += 1
            active["peak"] = max(active["peak"], active["now"])
        time.sleep(0.25)
        output = project.clip_dir(clip.index) / f"{canvas_override}.mp4"
        output.write_bytes(b"render")
        with lock:
            active["now"] -= 1
        return {f"mp4_{canvas_override}": str(output)}

    monkeypatch.setattr(service, "render_clip", fake_render)
    run, job = queue_batch(project, monkeypatch, [0, 1], ["portrait"])
    result = run(job)
    assert not result["failures"], result["failures"]
    assert len(result["exports"]) == 2
    assert active["peak"] == 1, "default hemat resource hanya satu pekerja render"


def test_cancel_during_render_is_not_saved(project, monkeypatch):
    def fake_render(snapshot, clip, job, *, canvas_override, persist):
        job.cancel_requested = True
        return {f"mp4_{canvas_override}": "cancelled.mp4"}

    monkeypatch.setattr(service, "render_clip", fake_render)
    run, batch_job = queue_batch(project, monkeypatch)
    with pytest.raises(jobs.JobCancelled):
        run(batch_job)
    # Dibatalkan saat dirender: hasil tidak disimpan ke klip.
    assert not projects.load_project(project.id).clip(0).files
    assert batch_job.status in ("cancelled", "queued")


def test_edit_invalidates_outputs_but_noop_and_title_keep_them(project):
    clip = project.clip(0)
    clip.files = {"mp4": "main.mp4", "mp4_square": "square.mp4", "voice": "voice.wav"}
    project.update_clip(0, {"canvas": clip.canvas, "title": "New title"})
    assert "mp4_square" in clip.files
    project.update_clip(0, {"canvas": "square"})
    assert clip.files == {"voice": "voice.wav"}


def test_regenerated_captions_invalidate_previous_exports(project):
    clip = project.clip(0)
    clip.files["mp4_square"] = "old-captions.mp4"
    project.transcript = {"segments": [{"start": 0, "end": 1, "text": "Updated captions"}]}
    service.generate_captions_for_clip(project, clip)
    assert clip.captions[0]["text"] == "Updated captions"
    assert "mp4_square" not in clip.files


def test_gallery_keeps_variants_and_omits_missing_files(project):
    output = project.clip_dir(0) / "square.mp4"
    output.write_bytes(b"render")
    project.clip(0).files = {"mp4_square": str(output), "mp4": str(output.with_name("gone.mp4"))}
    project.save()
    gallery = server.clip_gallery()
    assert len(gallery) == 2
    assert gallery[0]["files"] == {"mp4_square": str(output)}
    assert gallery[0]["project_id"] == project.id


def test_ffmpeg_stops_encoder_when_progress_cancels(monkeypatch):
    class Process:
        stderr = io.StringIO("frame= 10 time=00:00:01.00\n")
        stdout = io.StringIO()
        killed = False
        waited = False

        def kill(self):
            self.killed = True

        def wait(self, timeout=None):
            self.waited = True

    process = Process()
    forgotten = []
    monkeypatch.setattr(ffmpeg, "ffmpeg_path", lambda: "ffmpeg")
    monkeypatch.setattr(ffmpeg.proc, "spawn", lambda *args, **kwargs: process)
    monkeypatch.setattr(ffmpeg.proc, "forget", forgotten.append)

    def cancel(_):
        raise jobs.JobCancelled()

    with pytest.raises(jobs.JobCancelled):
        ffmpeg.run_ffmpeg([], total_duration=2, progress_cb=cancel)
    assert process.killed and process.waited and forgotten == [process]


def test_cancelled_queued_job_finishes_without_running():
    job = jobs.Job("queued", "batch-render", "Batch", cancel_requested=True)
    calls = []
    jobs.JobManager()._run(job, lambda current: calls.append(current))
    assert job.status == "cancelled" and job.finished is not None
    assert not calls
