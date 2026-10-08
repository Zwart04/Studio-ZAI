"""Real browser + FFmpeg smoke test, using only an isolated synthetic project.

Run with .venv-build/Scripts/python.exe tools/smoke_batch_ui.py.
Screenshots and generated media are left under build/batch-smoke-<id>.
"""
from __future__ import annotations

import json
import zipfile
import socket
import threading
import time
import uuid
from pathlib import Path

import uvicorn
from playwright.sync_api import expect, sync_playwright
from studiozai import config, projects, server
from studiozai.pipeline import timeline
from studiozai.utils import ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / f"batch-smoke-{uuid.uuid4().hex[:8]}"


def main():
    OUT.mkdir(parents=True)
    config._base_dir = lambda: OUT
    # Provider catalog fixture only: no user keys or live cloud inference.
    server.ai.request = lambda *args, **kwargs: {"data": [{"id":"fixture-flash-2"}, {"id":"fixture-pro-2"}, {"id":"text-embedding"}]}
    config.save_settings({"setup_version": 2, "setup_done": True, "lang": "id"})
    project = projects.Project.create("Demo pengujian - video sintetis")
    project.source_dir.mkdir()
    source = project.source_dir / "source.mp4"
    result = ffmpeg.run_ffmpeg([
        "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=15:duration=3",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(source),
    ])
    assert result.ok, result.stderr
    project.source, project.width, project.height, project.duration = str(source), 1280, 720, 3
    first = projects.Clip(0, 0, 1, title="First test clip", canvas="original", score=0.7)
    second = projects.Clip(1, 1, 2, title="Second test clip", canvas="original", score=0.9)
    for clip in (first, second):
        clip.captions = [{"start": 0, "end": 1, "text": "Subtitle uji"}]
    second.timeline = timeline.default_timeline(1, 2, str(source), canvas="original")
    project.clips = [first, second]
    project.save()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    app_server = uvicorn.Server(uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="error"))
    worker = threading.Thread(target=app_server.run, daemon=True)
    worker.start()
    deadline = time.monotonic() + 15
    while not app_server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    assert app_server.started
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 980})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{port}", wait_until="networkidle")
            expect(page.locator('#homeProjects [data-project]')).to_have_count(1)
            page.locator('#nav [data-page="projects"]').click()
            page.locator('#projectList [data-open]').click()
            expect(page.locator('#clipGrid [data-batch-clip]:checked')).to_have_count(2)
            page.locator('#clearClipSelection').click()
            expect(page.locator('#batchRenderBtn')).to_be_disabled()
            page.locator('#selectAllClips').click()
            page.locator('.batch-formats [value="square"]').check()
            page.locator('.batch-formats [value="landscape"]').check()
            expect(page.locator('#batchSummary')).to_contain_text('6 video')
            page.screenshot(path=str(OUT / 'batch-desktop.png'), full_page=True)
            with page.expect_response('**/batch-render') as response:
                page.locator('#batchRenderBtn').click()
            job_id = response.value.json()['id']
            print(f"Rendering six files, job {job_id}", flush=True)
            deadline = time.monotonic() + 180
            job = {}
            while time.monotonic() < deadline:
                job = page.request.get(f'http://127.0.0.1:{port}/api/jobs/{job_id}').json()
                if job['status'] in {'done', 'error', 'cancelled'}:
                    break
                page.wait_for_timeout(250)
            assert job.get('status') == 'done', job
            expect(page.locator('#clipGrid .download-link')).to_have_count(6, timeout=10000)
            with page.expect_download(timeout=30000) as downloaded:
                page.locator('#batchZipBtn').click()
            archive = downloaded.value
            archive.save_as(OUT / 'selected-clips.zip')
            with zipfile.ZipFile(OUT / 'selected-clips.zip') as bundle:
                assert len(bundle.namelist()) == 6 and bundle.testzip() is None
            actual = projects.load_project(project.id)
            expected_sizes = {'portrait': (1080, 1920), 'square': (1080, 1080), 'landscape': (1920, 1080)}
            for clip in actual.clips:
                assert clip.canvas == 'original'
                for shape, dimensions in expected_sizes.items():
                    path = Path(clip.files[f'mp4_{shape}'])
                    assert path.stat().st_size > 0
                    data = ffmpeg.ffprobe_json(path)
                    video = next(stream for stream in data['streams'] if stream['codec_type'] == 'video')
                    assert (video['width'], video['height']) == dimensions
                    assert any(stream['codec_type'] == 'audio' for stream in data['streams'])
            page.locator('#nav [data-page="gallery"]').click()
            expect(page.locator('#galleryGrid video')).to_have_count(2)
            page.locator('#gallerySearch').fill('Second')
            expect(page.locator('#galleryGrid .clip')).to_have_count(1)
            page.locator('#gallerySearch').fill('not-a-real-title')
            expect(page.locator('#galleryGrid .empty')).to_contain_text('Tidak ada klip')
            page.locator('#gallerySearch').fill('')
            page.locator('#gallerySort').select_option('score')
            expect(page.locator('#galleryGrid .meta strong').first).to_have_text('Second test clip')
            page.locator('#galleryStatus').select_option('ready')
            video = page.locator('#galleryGrid video').first
            video.evaluate('(el) => {el.muted=true; return el.play();}')
            page.wait_for_function("document.querySelector('#galleryGrid video').currentTime > 0")
            video.evaluate('(el) => el.pause()')
            with page.expect_download() as download:
                page.locator('#galleryGrid .download-link').first.click()
            assert download.value.failure() is None
            page.screenshot(path=str(OUT / 'gallery-desktop.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.screenshot(path=str(OUT / 'gallery-mobile.png'), full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontal overflow'
            page.set_viewport_size({'width': 1440, 'height': 980})
            page.locator('#langSeg [data-lang="en"]').click()
            expect(page.locator('#page-gallery h1')).to_have_text('Clip gallery')
            page.locator('#galleryGrid [data-gallery-open]').first.click()
            expect(page.locator('.editor-overlay #tlVideo')).to_be_visible(timeout=15000)
            page.locator('[data-creator="words"]').click()
            expect(page.locator('.creator-dialog')).to_be_visible()
            page.locator('[data-word="0"]').click()
            page.locator('#wordFont').select_option('Anton')
            page.locator('#wordColor').fill('#abff66')
            page.locator('#wordBold').check()
            page.locator('#wordAnimation').select_option('type')
            page.screenshot(path=str(OUT / 'creator-words.png'), full_page=True)
            page.locator('#applyWords').click()
            expect(page.locator('.creator-dialog')).to_have_count(0)
            page.locator('[data-inspector="clip"]').click()
            page.locator('#tlHook').fill('Hook podcast hasil edit')
            page.locator('#tlCanvas').select_option('portrait')
            page.locator('[data-creator="crop"]').click()
            page.locator('#cropX').fill('25')
            page.locator('#addKey').click()
            page.locator('#cropTime').fill('.8')
            page.locator('#cropTime').dispatch_event('change')
            page.locator('#cropX').fill('75')
            page.locator('#addKey').click()
            page.screenshot(path=str(OUT / 'creator-crop.png'), full_page=True)
            page.locator('#applyCrop').click()
            expect(page.locator('.creator-dialog')).to_have_count(0)
            page.evaluate('StudioTimeline.close()')
            fresh = projects.load_project(project.id)
            edited = fresh.clips[1]
            assert edited.title == 'Hook podcast hasil edit'
            assert edited.captions[0]['words'][0]['style']['font'] == 'Anton'
            assert edited.captions[0]['words'][0]['style']['bold']
            base = timeline.track(edited.timeline, 'video')[0]
            assert base['crop'] == 'manual' and len(base['framing']['keyframes']) == 2
            from studiozai import service
            output = service.render_clip(fresh, edited)
            assert Path(output['mp4']).stat().st_size > 1000
            assert r'\fnAnton' in Path(output['ass']).read_text(encoding='utf-8')
            page.evaluate('StudioTimeline.open(1)')
            page.locator('[data-inspector="clip"]').click()
            page.locator('[data-finishing="title"]').click()
            page.locator('#openingTitle').fill('Judul pembuka uji')
            page.locator('#openingPreset').select_option('yellow_label')
            page.locator('#saveTitle').click()
            expect(page.locator('.creator-dialog')).to_have_count(0)
            page.locator('[data-finishing="watermark"]').click()
            page.locator('#watermarkText').fill('@studio-test')
            page.locator('#watermarkOpacity').fill('50')
            page.locator('#saveWatermark').click()
            expect(page.locator('.creator-dialog')).to_have_count(0)
            page.locator('[data-creator="splitTop"]').click()
            page.locator('#cropX').fill('20')
            page.locator('#applyCrop').click()
            expect(page.locator('.creator-dialog')).to_have_count(0)
            page.locator('[data-creator="splitBottom"]').click()
            page.locator('#cropX').fill('75')
            page.locator('#applyCrop').click()
            expect(page.locator('.creator-dialog')).to_have_count(0)
            expect(page.locator('.canvas-badge')).to_have_text('Portrait 9:16')
            page.locator('[data-inspector="subtitles"]').click()
            page.locator('[data-creator="words"]').click()
            page.locator('#captionMode').select_option('box')
            page.locator('#selectWords').click()
            page.locator('#wordColor').fill('#ffffff')
            page.locator('#previewWords').click()
            expect(page.locator('#captionVideo')).to_be_visible(timeout=120000)
            page.locator('#applyWords').click()
            expect(page.locator('.creator-dialog')).to_have_count(0)
            page.screenshot(path=str(OUT/'editor-portrait.png'),full_page=True)
            page.evaluate('StudioTimeline.close()')
            fresh=projects.load_project(project.id);edited=fresh.clips[1]
            base=timeline.track(edited.timeline,'video')[0]
            assert base['canvas']=='portrait' and base['crop']=='split'
            assert base['framing']['top']['x']==.2 and base['framing']['bottom']['x']==.75
            assert any(i['id']=='creator_title' for i in timeline.track(edited.timeline,'text'))
            assert any(i['id']=='creator_watermark' and i['opacity']==.5 for i in timeline.track(edited.timeline,'text'))
            output=service.render_clip(fresh,edited)
            data=ffmpeg.ffprobe_json(output['mp4'])
            stream=next(s for s in data['streams'] if s['codec_type']=='video')
            assert (stream['width'],stream['height'])==(1080,1920)
            assert ',ActiveBox,,' in Path(output['ass']).read_text(encoding='utf-8')
            assert ffmpeg.run_ffmpeg(['-i',output['mp4'],'-frames:v','1',str(OUT/'export-portrait.png')]).ok
            upload = page.request.post(f'http://127.0.0.1:{port}/api/source-upload',
                headers={'x-filename': 'test-video.mp4', 'Content-Type': 'application/octet-stream'}, data=source.read_bytes())
            assert upload.ok and Path(upload.json()['path']).read_bytes() == source.read_bytes()
            page.locator('#nav [data-page="settings"]').click()
            card=page.locator('.ai-profile[data-kind="ai"]')
            card.locator('[data-ai="ai_provider"]').select_option('groq')
            card.locator('[data-ai="ai_api_key"]').fill('fixture-only')
            card.locator('[data-model="ai"]').focus()
            expect(card.locator('[data-model="ai"]')).to_have_value('fixture-flash-2')
            expect(card.locator('[data-model-status]')).to_contain_text('2 model terdeteksi')
            page.locator('#saveAiSettings').click()
            expect(page.locator('[data-ai="ai_api_key"]')).to_have_value('')
            assert server.get_settings()['ai_api_key']=='***'
            assert 'fixture-only' not in (OUT/'credentials.json').read_text()
            page.screenshot(path=str(OUT/'provider-model-picker.png'),full_page=True)
            assert not errors, errors
            browser.close()
        print(json.dumps({'status': 'passed', 'exports': 6, 'sizes': expected_sizes, 'screenshots': str(OUT)}, indent=2))
    finally:
        app_server.should_exit = True
        worker.join(timeout=10)


if __name__ == '__main__':
    main()
