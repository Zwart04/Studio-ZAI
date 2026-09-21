"""Clip rendering with FFmpeg: cut, frame, burn subtitles and mix audio."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from ..utils import ffmpeg
from . import crop, probe

ProgressCb = Callable[[float, str], None]
_ENCODER_CACHE: str | None = None


def selected_encoder(explicit: str | None = None) -> str:
    global _ENCODER_CACHE
    if explicit:
        return explicit
    if _ENCODER_CACHE is None:
        _ENCODER_CACHE = ffmpeg.detect_h264_encoder()
    return _ENCODER_CACHE


def encoder_args(encoder: str | None = None) -> list[str]:
    name = selected_encoder(encoder)
    if name == "h264_nvenc":
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "23"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]


def escape_filter_path(path: str | Path) -> str:
    """Escape a path for use inside an ffmpeg filter argument."""
    text = str(path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    return f"filename='{text}'"


def render_clip(
    src: str | Path,
    out: str | Path,
    start: float,
    end: float,
    crop_mode: str = "center",
    src_size: tuple[int, int] | None = None,
    subtitles: str | Path | None = None,
    audio_mode: str = "original",
    voice_path: str | Path | None = None,
    original_volume: float = 0.25,
    voice_volume: float = 1.0,
    encoder: str | None = None,
    progress_cb: ProgressCb | None = None,
) -> Path:
    """Render one vertical clip. audio_mode: original | voice | mix."""
    src = Path(src)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.2, float(end) - float(start))

    if src_size is None:
        info = probe.probe(src)
        src_size = (info.width or 1920, info.height or 1080)
    plan = crop.plan(crop_mode, src_size[0], src_size[1])

    filters: list[str] = []
    if plan.is_complex:
        filters.append(f"[0:v]{plan.complex_graph}".replace("[vout]", "[vsrc]"))
        video_label = "[vsrc]"
    else:
        filters.append(f"[0:v]{plan.simple_chain}[vsrc]")
        video_label = "[vsrc]"

    if subtitles:
        filters.append(f"{video_label}subtitles={escape_filter_path(subtitles)}[v]")
        video_label = "[v]"

    inputs: list[str] = ["-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(src)]
    map_audio = True

    if audio_mode == "voice" and voice_path:
        inputs += ["-i", str(voice_path)]
        filters.append(f"[1:a]volume={voice_volume:.3f}[a]")
        audio_label = "[a]"
    elif audio_mode == "mix":
        inputs += ["-i", str(voice_path)] if voice_path else []
        if voice_path:
            filters.append(
                f"[0:a]volume={original_volume:.3f}[oa];"
                f"[1:a]volume={voice_volume:.3f}[va];"
                f"[oa][va]amix=inputs=2:duration=first:normalize=0[a]"
            )
            audio_label = "[a]"
        else:
            filters.append("[0:a]volume=1.0[a]")
            audio_label = "[a]"
    else:
        if abs(voice_volume - 1.0) < 1e-6:
            map_audio = True
            audio_label = None
        else:
            filters.append(f"[0:a]volume={voice_volume:.3f}[a]")
            audio_label = "[a]"

    args: list[str] = list(inputs)
    if filters:
        args += ["-filter_complex", ";".join(filters)]
        args += ["-map", video_label]
    else:
        args += ["-map", "0:v:0"]
    if audio_label:
        args += ["-map", audio_label]
    elif map_audio:
        args += ["-map", "0:a?"]

    args += ["-c:a", "aac", "-b:a", "192k", *encoder_args(encoder), "-movflags", "+faststart", str(out)]

    def report(fraction: float) -> None:
        if progress_cb:
            progress_cb(min(99.0, max(0.0, fraction)), "merender klip")

    result = ffmpeg.run_ffmpeg(args, duration, report, timeout=7200)
    if not result.ok:
        raise RuntimeError(f"render gagal: {result.stderr[-400:]}")
    if progress_cb:
        progress_cb(100.0, "klip selesai")
    return out


def concat(paths: Sequence[str | Path], out: str | Path, encoder: str | None = None, progress_cb: ProgressCb | None = None) -> Path:
    """Concatenate rendered clips (same codec settings) into one file."""
    items = [Path(p) for p in paths]
    if not items:
        raise ValueError("tidak ada klip untuk digabung")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if len(items) == 1:
        items[0].replace(out)
        return out

    args: list[str] = []
    for item in items:
        args += ["-i", str(item)]
    streams = "".join(f"[{i}:v][{i}:a]" for i in range(len(items)))
    args += [
        "-filter_complex",
        f"{streams}concat=n={len(items)}:v=1:a=1[v][a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        *encoder_args(encoder),
        "-movflags",
        "+faststart",
        str(out),
    ]
    result = ffmpeg.run_ffmpeg(args, None, None, timeout=7200)
    if not result.ok:
        raise RuntimeError(f"concat gagal: {result.stderr[-400:]}")
    if progress_cb:
        progress_cb(100.0, "gabung selesai")
    return out


def thumbnail(src: str | Path, out: str | Path, at: float = 1.0) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    result = ffmpeg.run_ffmpeg(
        ["-ss", f"{max(0.0, at):.3f}", "-i", str(src), "-frames:v", "1", "-q:v", "3", str(out)],
        timeout=120,
    )
    if not result.ok:
        raise RuntimeError(f"gagal membuat thumbnail: {result.stderr[-200:]}")
    return out


def extract_segment(src: str | Path, out: str | Path, start: float, end: float) -> Path:
    """Lossless-ish stream copy cut (fast, used by the editor preview)."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    result = ffmpeg.run_ffmpeg(
        [
            "-ss",
            f"{start:.3f}",
            "-to",
            f"{end:.3f}",
            "-i",
            str(src),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            str(out),
        ],
        timeout=600,
    )
    if not result.ok:
        raise RuntimeError(f"potong cepat gagal: {result.stderr[-300:]}")
    return out
