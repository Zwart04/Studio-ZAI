"""Multi-track timeline rendering.

Timeline sebuah klip punya sampai empat track:

- ``video``  : satu item sumber (potongan ``project.source``).
- ``media``  : overlay gambar/video di atas video dasar.
- ``text``   : teks ber-template (dibakar lewat ASS, lihat ``pipeline.subtitle``).
- ``audio``  : musik/audio tambahan yang dicampur ke audio asli.

Modul ini hanya membangun graf FFmpeg. Teks (caption + item track teks) sudah
dirangkum jadi satu berkas ASS oleh pemanggil, jadi di sini cukup satu filter
``subtitles`` — sama untuk desktop maupun Android.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..utils import ffmpeg
from . import crop as crop_mod
from .render import AUDIO_ENCODE_ARGS, can_copy_audio, encoder_args, escape_filter_path

ProgressCb = Callable[[float, str], None]


def track(timeline: dict[str, Any] | None, kind: str) -> list[dict[str, Any]]:
    """Item pada track dengan [kind] (kosong kalau track tidak ada)."""
    for entry in (timeline or {}).get("tracks", []) or []:
        if entry.get("kind") == kind:
            return list(entry.get("items") or [])
    return []


def default_timeline(
    clip_start: float,
    clip_end: float,
    source: str,
    *,
    crop: str = "center",
    canvas: str = "portrait",
) -> dict[str, Any]:
    """Timeline awal untuk sebuah klip (satu item video + track kosong)."""
    return {
        "version": 1,
        "tracks": [
            {
                "id": "v1",
                "kind": "video",
                "items": [
                    {
                        "id": "v0",
                        "start": 0.0,
                        "end": max(0.2, float(clip_end) - float(clip_start)),
                        "src": str(source),
                        "srcStart": float(clip_start),
                        "type": "video",
                        "crop": crop,
                        "canvas": canvas,
                    }
                ],
            },
            {"id": "m1", "kind": "media", "items": []},
            {"id": "t1", "kind": "text", "items": []},
            {"id": "a1", "kind": "audio", "items": []},
        ],
    }


def duration_of(timeline: dict[str, Any] | None) -> float:
    longest = 0.0
    for entry in (timeline or {}).get("tracks", []) or []:
        for item in entry.get("items") or []:
            try:
                longest = max(longest, float(item.get("end", 0.0)))
            except (TypeError, ValueError):
                continue
    return longest


def _even(value: float) -> int:
    result = round(value)
    return result if result % 2 == 0 else result - 1


def _has_audio(path: str | Path) -> bool:
    """Apakah berkas punya stream audio (filter [0:a] gagal bila tidak ada)."""
    try:
        streams = ffmpeg.ffprobe_json(path).get("streams", [])
    except Exception:  # noqa: BLE001 - kalau tidak terbaca, anggap ada
        return True
    return any(stream.get("codec_type") == "audio" for stream in streams)


def render_timeline(
    source: str | Path,
    out: str | Path,
    timeline: dict[str, Any],
    *,
    src_size: tuple[int, int],
    subtitles: str | Path | None = None,
    voice_path: str | Path | None = None,
    original_volume: float = 1.0,
    voice_volume: float = 1.0,
    scale_to: tuple[int, int] | None = None,
    encoder: str | None = None,
    progress_cb: ProgressCb | None = None,
) -> Path:
    """Render a clip from its multi-track timeline."""
    source = Path(source)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    video_items = track(timeline, "video")
    base = video_items[0] if video_items else {}
    offset = float(base.get("srcStart", 0.0))
    duration = max(0.2, float(base.get("end", 0.0)) - float(base.get("start", 0.0)))
    if duration <= 0.2:
        duration = max(0.2, duration_of(timeline))

    crop_mode = str(base.get("crop", "center"))
    canvas = str(base.get("canvas", "portrait"))
    out_w, out_h = crop_mod.canvas_size(canvas, src_size[0], src_size[1])
    plan = crop_mod.plan(crop_mode, src_size[0], src_size[1], out_size=(out_w, out_h))

    inputs: list[str] = ["-ss", f"{offset:.3f}", "-t", f"{duration:.3f}", "-i", str(source)]
    filters: list[str] = []

    if plan.is_complex:
        filters.append(f"[0:v]{plan.complex_graph}".replace("[vout]", "[vbase]"))
    else:
        filters.append(f"[0:v]{plan.simple_chain}[vbase]")
    label = "[vbase]"

    index = 1
    # ---------------------------------------------------------- media overlays
    for item in track(timeline, "media"):
        media = str(item.get("src") or "")
        start = float(item.get("start", 0.0))
        end = float(item.get("end", 0.0))
        if not media or end <= start or not Path(media).exists():
            continue
        is_image = str(item.get("type", "image")).lower() != "video"
        if is_image:
            inputs += ["-loop", "1", "-t", f"{duration:.3f}", "-i", media]
        else:
            inputs += ["-ss", f"{float(item.get('srcStart', 0.0)):.3f}", "-t", f"{end - start:.3f}", "-i", media]

        scale = max(0.05, min(1.0, float(item.get("scale", 0.6))))
        x_ratio = max(0.0, min(1.0, float(item.get("x", 0.5))))
        y_ratio = max(0.0, min(1.0, float(item.get("y", 0.5))))
        width = _even(out_w * scale)
        filters.append(f"[{index}:v]scale={max(2, width)}:-2[s{index}]")
        filters.append(
            f"{label}[s{index}]overlay=x=(W-w)*{x_ratio:.4f}:y=(H-h)*{y_ratio:.4f}:"
            f"enable='between(t,{start:.3f},{end:.3f})'[v{index}]"
        )
        label = f"[v{index}]"
        index += 1

    # ------------------------------------------------------------------ audio
    audio_labels: list[str] = []
    copy_source_audio = (
        abs(original_volume - 1.0) < 1e-6
        and not track(timeline, "audio")
        and not (voice_path and Path(voice_path).exists())
        and can_copy_audio(source)
    )
    if _has_audio(source) and not copy_source_audio:
        filters.append(f"[0:a]volume={max(0.0, original_volume):.3f}[abase]")
        audio_labels.append("[abase]")

    for item in track(timeline, "audio"):
        media = str(item.get("src") or "")
        if not media or not Path(media).exists():
            continue
        start = max(0.0, float(item.get("start", 0.0)))
        end = float(item.get("end", 0.0))
        length = (end - start) if end > start else duration
        gain = max(0.0, float(item.get("gain", 1.0)))
        inputs += ["-i", media]
        # Dipotong ke panjang item lalu digeser ke posisinya di timeline (adelay).
        filters.append(
            f"[{index}:a]atrim=0:{max(0.1, length):.3f},asetpts=PTS-STARTPTS,"
            f"volume={gain:.3f},adelay={int(start * 1000)}:all=1[a{index}]"
        )
        audio_labels.append(f"[a{index}]")
        index += 1

    if voice_path and Path(voice_path).exists():
        inputs += ["-i", str(voice_path)]
        filters.append(f"[{index}:a]volume={max(0.0, voice_volume):.3f}[a{index}]")
        audio_labels.append(f"[a{index}]")
        index += 1

    if not audio_labels:
        # Sumber tanpa audio dan tidak ada track audio: keluaran tanpa suara.
        audio_map = "0:a?"
    elif len(audio_labels) == 1:
        audio_map = audio_labels[0]
    else:
        filters.append(
            "".join(audio_labels)
            + f"amix=inputs={len(audio_labels)}:duration=first:normalize=0[aaudio]"
        )
        audio_map = "[aaudio]"

    # ------------------------------------------------------------------ text
    if subtitles:
        filters.append(f"{label}subtitles={escape_filter_path(subtitles)}[vfinal]")
        label = "[vfinal]"

    args: list[str] = list(inputs)
    args += ["-filter_complex", ";".join(filters), "-map", label, "-map", audio_map]
    if scale_to:
        # `-s` adalah opsi keluaran dan tetap sah bersama -filter_complex, jadi
        # pratinjau cukup diperkecil tanpa mengubah graf filternya.
        args += ["-s", f"{scale_to[0]}x{scale_to[1]}"]
    args += [
        *(["-c:a", "copy"] if copy_source_audio else AUDIO_ENCODE_ARGS),
        *encoder_args(encoder),
        "-t",
        f"{duration:.3f}",
        "-movflags",
        "+faststart",
        str(out),
    ]

    def report(fraction: float) -> None:
        if progress_cb:
            progress_cb(min(99.0, max(0.0, fraction)), "merender klip")

    result = ffmpeg.run_ffmpeg(args, duration, report, timeout=7200)
    if not result.ok:
        raise RuntimeError(f"render timeline gagal: {result.stderr[-400:]}")
    if progress_cb:
        progress_cb(100.0, "klip selesai")
    return out
