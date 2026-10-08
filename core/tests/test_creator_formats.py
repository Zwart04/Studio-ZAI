import copy
import shutil

import pytest

from studiozai import projects, server
from studiozai.pipeline import crop, subtitle, timeline
from studiozai.utils import ffmpeg


def test_canvas_changes_sync_timeline_and_invalidate_stale_landscape():
    clip = projects.Clip(0, 0, 5, canvas="landscape", files={"mp4": "old.mp4"})
    clip.timeline = timeline.default_timeline(0, 5, "source.mp4", canvas="landscape")
    project = projects.Project("test", "test", clips=[clip])
    project.update_clip(0, {"canvas": "portrait"})
    assert clip.canvas == timeline.track(clip.timeline, "video")[0]["canvas"] == "portrait"
    assert "mp4" not in clip.files
    modified = copy.deepcopy(clip.timeline)
    timeline.track(modified, "video")[0]["canvas"] = "square"
    project.update_clip(0, {"timeline": modified})
    assert clip.canvas == "square"


def test_manual_clips_start_portrait_without_changing_explicit_original():
    assert server.ManualClip(start=0, end=3).canvas == "portrait"
    assert server.ManualClip(start=0, end=3, canvas="original").canvas == "original"


@pytest.mark.parametrize("mode", ["word", "box", "highlight"])
def test_active_word_captions_have_separate_timed_events(mode):
    caption = subtitle.Caption(0, 2, "Halo dunia", words=[
        {"word": "Halo", "start": 0, "end": .8},
        {"word": "dunia", "start": 1, "end": 2},
    ], style={"mode": mode, "highlight": "#abff66", "boxColor": "#112233"})
    ass = subtitle.to_ass([caption])
    assert "Dialogue: 0,0:00:01.00,0:00:02.00" in ass
    if mode == "box":
        assert ",ActiveBox,," in ass and r"\3c&H332211&" in ass
    elif mode == "highlight":
        assert r"\c&H66ffab&" in ass
    else:
        assert "Halo dunia" not in "\n".join(line for line in ass.splitlines() if line.startswith("Dialogue"))


def test_split_export_is_portrait_and_uses_two_distinct_source_regions(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg is required for actual render")
    image = pytest.importorskip("PIL.Image")
    source = tmp_path / "two-regions.mp4"
    result = ffmpeg.run_ffmpeg(["-f", "lavfi", "-i", "color=red:s=160x180:d=1:r=10",
        "-f", "lavfi", "-i", "color=blue:s=160x180:d=1:r=10", "-filter_complex", "[0:v][1:v]hstack[v]",
        "-map", "[v]", "-c:v", "libx264", str(source)])
    assert result.ok, result.stderr
    framing = {"fraction": .5, "top": {"x": .2, "y": .5, "zoom": 2}, "bottom": {"x": .8, "y": .5, "zoom": 2}}
    plan = crop.plan("split", 320, 180, (90, 160), framing=framing)
    output = tmp_path / "portrait.mp4"
    result = ffmpeg.run_ffmpeg(["-i", str(source), "-filter_complex", "[0:v]" + plan.complex_graph,
        "-map", "[vout]", "-c:v", "libx264", str(output)])
    assert result.ok, result.stderr
    stream = ffmpeg.ffprobe_json(output)["streams"][0]
    assert (stream["width"], stream["height"]) == (90, 160)
    frame = tmp_path / "frame.png"
    assert ffmpeg.run_ffmpeg(["-i", str(output), "-frames:v", "1", str(frame)]).ok
    with image.open(frame) as pixels:
        top, bottom = pixels.getpixel((45, 30)), pixels.getpixel((45, 130))
    assert top[0] > 200 and top[2] < 30
    assert bottom[2] > 200 and bottom[0] < 30
