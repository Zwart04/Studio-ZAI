"""Build a reproducible demo workspace from generated media and local speech models.
Run with the build venv; --serve exposes the seeded workspace on localhost:8752.
No personal projects are used in README screenshots.
"""
import argparse
import subprocess
from pathlib import Path

from studiozai import config, projects, service
from studiozai.pipeline import timeline, voice

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "build" / "readme-demo-v18-release"
real_models = config.models_dir()
config._base_dir = lambda: DEMO
config.models_dir = lambda: real_models


def prepare():
    DEMO.mkdir(parents=True, exist_ok=True)
    config.save_settings({"setup_version": 2, "setup_done": True, "asr_model": "whisper-tiny-int8"})
    existing = projects.list_projects()
    if existing:
        return existing[0]
    project = projects.Project.create("Studio Notes — Setiap ide punya cerita", language="id")
    wav = project.source_dir / "narration.wav"
    wav.parent.mkdir(parents=True, exist_ok=True)
    voice.synthesize("Setiap ide punya cerita. Mulai dari satu video. Pilih bagian yang kamu suka, tambahkan suara, lalu susun kata menjadi cerita. Karya berikutnya dimulai dari sini.", wav, lang="id")
    source = project.source_dir / "studio-session.mp4"
    regular = "fontfile='C\\:/Windows/Fonts/arial.ttf'"
    bold = "fontfile='C\\:/Windows/Fonts/arialbd.ttf'"
    vf = ",".join([
        "drawbox=x=80:y=100:w=1120:h=1:color=0x3a3a3c:t=fill",
        f"drawtext={regular}:text='STUDIO NOTES':fontsize=19:fontcolor=0xaaaaae:x=80:y=62",
        f"drawtext={regular}:text='01 / CREATIVE SESSION':fontsize=19:fontcolor=0xaaaaae:x=w-tw-80:y=62",
        f"drawtext={bold}:text='Setiap ide':fontsize=78:fontcolor=white:x=(w-tw)/2:y=242",
        f"drawtext={bold}:text='punya cerita.':fontsize=78:fontcolor=white:x=(w-tw)/2:y=332",
        f"drawtext={regular}:text='Buat. Susun. Bagikan.':fontsize=22:fontcolor=0xaaaaae:x=(w-tw)/2:y=460",
        "fade=t=in:st=0:d=0.4",
    ])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x151517:s=1280x720:r=24", "-i", str(wav), "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(source)], check=True)
    service.ingest(project, str(source))
    transcript = service.ensure_transcript(project, model_id="whisper-tiny-int8", lang="id")
    assert transcript.get("segments"), "Whisper must recognize generated Indonesian narration"
    clip = projects.Clip(index=0, start=0, end=min(project.duration, 12), title="Setiap ide punya cerita", canvas="original", crop="fit", subtitle_preset="clean")
    clip.captions = service.captions_for_range(transcript, clip.start, clip.end)
    clip.timeline = timeline.default_timeline(clip.start, clip.end, project.source, crop="fit", canvas="original")
    project.clips = [clip]
    project.save()
    service.render_clip(project, clip)
    print("Demo ready:", project.id, "captions:", len(clip.captions), flush=True)
    return project


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8752)
    args = parser.parse_args()
    prepare()
    if args.serve:
        import uvicorn
        uvicorn.run("studiozai.server:app", host="127.0.0.1", port=args.port)
