"""Test the packaged creator runtime with isolated, synthetic app data."""
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path
from PIL import Image

from studiozai import __version__
from studiozai.pipeline.timeline import default_timeline, track
from studiozai.utils import ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build' / f'creator-exe-{uuid.uuid4().hex[:8]}'


def main():
    OUT.mkdir(parents=True)
    source = OUT / 'source.mp4'
    rendered = ffmpeg.run_ffmpeg(['-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=15:duration=3',
        '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3', '-c:v', 'libx264', '-preset', 'ultrafast',
        '-c:a', 'aac', '-shortest', str(source)])
    assert rendered.ok, rendered.stderr
    models = ROOT / '.test-fixtures/translation-smoke/translation'
    assert (models / 'id-en/model/model.bin').exists(), 'Run the real translation smoke first'
    shutil.copytree(models, OUT / 'StudioZAI/translation', copy_function=os.link)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    def request(route, payload=None, method=None):
        req = urllib.request.Request(base+route, data=json.dumps(payload).encode() if payload is not None else None,
            method=method, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    def wait(job):
        deadline = time.monotonic()+180
        while time.monotonic()<deadline:
            result = request('/api/jobs/'+job['id'])
            if result['status']=='done':
                return result['result']
            if result['status'] in {'error','cancelled'}:
                raise RuntimeError(result)
            time.sleep(.4)
        raise TimeoutError(job)
    with (OUT/'server.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen([str(ROOT/'dist/StudioZAI/StudioZAI.exe'),'serve','--port',str(port),'--no-browser'],
            env={**os.environ,'LOCALAPPDATA':str(OUT)}, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            for _ in range(120):
                try:
                    health=request('/api/health')
                    break
                except OSError:
                    assert process.poll() is None, (OUT/'server.log').read_text()
                    time.sleep(.5)
            else:
                raise TimeoutError('Packaged startup')
            assert health['version']==__version__
            assert {'groq','gemini'} <= request('/api/ai/providers')['providers'].keys()
            p=request('/api/projects', {'title':'Packaged creator test','source':str(source),'lang':'id'})
            route='/api/projects/'+p['id']
            for _ in range(80):
                p=request(route)
                if p['duration']>0:
                    break
                time.sleep(.2)
            request(route+'/clips',{'start':0,'end':2,'canvas':'portrait'})
            logo=OUT/'logo.png'
            Image.new('RGBA',(96,96),(255,0,255,255)).save(logo)
            upload=urllib.request.Request(base+route+'/assets-upload',data=logo.read_bytes(),
                headers={'Content-Type':'image/png','X-Filename':'logo.png'})
            with urllib.request.urlopen(upload,timeout=30) as response:
                logo_path=json.load(response)['path']
            timeline=default_timeline(0,2,p['source'],crop='split',canvas='portrait')
            track(timeline,'video')[0]['framing']={'fraction':.35,'top':{'x':.25,'y':.2,'zoom':2},'bottom':{'x':.75,'y':.5}}
            next(t for t in timeline['tracks'] if t['kind']=='text')['items'].append(
                {'id':'creator_title','type':'text','text':'Judul pembuka','template':'viral_yellow',
                 'start':0,'end':2,'x':.5,'y':.15,'fontSize':86})
            next(t for t in timeline['tracks'] if t['kind']=='media')['items'].append(
                {'id':'creator_watermark','type':'image','src':logo_path,'start':0,'end':2,
                 'x':.85,'y':.15,'scale':.12,'opacity':.5})
            rows=[{'start':0,'end':2,'text':'Halo dunia','style':{'font':'Anton','mode':'box','boxColor':'#112233','animation':'pop','x':.5,'y':.75},
                'words':[{'word':'Halo','start':0,'end':1,'style':{'color':'#abff66'}},{'word':'dunia','start':1,'end':2}]}]
            request(route+'/clips/0',{'captions':rows,'timeline':timeline},'PATCH')
            output=wait(request(route+'/clips/0/render',{},'POST'))['files']
            assert Path(output['mp4']).stat().st_size>1000
            metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',output['mp4']]))
            video=next(s for s in metadata['streams'] if s['codec_type']=='video')
            assert video['height'] > video['width'], video
            assert abs(video['width']/video['height'] - 9/16) <= 2/video['height'], video
            before=request(route)['clips'][0]['captions']
            wait(request(route+'/clips/0/preview',{'captions':[{**rows[0],'text':'Draft preview only'}]}))
            assert request(route)['clips'][0]['captions']==before, 'Draft preview persisted edits'
            translated=wait(request(route+'/translate',{'captions':rows,'source':'id','target':'en'}))
            assert translated['captions'][0]['text'].lower().startswith('hello')
            assert Path(translated['files']['vtt']).exists()
            face_source=ROOT/'.test-fixtures/face-smoke/face.mp4'
            assert face_source.exists()
            f=request('/api/projects',{'title':'Face runtime test','source':str(face_source),'lang':'id'})
            for _ in range(80):
                f=request('/api/projects/'+f['id'])
                if f['duration']>0:
                    break
                time.sleep(.2)
            tracking=wait(request('/api/projects/'+f['id']+'/track-face',{'start':0,'end':1.5}))
            assert len(tracking['keyframes'])>=2
            report={'version':health['version'],'render':output['mp4'],'translation':translated['captions'][0]['text'],
                'face_keyframes':len(tracking['keyframes']),'dimensions':[video['width'],video['height']],
                'features':['gaming split','opening title','uploaded image watermark','active word box','draft preview'], 'status':'passed'}
            (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(json.dumps(report,indent=2),flush=True)
        finally:
            process.terminate()
            process.wait(timeout=20)


if __name__=='__main__':
    main()
