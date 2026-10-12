"""Bukti real: jalur transkrip di EXE yang dulu error metadata_errors.

Menyalakan EXE paket (serve terisolasi), memakai model tiny yang sudah ada,
membuat proyek dari audio lokal, lalu meminta caption otomatis.
Lolos = job captions selesai TANPA TypeError metadata_errors.
"""
import json
import os
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8741"


def request(route, payload=None, method=None):
    req = urllib.request.Request(BASE + route, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def wait_job(job, deadline_s=600):
    deadline = time.monotonic() + deadline_s
    while time.monotonic() < deadline:
        result = request('/api/jobs/' + job['id'])
        if result['status'] == 'done':
            return result['result']
        if result['status'] in {'error', 'cancelled'}:
            raise RuntimeError(f"JOB GAGAL: {result}")
        time.sleep(1.0)
    raise TimeoutError('Pekerjaan caption melebihi batas waktu')


if __name__ == '__main__':
    test_dir = ROOT / f'build/packaged-smoke-transcribe-{uuid.uuid4().hex[:8]}'
    test_dir.mkdir(parents=True)
    env = dict(os.environ, LOCALAPPDATA=str(test_dir))
    process = subprocess.Popen(
        [os.environ.get('STUDIOZAI_SMOKE_EXE', str(ROOT / 'dist/StudioZAI/StudioZAI.exe')), 'serve', '--port', '8741', '--no-browser'],
        env=env, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        for _ in range(90):
            try:
                request('/api/health')
                break
            except OSError:
                if process.poll() is not None:
                    raise RuntimeError('Packaged server exited')
                time.sleep(.5)
        else:
            raise TimeoutError('Packaged server did not start')
        from studiozai.models import manager
        model = manager.model_dir('whisper-tiny-int8')
        if not manager.is_installed('whisper-tiny-int8'):
            raise RuntimeError('Tiny belum terpasang; smoke tidak mengunduh model.')
        request('/api/settings', {'values': {'asr_model': str(model)}})
        source = test_dir / 'tone.mp4'
        from studiozai.utils import ffmpeg
        made = ffmpeg.run_ffmpeg(['-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=10:duration=4',
            '-f', 'lavfi', '-i', 'sine=frequency=440:duration=4',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', '-shortest', str(source)])
        assert made.ok, made.stderr
        project = request('/api/projects', {'title': 'Transcribe smoke', 'source': str(source), 'lang': 'id'})
        for _ in range(60):
            project = request('/api/projects/' + project['id'])
            if project['duration'] > 0:
                break
            time.sleep(.3)
        assert project['duration'] > 0
        route = '/api/projects/' + project['id']
        request(route + '/clips', {'start': 0, 'end': 4, 'canvas': 'original'})
        result = wait_job(request(route + '/clips/0/captions', {}, 'POST'))
        print(json.dumps({'captions': result['captions'], 'project': project['id']}))
        print('Transkrip EXE paket lolos tanpa error metadata_errors.')
        request(route, method='DELETE')
    finally:
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
