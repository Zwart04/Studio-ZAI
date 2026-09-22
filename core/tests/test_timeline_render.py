"""Render timeline end-to-end memakai FFmpeg sungguhan.

Uji unit lain hanya memeriksa bentuk perintah; berkas ini benar-benar
menjalankan FFmpeg pada berkas media yang dibuat sendiri, sehingga kesalahan
graf filter (label salah, overlay tidak cocok, audio tanpa stream) langsung
ketahuan. Dilewati otomatis kalau ffmpeg/ffprobe tidak ada di PATH.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from studiozai.pipeline import subtitle, timeline
from studiozai.utils import ffmpeg

pytestmark = pytest.mark.skipif(
    not ffmpeg.ffmpeg_available(), reason="ffmpeg tidak tersedia di PATH"
)


def _run(args: list[str]) -> None:
    # check=False: kode keluar diperiksa sendiri agar pesan galatnya bisa
    # ditampilkan (stderr ffmpeg yang menjelaskan masalahnya).
    result = subprocess.run(["ffmpeg", "-y", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg gagal: {result.stderr[-500:]}")


def _video_size(path: Path) -> tuple[int, int]:
    streams = ffmpeg.ffprobe_json(path).get("streams", [])
    for stream in streams:
        if stream.get("codec_type") == "video":
            return int(stream.get("width") or 0), int(stream.get("height") or 0)
    raise AssertionError("tidak ada stream video pada hasil render")


def _duration(path: Path) -> float:
    info = ffmpeg.ffprobe_json(path)
    return float(info.get("format", {}).get("duration") or 0)


@pytest.fixture(scope="module")
def media(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    work = tmp_path_factory.mktemp("timeline")
    source = work / "source.mp4"
    image = work / "logo.png"
    music = work / "music.m4a"
    silent = work / "silent.mp4"

    # Sumber 720p + audio (dipakai untuk semua kasus selain "tanpa audio").
    _run([
        "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440",
        "-t", "6", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(source),
    ])
    _run(["-f", "lavfi", "-i", "color=c=red:s=200x200", "-frames:v", "1", str(image)])
    _run(["-f", "lavfi", "-i", "sine=frequency=880", "-t", "5", "-c:a", "aac", str(music)])
    # Sumber tanpa stream audio sama sekali.
    _run([
        "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=25", "-t", "3",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(silent),
    ])
    return {"source": source, "image": image, "music": music, "silent": silent}


def _full_timeline(media: dict[str, Path]) -> dict:
    """Timeline dengan keempat jenis track terisi."""
    return {
        "version": 1,
        "tracks": [
            {"id": "v1", "kind": "video", "items": [
                {"id": "v0", "start": 0, "end": 6, "src": str(media["source"]),
                 "srcStart": 0, "type": "video", "crop": "fit", "canvas": "portrait"},
            ]},
            {"id": "m1", "kind": "media", "items": [
                {"id": "m0", "start": 1, "end": 3, "src": str(media["image"]),
                 "type": "image", "x": 0.8, "y": 0.2, "scale": 0.35},
            ]},
            {"id": "t1", "kind": "text", "items": [
                {"id": "t0", "start": 0.5, "end": 3.0, "text": "JUDUL", "template": "title_card",
                 "x": 0.5, "y": 0.3},
            ]},
            {"id": "a1", "kind": "audio", "items": [
                {"id": "a0", "start": 1, "end": 5, "src": str(media["music"]), "gain": 0.4},
            ]},
        ],
    }


def test_render_timeline_lengkap(media: dict[str, Path], tmp_path: Path) -> None:
    """Video + media overlay + teks + musik → kanvas potrait 1080x1920."""
    captions = [subtitle.Caption(0.2, 2.0, "Halo dunia"), subtitle.Caption(2.2, 4.5, "Baris kedua")]
    files = subtitle.write_subtitles(
        captions, tmp_path, "subs", preset="tiktok_pop", play_res=(1080, 1920),
        text_items=[{"start": 0.5, "end": 3.0, "text": "JUDUL", "template": "title_card",
                     "x": 0.5, "y": 0.3}],
    )
    out = tmp_path / "clip.mp4"
    timeline.render_timeline(
        media["source"], out, _full_timeline(media),
        src_size=(1280, 720), subtitles=files["ass"], original_volume=0.8,
    )
    assert out.exists() and out.stat().st_size > 0
    assert _video_size(out) == (1080, 1920)
    assert 5.5 <= _duration(out) <= 6.5


def test_render_timeline_skala_pratinjau(media: dict[str, Path], tmp_path: Path) -> None:
    """scale_to dipakai editor untuk pratinjau cepat."""
    out = tmp_path / "preview.mp4"
    timeline.render_timeline(
        media["source"], out, _full_timeline(media),
        src_size=(1280, 720), scale_to=(540, 960),
    )
    assert _video_size(out) == (540, 960)


def test_render_timeline_sumber_tanpa_audio(media: dict[str, Path], tmp_path: Path) -> None:
    """Tanpa stream audio, graf tidak boleh memaksa [0:a] (dulu akan gagal)."""
    tl = {
        "version": 1,
        "tracks": [
            {"id": "v1", "kind": "video", "items": [
                {"id": "v0", "start": 0, "end": 3, "src": str(media["silent"]),
                 "srcStart": 0, "type": "video", "crop": "blur", "canvas": "portrait"},
            ]},
        ],
    }
    out = tmp_path / "silent_out.mp4"
    timeline.render_timeline(media["silent"], out, tl, src_size=(1280, 720))
    assert _video_size(out) == (1080, 1920)


def test_render_timeline_media_hilang_diabaikan(media: dict[str, Path], tmp_path: Path) -> None:
    """Item media yang berkasnya sudah tidak ada dilewati, bukan membuat render gagal."""
    tl = _full_timeline(media)
    tl["tracks"][1]["items"].append(
        {"id": "m1", "start": 3, "end": 4, "src": str(tmp_path / "tidak-ada.png"),
         "type": "image", "x": 0.5, "y": 0.5, "scale": 0.5}
    )
    out = tmp_path / "missing.mp4"
    timeline.render_timeline(media["source"], out, tl, src_size=(1280, 720))
    assert _video_size(out) == (1080, 1920)


def test_default_timeline_mengikuti_potongan_klip() -> None:
    tl = timeline.default_timeline(12.0, 20.0, "video.mp4", crop="blur", canvas="square")
    items = timeline.track(tl, "video")
    assert items[0]["srcStart"] == 12.0
    assert items[0]["end"] == 8.0  # durasi klip, bukan waktu absolut
    assert items[0]["crop"] == "blur"
    assert timeline.duration_of(tl) == 8.0
