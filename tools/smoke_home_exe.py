"""Exercise transcript-only and canvas rendering through the packaged HTTP API."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import uuid

from studiozai import __version__
from studiozai.utils import ffmpeg
from smoke_exe import request, wait_job

root = Path(__file__).resolve().parents[1]
isolated = root / 'build' / ('home-exe-test-' + uuid.uuid4().hex[:8])
isolated.mkdir()
source = isolated / 'fixture.mp4'
result = ffmpeg.run_ffmpeg(['-f', 'lavfi', '-i', 'testsrc2=size=640x360:r=10:d=4', '-f', 'lavfi', '-i',
    'sine=frequency=440:duration=4', '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', '-shortest', str(source)])
assert result.ok, result.stderr
source.with_suffix('.srt').write_text('1\n00:00:00,000 --> 00:00:03,800\nPackaged transcript fixture.\n', encoding='utf-8')
exe = os.environ.get('STUDIOZAI_SMOKE_EXE', str(root / 'dist/StudioZAI/StudioZAI.exe'))
process = subprocess.Popen([exe, 'serve', '--port', '8740', '--no-browser'],
    env=dict(os.environ, LOCALAPPDATA=str(isolated)), creationflags=subprocess.CREATE_NO_WINDOW)
try:
    for _ in range(120):
        try:
            health = request('/api/health')
            break
        except OSError:
            if process.poll() is not None:
                raise RuntimeError('Packaged server exited')
            time.sleep(.5)
    assert health['version'] == __version__, health
    for path in (root / 'ui').glob('*'):
        if path.suffix in {'.js', '.css', '.html'}:
            with urllib.request.urlopen('http://127.0.0.1:8740/' + path.name) as response:
                assert response.read() == path.read_bytes(), path.name
    project = request('/api/projects', {'title': 'Home regression fixture', 'source': '', 'lang': 'en-US'})
    route = '/api/projects/' + project['id']
    task = wait_job(request(route + '/process', {'source': str(source), 'task': 'transcript', 'processing_mode': 'local'}))
    assert task['project']['clips'] == []
    assert task['project']['execution']['task'] == 'transcript'
    with urllib.request.urlopen('http://127.0.0.1:8740' + route + '/transcript.srt') as response:
        assert 'Packaged transcript fixture.' in response.read().decode()
    task = wait_job(request(route + '/process', {'source': str(source), 'task': 'moments', 'processing_mode': 'local',
        'canvas': 'classic', 'crop': 'fit', 'use_llm': False, 'count': 1, 'caption_motion': 'elastic'}))
    clip = task['project']['clips'][0]
    assert clip['canvas'] == 'classic' and clip['crop'] == 'fit'
    assert clip['captions'] and all(c['style']['animation'] == 'bounce' for c in clip['captions'])
    preview = wait_job(request(route + '/clips/0/preview', {}))
    final = wait_job(request(route + '/clips/0/render', {}))['files']['mp4']
    video = next(s for s in ffmpeg.ffprobe_json(final)['streams'] if s['codec_type'] == 'video')
    assert (video['width'], video['height']) == (1440, 1080)
    assert Path(preview['mp4']).stat().st_size > 1000
    report = {'version': health['version'], 'ui_matches_source': True, 'transcript_only': True,
        'srt': True, 'moments': True, 'preview': True, 'render_dimensions': [video['width'], video['height']], 'data': str(isolated)}
    (isolated / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
finally:
    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], capture_output=True, timeout=15)
    process.wait(timeout=15)
