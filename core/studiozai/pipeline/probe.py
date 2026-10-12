"""Inspect media files and extract audio tracks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..utils import ffmpeg


@dataclass
class MediaInfo:
    path: str
    duration: float
    width: int
    height: int
    fps: float
    has_video: bool
    has_audio: bool
    size_bytes: int

    @property
    def is_vertical(self) -> bool:
        return self.height > self.width if self.width else False

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "duration": round(self.duration, 3),
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "has_video": self.has_video,
            "has_audio": self.has_audio,
            "size_bytes": self.size_bytes,
        }


def _fraction_to_float(value: str | None) -> float:
    if not value:
        return 0.0
    if "/" in value:
        num, _, den = value.partition("/")
        try:
            return float(num) / float(den or 1)
        except (ValueError, ZeroDivisionError):
            return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def probe(path: str | Path) -> MediaInfo:
    data = ffmpeg.ffprobe_json(path)
    streams = data.get("streams", [])
    fmt = data.get("format", {})
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(fmt.get("duration") or (video or {}).get("duration") or 0.0)
    width = int((video or {}).get("width") or 0)
    height = int((video or {}).get("height") or 0)
    rotation = (video or {}).get("tags", {}).get("rotate", 0)
    for side in (video or {}).get("side_data_list", []):
        if "rotation" in side:
            rotation = side["rotation"]
            break
    try:
        quarter_turn = round(float(rotation) / 90) % 2 == 1
    except (TypeError, ValueError, OverflowError):
        quarter_turn = False
    # FFmpeg autorotates before filtering, so crop coordinates use display dimensions.
    if quarter_turn:
        width, height = height, width
    return MediaInfo(
        path=str(path),
        duration=duration,
        width=width,
        height=height,
        fps=_fraction_to_float((video or {}).get("avg_frame_rate")),
        has_video=video is not None,
        has_audio=audio is not None,
        size_bytes=int(fmt.get("size") or Path(path).stat().st_size),
    )


def extract_audio(
    src: str | Path,
    dest: str | Path,
    sample_rate: int = 16000,
    mono: bool = True,
    progress_cb=None,
    total_duration: float | None = None,
) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "-i",
        str(src),
        "-vn",
        "-ac",
        "1" if mono else "2",
        "-ar",
        str(sample_rate),
        "-acodec",
        "pcm_s16le",
        str(dest),
    ]
    result = ffmpeg.run_ffmpeg(args, total_duration, progress_cb, timeout=3600)
    if not result.ok:
        raise RuntimeError(f"gagal mengekstrak audio: {result.stderr[-300:]}")
    return dest
