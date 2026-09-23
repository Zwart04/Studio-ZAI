import asyncio
import json

import pytest

from studiozai import config, jobs, projects, server, typography
from studiozai.pipeline import subtitle


def test_progress_survives_bounded_event_history(monkeypatch):
    job = jobs.Job('test', 'process', 'Long video', status='running')
    for i in range(450):
        job.report(48, 'transcribe', f'segment {i}')
    monkeypatch.setattr(jobs.MANAGER, 'get', lambda _: job)

    async def read():
        response = server.job_events('test')
        first = await anext(response.body_iterator)
        assert 'segment 449' in first
        job.report(75, 'transcribe', 'finished transcription')
        second = await asyncio.wait_for(anext(response.body_iterator), 2)
        assert 'finished transcription' in second
        job.status = 'done'
        assert '"type": "end"' in await anext(response.body_iterator)
        await response.body_iterator.aclose()
    asyncio.run(read())


def test_split_retains_styles_and_retimes_captions(monkeypatch, tmp_path):
    monkeypatch.setattr(config, '_base_dir', lambda: tmp_path)
    project = projects.Project.create('Actual video title')
    clip = projects.Clip(0, 100, 120, subtitle_preset='viral_yellow',
        captions=[{'start': 12, 'end': 14, 'text': 'hello'}])
    project.add_clip(clip)
    left, right = project.split_clip(0, 110)
    assert left.captions == []
    assert right.captions == [{'start': 2, 'end': 4, 'text': 'hello'}]
    assert right.subtitle_preset == 'viral_yellow'
    assert right.storage_id != left.storage_id


def test_custom_typography_persists_and_renders(monkeypatch, tmp_path):
    monkeypatch.setattr(config, '_base_dir', lambda: tmp_path)
    monkeypatch.setattr(subtitle, 'PRESETS', dict(subtitle.PRESETS))
    key, _ = typography.create({'name':'My style','font':'Anton','color':'#ABCDEF','size':80})
    assert key in typography.load()
    ass = subtitle.to_ass([subtitle.Caption(0, 2, 'Saved style')], preset=key)
    assert 'Anton,80' in ass and '&H00EFCDAB' in ass
    with pytest.raises(ValueError):
        typography.create({'color':'bad ASS injection'})


def test_manual_range_reuses_source(monkeypatch, tmp_path):
    monkeypatch.setattr(config, '_base_dir', lambda: tmp_path)
    project = projects.Project.create('Source title')
    source = project.source_dir / 'video.mp4'
    source.parent.mkdir()
    source.write_bytes(b'fixture')
    project.source = str(source)
    project.duration = 4686
    project.save()
    clip = server.create_manual_clip(project.id, server.ManualClip(start=4600,end=4630))
    assert clip['canvas'] == 'original'
    assert clip['title'].startswith('Source title')
    assert json.loads(project.project_file.read_text())['source'] == str(source)


def test_duplicate_owns_media_after_original_deleted(monkeypatch, tmp_path):
    from pathlib import Path
    monkeypatch.setattr(config, '_base_dir', lambda: tmp_path)
    project = projects.Project.create('Keep my source')
    project.source_dir.mkdir()
    source = project.source_dir / 'source.mp4'
    source.write_bytes(b'source fixture')
    project.source = str(source)
    clip = project.add_clip(projects.Clip(0, 0, 5))
    output = project.clip_dir(0) / 'clip.mp4'
    output.write_bytes(b'render fixture')
    clip.files['mp4'] = str(output)
    project.save()
    clone = projects.duplicate_project(project.id)
    projects.delete_project(project.id)
    assert clone.media_path().read_bytes() == b'source fixture'
    assert Path(clone.clips[0].files['mp4']).read_bytes() == b'render fixture'
