"""Highlight detection: heuristic (no AI) scoring with an optional local-LLM ranking."""

from __future__ import annotations

import json
import math
import subprocess
import sys
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

WEIGHT_LOUDNESS_AVG = 0.28
WEIGHT_LOUDNESS_PEAK = 0.22
WEIGHT_DENSITY = 0.30
WEIGHT_SILENCE = 0.10
WEIGHT_BOUNDARY = 0.10

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
    proc = subprocess.run(cmd, capture_output=True, check=False, creationflags=_no_window_flags())
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
) -> list[dict[str, Any]]:
    """Attach normalised loudness / word-density / silence / boundary features and a score."""
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
        scored.append(
            {
                **window,
                "score": float(score),
                "loudness": round(avg_norm, 4),
                "peak": round(peak_norm, 4),
                "density": round(density_norm, 4),
                "silence_ratio": round(silence_ratio, 4),
                "boundary": round(boundary, 4),
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
) -> list[ClipCandidate]:
    """Pick top-N non-overlapping clip candidates (deterministic, no AI required)."""
    windows = []
    if transcript and transcript.get("segments"):
        windows = sentence_windows(transcript, min_len, max_len)
    candidates_pool: list[dict[str, Any]] = []
    if windows:
        # Scoring window (besar, overlap) -> skor dulu, BARU dipotong jadi klip.
        # Catatan: top_windows sengaja diurut waktu (bukan skor) supaya cakupan
        # video merata — kalau hanya window skor tertinggi, kandidat menumpuk
        # di satu bagian video saja (bug yang baru saja direproduksi).
        scored_windows = score_windows(windows, envelope, silences)
        ranked = sorted(scored_windows, key=lambda w: (-w["score"], w["start"]))
        keep_n = max(count * 3, 3)
        top_windows = sorted(ranked[:keep_n], key=lambda w: w["start"])
        for window in top_windows:
            for carved in carve_clip_windows(window, silences, min_len, max_len):
                candidates_pool.append(carved)
    if not candidates_pool:
        windows = slide_windows(duration, min_len, max_len)
        candidates_pool = list(windows)
    scored = score_windows(candidates_pool, envelope, silences)
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
    min_len: float = DEFAULT_MIN_LEN,
    max_len: float = DEFAULT_MAX_LEN,
    video_duration: float = 0.0,
    progress_cb: ProgressCb | None = None,
) -> list[ClipCandidate]:
    """End-to-end heuristic analysis of a media file (no AI unless transcript is given)."""
    if progress_cb:
        progress_cb(5.0, "mendekode audio")
    samples = decode_pcm(media_path)
    duration = samples.size / 16000.0
    if video_duration > 0:
        duration = video_duration
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
