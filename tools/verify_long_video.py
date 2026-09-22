"""Opt-in real-media regression run. Downloads stay under ignored build/.

Usage: python tools/verify_long_video.py https://youtu.be/VIDEO_ID
Requires the ASR model to be installed; never includes media in release assets.
"""
import json
import sys
import time
from pathlib import Path

from studiozai import config, projects, service
from studiozai.pipeline import download, probe, timeline, transcribe

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "build" / "long-video-qa"
real_models = config.models_dir()
config._base_dir = lambda: WORK
config.models_dir = lambda: real_models
WORK.mkdir(parents=True, exist_ok=True)
config.save_settings({"asr_model": "whisper-tiny-int8"})
last = 0.0


def progress(percent, message):
    global last
    if time.monotonic() - last > 10 or percent >= 100:
        print(f"{percent:.1f}% {message}", flush=True)
        last = time.monotonic()


def main():
    url = sys.argv[1]
    info = download.fetch_info(url)
    languages = sorted({t["lang"] for t in info["audio_tracks"]})
    assert "id" in languages
    print(f"duration={info['duration']} audio_languages={languages}", flush=True)
    marker = WORK / "project-id.txt"
    if marker.exists():
        project = projects.load_project(marker.read_text().strip())
    else:
        project = projects.Project.create(info["title"], language="id")
        result = download.download(url, project.source_dir, format_id=download.pick_format_id([], "480p"), audio_lang="id", progress_cb=progress)
        service.ingest(project, result["path"])
        marker.write_text(project.id)
    assert project.duration > 3600
    if not project.transcript.get("segments"):
        project.transcript = transcribe.transcribe(project.source, "whisper-tiny-int8", lang="id", progress_cb=progress)
        project.save()
    segments = project.transcript["segments"]
    assert segments and segments[-1]["end"] > 3600
    print(f"transcribed {len(segments)} segments, last={segments[-1]['end']}", flush=True)
    candidates = service.generate_clips(project, count=3, min_len=15, max_len=25)
    report = {"url": url, "duration": project.duration, "languages": languages,
              "selected_audio": "id", "transcript_segments": len(segments),
              "last_segment_end": segments[-1]["end"], "automatic_clips": len(candidates), "renders": []}
    for idx, (start, canvas, preset) in enumerate([(30, "original", "viral_yellow"), (3650, "square", "editorial_cream"), (project.duration - 25, "portrait", "pink_label")]):
        clip = projects.Clip(index=idx, start=start, end=start+12, title=f"Long-video QA {idx}", canvas=canvas, crop="fit", subtitle_preset=preset)
        clip.captions = service.captions_for_range(project.transcript, clip.start, clip.end)
        assert clip.captions
        clip.timeline = timeline.default_timeline(clip.start, clip.end, project.source, crop="fit", canvas=canvas)
        clip.timeline["tracks"][2]["items"].append({"id":"qa-text", "text":"Position test", "start":0,"end":3,"x":.5,"y":.18,"template":"mint_punch"})
        project.clips = [clip]
        project.save()
        files = service.render_clip(project, clip)
        output = probe.probe(files["mp4"])
        assert abs(output.duration-12) < .2 and output.has_audio
        expected = project.width/project.height if canvas == "original" else (1 if canvas == "square" else 9/16)
        assert abs(output.width/output.height-expected) < .01
        preview = service.render_preview(project, clip)
        pinfo = probe.probe(preview["mp4"])
        assert abs(pinfo.width/pinfo.height-expected) < .01
        report["renders"].append({"start":start,"canvas":canvas,"preset":preset,"captions":len(clip.captions),"output":output.as_dict(),"preview":pinfo.as_dict()})
        print(f"PASS render {start:.1f}s {canvas} {preset}", flush=True)
    (WORK / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("PASS long-video workflow", flush=True)


if __name__ == "__main__":
    main()
