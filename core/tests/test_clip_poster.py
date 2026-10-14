from types import SimpleNamespace

import pytest
from PIL import Image

from studiozai import service
from studiozai.utils import ffmpeg


def test_poster_uses_clip_start_and_changes_after_trim(tmp_path):
    source = tmp_path / "source.mp4"
    result = ffmpeg.run_ffmpeg(["-f", "lavfi", "-i", "color=red:s=64x64:d=2",
        "-f", "lavfi", "-i", "color=blue:s=64x64:d=2", "-filter_complex",
        "[0:v][1:v]concat=n=2:v=1:a=0", "-c:v", "libx264", str(source)])
    assert result.ok
    project = SimpleNamespace(id="poster-test", media_path=lambda: source,
        clip_dir=lambda _: tmp_path / "clip")
    clip = SimpleNamespace(index=0, storage_id="stable", start=0.0, end=4.0)
    first = service.clip_poster(project, clip)
    assert service.clip_poster(project, clip) == first
    clip.start = 2.5
    second = service.clip_poster(project, clip)
    assert first != second
    r, _, b = Image.open(first).convert("RGB").getpixel((32, 32))
    assert r > b + 100
    r, _, b = Image.open(second).convert("RGB").getpixel((32, 32))
    assert b > r + 100


def test_offline_poster_never_downloads(tmp_path, monkeypatch):
    project = SimpleNamespace(id="offline-poster", media_path=lambda: None,
        source_url="https://example.com/video", clip_dir=lambda _: tmp_path,
        segment_path=lambda _: None, segment_bounds=lambda _: (0, 0),
        processing_mode="offline", online=True)
    clip = SimpleNamespace(index=0, storage_id="stable", start=1, end=3)
    monkeypatch.setattr(service.download, "download_range", lambda *a, **k: pytest.fail("network"))
    with pytest.raises(FileNotFoundError):
        service.clip_poster(project, clip)
