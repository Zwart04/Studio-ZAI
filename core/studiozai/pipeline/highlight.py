"""Highlight detection: heuristic (no AI) scoring with an optional local-LLM ranking."""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ..utils import ffmpeg, proc

DEFAULT_MIN_LEN = 15.0
DEFAULT_MAX_LEN = 60.0
HOP_SECONDS = 0.5

# These are safety limits for unusually long sections, not user-facing target
# durations. Shorter product chapters keep their full natural length.
ADAPTIVE_SOFT_SPLIT = 155.0
ADAPTIVE_HARD_SPLIT = 180.0
ADAPTIVE_UTTERANCE_SPLIT = 90.0
_VERDICT = re.compile(
    r"\b(?:jadi|kesimpulan|menurut saya|rekomendasi|recommended|worth|layak|bagus|buruk|"
    r"lumayan|suka|mantap|overall|in conclusion|i recommend|i like|good value)\b",
    re.IGNORECASE,
)
_TOPIC_START = re.compile(
    r"\b(?:"
    r"(?:produk|speaker|barang|item|model|unit|pilihan|perangkat)\s+(?:yang\s+)?"
    r"(?:pertama|kedua|ketiga|keempat|kelima|berikutnya|selanjutnya|terakhir|termurah|termahal|ke[- ]?\d+)"
    r"\s+(?:ini|adalah)"
    r"|(?:produk|speaker|barang|item|model|unit)\s+ke[- ]?\d{1,2}\b"
    r"|(?:nomor|no\.)\s*(?:ke[- ]?)?(?:\d{1,2}|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\b"
    r"|(?:yang|sekarang)\s+(?:pertama|kedua|ketiga|keempat|kelima|keenam|ketujuh|kedelapan|"
    r"kesembilan|kesepuluh|ke[- ]?\d+|terakhir)\s+(?:ini|adalah|dulu)"
    r"|(?:first|second|third|next|last|cheapest|most expensive)\s+"
    r"(?:product|speaker|item|model|device)"
    r"|(?:sekarang|selanjutnya|berikutnya|pertama|kedua|ketiga|lanjut)\s+"
    r"(?:kita\s+)?(?:bahas|lihat|review|ulas|coba|tes|uji|masuk\s+ke)"
    r"|(?:now|next|first|second|third)\s+(?:let'?s\s+)?"
    r"(?:review|look\s+at|test|try|talk\s+about)"
    r")\b",
    re.IGNORECASE,
)

WEIGHT_LOUDNESS_AVG = 0.28
WEIGHT_LOUDNESS_PEAK = 0.22
WEIGHT_DENSITY = 0.30
WEIGHT_SILENCE = 0.10
WEIGHT_BOUNDARY = 0.10
# Bonus di luar bobot dasar (tidak menormalkan ulang skor lama):
# retensi penonton YouTube bila tersedia, dan ciri hook dari teks.
WEIGHT_HEATMAP = 0.20
WEIGHT_HOOK = 0.15

# Kata hook Indonesia + Inggris: janji, larangan, angka, rasa ingin tahu.
HOOK_WORDS = frozenset(
    ["jangan", "rahasia", "gratis", "salah", "berhenti", "awas", "terbukti", "cara", "trik", "error", "gagal", "luar", "biasa", "wajib", "penting", "akhirnya", "ternyata", "stop", "secret", "free", "mistake", "never", "always", "why", "how", "warning", "proven", "best", "worst"]
)


def hook_score(text: str) -> float:
    """Ciri hook dari teks jendela (0..1): tanya/seru, angka, kata hook."""
    words = re.findall(r"[^\W\d_]+|\d+", (text or "").lower())
    if not words:
        return 0.0
    score = 0.0
    joined = " ".join(words)
    if re.search(r"[?!]", text or ""):
        score += 0.4
    if re.search(r"\d", joined):
        score += 0.3
    hits = sum(1 for w in words if w in HOOK_WORDS)
    score += min(0.6, 0.3 * hits)
    return round(min(1.0, score), 3)


def heat_average(heatmap: Sequence[dict[str, Any]], start: float, end: float) -> float:
    """Rata-rata retensi penonton pada rentang (0..1); kosong berarti 0."""
    if not heatmap or end <= start:
        return 0.0
    total = weight = 0.0
    for point in heatmap:
        try:
            ps = float(point.get("start", 0.0))
            pe = float(point.get("end", ps))
            value = float(point.get("value", 0.0))
        except (AttributeError, TypeError, ValueError):
            continue
        overlap = max(0.0, min(end, pe) - max(start, ps))
        if overlap > 0:
            total += value * overlap
            weight += overlap
    return round(total / weight, 4) if weight else 0.0

ProgressCb = Callable[[float, str], None]


@dataclass
class ClipCandidate:
    start: float
    end: float
    score: float
    reason: str
    title: str = ""
    words: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "duration": self.duration,
            "score": round(self.score, 4),
            "reason": self.reason,
            "title": self.title,
        }


# --------------------------------------------------------------------------- audio


def _no_window_flags() -> int:
    """On Windows, prevent child process consoles from flashing on screen."""
    if sys.platform == "win32":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return 0


