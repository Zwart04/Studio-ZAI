"""Render every motion preset through FFmpeg/libass using synthetic captions."""
import json
from pathlib import Path

from studiozai.pipeline import caption_style, subtitle
from studiozai.utils import ffmpeg

root = Path(__file__).resolve().parents[1]
out = root / 'build' / 'caption-motion-render'
out.mkdir(parents=True, exist_ok=True)
checks = []
for name in caption_style.MOTION_STYLES:
    rows = [{'start': 0, 'end': 3, 'text': 'Ini momen menarik', 'words': [
        {'word': word, 'start': i, 'end': i + 1}
        for i, word in enumerate(['Ini', 'momen', 'menarik'])]}]
    caption_style.apply_motion(rows, name)
    rows[0]['style']['size'] = 110
    ass = out / f'{name}.ass'
    ass.write_text(subtitle.to_ass([subtitle.Caption(**rows[0])], play_res=(360, 640)), encoding='utf-8')
    relative = ass.relative_to(root).as_posix()
    video = out / f'{name}.mp4'
    result = ffmpeg.run_ffmpeg(['-y', '-f', 'lavfi', '-i', 'color=c=black:s=360x640:r=30:d=3',
        '-vf', f"ass='{relative}'", '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', str(video)])
    assert result.ok, result.stderr
    frames = []
    for time in (.05, .18, 1.15):
        image = out / f'{name}-{time}.png'
        result = ffmpeg.run_ffmpeg(['-y', '-ss', str(time), '-i', str(video), '-frames:v', '1', str(image)])
        assert result.ok, result.stderr
        from PIL import Image
        with Image.open(image) as picture:
            assert picture.getbbox(), 'Subtitle render is blank'
            frames.append(picture.tobytes())
    if name != 'plain':
        assert frames[0] != frames[2], name
    if name in {'pop', 'elastic', 'word'}:
        assert frames[0] != frames[1], name
    checks.append(name)
print(json.dumps({'rendered': checks, 'decoded_frames_verified': True}))
