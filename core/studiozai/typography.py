"""Small, validated user typography presets; no arbitrary ASS instructions."""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from . import config

FONTS = ("Inter", "Anton", "Barlow Condensed", "DM Serif Display", "Kalam")


def load() -> dict[str, dict[str, Any]]:
    path = config.data_dir() / "typography.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def create(values: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    def colour(key: str, default: str) -> tuple[str, str]:
        value = str(values.get(key, default)).upper()
        if not re.fullmatch(r"#[0-9A-F]{6}", value):
            raise ValueError(f"Warna {key} harus berbentuk #RRGGBB")
        return value, f"&H00{value[5:7]}{value[3:5]}{value[1:3]}"

    font = values.get("font", "Inter")
    if font not in FONTS:
        raise ValueError("Font tidak tersedia")
    name = str(values.get("name", "Template saya")).strip()[:48]
    primary_hex, primary = colour("color", "#FFFFFF")
    outline_hex, outline = colour("outline_color", "#000000")
    _, secondary = colour("highlight", "#FFFFFF")
    style = {
        "label": name or "Template saya", "font": font,
        "size": max(24, min(144, float(values.get("size", 64)))),
        "primary": primary, "secondary": secondary, "outline_colour": outline,
        "outline": max(0, min(10, float(values.get("outline", 3)))),
        "shadow": 1, "bold": -1 if values.get("bold", True) else 0,
        "border_style": 3 if values.get("box") else 1,
        "karaoke": bool(values.get("karaoke")), "anim": "", "margin_v": 220,
        "preview_color": primary_hex, "preview_outline": outline_hex,
        "category": "Custom", "sample": "Your words. Your style.",
    }
    key = "custom_" + uuid.uuid4().hex[:12]
    presets = load()
    presets[key] = style
    (config.data_dir() / "typography.json").write_text(json.dumps(presets, ensure_ascii=False, indent=2), encoding="utf-8")
    return key, style