def decode_pcm(path: str | Path, sample_rate: int = 16000) -> np.ndarray:
    """Decode any media file to mono float32 PCM using ffmpeg."""
    cmd = [
        ffmpeg.ffmpeg_path(),
        "-hide_banner",
        "-nostdin",
        "-i",
        str(path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "f32le",
        "-",
    ]
    code, out, err = proc.run_bytes(cmd, timeout=600)
    if code != 0:
        raise RuntimeError(f"gagal mendekode audio: {err[-300:]}")
    return np.frombuffer(out, dtype=np.float32)


def rms_envelope(
    samples: np.ndarray, sample_rate: int, hop_seconds: float = HOP_SECONDS
) -> tuple[np.ndarray, np.ndarray]:
    hop = max(1, int(sample_rate * hop_seconds))
    if samples.size < hop:
        padded = np.pad(samples, (0, hop - samples.size))
    else:
        usable = samples.size - (samples.size % hop)
        padded = samples[:usable]
    frames = padded.reshape(-1, hop)
    rms = np.sqrt(np.mean(np.square(frames), axis=1) + 1e-12)
    times = np.arange(rms.size) * hop_seconds
    return times, rms.astype(np.float64)


def silent_intervals(
    samples: np.ndarray,
    sample_rate: int,
    hop_seconds: float = 0.25,
    threshold_db: float = -38.0,
    min_silence: float = 0.4,
) -> list[tuple[float, float]]:
    times, rms = rms_envelope(samples, sample_rate, hop_seconds)
    if rms.size == 0:
        return []
    peak = float(np.max(rms)) or 1e-9
    db = 20.0 * np.log10(np.maximum(rms, 1e-9) / peak)
    silent = db < threshold_db
    intervals: list[tuple[float, float]] = []
    start: float | None = None
    for index, flag in enumerate(silent):
        if flag and start is None:
            start = float(times[index])
        elif not flag and start is not None:
            intervals.append((start, float(times[index])))
            start = None
    if start is not None:
        intervals.append((start, float(times[-1]) + hop_seconds))
    return merge_intervals([(a, b) for a, b in intervals if b - a >= min_silence])


def merge_intervals(
    intervals: Iterable[tuple[float, float]], gap: float = 0.15
) -> list[tuple[float, float]]:
    ordered = sorted((float(a), float(b)) for a, b in intervals if b > a)
    merged: list[tuple[float, float]] = []
    for start, end in ordered:
        if merged and start - merged[-1][1] <= gap:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def overlap_seconds(
    intervals: Sequence[tuple[float, float]], start: float, end: float
) -> float:
    total = 0.0
    for a, b in intervals:
        total += max(0.0, min(b, end) - max(a, start))
    return total


# --------------------------------------------------------------------------- windows


def _segment_words(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    words: list[dict[str, Any]] = []
    for segment in transcript.get("segments", []):
        words.extend(segment.get("words") or [])
    return words


def sentence_windows(
    transcript: dict[str, Any],
    min_len: float = DEFAULT_MIN_LEN,
    max_len: float = DEFAULT_MAX_LEN,
    window_seconds: float = 90.0,
) -> list[dict[str, Any]]:
    """Build scoring windows aligned to whisper segment boundaries (openshorts-style).

    Windows grow segment-by-segment to ~window_seconds (toleransi 1.25x agar
    kalimat tidak terpotong), dan window berikutnya overlap ~30 detik dari
    ujung window sebelumnya — supaya momen viral tidak terbelah di tengah.
    Berbeda dari pengelompokan 1-segment-1-window yang lama: tiap window
    SELALU ditutup rapat sehingga kandidat tidak pernah "membesar" keluar batas.
    """
    segments = []
    for segment in transcript.get("segments", []):
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        start = float(segment.get("start", 0))
        end = float(segment.get("end", 0))
        if end <= start:
            continue
        segments.append((start, end, text, segment.get("words") or []))

    overlap_seconds = 30.0
    windows: list[dict[str, Any]] = []
    i = 0
    n = len(segments)
    while i < n:
        w_start = segments[i][0]
        j = i
        while j + 1 < n and segments[j + 1][1] - w_start <= window_seconds * 1.25:
            j += 1
            if segments[j][1] - w_start >= window_seconds:
                break
        w_end = segments[j][1]
        text = " ".join(seg[2] for seg in segments[i : j + 1]).strip()
        words: list[dict[str, Any]] = []
        for seg in segments[i : j + 1]:
            words.extend(seg[3])
        if text and w_end > w_start:
            windows.append(
                {
                    "start": w_start,
                    "end": w_end,
                    "duration": round(w_end - w_start, 3),
                    "text": text,
                    "words": words,
                }
            )
        if j >= n - 1:
            break
        target = w_end - overlap_seconds
        k = i + 1
        while k <= j and segments[k][0] < target:
            k += 1
        i = max(k, i + 1)

    if not windows:
        text = str(transcript.get("text", "") or "").strip()
        words = _segment_words(transcript)
        if text:
            windows.append({"start": 0.0, "end": 0.0, "duration": 0.0, "text": text, "words": words})
    return [w for w in windows if w["duration"] > 1.0 or w["duration"] == 0.0]


def _window_from_segments(segments: list[dict[str, Any]]) -> dict[str, Any]:
    start = float(segments[0]["start"])
    end = float(segments[-1]["end"])
    text = " ".join(s.get("text", "").strip() for s in segments).strip()
    words: list[dict[str, Any]] = []
    for segment in segments:
        words.extend(segment.get("words") or [])
    return {
        "start": start,
        "end": end,
        "duration": round(end - start, 3),
        "text": text,
        "words": words,
    }


def carve_clip_windows(
    window: dict[str, Any],
    silences: Sequence[tuple[float, float]],
    min_len: float = DEFAULT_MIN_LEN,
    max_len: float = DEFAULT_MAX_LEN,
) -> list[dict[str, Any]]:
    """Potong SATU scoring window menjadi kandidat klip yang SELALU dalam batas.

    Aturan: kandidat tumbuh kata-per-kata; begitu mencapai min_len, kandidat
    ditutup di jeda terdekat (batas kalimat) SELAMBATNYA max_len. Hasilnya
    kandidat tidak pernah lebih panjang dari max_len — tidak ada lagi "klip
    60+ detik membesar" seperti bug sebelumnya.
    """
    words = list(window.get("words") or [])
    if not words:
        text = str(window.get("text", "")).strip()
        if not text or window["end"] - window["start"] <= 0:
            return []
        span = window["end"] - window["start"]
        out: list[dict[str, Any]] = []
        cursor = window["start"]
        while cursor < window["end"] - 1.0:
            end = min(cursor + max_len, window["end"])
            if end - cursor < min(3.0, min_len):
                break
            chunk_words = [w for w in words if w.get("start", 0) >= cursor and w.get("end", 0) <= end]
            out.append(
                {
                    "start": round(cursor, 3),
                    "end": round(end, 3),
                    "duration": round(end - cursor, 3),
                    "text": text,
                    "words": chunk_words,
                }
            )
            cursor = end
        return out

    carved: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for word in words:
        current.append(word)
        span = float(current[-1].get("end", 0)) - float(current[0].get("start", 0))
        if span < min_len:
            continue
        # Sudah cukup panjang: tutup di sini (batas kata = batas kalimat alami).
        start = float(current[0].get("start", 0))
        end = float(current[-1].get("end", 0))
        if end - start > max_len:
            # Kata ini membuat kelebihan: tutup kandidat SEBELUM kata ini,
            # lalu mulai kandidat baru dari kata ini.
            prev = current[:-1]
            if prev:
                p_start = float(prev[0].get("start", 0))
                p_end = float(prev[-1].get("end", 0))
                if p_end - p_start >= min(5.0, min_len):
                    carved.append(
                        {
                            "start": round(p_start, 3),
                            "end": round(p_end, 3),
                            "duration": round(p_end - p_start, 3),
                            "text": " ".join(str(w.get("word", "")) for w in prev).strip(),
                            "words": list(prev),
                        }
                    )
            current = [word]
            continue
        text = " ".join(str(w.get("word", "")) for w in current).strip()
        carved.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(end - start, 3),
                "text": text,
                "words": list(current),
            }
        )
        current = []
    if current:
        start = float(current[0].get("start", 0))
        end = float(current[-1].get("end", 0))
        if end - start >= min(5.0, min_len) and end - start <= max_len:
            carved.append(
                {
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "duration": round(end - start, 3),
                    "text": " ".join(str(w.get("word", "")) for w in current).strip(),
                    "words": list(current),
                }
            )
    _ = silences  # jeda dipakai di tahap snap, bukan di sini
    return [c for c in carved if c["duration"] > 1.0]


