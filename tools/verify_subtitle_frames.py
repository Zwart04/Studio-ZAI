"""Render real MP4s and compare decoded frames for each subtitle effect."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from studiozai.pipeline import render, subtitle
from studiozai.utils import ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/hybrid-subtitle-frames'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT/'source.mp4'
    made = ffmpeg.run_ffmpeg(['-f','lavfi','-i','color=c=black:s=360x640:r=30:d=3','-c:v','libx264',str(source)],timeout=60)
    assert made.ok
    report = []
    for effect in ('word','highlight','box','karaoke','pop','bounce','fade','rise','zoom','typewriter'):
        style = {'mode':effect if effect in ('word','highlight','box','karaoke') else 'line',
                 'animation':effect if effect not in ('word','highlight','box','karaoke') else 'none',
                 'x':.5,'y':.82,'size':100,'color':'#ffffff','highlight':'#abff66'}
        cue = subtitle.Caption(.4,2.4,'Halo dunia',words=[{'word':'Halo','start':.4,'end':1.4},
            {'word':'dunia','start':1.4,'end':2.4}],style=style)
        ass = OUT/f'{effect}.ass'
        ass.write_text(subtitle.to_ass([cue],play_res=(360,640)), encoding='utf-8')
        output = render.render_clip(source, OUT/f'{effect}.mp4',0,3,out_size=(360,640),subtitles=ass,encoder='libx264')
        frames = []
        for index, at in enumerate((.2,.433,.55,1.5,2.8)):
            image = OUT/f'{effect}-{index}.png'
            taken = ffmpeg.run_ffmpeg(['-ss',str(at),'-i',str(output),'-frames:v','1',str(image)],timeout=60)
            assert taken.ok
            frames.append(np.asarray(Image.open(image).convert('RGB')).astype(np.int16))
        visible = int(np.count_nonzero(np.max(np.abs(frames[2]-frames[0]),axis=2)>30))
        cleared = int(np.count_nonzero(np.max(np.abs(frames[4]-frames[0]),axis=2)>30))
        change = int(np.count_nonzero(np.max(np.abs(frames[1]-frames[3]),axis=2)>30))
        assert visible > 30 and cleared < 10, (effect,visible,cleared)
        assert change > 10, (effect,'animation/word change absent')
        report.append({'effect':effect,'size':[360,640],'visible_pixels':visible,'changed_pixels':change,'after_pixels':cleared})
        print(effect,'PASS',flush=True)
    (OUT/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
