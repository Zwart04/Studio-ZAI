"""Subtitle building: word grouping plus SRT / VTT / ASS (burned-in) output."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..utils.text import ass_timestamp, srt_timestamp, vtt_timestamp

DEFAULT_MAX_WORDS = 6
DEFAULT_MAX_CHARS = 42
DEFAULT_GAP = 0.7
DEFAULT_MAX_DURATION = 3.5

PRESETS: dict[str, dict[str, Any]] = {
    "clean": {
        "font": "Inter",
        "size": 64,
        "primary": "&H00FFFFFF",
        "secondary": "&H00FFFFFF",
        "outline_colour": "&H00101010",
        "bold": 0,
        "outline": 3,
        "shadow": 1,
        "margin_v": 240,
        "karaoke": False,
    },
    "bold_highlight": {
        "font": "Inter",
        "size": 72,
        "primary": "&H00FFFFFF",
        "secondary": "&H0000E1FF",
        "outline_colour": "&H00101010",
        "bold": -1,
        "outline": 4,
        "shadow": 1,
        "margin_v": 260,
        "karaoke": True,
    },
}

# Posisi subtitle. "off" = jangan bakar subtitle sama sekali (dipakai kalau
# video sumber sudah punya subtitle bawaan, mis. dari YouTube).
POSITIONS: dict[str, int] = {"bottom": 2, "middle": 5, "top": 8}
POSITION_CHOICES = ("bottom", "middle", "top", "off")


@dataclass
class Caption:
    start: float
    end: float
    text: str
    words: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "text": self.text,
            "words": self.words,
        }


def group_words(
    words: Sequence[dict[str, Any]],
    max_words: int = DEFAULT_MAX_WORDS,
    max_chars: int = DEFAULT_MAX_CHARS,
    gap: float = DEFAULT_GAP,
    max_duration: float = DEFAULT_MAX_DURATION,
) -> list[Caption]:
    """Split word timestamps into readable captions (deterministic)."""
    captions: list[Caption] = []
    buffer: list[dict[str, Any]] = []

    def flush() -> None:
        if not buffer:
            return
        text = " ".join(w["word"] for w in buffer).strip()
        captions.append(
            Caption(
                start=float(buffer[0]["start"]),
                end=float(buffer[-1]["end"]),
                text=text,
                words=[dict(w) for w in buffer],
            )
        )
        buffer.clear()

    for word in words:
        text = str(word.get("word", "")).strip()
        if not text:
            continue
        if buffer:
            joined = " ".join([w["word"] for w in buffer] + [text])
            too_long = len(joined) > max_chars
            too_many = len(buffer) >= max_words
            big_gap = float(word.get("start", 0)) - float(buffer[-1].get("end", 0)) > gap
            too_slow = float(word.get("end", 0)) - float(buffer[0].get("start", 0)) > max_duration
            ends_sentence = bool(re.search(r"[.!?…]$", buffer[-1]["word"]))
            if too_long or too_many or big_gap or too_slow or ends_sentence:
                flush()
        buffer.append({"word": text, "start": float(word.get("start", 0)), "end": float(word.get("end", 0))})
    flush()
    return captions


def _split_plain_text(text: str, max_words: int, max_chars: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for token in text.split():
        candidate = " ".join(current + [token])
        if current and (len(candidate) > max_chars or len(current) >= max_words):
            chunks.append(" ".join(current))
            current = [token]
        else:
            current.append(token)
    if current:
        chunks.append(" ".join(current))
    return chunks


def captions_from_segments(
    segments: Iterable[dict[str, Any]],
    max_words: int = DEFAULT_MAX_WORDS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[Caption]:
    """Build captions from transcript segments; uses word timings when available."""
    captions: list[Caption] = []
    for segment in segments:
        words = segment.get("words") or []
        if words:
            captions.extend(group_words(words, max_words=max_words, max_chars=max_chars))
            continue
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        chunks = _split_plain_text(text, max_words, max_chars)
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start + 2.0))
        span = max(0.4, end - start) / max(1, len(chunks))
        for index, chunk in enumerate(chunks):
            captions.append(
                Caption(start=start + index * span, end=start + (index + 1) * span, text=chunk)
            )
    return [c for c in captions if c.text]


def to_srt(captions: Sequence[Caption]) -> str:
    lines: list[str] = []
    for index, caption in enumerate(captions, start=1):
        lines.append(str(index))
        lines.append(f"{srt_timestamp(caption.start)} --> {srt_timestamp(caption.end)}")
        lines.append(caption.text)
        lines.append("")
    return "\n".join(lines)


def to_vtt(captions: Sequence[Caption]) -> str:
    lines = ["WEBVTT", ""]
    for caption in captions:
        lines.append(f"{vtt_timestamp(caption.start)} --> {vtt_timestamp(caption.end)}")
        lines.append(caption.text)
        lines.append("")
    return "\n".join(lines)


def ass_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("\n", "\\N")
    )


def _karaoke_text(caption: Caption, preset: dict[str, Any]) -> str:
    if not preset.get("karaoke") or not caption.words:
        return ass_escape(caption.text)
    parts: list[str] = []
    for word in caption.words:
        duration_cs = max(1, round((float(word["end"]) - float(word["start"])) * 100))
        parts.append(f"{{\\k{duration_cs}}}{ass_escape(str(word['word']))}")
    return " ".join(parts)


def to_ass(
    captions: Sequence[Caption],
    preset: str = "clean",
    play_res: tuple[int, int] = (1080, 1920),
    title: str = "Studio ZAI",
    position: str = "bottom",
) -> str:
    style = dict(PRESETS.get(preset, PRESETS["clean"]))
    width, height = play_res
    # Posisi subtitle: "off" -> tidak ada event (tidak ada yang dibakar).
    alignment = POSITIONS.get(position, 2)
    scale = height / 1920.0  # margin disetel untuk kanvas 1920 tinggi
    if position == "middle":
        style["margin_v"] = 0
    elif position == "top":
        style["margin_v"] = int(150 * scale)
    else:
        style["margin_v"] = int(style["margin_v"] * scale)
    style["alignment"] = alignment
    header = [
        "[Script Info]",
        f"Title: {title}",
        "ScriptType: v4.00+",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "",
        "[V4+ Styles]",
        (
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
            "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
        ),
        (
            "Style: Default,{font},{size},{primary},{secondary},{outline_colour},&H80000000,"
            "{bold},0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},60,60,{margin_v},1".format(**style)
        ),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    events = [] if position == "off" else [
        f"Dialogue: 0,{ass_timestamp(c.start)},{ass_timestamp(max(c.end, c.start + 0.2))},Default,,0,0,0,,{_karaoke_text(c, style)}"
        for c in captions
    ]
    return "\n".join(header + events) + "\n"


def write_subtitles(
    captions: Sequence[Caption],
    out_dir: str | Path,
    stem: str,
    preset: str = "clean",
    play_res: tuple[int, int] = (1080, 1920),
    position: str = "bottom",
) -> dict[str, str]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    srt_path = out_dir / f"{stem}.srt"
    vtt_path = out_dir / f"{stem}.vtt"
    ass_path = out_dir / f"{stem}.ass"
    srt_path.write_text(to_srt(captions), encoding="utf-8")
    vtt_path.write_text(to_vtt(captions), encoding="utf-8")
    ass_path.write_text(to_ass(captions, preset, play_res, position=position), encoding="utf-8")
    return {"srt": str(srt_path), "vtt": str(vtt_path), "ass": str(ass_path)}


def captions_dict(captions: Sequence[Caption]) -> list[dict[str, Any]]:
    return [c.as_dict() for c in captions]