def slide_windows(
    duration: float,
    min_len: float = DEFAULT_MIN_LEN,
    max_len: float = DEFAULT_MAX_LEN,
    step: float | None = None,
) -> list[dict[str, Any]]:
    if duration <= 0:
        return []
    length = min(max_len, max(min_len, duration))
    step = step or max(min_len, length / 2.0)
    windows: list[dict[str, Any]] = []
    start = 0.0
    while start + length <= duration + 1e-6:
        windows.append({"start": start, "end": start + length, "duration": length, "text": "", "words": []})
        start += step
    if not windows:
        windows.append({"start": 0.0, "end": duration, "duration": duration, "text": "", "words": []})
    return windows


def snap_to_words(
    start: float, end: float, words: Sequence[dict[str, Any]], tolerance: float = 2.5
) -> tuple[float, float]:
    if not words:
        return start, end
    begins = [w["start"] for w in words]
    ends = [w["end"] for w in words]
    snapped_start = min((b for b in begins if abs(b - start) <= tolerance), default=start, key=lambda b: abs(b - start))
    snapped_end = min((e for e in ends if abs(e - end) <= tolerance), default=end, key=lambda e: abs(e - end))
    if snapped_end <= snapped_start:
        return start, end
    return float(snapped_start), float(snapped_end)


