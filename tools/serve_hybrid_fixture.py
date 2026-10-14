"""Isolated real API fixture for browser regression tests."""
import argparse
import json
from pathlib import Path
import uvicorn
from studiozai import config, projects
from studiozai.utils import ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/hybrid-browser'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8768)
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    config._base_dir=lambda:OUT/'isolated-data'
    source=OUT/'source.mp4'
    result=ffmpeg.run_ffmpeg(['-f','lavfi','-i','testsrc2=size=640x360:r=15:d=5','-f','lavfi','-i',
        'sine=frequency=440:duration=5','-c:v','libx264','-preset','ultrafast','-c:a','aac','-shortest',str(source)])
    assert result.ok,result.stderr
    source.with_suffix('.srt').write_text('1\n00:00:00,000 --> 00:00:04,500\nCaption fixture for transcript-only testing.\n', encoding='utf-8')
    project=projects.Project.create('Browser fixture',str(source))
    project.duration=5;project.width=640;project.height=360
    project.source_url='https://youtu.be/oPZY7nKtUTc'  # Public source image; playback remains synthetic local media.
    project.add_clip(projects.Clip(0,1,4,title='Subtitle fixture',canvas='portrait',captions=[
        {'start':0,'end':3,'text':'Halo dunia','style':{'mode':'highlight'},
         'words':[{'word':'Halo','start':0,'end':1.5},{'word':'dunia','start':1.5,'end':3}]}]))
    project.save()
    project.add_clip(projects.Clip(1,0,2,title='Landscape fixture',canvas='landscape',score=.9))
    project.add_clip(projects.Clip(2,0,2,title='Square fixture',canvas='square',score=.4))
    project.save()
    (OUT/'fixture.json').write_text(json.dumps({'project_id':project.id,'source':str(source)}),encoding='utf-8')
    from studiozai.server import app
    uvicorn.run(app,host='127.0.0.1',port=args.port,log_level='error')


if __name__=='__main__':
    main()
