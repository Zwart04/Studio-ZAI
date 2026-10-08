"""Safe ASS overrides shared by caption previews and exports."""
from __future__ import annotations

import math
import re
from typing import Any

FONTS = ("Inter", "Anton", "Barlow Condensed", "DM Serif Display", "Kalam")
ANIMATIONS = ("none", "pop", "fade", "rise", "zoom", "type")


def number(value: Any, fallback: float, low: float, high: float) -> float:
    try:
        result = float(value)
        return max(low, min(high, result)) if math.isfinite(result) else fallback
    except (ValueError, TypeError):
        return fallback


def tags(style: dict, scale: float, width: int, height: int, *, position: bool = True) -> str:
    result = ""
    if style.get("font") in FONTS:
        result += rf"\fn{style['font']}"
    if "size" in style:
        result += rf"\fs{number(style['size'], 56, 14, 160) * scale:.1f}"
    color = str(style.get("color", ""))
    if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        result += rf"\c&H{color[5:7]}{color[3:5]}{color[1:3]}&"
    if "bold" in style:
        result += rf"\b{1 if style['bold'] else 0}"
    if position and ("x" in style or "y" in style):
        x = number(style.get("x"), .5, .05, .95) * width
        y = number(style.get("y"), .82, .05, .95) * height
        if style.get("animation") == "rise":
            result += rf"\an5\move({x:.0f},{y + height * .04:.0f},{x:.0f},{y:.0f},0,220)"
        else:
            result += rf"\an5\pos({x:.0f},{y:.0f})"
    animation = style.get("animation")
    result += {"pop": r"\fscx75\fscy75\t(0,130,\fscx108\fscy108)\t(130,220,\fscx100\fscy100)",
               "fade": r"\fad(150,120)", "zoom": r"\fscx85\fscy85\t(0,300,\fscx100\fscy100)",
               "rise": r"\fad(100,80)"}.get(animation, "")
    return result


def text(caption, preset: dict, width: int, height: int) -> str:
    from .subtitle import _karaoke_text, ass_escape
    scale = height / 1920
    base = caption.style or {}
    if not base and not any(w.get("style") for w in caption.words):
        return str(preset.get("anim", "")) + _karaoke_text(caption, preset)
    prefix = "{" + tags(base, scale, width, height) + "}" if base else str(preset.get("anim", ""))
    if not caption.words:
        return prefix + ass_escape(caption.text)
    parts = []
    cursor = caption.start
    for word in caption.words:
        style = {**base, **(word.get("style") or {})}
        override = r"\rDefault" + tags(style, scale, width, height, position=False)
        start = number(word.get("start"), cursor, caption.start, caption.end)
        end = number(word.get("end"), start, start, caption.end)
        if style.get("animation") == "type":
            at = round((start - caption.start) * 1000)
            override += rf"\alpha&HFF&\t({at},{at + 1},\alpha&H00&)"
        elif preset.get("karaoke"):
            # Explicit start also preserves pauses between recognized words.
            override += rf"\kt{round((start - caption.start) * 100)}\k{max(1, round((end - start) * 100))}"
        parts.append("{" + override + "}" + ass_escape(str(word.get("word", ""))))
        cursor = end
    return prefix + " ".join(parts)


def events(caption, preset: dict, width: int, height: int) -> list[str]:
    import copy

    from .subtitle import ass_timestamp
    def event(start, end, row, name="Default"):
        return f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},{name},,0,0,0,,{text(row, preset, width, height)}"
    mode = (caption.style or {}).get("mode", "line")
    if mode not in {"word", "box", "highlight"}:
        return [event(caption.start, max(caption.end, caption.start + .2), caption)]
    words = caption.words
    if not words:
        tokens = caption.text.split()
        span = (caption.end - caption.start) / max(1, len(tokens))
        words = [{"word": w, "start": caption.start + i * span, "end": caption.start + (i + 1) * span} for i, w in enumerate(tokens)]
    result = []
    cursor = caption.start
    for index, word in enumerate(words):
        start = number(word.get("start"), cursor, caption.start, caption.end)
        end = number(word.get("end"), start, start, caption.end)
        if end <= start:
            continue
        row = copy.deepcopy(caption)
        if mode == "highlight":
            row.words = copy.deepcopy(words)
            color = caption.style.get("highlight", "#abff66")
            row.words[index]["style"] = {**row.words[index].get("style", {}), "color": color}
            if start > cursor:
                result.append(event(cursor, start, caption))
        else:
            row.text = str(word.get("word", ""))
            row.words = []
            row.style = {**caption.style, **word.get("style", {})}
            if mode == "box":
                color = str(row.style.get("boxColor", "#111111"))
                row.style["boxColor"] = color if re.fullmatch(r"#[0-9a-fA-F]{6}", color) else "#111111"
        rendered = event(start, end, row, "ActiveBox" if mode == "box" else "Default")
        if mode == "box":
            color = row.style.get("boxColor", "#111111")
            rendered = rendered.replace(",,0,0,0,,", f",,0,0,0,,{{\\3c&H{color[5:7]}{color[3:5]}{color[1:3]}&}}")
        result.append(rendered)
        cursor = end
    if mode == "highlight" and cursor < caption.end:
        result.append(event(cursor, caption.end, caption))
    return result
