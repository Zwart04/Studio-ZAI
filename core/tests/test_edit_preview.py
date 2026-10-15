from studiozai import config, edit_preview, projects, resources
from studiozai.pipeline import subtitle
from studiozai.utils import ffmpeg


def test_edit_proxy_reused_for_style_changes_but_not_trim(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path / "data")
    source = tmp_path / "source.mp4"
    result = ffmpeg.run_ffmpeg(["-f", "lavfi", "-i", "testsrc2=s=1280x720:r=24:d=2",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:v", "libx264",
        "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(source)])
    assert result.ok
    project = projects.Project.create("Proxy", str(source))
    project.duration = 2
    clip = projects.Clip(0, .25, 1.75)
    project.add_clip(clip)
    project.save()
    first = edit_preview.prepare(project, clip)
    ffmpeg.validate_video(first["path"], duration=1.5, size=(640, 360), require_audio=True)
    clip.captions = [{"text": "changed", "start": 0, "end": 1}]
    clip.canvas = "square"
    assert edit_preview.ready(project, clip) == first
    clip.start = .5
    assert edit_preview.ready(project, clip) is None
    assert source.is_file()


def test_light_profile_caps_threads(monkeypatch):
    monkeypatch.setattr(config, "load_settings", lambda: {"performance_mode": "light"})
    monkeypatch.setattr(resources.os, "cpu_count", lambda: 4)
    assert resources.cpu_threads() == 1
    monkeypatch.setattr(resources.os, "cpu_count", lambda: 16)
    assert resources.cpu_threads() == 2


def test_text_overlay_style_reaches_ass_export():
    ass = subtitle.to_ass([], text_items=[{"text": "Judul baru", "start": 0, "end": 2,
        "template": "clean", "style": {"font": "Kalam", "size": 90, "animation": "bounce"}}])
    assert r"\fnKalam" in ass
    assert r"\fs90.0" in ass
    assert r"\fscy70" in ass