def snap_clip_to_pauses(
    start: float,
    end: float,
    words: Sequence[dict[str, Any]],
    silences: Sequence[tuple[float, float]],
    duration: float,
    min_len: float = DEFAULT_MIN_LEN,
    max_len: float = DEFAULT_MAX_LEN,
    search_window: float = 1.5,
    max_lead: float = 0.35,
    max_tail: float = 0.45,
) -> tuple[float, float]:
    """Snap a clip onto word boundaries and breathe into the surrounding pauses.

    Adapted from openshorts' snap_clip_to_words: land cuts in silence so the
    clip never starts/ends mid-word. Falls back to the raw span if nothing fits.
    """
    original = (round(float(start), 3), round(float(end), 3))
    if not words:
        return original

    starts = [float(w.get("start", 0)) for w in words]
    ends = [float(w.get("end", 0)) for w in words]

    new_start = float(start)
    candidates = [s for s in starts if abs(s - new_start) <= search_window]
    if candidates:
        word_start = min(candidates, key=lambda s: abs(s - new_start))
        previous_ends = [e for e in ends if e <= word_start]
        gap = max(0.0, word_start - max(previous_ends)) if previous_ends else max_lead
        new_start = max(0.0, word_start - min(max_lead, gap / 2))

    new_end = float(end)
    candidates = [e for e in ends if abs(e - new_end) <= search_window]
    if candidates:
        word_end = min(candidates, key=lambda e: abs(e - new_end))
        next_starts = [s for s in starts if s >= word_end]
        gap = max(0.0, min(next_starts) - word_end) if next_starts else max_tail
        new_end = min(float(duration), word_end + min(max_tail, gap / 2))

    if new_end - new_start < min_len:
        later = sorted(e for e in ends if e >= new_start + min_len)
        if later and later[0] - new_start <= max_len:
            new_end = min(float(duration), later[0] + 0.2)
        else:
            return original
    if new_end - new_start > max_len:
        earlier = [e for e in ends if new_start < e <= new_start + max_len]
        new_end = (max(earlier) + 0.2) if earlier else new_start + max_len
        new_end = min(new_end, new_start + max_len, float(duration))

    if new_end <= new_start or new_end - new_start < min_len:
        return original
    return round(new_start, 3), round(new_end, 3)


