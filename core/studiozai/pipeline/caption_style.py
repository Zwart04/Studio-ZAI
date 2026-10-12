"""Safe ASS overrides shared by caption previews and exports."""
from __future__ import annotations

import math
import re
from typing import Any

FONTS = ("Inter", "Anton", "Barlow Condensed", "DM Serif Display", "Kalam")
ANIMATIONS = ("none", "pop", "bounce", "fade", "rise", "zoom", "type", "typewriter")

# Mode "highlight" meniru animasi kata aktif dari cheat-clip-pro: kata dikemas
# ke potongan pendek satu baris, lalu dipotong menjadi irisan waktu yang saling
# bersambung sehingga sorotan tidak pernah berkedip di sela jeda bicara.
# Angka-angka di bawah persis milik cheat-clip-pro (video_engine.py).
CHUNK_MAX_WORDS = 3       # maksimum kata per potongan -> dijamin satu baris
CHUNK_MAX_CHARS = 22      # maksimum karakter per potongan
CHUNK_PAUSE = 0.38        # jeda bicara (detik) yang memecah potongan
CHUNK_MIN_DURATION = 0.35 # panjang minimum satu potongan
CHUNK_TAIL_PAD = 0.12     # ekor potongan agar kata terakhir tidak terpotong
CHUNK_GAP = 0.28          # jarak minimum antar potongan yang saling dorong
SLICE_MIN = 0.16          # irisan minimum per kata (menahan mikro-kedip)


def number(value: Any, fallback: float, low: float, high: float) -> float:
    try:
        result = float(value)
        return max(low, min(high, result)) if math.isfinite(result) else fallback
    except (ValueError, TypeError):
        return fallback


