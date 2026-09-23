"""Verify the packaged server using isolated app data and generated demo media."""
import json
import os
import subprocess
import time
import urllib.request
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
    env = dict(os.environ, LOCALAPPDATA=str(ROOT / 'build/packaged-smoke-v16'))
    process = subprocess.Popen([str(ROOT / 'dist/StudioZAI/StudioZAI.exe'), 'serve', '--port', '8740', '--no-browser'],
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
        assert health['version'] == '1.6.0', health
        voices = request('/api/voices')
        assert voices['available']['piper'] and voices['available']['zipvoice'], voices
        assert 'anthropic' in request('/api/ai/providers')['providers']
        assert request('/api/images') == []
        with urllib.request.urlopen(BASE + '/timeline.js?v=1.6.0') as response:
            script = response.read().decode()
            assert 'schedulePreview()' in script and 'data-tl="preview"' not in script
        source = next((ROOT / 'build/readme-demo-v16/projects').glob('*/source/studio-session.mp4'))
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
            'unique_previews': True, 'render': final['mp4'], 'project': project['id']}
        (ROOT / 'build/packaged-smoke-v160.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        request(route, method='DELETE')
        assert not (Path(env['LOCALAPPDATA']) / 'StudioZAI/projects' / project['id']).exists()
        print(json.dumps(report))
        print('Packaged Windows smoke passed, including preview, export and cleanup.')
    finally:
        process.terminate()
        process.wait(timeout=15)
