"""Highlight detection: heuristic (no AI) scoring with an optional local-LLM ranking."""

from __future__ import annotations

import json
import math
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ..utils import ffmpeg

DEFAULT_MIN_LEN = 15.0
DEFAULT_MAX_LEN = 60.0
HOP_SECONDS = 0.5

WEIGHT_LOUDNESS = 0.55
WEIGHT_DENSITY = 0.35
WEIGHT_SILENCE = 0.10

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
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gagal mendekode audio: {proc.stderr[-300:].decode('utf-8', 'replace')}")
    return np.frombuffer(proc.stdout, dtype=np.float32)


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
) -> list[dict[str, Any]]:
    """Group whisper segments into clip-sized windows that respect sentence boundaries."""
    windows: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for segment in transcript.get("segments", []):
        if segment.get("end", 0) - segment.get("start", 0) <= 0:
            continue
        candidate = current + [segment]
        span = candidate[-1]["end"] - candidate[0]["start"]
        if current and span > max_len:
            windows.append(_window_from_segments(current))
            current = [segment]
        elif not current and span >= min_len:
            windows.append(_window_from_segments([segment]))
        else:
            current = candidate
            if span >= min_len:
                windows.append(_window_from_segments(current))
                current = []
    if current:
        windows.append(_window_from_segments(current))
    return [w for w in windows if w["duration"] > 1.0]


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


def title_from_text(text: str, max_words: int = 7) -> str:
    words = [w for w in text.split() if w]
    if not words:
        return ""
    title = " ".join(words[:max_words])
    return title if len(words) <= max_words else f"{title}…"


# --------------------------------------------------------------------------- scoring


def score_windows(
    windows: Sequence[dict[str, Any]],
    envelope: tuple[np.ndarray, np.ndarray] | None,
    silences: Sequence[tuple[float, float]],
) -> list[dict[str, Any]]:
    """Attach normalised loudness / word-density / silence features and a score."""
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
            loudness = float(np.mean(rms[mask])) if np.any(mask) else 0.0
        else:
            loudness = 0.0
        loudness_norm = loudness / peak_rms if peak_rms else 0.0
        density_norm = density / peak_density if peak_density else 0.0
        silent = overlap_seconds(silences, window["start"], window["end"])
        silence_ratio = min(1.0, silent / max(1.0, window["duration"]))
        score = (
            WEIGHT_LOUDNESS * loudness_norm
            + WEIGHT_DENSITY * density_norm
            + WEIGHT_SILENCE * (1.0 - silence_ratio)
        )
        scored.append(
            {
                **window,
                "score": float(score),
                "loudness": round(loudness_norm, 4),
                "density": round(density_norm, 4),
                "silence_ratio": round(silence_ratio, 4),
            }
        )
    return scored


def _reason(window: dict[str, Any]) -> str:
    parts = [f"loudness {window['loudness']:.2f}"]
    if window.get("density"):
        parts.append(f"kepadatan kata {window['density']:.2f}")
    if window.get("silence_ratio"):
        parts.append(f"sunyi {window['silence_ratio'] * 100:.0f}%")
    return ", ".join(parts)


def select_top(
    scored: Sequence[dict[str, Any]], count: int, overlap_tolerance: float = 1.0
) -> list[dict[str, Any]]:
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
) -> list[ClipCandidate]:
    """Pick top-N non-overlapping clip candidates (deterministic, no AI required)."""
    windows = []
    if transcript and transcript.get("segments"):
        windows = sentence_windows(transcript, min_len, max_len)
    if not windows:
        windows = slide_windows(duration, min_len, max_len)
    scored = score_windows(windows, envelope, silences)
    chosen = select_top(scored, count)
    candidates: list[ClipCandidate] = []
    for window in chosen:
        start, end = snap_to_words(window["start"], window["end"], window.get("words") or [])
        candidates.append(
            ClipCandidate(
                start=start,
                end=end,
                score=window["score"],
                reason=_reason(window),
                title=title_from_text(window.get("text", "")),
                words=list(window.get("words") or []),
            )
        )
    return candidates


def analyze_media(
    media_path: str | Path,
    transcript: dict[str, Any] | None = None,
    count: int = 5,
    min_len: float = DEFAULT_MIN_LEN,
    max_len: float = DEFAULT_MAX_LEN,
    progress_cb: ProgressCb | None = None,
) -> list[ClipCandidate]:
    """End-to-end heuristic analysis of a media file (no AI unless transcript is given)."""
    if progress_cb:
        progress_cb(5.0, "mendekode audio")
    samples = decode_pcm(media_path)
    duration = samples.size / 16000.0
    if progress_cb:
        progress_cb(45.0, "mengukur loudness & jeda")
    envelope = rms_envelope(samples, 16000)
    silences = silent_intervals(samples, 16000)
    clips = pick_clips(duration, envelope, silences, transcript, count, min_len, max_len)
    if progress_cb:
        progress_cb(100.0, f"{len(clips)} kandidat klip")
    return clips


# --------------------------------------------------------------------------- optional LLM


def rank_with_llm(
    transcript: dict[str, Any],
    count: int = 5,
    base_url: str = "http://127.0.0.1:11434/v1",
    model: str = "qwen2.5:7b",
    api_key: str | None = None,
    timeout: int = 120,
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
        '{"start":<detik>,"end":<detik>,"title":"<judul singkat>"}. '
        f"Durasi tiap momen 15-60 detik.\n\n{numbered}"
    )
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "Jawab hanya dengan JSON valid."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {api_key}"} if api_key else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
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
        if finish - begin < 3:
            continue
        results.append(
            {
                "start": begin,
                "end": finish,
                "score": 1.0,
                "reason": "dipilih LLM lokal",
                "title": str(item.get("title") or "").strip(),
            }
        )
    return results[:count]


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