def tags(style: dict, scale: float, width: int, height: int, *, position: bool = True) -> str:
    result = ""
    # \q2 = tanpa wrap. Mode highlight selalu memakai potongan <= CHUNK_MAX_CHARS
    # sehingga teks dijamin tetap satu baris (cheat-clip-pro memasang \q2 pada
    # setiap Dialogue-nya). Diletakkan setelah \rDefault di pemanggilan kata.
    if style.get("nowrap"):
        result += r"\q2"
    if style.get("font") in FONTS:
        result += rf"\fn{style['font']}"
    if "size" in style:
        result += rf"\fs{number(style['size'], 56, 14, 160) * scale:.1f}"
    color = str(style.get("color", ""))
    if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        result += rf"\c&H{color[5:7]}{color[3:5]}{color[1:3]}&"
    if "bold" in style:
        result += rf"\b{1 if style['bold'] else 0}"
    if position and ("x" in style or "y" in style or style.get("animation") == "rise"):
        x = number(style.get("x"), .5, .05, .95) * width
        y = number(style.get("y"), .82, .05, .95) * height
        if style.get("animation") == "rise":
            result += rf"\an5\move({x:.0f},{y + height * .04:.0f},{x:.0f},{y:.0f},0,220)"
        else:
            result += rf"\an5\pos({x:.0f},{y:.0f})"
    animation = style.get("animation")
    result += {"pop": r"\fscx75\fscy75\t(0,130,\fscx108\fscy108)\t(130,220,\fscx100\fscy100)",
               "bounce": r"\fscy70\t(0,100,\fscy120)\t(100,220,\fscy100)",
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
        if style.get("animation") in {"type", "typewriter"}:
            at = round((start - caption.start) * 1000)
            override += rf"\alpha&HFF&\t({at},{at + 1},\alpha&H00&)"
        elif preset.get("karaoke") or base.get("mode") == "karaoke":
            # Explicit start also preserves pauses between recognized words.
            override += rf"\kt{round((start - caption.start) * 100)}\kf{max(1, round((end - start) * 100))}"
            if base.get("mode") == "karaoke":
                for tag, value, fallback in (("1c", base.get("highlight"), "#abff66"), ("2c", style.get("color"), "#ffffff")):
                    color = str(value)
                    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                        color = fallback
                    override += rf"\{tag}&H{color[5:7]}{color[3:5]}{color[1:3]}&"
        parts.append("{" + override + "}" + ass_escape(str(word.get("word", ""))))
        cursor = end
    return prefix + " ".join(parts)


def _normalized_words(caption, words) -> list[dict]:
    """Kata dengan start/end yang sudah di-clamp ke jendela caption."""
    result = []
    cursor = caption.start
    for word in words:
        start = number(word.get("start"), cursor, caption.start, caption.end)
        end = number(word.get("end"), start, start, caption.end)
        if end <= start:
            continue
        result.append({**word, "start": start, "end": end})
        cursor = end
    return result


def _pack_chunks(words: list[dict]) -> list[list[dict]]:
    """Kemas kata ke potongan 1-3 kata / <=22 karakter.

    Pecah pada jeda bicara >= CHUNK_PAUSE atau tanda akhir kalimat, supaya kata
    tidak menggantung di tengah keheningan (resep cheat-clip-pro).
    """
    chunks: list[list[dict]] = []
    current: list[dict] = []
    chars = 0
    for item in words:
        token = str(item.get("word", ""))
        paused = bool(current) and (item["start"] - current[-1]["end"]) >= CHUNK_PAUSE
        sentence = bool(current) and str(current[-1].get("word", "")).endswith((".", "?", "!"))
        if len(current) >= CHUNK_MAX_WORDS or paused or sentence or (current and chars + len(token) > CHUNK_MAX_CHARS):
            chunks.append(current)
            current, chars = [item], len(token)
        else:
            current.append(item)
            chars += len(token) + 1
    if current:
        chunks.append(current)
    return chunks


def _chunk_bounds(chunks: list[list[dict]], caption) -> list[tuple[float, float]]:
    """Batas tiap potongan: monoton, tidak saling tumpang tindih, di-clamp caption."""
    bounds: list[list[float]] = []
    for chunk in chunks:
        start = chunk[0]["start"]
        end = max(start + CHUNK_MIN_DURATION, chunk[-1]["end"] + CHUNK_TAIL_PAD)
        if bounds:
            previous_end = bounds[-1][1]
            start = max(start, previous_end)
            if end <= start:
                end = start + CHUNK_GAP
        bounds.append([start, end])
    for index in range(len(bounds) - 1):
        current, following = bounds[index], bounds[index + 1]
        if current[1] > following[0]:
            split = max(current[0] + CHUNK_GAP, following[0])
            current[1] = split
            if following[0] < split:
                following[0] = split
                following[1] = max(split + CHUNK_GAP, following[1])
    # Caption Studio ZAI berdiri berdampingan, jadi potongan yang boleh melewati
    # caption.end akan menabrak Dialogue pertama caption berikutnya.
    return [(min(max(s, caption.start), caption.end), min(max(e, s), caption.end)) for s, e in bounds]


def _word_slices(chunk: list[dict], start: float, end: float) -> list[tuple[float, float]]:
    """Irisan waktu kata yang saling bersambung (tanpa jeda kosong)."""
    if end <= start:
        return []
    count = len(chunk)
    if count == 1:
        return [(start, end)]
    points = [start]
    for index in range(1, count):
        raw = chunk[index]["start"]
        lowest = points[-1] + SLICE_MIN
        highest = end - SLICE_MIN * (count - index)
        if lowest > highest:
            point = points[-1] + (end - points[-1]) / (count - index + 1)
        else:
            point = max(lowest, min(highest, raw))
        points.append(point)
    points.append(end)
    return [(points[k], points[k + 1]) for k in range(count)]


def _highlight_events(caption, words, event, copy) -> list[str]:
    """Satu Dialogue per irisan: teks potongan, hanya kata aktif yang diwarnai."""
    color = str((caption.style or {}).get("highlight", "#abff66"))
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        color = "#abff66"
    chunks = _pack_chunks(_normalized_words(caption, words))
    if not chunks:
        return []
    result = []
    for chunk, (start, end) in zip(chunks, _chunk_bounds(chunks, caption)):
        for active, (slice_start, slice_end) in enumerate(_word_slices(chunk, start, end)):
            if slice_end <= slice_start:
                continue
            row = copy.deepcopy(caption)
            row.text = " ".join(str(item.get("word", "")) for item in chunk)
            row.words = [
                {**item, "style": {**(item.get("style") or {}), "nowrap": True,
                                   **({"color": color} if index == active else {})}}
                for index, item in enumerate(chunk)
            ]
            result.append(event(slice_start, slice_end, row))
    return result


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
    if mode == "highlight":
        return _highlight_events(caption, words, event, copy)
    result = []
    cursor = caption.start
    for word in words:
        start = number(word.get("start"), cursor, caption.start, caption.end)
        end = number(word.get("end"), start, start, caption.end)
        if end <= start:
            continue
        row = copy.deepcopy(caption)
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
    return result
