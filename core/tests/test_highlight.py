import numpy as np
import pytest

from studiozai.pipeline import highlight


def make_signal(sample_rate: int = 16000) -> np.ndarray:
    quiet = np.zeros(int(sample_rate * 2), dtype=np.float32)
    t = np.arange(int(sample_rate * 4)) / sample_rate
    tone = (0.5 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    return np.concatenate([quiet, tone, quiet])


def test_rms_envelope_shape():
    samples = make_signal()
    times, rms = highlight.rms_envelope(samples, 16000, hop_seconds=0.5)
    assert times.size == rms.size == 16
    assert rms.max() > 0.1
    assert rms.min() < 0.01


def test_silent_intervals_detects_silence():
    samples = make_signal()
    intervals = highlight.silent_intervals(samples, 16000)
    assert len(intervals) == 2
    assert intervals[0][0] == pytest.approx(0.0, abs=0.3)
    assert intervals[0][1] == pytest.approx(2.0, abs=0.3)
    assert intervals[1][0] == pytest.approx(6.0, abs=0.3)


def test_merge_intervals():
    merged = highlight.merge_intervals([(0, 1), (1.05, 2), (5, 6)], gap=0.1)
    assert merged == [(0, 2), (5, 6)]


def test_slide_windows_and_selection_are_deterministic():
    windows = highlight.slide_windows(120, min_len=15, max_len=60)
    assert [w["start"] for w in windows] == [0.0, 30.0, 60.0]
    scored = highlight.score_windows(windows, None, [])
    chosen = highlight.select_top(scored, requested_count=2)
    assert [w["start"] for w in chosen] == [0.0, 60.0]


def test_sentence_windows_respect_bounds():
    # Dua segmen pendek -> satu scoring window (openshorts-style: ~90 dtk).
    transcript = {
        "segments": [
            {"start": 0, "end": 20, "text": "pertama", "words": [{"word": "pertama", "start": 0, "end": 20}]},
            {"start": 20, "end": 40, "text": "kedua", "words": [{"word": "kedua", "start": 20, "end": 40}]},
        ]
    }
    windows = highlight.sentence_windows(transcript, min_len=15, max_len=60)
    assert len(windows) == 1
    assert windows[0]["start"] == 0.0
    assert windows[0]["end"] == 40.0
    assert windows[0]["duration"] == 40.0


def test_sentence_windows_overlap_and_cover_long_video():
    # Segmen 30 detik x 8 (=240 dtk) -> beberapa window yang overlap & menutup semua.
    segments = []
    for i in range(8):
        segments.append(
            {
                "start": i * 30.0,
                "end": (i + 1) * 30.0,
                "text": f"bagian {i}",
                "words": [{"word": f"b{i}", "start": i * 30.0, "end": (i + 1) * 30.0}],
            }
        )
    windows = highlight.sentence_windows({"segments": segments}, min_len=15, max_len=60)
    assert len(windows) >= 3
    assert windows[0]["start"] == 0.0
    assert windows[-1]["end"] == 240.0
    # ada overlap antar window berurutan
    assert any(windows[i + 1]["start"] < windows[i]["end"] for i in range(len(windows) - 1))
    # tiap window ditutup rapat (tidak terbuka)
    assert all(w["end"] - w["start"] <= 90 * 1.25 + 1e-6 for w in windows)


def test_carve_clip_windows_never_exceed_max():
    window = {
        "start": 0.0,
        "end": 110.0,
        "duration": 110.0,
        "text": "x",
        "words": [{"word": f"k{i}", "start": i * 0.7, "end": i * 0.7 + 0.4} for i in range(150)],
    }
    carved = highlight.carve_clip_windows(window, [], min_len=15, max_len=60)
    assert carved, "window berisi kata harus menghasilkan kandidat"
    assert all(c["end"] - c["start"] <= 60 for c in carved), "kandidat tidak boleh lebih dari max"
    assert all(c["end"] - c["start"] >= 5 for c in carved), "kandidat ekor terlalu pendek"
    # kandidat berurutan dan menutup window tanpa celah besar
    assert carved[0]["start"] == 0.0
    assert all(carved[i + 1]["start"] >= carved[i]["start"] for i in range(len(carved) - 1))


def test_pick_clips_bounded_and_spread():
    # Transkrip sintetis 330 detik: 5 klip harus DALAM 15-60 dtk dan TERSBAR.
    words = []
    t = 0.0
    for i in range(600):
        words.append({"word": f"k{i}", "start": round(t, 2), "end": round(t + 0.35, 2)})
        t += 0.55
    segments = []
    for s in range(0, 600, 40):
        chunk = words[s : s + 40]
        segments.append(
            {
                "start": chunk[0]["start"],
                "end": chunk[-1]["end"],
                "text": " ".join(w["word"] for w in chunk),
                "words": chunk,
            }
        )
    duration = segments[-1]["end"]
    clips = highlight.pick_clips(duration, None, [], {"segments": segments}, count=5, min_len=15, max_len=60)
    assert len(clips) == 5
    assert all(15 <= (c.end - c.start) <= 60 for c in clips)
    starts = [c.start for c in clips]
    assert max(starts) - min(starts) >= 60, "klip harus tersebar, tidak menumpuk di awal"


def test_pick_clips_without_ai():
    clips = highlight.pick_clips(duration=120, count=2, min_len=15, max_len=60)
    assert len(clips) == 2
    assert clips[0].start == 0.0
    assert all(c.duration >= 15 for c in clips)
    assert all(c.score > 0 for c in clips)


def test_pick_clips_prefers_loud_window():
    sample_rate = 16000
    quiet = np.zeros(sample_rate * 20, dtype=np.float32)
    t = np.arange(sample_rate * 20) / sample_rate
    loud = (0.8 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
    samples = np.concatenate([quiet, loud])
    envelope = highlight.rms_envelope(samples, sample_rate)
    transcript = {
        "segments": [
            {"start": 0, "end": 20, "text": "bagian sunyi", "words": [{"word": "sunyi", "start": 0, "end": 20}]},
            {"start": 20, "end": 40, "text": "bagian ramai", "words": [{"word": "ramai", "start": 20, "end": 40}]},
        ]
    }
    clips = highlight.pick_clips(
        duration=40, envelope=envelope, silences=[(0, 20)], transcript=transcript, count=1
    )
    assert len(clips) == 1
    assert clips[0].start >= 19.0
    assert clips[0].score >= 0.9


def test_snap_to_words():
    words = [{"word": "a", "start": 1.0, "end": 1.5}, {"word": "b", "start": 1.5, "end": 2.0}]
    assert highlight.snap_to_words(1.2, 1.9, words) == (1.0, 2.0)
    assert highlight.snap_to_words(30.0, 40.0, words) == (30.0, 40.0)


def test_title_from_text():
    assert highlight.title_from_text("satu dua tiga") == "satu dua tiga"
    assert highlight.title_from_text(" ".join(str(i) for i in range(10))).endswith("…")
