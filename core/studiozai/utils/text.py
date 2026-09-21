"""Utility helpers."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str, fallback: str = "clip", max_length: int = 80) -> str:
    """Make any string safe to use as a file name (blocks path traversal)."""
    name = unicodedata.normalize("NFKC", name or "")
    name = name.replace("..", ".")
    name = UNSAFE_CHARS.sub("_", name)
    name = name.strip(" ._")
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"-{2,}", "-", name)
    if len(name) > max_length:
        name = name[:max_length].rstrip("-_.")
    return name or fallback


def safe_join(directory: Path, name: str) -> Path:
    """Join directory + sanitized name and assert the result stays inside directory."""
    directory = Path(directory).resolve()
    target = (directory / sanitize_filename(name)).resolve()
    if directory != target and directory not in target.parents:
        raise ValueError(f"unsafe path: {name!r}")
    return target


def srt_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def vtt_timestamp(seconds: float) -> str:
    return srt_timestamp(seconds).replace(",", ".")


def ass_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    cs = round(seconds * 100)
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6_000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def clock(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def human_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024 or unit == "TB":
            return f"{num_bytes:.0f} {unit}" if unit in ("B", "KB") else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"
