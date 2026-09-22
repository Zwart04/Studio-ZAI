"""Build a reproducible demo workspace from generated media and local speech models.
Run with the build venv; --serve exposes the seeded workspace on localhost:8751.
No personal projects are used in README screenshots.
"""
import argparse
import subprocess
from pathlib import Path

from studiozai import config, projects, service
from studiozai.pipeline import voice, timeline

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "build" / "readme-demo"
real_models = config.models_dir()
config._base_dir = lambda: DEMO
config.models_dir = lambda: real_models


def prepare():
    DEMO.mkdir(parents=True, exist_ok=True)
    config.save_settings({"setup_version": 2, "setup_done": True, "asr_model": "whisper-tiny-int8"})
    existing = projects.list_projects()
    if existing:
        return existing[0]
    project = projects.Project.create("Studio session — dari ide menjadi klip", language="id")
    wav = project.source_dir / "narration.wav"
    wav.parent.mkdir(parents=True, exist_ok=True)
    voice.synthesize("Selamat datang di Studio ZAI. Ubah video menjadi klip, tambahkan subtitle otomatis, dan sesuaikan gaya teks. Semua diproses di perangkatmu sendiri.", wav, lang="id")
    source = project.source_dir / "studio-session.mp4"
    vf = "drawgrid=w=80:h=80:t=1:c=0x234251,drawbox=x=80:y=170:w=8:h=270:color=0x73e0c8:t=fill,drawtext=fontfile='C\\:/Windows/Fonts/arialbd.ttf':text='MAKE IT YOURS.':fontsize=70:fontcolor=white:x=120:y=210,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='A local creative workflow':fontsize=30:fontcolor=0x9bbbc8:x=124:y=308,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='STUDIO ZAI  /  DEMO SESSION':fontsize=19:fontcolor=0x73e0c8:x=124:y=390"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x10222d:s=1280x720:r=24", "-i", str(wav), "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(source)], check=True)
    service.ingest(project, str(source))
    transcript = service.ensure_transcript(project, model_id="whisper-tiny-int8", lang="id")
    assert transcript.get("segments"), "Whisper must recognize generated Indonesian narration"
    clip = projects.Clip(index=0, start=0, end=min(project.duration, 12), title="Create. Caption. Export.", canvas="original", crop="fit", subtitle_preset="tiktok_pop")
    clip.captions = service.captions_for_range(transcript, clip.start, clip.end)
    clip.timeline = timeline.default_timeline(clip.start, clip.end, project.source, crop="fit", canvas="original")
    clip.timeline["tracks"][2]["items"].append({"id": "t0", "start": 0, "end": 4, "text": "YOUR NEXT STORY STARTS HERE", "template": "minimal_lower", "x": 0.5, "y": 0.16})
    project.clips = [clip]
    project.save()
    service.render_clip(project, clip)
    print("Demo ready:", project.id, "captions:", len(clip.captions), flush=True)
    return project


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    prepare()
    if args.serve:
        import uvicorn
        uvicorn.run("studiozai.server:app", host="127.0.0.1", port=8751)
