"""Subtitle building: word grouping plus SRT / VTT / ASS (burned-in) output.

ASS dipakai untuk SEMUA teks di video (caption otomatis maupun item track teks
dari editor timeline). Alasannya: satu berkas gaya bisa memuat banyak style
(template tipografi), penempatan bebas lewat ``\\pos``, dan hasilnya identik di
desktop maupun Android — tanpa perlu menyalin font lewat filter ``drawtext``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..utils.text import ass_timestamp, srt_timestamp, vtt_timestamp

# Caption dibuat lebih pendek dan margin lebih lega daripada versi lama
# (42 karakter / margin 60) — pada kanvas 1080x1920 teks sepanjang itu melebihi
# area aman dan terlihat terpotong di tepi.
DEFAULT_MAX_WORDS = 5
DEFAULT_MAX_CHARS = 28
DEFAULT_GAP = 0.7
DEFAULT_MAX_DURATION = 3.5
DEFAULT_MARGIN_H = 90

# Template tipografi. Semua ukuran ditulis untuk kanvas tinggi 1920 lalu
# diskalakan otomatis (lihat to_ass), jadi tetap proporsional di kanvas lain.
PRESETS: dict[str, dict[str, Any]] = {
    "clean": {
        "label": "Clean",
        "font": "Inter",
        "size": 56,
        "primary": "&H00FFFFFF",
        "secondary": "&H00FFFFFF",
        "outline_colour": "&H00101010",
        "bold": 0,
        "outline": 3,
        "shadow": 1,
        "border_style": 1,
        "margin_v": 220,
        "karaoke": False,
        "anim": r"{\fad(120,120)}",
    },
    "bold_highlight": {
        "label": "Bold highlight",
        "font": "Inter",
        "size": 68,
        "primary": "&H00FFFFFF",
        "secondary": "&H0000E1FF",
        "outline_colour": "&H00101010",
        "bold": -1,
        "outline": 4,
        "shadow": 1,
        "border_style": 1,
        "margin_v": 250,
        "karaoke": True,
        "anim": "",
    },
    "tiktok_pop": {
        "label": "TikTok pop",
        "font": "Inter",
        "size": 76,
        "primary": "&H00FFFFFF",
        "secondary": "&H0000E1FF",
        "outline_colour": "&H00000000",
        "bold": -1,
        "outline": 5,
        "shadow": 2,
        "border_style": 1,
        "margin_v": 300,
        "karaoke": True,
        "anim": r"{\fad(80,80)\fscx94\fscy94\t(0,150,\fscx100\fscy100)}",
    },
    "karaoke_fill": {
        "label": "Karaoke fill",
        "font": "Inter",
        "size": 66,
        "primary": "&H00FFFFFF",
        "secondary": "&H0000D158",
        "outline_colour": "&H00101010",
        "bold": -1,
        "outline": 3,
        "shadow": 1,
        "border_style": 1,
        "margin_v": 250,
        "karaoke": True,
        "anim": "",
    },
    "title_card": {
        "label": "Title card",
        "font": "Inter",
        "size": 96,
        "primary": "&H00FFFFFF",
        "secondary": "&H00FFFFFF",
        "outline_colour": "&H00101010",
        "bold": -1,
        "outline": 4,
        "shadow": 2,
        "border_style": 1,
        "margin_v": 0,
        "karaoke": False,
        "anim": r"{\fad(160,160)}",
    },
    "minimal_lower": {
        "label": "Minimal lower",
        "font": "Inter",
        "size": 44,
        "primary": "&H00F2F2F7",
        "secondary": "&H00F2F2F7",
        "outline_colour": "&H00101010",
        "bold": 0,
        "outline": 2,
        "shadow": 0,
        "border_style": 1,
        "margin_v": 140,
        "karaoke": False,
        "anim": r"{\fad(100,100)}",
    },
    "neon": {
        "label": "Neon",
        "font": "Inter",
        "size": 70,
        "primary": "&H00FFFFFF",
        "secondary": "&H00FF453A",
        "outline_colour": "&H00FF453A",
        "bold": -1,
        "outline": 5,
        "shadow": 4,
        "border_style": 1,
        "margin_v": 260,
        "karaoke": False,
        "anim": r"{\fad(120,120)}",
    },
    "subtitle_box": {
        "label": "Subtitle box",
        "font": "Inter",
        "size": 54,
        "primary": "&H00FFFFFF",
        "secondary": "&H00FFFFFF",
        "outline_colour": "&H99000000",
        "bold": 0,
        "outline": 12,
        "shadow": 0,
        "border_style": 3,
        "margin_v": 220,
        "karaoke": False,
        "anim": r"{\fad(120,120)}",
    },
}

DEFAULT_PRESET = "clean"

# Creator-style templates use bundled OFL fonts and distinct render colors.
# Generate the Android mirror with tools/sync_text_presets.py after changes.
for _id, _label, _font, _color, _outline, _box, _category, _sample in [
    ("viral_yellow", "Viral Yellow", "Anton", "#FFE55C", "#111111", False, "Pop", "MAKE IT HAPPEN"),
    ("mint_punch", "Mint Punch", "Anton", "#79F2C0", "#10261F", False, "Pop", "STAY CREATIVE"),
    ("pink_pop", "Pink Pop", "Barlow Condensed", "#FF8FD8", "#4A143A", False, "Pop", "YOUR MOMENT"),
    ("ice_blue", "Ice Blue", "Anton", "#A4E8FF", "#123D61", False, "Pop", "NEXT LEVEL"),
    ("orange_burst", "Orange Burst", "Anton", "#FFAE54", "#451E0B", False, "Pop", "LET'S GO"),
    ("lilac_glow", "Lilac Glow", "Barlow Condensed", "#E7C3FF", "#783CAE", False, "Neon", "AFTER HOURS"),
    ("cyan_neon", "Cyan Neon", "Barlow Condensed", "#E9FFFF", "#00BFD6", False, "Neon", "LIGHT IT UP"),
    ("rose_neon", "Rose Neon", "Barlow Condensed", "#FFF3FA", "#F02B89", False, "Neon", "FEEL THE VIBE"),
    ("editorial_cream", "Editorial", "DM Serif Display", "#FFEAC5", "#282016", False, "Editorial", "A little magic"),
    ("cinema_white", "Cinema", "DM Serif Display", "#FFFFFF", "#111111", False, "Editorial", "Every frame matters"),
    ("handwritten", "Handwritten", "Kalam", "#FFF0A1", "#2C2612", False, "Editorial", "made with love"),
    ("ink_note", "Ink Note", "Kalam", "#AADFD2", "#101C1A", False, "Editorial", "one more story"),
    ("yellow_label", "Yellow Label", "Barlow Condensed", "#171717", "#FFE55C", True, "Label", "SAVE THIS TIP"),
    ("pink_label", "Pink Label", "Barlow Condensed", "#311529", "#FFA9DB", True, "Label", "GOOD TO KNOW"),
    ("mint_label", "Mint Label", "Barlow Condensed", "#112A23", "#91EDCC", True, "Label", "QUICK TUTORIAL"),
    ("news_flash", "News Flash", "Anton", "#FFFFFF", "#D92D40", True, "Label", "THE BIG UPDATE"),
    ("podcast_white", "Podcast Bold", "Anton", "#FFFFFF", "#121212", False, "Pop", "INI INTINYA"),
    ("coral_caption", "Coral Caption", "Barlow Condensed", "#FFB49E", "#25150F", False, "Pop", "CERITA HARI INI"),
    ("paper_note", "Paper Note", "Kalam", "#FFFFFF", "#182333", False, "Editorial", "Catatan kecil"),
    ("serif_story", "Serif Story", "DM Serif Display", "#DCE8FF", "#15243A", False, "Editorial", "Di balik cerita"),
    ("white_label", "White Label", "Anton", "#161616", "#FFFFFF", True, "Label", "SATU HAL PENTING"),
    ("blue_label", "Blue Label", "Barlow Condensed", "#FFFFFF", "#174C83", True, "Label", "COBA CARA INI"),
]:
    def _ass_color(hex_color: str) -> str:
        return "&H00" + hex_color[5:7] + hex_color[3:5] + hex_color[1:3]

    PRESETS[_id] = {
        **PRESETS["clean"], "label": _label, "font": _font, "size": 76,
        "primary": _ass_color(_color), "secondary": _ass_color(_color),
        "outline_colour": _ass_color(_outline), "bold": 0 if _font in ("Anton", "DM Serif Display") else -1,
        "outline": 10 if _box else (4 if _category == "Pop" else 2),
        "shadow": 4 if _category == "Neon" else 0, "border_style": 3 if _box else 1,
        "sample": _sample, "category": _category, "preview_color": _color,
        "preview_outline": _outline, "italic": _font == "DM Serif Display",
        "anim": PRESETS["tiktok_pop"]["anim"] if _category == "Pop" else PRESETS["clean"]["anim"],
    }

# Posisi subtitle. "off" = jangan bakar subtitle sama sekali (dipakai kalau
# video sumber sudah punya subtitle bawaan, mis. dari YouTube).
POSITIONS: dict[str, int] = {"bottom": 2, "middle": 5, "top": 8}
POSITION_CHOICES = ("bottom", "middle", "top", "off")


def preset_list() -> list[dict[str, Any]]:
    """Daftar template untuk galeri di UI."""
    return [{"id": key, "label": value.get("label", key),
             "font": value.get("font", "Inter"), "category": value.get("category", "Essential"),
             "size": value.get("size", 76), "bold": bool(value.get("bold", 0)), "karaoke": bool(value.get("karaoke")),
             "sample": value.get("sample", "Tell your story"),
             "color": value.get("preview_color", "#FFFFFF"),
             "outline": value.get("preview_outline", "#161B22"),
             "box": "yes" if value.get("border_style") == 3 else "no",
             "italic": "yes" if value.get("italic") else "no"}
            for key, value in PRESETS.items()]


def template_id(name: Any) -> str:
    """Nama template yang aman dipakai sebagai nama style ASS.

    Dipakai di dua tempat (pembuatan style dan event Dialogue) supaya keduanya
    selalu menunjuk style yang sama — kalau tidak, event bisa merujuk style yang
    tidak pernah dibuat dan libass diam-diam memakai Default.
    """
    text = str(name or DEFAULT_PRESET)
    if text.startswith("custom_") and text not in PRESETS:
        from .. import typography
        PRESETS.update(typography.load())
    return text if text in PRESETS else DEFAULT_PRESET


@dataclass
class Caption:
    start: float
    end: float
    text: str
    words: list[dict[str, Any]] = field(default_factory=list)
    style: dict[str, Any] = field(default_factory=dict)
    timing_quality: str = "unknown"

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "text": self.text,
            "words": self.words,
            "style": self.style,
            **({"timing_quality": self.timing_quality} if self.timing_quality != "unknown" else {}),
        }


# Kata/efek non-ucapan yang sering ditulis model ASR sebagai "kata".
_SOUND_WORDS = (
    "laughter|applause|music|cheering|snickering|giggle|cough|laughs|"
    "tawa|tepuk|musik|sorak|batuk|tertawa|bertepuk"
)

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]"
)


def clean_caption_text(text: str) -> str:
    """Bersihkan teks caption dari tag suara/emoji agar sesuai ucapan.

    Model ASR sering menulis ``[Musik]``, ``(tertawa)``, ``*cheering*`` atau
    emoji sebagai bagian transkrip. Tanpa dibersihkan, teks itu ikut terbakar
    ke subtitle dan terlihat "tidak sesuai ucapan". Tanda baca wajar
    (! ? . , : ; - ' ") dipertahankan; hanya pola non-ucapan yang dibuang.
    """
    if not text:
        return ""
    # Kurung hanya dibuang bila isinya kata suara; jika tidak, dipertahankan.
    cleaned = re.sub(r"\((?:[^()]*?)\)", lambda m: " " if re.search(
        rf"(?i)\b({_SOUND_WORDS})\b", m.group(0)) else m.group(0), text)
    cleaned = re.sub(r"\[.*?\]|\*.*?\*", " ", cleaned)
    cleaned = re.sub(rf"\b({_SOUND_WORDS})\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = _EMOJI_RE.sub("", cleaned)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


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
        text = clean_caption_text(str(word.get("word", "")))
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
        text = clean_caption_text(str(segment.get("text", "")))
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
        at = max(0, round((float(word["start"]) - caption.start) * 100))
        parts.append(f"{{\\kt{at}\\kf{duration_cs}}}{ass_escape(str(word['word']))}")
    return " ".join(parts)


def _style_line(name: str, style: dict[str, Any], scale: float, alignment: int, margin_v: int) -> str:
    # Nilai ditulis satu per satu (bukan **style) karena style juga memuat
    # "margin_v" dari preset — menyebarnya bersama margin_v hasil hitungan
    # membuat str.format menerima argumen ganda.
    values = {
        "name": name,
        "font": style.get("font", "Inter"),
        "size": max(10, round(style.get("size", 56) * scale)),
        "primary": style.get("primary", "&H00FFFFFF"),
        "secondary": style.get("secondary", "&H00FFFFFF"),
        "outline_colour": style.get("outline_colour", "&H00101010"),
        "bold": style.get("bold", 0),
        "italic": -1 if style.get("italic") else 0,
        "border": style.get("border_style", 1),
        "outline": round(style.get("outline", 3) * scale, 2),
        "shadow": round(style.get("shadow", 1) * scale, 2),
        "align": alignment,
        "margin_h": int(DEFAULT_MARGIN_H * scale),
        "margin_v": margin_v,
    }
    return (
        "Style: {name},{font},{size},{primary},{secondary},{outline_colour},&H80000000,"
        "{bold},{italic},0,0,100,100,0,0,{border},{outline},{shadow},{align},"
        "{margin_h},{margin_h},{margin_v},1"
    ).format(**values)


def text_item_events(text_items: Sequence[dict[str, Any]], width: int, height: int) -> list[str]:
    """Event ASS untuk item track teks pada timeline.

    ``x``/``y`` adalah rasio 0..1 terhadap kanvas; dikonversi ke ``\\pos`` agar
    penempatan tetap sama di resolusi apa pun.
    """
    events: list[str] = []
    for item in text_items or []:
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        template = template_id(item.get("template"))
        start = float(item.get("start", 0.0))
        end = max(start + 0.2, float(item.get("end", start + 2.0)))
        x = int(max(0.0, min(1.0, float(item.get("x", 0.5)))) * width)
        y = int(max(0.0, min(1.0, float(item.get("y", 0.5)))) * height)
        anim = PRESETS[template].get("anim", "")
        from .caption_style import number, tags
        item_style = item.get("style") or {}
        if item_style:
            anim = "{" + tags({**item_style, "x": item.get("x", .5), "y": item.get("y", .5)}, height / 1920, width, height) + "}"
        size = number(item.get("fontSize") or PRESETS[template].get("size", 56), 56, 14, 160) * height / 1920
        alpha = round((1 - number(item.get("opacity"), 1, 0, 1)) * 255)
        events.append(
            f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},Tpl_{template},,0,0,0,,"
            f"{{\\an5\\pos({x},{y})}}{{\\fs{size:.1f}\\alpha&H{alpha:02X}&}}{anim}{ass_escape(text)}"
        )
    return events


def to_ass(
    captions: Sequence[Caption],
    preset: str = DEFAULT_PRESET,
    play_res: tuple[int, int] = (1080, 1920),
    title: str = "Studio ZAI",
    position: str = "bottom",
    text_items: Sequence[dict[str, Any]] | None = None,
) -> str:
    style = dict(PRESETS[template_id(preset)])
    width, height = play_res
    scale = height / 1920.0  # semua ukuran preset ditulis untuk tinggi 1920

    alignment = POSITIONS.get(position, 2)
    if position == "middle":
        margin_v = 0
    elif position == "top":
        margin_v = int(150 * scale)
    else:
        margin_v = int(style.get("margin_v", 220) * scale)

    styles = [_style_line("Default", style, scale, alignment, margin_v)]
    styles.append(_style_line("ActiveBox", {**style, "border_style": 3, "outline": 10}, scale, alignment, margin_v))
    # Satu style per template yang benar-benar dipakai item teks.
    used_templates = sorted({template_id(i.get("template")) for i in (text_items or [])})
    for template in used_templates:
        template_style = dict(PRESETS[template])
        styles.append(_style_line(f"Tpl_{template}", template_style, scale, 5, 0))

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
        *styles,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    events: list[str] = []
    if position != "off":
        for caption in captions:
            from dataclasses import replace

            from .caption_style import events as styled_events
            positioned = replace(caption, style={"x": .5, "y": {"top": .15, "middle": .5}.get(position, .82), **(caption.style or {})})
            events.extend(styled_events(positioned, style, width, height))
    events.extend(text_item_events(text_items or [], width, height))
    return "\n".join(header + events) + "\n"


def write_subtitles(
    captions: Sequence[Caption],
    out_dir: str | Path,
    stem: str,
    preset: str = DEFAULT_PRESET,
    play_res: tuple[int, int] = (1080, 1920),
    position: str = "bottom",
    text_items: Sequence[dict[str, Any]] | None = None,
) -> dict[str, str]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    srt_path = out_dir / f"{stem}.srt"
    vtt_path = out_dir / f"{stem}.vtt"
    ass_path = out_dir / f"{stem}.ass"
    srt_path.write_text(to_srt(captions), encoding="utf-8")
    vtt_path.write_text(to_vtt(captions), encoding="utf-8")
    ass_path.write_text(
        to_ass(captions, preset, play_res, position=position, text_items=text_items),
        encoding="utf-8",
    )
    return {"srt": str(srt_path), "vtt": str(vtt_path), "ass": str(ass_path)}


def captions_dict(captions: Sequence[Caption]) -> list[dict[str, Any]]:
    return [c.as_dict() for c in captions]