def clip_count_targets(video_duration: float, requested: int) -> tuple[int, int]:
    """Floor/ceiling for clip count, scaling with source length (openshorts-style).

    Longer sources deserve more clips, but never more than the user asked for.
    """
    requested = max(1, int(requested))
    if video_duration <= 0:
        return 1, requested
    minutes = video_duration / 60.0
    low = max(1, min(requested, int(minutes // 15) + 1))
    high = max(low, requested)
    return low, high


def title_from_text(text: str, max_words: int = 7) -> str:
    words = [w for w in text.split() if w]
    if not words:
        return ""
    title = " ".join(words[:max_words])
    return title if len(words) <= max_words else f"{title}…"


def _valid_segments(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for row in transcript.get("segments") or []:
        try:
            start, end = float(row["start"]), float(row["end"])
        except (KeyError, TypeError, ValueError):
            continue
        text = str(row.get("text") or "").strip()
        if math.isfinite(start) and math.isfinite(end) and end > start and text:
            segments.append({**row, "start": start, "end": end, "text": text})
    return sorted(segments, key=lambda row: row["start"])


def _introduces_topic(segments: Sequence[dict[str, Any]], index: int) -> bool:
    current = segments[index]["text"]
    following = segments[index + 1]["text"] if index + 1 < len(segments) else ""
    # Auto captions and ASR commonly split "Nomor" and "6" across events.
    match = _TOPIC_START.search(f"{current} {following}")
    if not match or match.start() >= len(current):
        return False
    preceding = current[max(0, match.start() - 24): match.start()].lower()
    # "dari speaker pertama" is a comparison with an earlier product.
    if re.search(r"(?:dari|daripada|dibanding(?:kan)?(?:\s+dengan)?)\s*$", preceding):
        return False
    if re.search(r"\b(?:lebih\s+suka|suka|prefer|lebih\s+baik|better)\s*$", preceding):
        return False
    return re.search(r"\bnomor\s+\d+\s+ya\s+ini\b", current.lower()) is None


def _topic_start_time(segments: Sequence[dict[str, Any]], index: int) -> float:
    """Move an intro inside a Whisper segment to the first matching word."""
    row = segments[index]
    words = row.get("words") or []
    if not words:
        return float(row["start"])
    following = segments[index + 1]["text"] if index + 1 < len(segments) else ""
    match = _TOPIC_START.search(f"{row['text']} {following}")
    if not match:
        return float(row["start"])
    before = len(row["text"][:match.start()].split())
    if before >= len(words):
        return float(row["start"])
    try:
        return max(float(row["start"]), float(words[before]["start"]))
    except (TypeError, ValueError, KeyError):
        return float(row["start"])


def _adaptive_transcript_windows(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep a product/topic review intact instead of carving at a word count.

    Whisper segments often split in mid-sentence, so ordinary material is
    grouped until a sentence or pause. Explicit introductions ("produk kedua",
    "next speaker", etc.) define stronger chapter boundaries. This is a
    deterministic local fallback; an installed LLM can rank the same material.
    """
    segments = _valid_segments(transcript)
    if not segments:
        return []

    anchors = [0]
    for index, segment in enumerate(segments):
        if (index and _introduces_topic(segments, index)
                and segment["start"] - segments[anchors[-1]]["start"] >= 8.0):
            # A product can be introduced across two adjacent ASR segments.
            anchors.append(index)

    windows: list[dict[str, Any]] = []
    if len(anchors) > 1:
        for chapter_index, begin in enumerate(anchors):
            stop = anchors[chapter_index + 1] if chapter_index + 1 < len(anchors) else len(segments)
            cursor = begin
            while cursor < stop:
                first = segments[cursor]
                remainder = segments[stop - 1]["end"] - first["start"]
                if remainder <= ADAPTIVE_HARD_SPLIT:
                    cut = stop
                else:
                    possible = [
                        i for i in range(cursor + 1, stop + 1)
                        if segments[i - 1]["end"] - first["start"] <= ADAPTIVE_HARD_SPLIT
                    ]
                    if not possible:
                        cut = cursor + 1
                    else:
                        cut = min(
                            possible,
                            key=lambda i: (
                                abs(segments[i - 1]["end"] - first["start"] - ADAPTIVE_SOFT_SPLIT)
                                - (10.0 if re.search(r"[.!?]$", segments[i - 1]["text"]) else 0.0)
                                - (6.0 if _VERDICT.search(" ".join(s["text"] for s in segments[max(cursor, i - 3):i])) else 0.0)
                            ),
                        )
                window = _window_from_segments(segments[cursor:cut])
                if window["duration"] >= 3.0:
                    window["topic_intro"] = (cursor == begin and begin != 0) or (
                        cursor == 0 and _introduces_topic(segments, 0)
                    )
                    if window["topic_intro"]:
                        window["start"] = _topic_start_time(segments, cursor)
                        window["duration"] = round(window["end"] - window["start"], 3)
                    window["chapter_start"] = cursor == begin
                    windows.append(window)
                cursor = cut
    else:
        cursor = 0
        while cursor < len(segments):
            cut = cursor + 1
            while cut < len(segments):
                span = segments[cut - 1]["end"] - segments[cursor]["start"]
                last = segments[cut - 1]
                gap = segments[cut]["start"] - last["end"]
                if span >= ADAPTIVE_UTTERANCE_SPLIT or gap >= 1.0:
                    break
                if span >= 40.0 and re.search(r"[.!?]$", last["text"]):
                    break
                if span >= 15.0 and last["end"] - last["start"] >= 15.0:
                    break
                cut += 1
            window = _window_from_segments(segments[cursor:cut])
            if window["duration"] >= 3.0:
                window["topic_intro"] = False
                window["chapter_start"] = True
                windows.append(window)
            cursor = cut
    return windows


def _adaptive_audio_windows(
    duration: float, silences: Sequence[tuple[float, float]]
) -> list[dict[str, Any]]:
    """Use audible pauses when speech recognition is unavailable."""
    if duration <= 0:
        return []
    target = min(90.0, max(30.0, duration / 12.0))
    windows: list[dict[str, Any]] = []
    start = 0.0
    while start < duration - 1.0:
        desired = min(duration, start + target)
        if duration - desired < 12.0:
            desired = duration
        if desired < duration:
            pause_points = [
                (a + b) / 2.0 for a, b in silences
                if b - a >= 0.4 and start + 15.0 <= (a + b) / 2.0 <= start + ADAPTIVE_HARD_SPLIT
            ]
            if pause_points:
                desired = min(pause_points, key=lambda point: abs(point - desired))
        if desired <= start + 1.0:
            desired = min(duration, start + target)
        windows.append({
            "start": round(start, 3), "end": round(desired, 3),
            "duration": round(desired - start, 3), "text": "", "words": [],
            "topic_intro": False, "chapter_start": True,
        })
        start = desired
    return windows


# --------------------------------------------------------------------------- scoring


def _nearest_silence_gap(silences: Sequence[tuple[float, float]], point: float) -> float:
    """Distance (s) from a point to the nearest silence edge; big when none."""
    best = float("inf")
    for start, end in silences:
        best = min(best, abs(point - start), abs(point - end))
    return best if best != float("inf") else 999.0


def score_windows(
    windows: Sequence[dict[str, Any]],
    envelope: tuple[np.ndarray, np.ndarray] | None,
    silences: Sequence[tuple[float, float]],
    heatmap: Sequence[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Attach normalised loudness / word-density / silence / boundary features and a score.

    Bila heatmap retensi tersedia, jendela yang sering ditonton ulang mendapat
    bonus; bila jendela punya teks, ciri hook (tanya/angka/kata hook) menambah
    bonus. Tanpa keduanya, skor identik seperti sebelumnya.
    """
    if envelope is not None:
        times, rms = envelope
        peak_rms = float(np.max(rms)) if rms.size else 1.0
    else:
        times, peak_rms = np.array([]), 1.0

    densities = [max(0.0, len(w.get("words") or []) or len(w.get("text", "").split())) / max(1.0, w["duration"]) for w in windows]
    peak_density = max(densities) if densities else 0.0

    scored: list[dict[str, Any]] = []
    for window, density in zip(windows, densities):
        if envelope is not None and times.size:
            mask = (times >= window["start"]) & (times < window["end"])
            if np.any(mask):
                avg_loudness = float(np.mean(rms[mask]))
                peak_loudness = float(np.max(rms[mask]))
            else:
                avg_loudness = peak_loudness = 0.0
        else:
            avg_loudness = peak_loudness = 0.0
        avg_norm = avg_loudness / peak_rms if peak_rms else 0.0
        peak_norm = peak_loudness / peak_rms if peak_rms else 0.0
        density_norm = density / peak_density if peak_density else 0.0
        silent = overlap_seconds(silences, window["start"], window["end"])
        silence_ratio = min(1.0, silent / max(1.0, window["duration"]))
        # Natural cut bonus: boundaries that land on/near a pause cut cleaner.
        gap_start = _nearest_silence_gap(silences, window["start"])
        gap_end = _nearest_silence_gap(silences, window["end"])
        boundary = max(0.0, 1.0 - (gap_start + gap_end) / 3.0)

        score = (
            WEIGHT_LOUDNESS_AVG * avg_norm
            + WEIGHT_LOUDNESS_PEAK * peak_norm
            + WEIGHT_DENSITY * density_norm
            + WEIGHT_SILENCE * (1.0 - silence_ratio)
            + WEIGHT_BOUNDARY * boundary
        )
        heat = heat_average(heatmap, window["start"], window["end"])
        hook = hook_score(str(window.get("text", "")))
        score += WEIGHT_HEATMAP * heat + WEIGHT_HOOK * hook
        scored.append(
            {
                **window,
                "score": float(score),
                "loudness": round(avg_norm, 4),
                "peak": round(peak_norm, 4),
                "density": round(density_norm, 4),
                "silence_ratio": round(silence_ratio, 4),
                "boundary": round(boundary, 4),
                "heat": heat,
                "hook": hook,
            }
        )
    return scored


def _reason(window: dict[str, Any]) -> str:
    parts = [f"energi {window['loudness']:.2f}"]
    if window.get("peak"):
        parts.append(f"puncak {window['peak']:.2f}")
    if window.get("density"):
        parts.append(f"kata padat {window['density']:.2f}")
    if window.get("boundary"):
        parts.append(f"potongan rapi {window['boundary']:.2f}")
    if window.get("heat"):
        parts.append(f"retensi {window['heat']:.2f}")
    if window.get("hook"):
        parts.append(f"hook {window['hook']:.2f}")
    if window.get("silence_ratio"):
        parts.append(f"sunyi {window['silence_ratio'] * 100:.0f}%")
    return ", ".join(parts)


def select_top(
    scored: Sequence[dict[str, Any]],
    requested_count: int = 5,
    overlap_tolerance: float = 5.0,
    video_duration: float = 0.0,
) -> list[dict[str, Any]]:
    """Best-k selection, openshorts-style: longer sources deserve more clips.

    overlap_tolerance default 5 detik: potongan di batas kalimat yang sedikit
    bersinggungan masih boleh (terlalu ketat -> klip menumpuk di awal saja).
    """
    count = requested_count
    if video_duration > 0:
        _, ceiling = clip_count_targets(video_duration, requested_count)
        count = max(1, min(count, ceiling))
    chosen: list[dict[str, Any]] = []
    for window in sorted(scored, key=lambda w: (-w["score"], w["start"])):
        if len(chosen) >= count:
            break
        if any(
            overlap_seconds([(c["start"], c["end"])], window["start"], window["end"])
            > overlap_tolerance
            for c in chosen
        ):
            continue
        chosen.append(window)
    return sorted(chosen, key=lambda w: w["start"])


def pick_clips(
    duration: float,
    envelope: tuple[np.ndarray, np.ndarray] | None = None,
    silences: Sequence[tuple[float, float]] = (),
    transcript: dict[str, Any] | None = None,
    count: int = 5,
    min_len: float = DEFAULT_MIN_LEN,
    max_len: float = DEFAULT_MAX_LEN,
    heatmap: Sequence[dict[str, Any]] = (),
) -> list[ClipCandidate]:
    """Pick top-N non-overlapping clip candidates (deterministic, no AI required)."""
    # Zero means that the editor decides the duration from topical and speech
    # boundaries. Explicit positive limits remain supported for older API/CLI
    # callers that intentionally requested a fixed range.
    if min_len <= 0 or max_len <= 0:
        windows = _adaptive_transcript_windows(transcript) if transcript else []
        if not windows:
            windows = _adaptive_audio_windows(duration, silences)
        scored = score_windows(windows, envelope, silences, heatmap)
        for window in scored:
            if window.get("topic_intro"):
                window["score"] += 0.3
            elif window.get("chapter_start"):
                window["score"] += 0.04
        chosen = select_top(scored, count, overlap_tolerance=0.5, video_duration=duration)
        candidates: list[ClipCandidate] = []
        for window in chosen:
            start = round(max(0.0, min(duration, float(window["start"]))), 3)
            end = round(max(0.0, min(duration, float(window["end"]))), 3)
            if end - start < 1.0:
                continue
            candidates.append(ClipCandidate(
                start=start,
                end=end,
                score=float(window["score"]),
                reason=("awal topik; " if window.get("topic_intro") else "") + _reason(window),
                title=title_from_text(window.get("text", "")),
                words=list(window.get("words") or []),
            ))
        return candidates

    windows = []
    if transcript and transcript.get("segments"):
        windows = sentence_windows(transcript, min_len, max_len)
    candidates_pool: list[dict[str, Any]] = []
    if windows:
        # Scoring window (besar, overlap) -> skor dulu, BARU dipotong jadi klip.
        # Catatan: top_windows sengaja diurut waktu (bukan skor) supaya cakupan
        # video merata — kalau hanya window skor tertinggi, kandidat menumpuk
        # di satu bagian video saja (bug yang baru saja direproduksi).
        scored_windows = score_windows(windows, envelope, silences, heatmap)
        ranked = sorted(scored_windows, key=lambda w: (-w["score"], w["start"]))
        keep_n = max(count * 3, 3)
        top_windows = sorted(ranked[:keep_n], key=lambda w: w["start"])
        for window in top_windows:
            candidates_pool.extend(carve_clip_windows(window, silences, min_len, max_len))
    if not candidates_pool:
        windows = slide_windows(duration, min_len, max_len)
        candidates_pool = list(windows)
    scored = score_windows(candidates_pool, envelope, silences, heatmap)
    chosen = select_top(scored, count, video_duration=duration)
    candidates: list[ClipCandidate] = []
    for window in chosen:
        words = window.get("words") or []
        if words:
            start, end = snap_clip_to_pauses(
                window["start"], window["end"], words, silences, duration, min_len, max_len
            )
        else:
            start, end = window["start"], window["end"]
        # Jaminan akhir: tidak pernah keluar dari batas durasi yang diminta.
        if end - start > max_len:
            end = start + max_len
        candidates.append(
            ClipCandidate(
                start=round(start, 3),
                end=round(end, 3),
                score=window["score"],
                reason=_reason(window),
                title=title_from_text(window.get("text", "")),
                words=list(words),
            )
        )
    return candidates


def analyze_media(
    media_path: str | Path,
    transcript: dict[str, Any] | None = None,
    count: int = 5,
    min_len: float = 0.0,
    max_len: float = 0.0,
    video_duration: float = 0.0,
    progress_cb: ProgressCb | None = None,
    heatmap: Sequence[dict[str, Any]] = (),
) -> list[ClipCandidate]:
    """End-to-end heuristic analysis of a media file (no AI unless transcript is given)."""
    if progress_cb:
        progress_cb(5.0, "mendekode audio")
    duration, envelope, silences = cached_audio_features(media_path, progress_cb)
    if video_duration > 0:
        duration = video_duration
    if progress_cb:
        progress_cb(45.0, "mengukur loudness & jeda")
    clips = pick_clips(duration, envelope, silences, transcript, count, min_len, max_len, heatmap)
    if progress_cb:
        progress_cb(100.0, f"{len(clips)} kandidat klip")
    return clips


def cached_audio_features(path, progress_cb=None):
    import threading

    from .. import cache
    identifier = cache.key("acoustic-features-v1", cache.file_identity(path))
    previous = cache.read(identifier)
    if previous is None:
        values, samples = [], 0
        with ffmpeg._ENCODER_SLOT:
            child = proc.spawn([ffmpeg.ffmpeg_path(), "-nostdin", "-v", "error", "-i", str(path),
                                "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            timer = threading.Timer(600, child.kill)
            timer.start()
            try:
                while True:
                    raw = child.stdout.read(4000 * 4)
                    if not raw:
                        break
                    vector = np.frombuffer(raw, dtype=np.float32)
                    samples += vector.size
                    values.append(float(np.sqrt(np.mean(vector * vector) + 1e-12)))
                    if progress_cb:
                        progress_cb(20, "mengukur audio dengan buffer terbatas")
                child.wait()
                if child.returncode:
                    raise RuntimeError("Audio tidak dapat dibaca atau timeout")
            finally:
                timer.cancel()
                if child.poll() is None:
                    child.kill()
                child.wait()
                child.stdout.close()
                proc.forget(child)
        previous = {"duration": samples / 16000, "rms": values}
        cache.write(identifier, previous)
    rms = np.asarray(previous["rms"], dtype=np.float64)
    times = np.arange(rms.size) * .25
    silent = 20 * np.log10(np.maximum(rms, 1e-9) / max(float(np.max(rms)) if rms.size else 0, 1e-9)) < -38
    intervals, start = [], None
    for i, flag in enumerate(silent):
        if flag and start is None:
            start = float(times[i])
        elif not flag and start is not None:
            if times[i] - start >= .4:
                intervals.append((start, float(times[i])))
            start = None
    if start is not None and previous["duration"] - start >= .4:
        intervals.append((start, previous["duration"]))
    return previous["duration"], (times, rms), intervals


# --------------------------------------------------------------------------- optional LLM


def _rank_chunk(
    transcript: dict[str, Any],
    count: int = 5,
    base_url: str = "http://127.0.0.1:11434/v1",
    model: str = "qwen2.5:7b",
    api_key: str | None = None,
    timeout: int = 120,
    provider: str | None = None,
    min_len: float = 0,
    max_len: float = 0,
) -> list[dict[str, Any]]:
    """Ask a local OpenAI-compatible server to pick moments from the transcript text."""
    segments = transcript.get("segments", [])
    if not segments:
        return []
    numbered = "\n".join(
        f"[{i}] {s['start']:.1f}-{s['end']:.1f} {s['text']}" for i, s in enumerate(segments)
    )
    prompt = (
        f"Kamu editor shorts. Pilih maksimal {count} momen paling menarik dari transkrip "
        "ber-nomor berikut. Balas HANYA JSON array dengan objek "
        '{"start":<detik>,"end":<detik>,"title":"<hook singkat>","score":<0..1>,"reason":"<alasan>"}. '
        "Pilih tanya-jawab lengkap, cerita, hook, atau poin utama yang mandiri. "
        "Sertakan konteks pertanyaan dan akhir jawaban. Hindari iklan dan pengulangan. "
        "Durasi maksimal 180 detik. "
        "Pilih durasi sesuai isi, jangan memotong kalimat atau mulai di tengah ulasan. "
        f"Utamakan momen yang mandiri dan jelas untuk media sosial.\n\n{numbered}"
    )
    if provider:
        from .. import ai
        content = ai.text(prompt, model_override=model or None)
    else:
        from .. import ai
        try:
            base_url = ai.validate_provider_base("compatible", base_url)
            body = ai.request(base_url, "/chat/completions", api_key or "", {
                "model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2,
            })
        except (RuntimeError, ValueError, OSError):
            return []
        content = (body.get("choices") or [{}])[0].get("message", {}).get("content", "")
    start = content.find("[")
    end = content.rfind("]")
    if start < 0 or end < 0:
        return []
    try:
        parsed = json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        return []
    results: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        try:
            begin = float(item["start"])
            finish = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        max_end = max((float(s.get("end", 0)) for s in segments), default=0)
        if not math.isfinite(begin) or not math.isfinite(finish) or begin < float(segments[0].get("start", 0)) or not (min_len or 3) <= finish - begin <= (max_len or 180) or finish > max_end + 1:
            continue
        try:
            score = float(item.get("score", .8))
        except (TypeError, ValueError):
            score = .8
        results.append(
            {
                "start": begin,
                "end": finish,
                "score": max(0, min(1, score)) if math.isfinite(score) else .8,
                "reason": str(item.get("reason") or "dipilih AI")[:300],
                "title": str(item.get("title") or "").strip(),
            }
        )
    return results[:count]


def rank_with_llm(transcript: dict[str, Any], count: int = 5, candidates=None, **kwargs) -> list[dict[str, Any]]:
    if candidates is not None:
        from ..local_llm import rank_shortlist
        return rank_shortlist(transcript, candidates, count=count, **kwargs)
    """Bound input size for long podcasts, then deduplicate overlapping results."""
    segments = _valid_segments(transcript)
    if not segments:
        return []
    count = count if count > 0 else max(3, min(10, math.ceil(segments[-1]["end"] / 300)))
    chunks, chunk, length = [], [], 0
    for row in segments:
        size = len(str(row.get("text", ""))) + 40
        if chunk and length + size > 18000:
            chunks.append(chunk)
            chunk, length = [chunk[-1]], len(str(chunk[-1].get("text", ""))) + 40
        chunk.append(row)
        length += size
    if chunk:
        chunks.append(chunk)
    rows = []
    for chunk in chunks:
        rows.extend(_rank_chunk({"segments": chunk}, count=count, **kwargs))
    chosen = []
    for row in sorted(rows, key=lambda r: (-r["score"], r["start"])):
        if any(min(row["end"], r["end"]) - max(row["start"], r["start"]) > .5 for r in chosen):
            continue
        chosen.append(row)
        if len(chosen) >= count:
            break
    return sorted(chosen, key=lambda r: r["start"])


def to_candidates(rows: Iterable[dict[str, Any]], words: Sequence[dict[str, Any]] = ()) -> list[ClipCandidate]:
    candidates: list[ClipCandidate] = []
    for row in rows:
        start = float(row["start"])
        end = float(row["end"])
        start, end = snap_to_words(start, end, words)
        candidates.append(
            ClipCandidate(
                start=start,
                end=end,
                score=float(row.get("score", 1.0)),
                reason=str(row.get("reason", "dipilih")),
                title=str(row.get("title") or ""),
            )
        )
    return candidates


def write_candidates(path: str | Path, candidates: Sequence[ClipCandidate]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([c.as_dict() for c in candidates], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return path


def is_finite(value: float) -> bool:
    return math.isfinite(value)
