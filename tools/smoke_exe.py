"""Verify the packaged server using isolated app data and generated demo media."""
import json
import os
import subprocess
import time
import urllib.request
import uuid
from studiozai import __version__
from studiozai.utils import ffmpeg
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8740"


def request(route, payload=None, method=None):
    req = urllib.request.Request(BASE + route, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def wait_job(job):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        result = request('/api/jobs/' + job['id'])
        if result['status'] == 'done':
            return result['result']
        if result['status'] in {'error', 'cancelled'}:
            raise RuntimeError(result)
        time.sleep(.4)
    raise TimeoutError('Packaged render exceeded 120 seconds')


if __name__ == '__main__':
    # Use fresh app data on every run so earlier smoke images/projects cannot
    # make the empty-state assertion depend on test order.
    test_dir = ROOT / f'build/packaged-smoke-{uuid.uuid4().hex[:8]}'
    test_dir.mkdir(parents=True)
    env = dict(os.environ, LOCALAPPDATA=str(test_dir))
    # Reuse an already verified weight through an NTFS hardlink for the
    # packaged-image smoke. This does not copy 683 MB or modify the original.
    image_model = Path(os.environ.get('LOCALAPPDATA', '')) / 'StudioZAI/models/sdxs-512'
    packaged_model = Path(env['LOCALAPPDATA']) / 'StudioZAI/models/sdxs-512'
    image_weight = 'sdxs-512-tinySDdistilled_Q8_0.gguf'
    test_local_image = os.environ.get('STUDIOZAI_SMOKE_IMAGE') == '1' and (image_model / image_weight).is_file()
    if test_local_image:
        packaged_model.mkdir(parents=True, exist_ok=True)
        if not (packaged_model / image_weight).exists():
            os.link(image_model / image_weight, packaged_model / image_weight)
        (packaged_model / '.installed').write_text(
            (image_model / '.installed').read_text(encoding='utf-8'), encoding='utf-8')
    process = subprocess.Popen([os.environ.get('STUDIOZAI_SMOKE_EXE', str(ROOT / 'dist/StudioZAI/StudioZAI.exe')), 'serve', '--port', '8740', '--no-browser'],
        env=env, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        for _ in range(90):
            try:
                health = request('/api/health')
                break
            except OSError:
                if process.poll() is not None:
                    raise RuntimeError('Packaged server exited')
                time.sleep(.5)
        else:
            raise TimeoutError('Packaged server did not start')
        assert health['version'] == __version__, health
        voices = request('/api/voices')
        assert voices['available']['piper'] and voices['available']['zipvoice'], voices
        assert 'anthropic' in request('/api/ai/providers')['providers']
        assert request('/api/images') == []
        local_model = os.environ.get('STUDIOZAI_SMOKE_GGUF')
        if local_model:
            loaded = wait_job(request('/api/local-llm/start', {'path': local_model}))
            discovered = request('/api/local-llm/models')
            assert any(row['id'] == loaded['model'] for row in discovered['models'])
            request('/api/local-llm/stop', {}, 'POST')
        if test_local_image:
            generated = wait_job(request('/api/images', {
                'prompt': 'minimalist studio product photograph of a small speaker',
                'provider': 'sdxs_local',
            }))['image']
            assert Path(generated).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
        with urllib.request.urlopen(BASE + '/timeline.js?v=' + __version__) as response:
            script = response.read().decode()
            assert 'schedulePreview()' in script and 'data-tl="preview"' not in script
        source = test_dir / 'source.mp4'
        generated_source = ffmpeg.run_ffmpeg(['-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=15:duration=4',
            '-f', 'lavfi', '-i', 'sine=frequency=440:duration=4', '-c:v', 'libx264', '-preset', 'ultrafast',
            '-c:a', 'aac', '-shortest', str(source)])
        assert generated_source.ok, generated_source.stderr
        project = request('/api/projects', {'title': 'Packaged smoke', 'source': str(source), 'lang': 'id'})
        for _ in range(60):
            project = request('/api/projects/' + project['id'])
            if project['duration'] > 0:
                break
            time.sleep(.3)
        assert project['duration'] > 0
        route = '/api/projects/' + project['id']
        request(route + '/clips', {'start': 1, 'end': 3, 'canvas': 'original'})
        request(route + '/clips/0', {'captions': [{'start': 0, 'end': 2, 'text': 'Studio ZAI'}]}, 'PATCH')
        first = wait_job(request(route + '/clips/0/preview', {}, 'POST'))
        second = wait_job(request(route + '/clips/0/preview', {}, 'POST'))
        assert first['mp4'] != second['mp4']
        assert Path(first['mp4']).exists() and Path(second['mp4']).stat().st_size > 1000
        final = wait_job(request(route + '/clips/0/render', {}, 'POST'))['files']
        assert Path(final['mp4']).stat().st_size > 1000
        report = {'health': health, 'voice_runtimes': voices['available'],
            'bundled_gguf_runtime': bool(local_model),
            'unique_previews': True, 'local_image': test_local_image,
            'render': final['mp4'], 'project': project['id']}
        (test_dir / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        request(route, method='DELETE')
        assert not (Path(env['LOCALAPPDATA']) / 'StudioZAI/projects' / project['id']).exists()
        print(json.dumps(report))
        print('Packaged Windows smoke passed, including preview, export and cleanup.')
    finally:
        # Bunuh seluruh tree proses (launcher EXE bisa menelurkan anak server);
        # terminate() saja sering menyisakan server yang mengunci _internal.
        try:
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        except Exception:
            pass
        try:
            process.terminate()
        except Exception:
            pass
        try:
            process.wait(timeout=15)
        except Exception:
            pass
