"""Animasi kata aktif (mode "highlight") yang dipang dari cheat-clip-pro.

cheat-clip-pro mengemas kata ke potongan pendek satu baris lalu memotongnya
menjadi irisan waktu yang saling bersambung, sehingga sorotan tidak pernah
berkedip di tengah kalimat. Uji-uji di bawah mengunci perilaku itu supaya
porting tidak diam-diam kembali ke versi lama yang menyisakan jeda kosong
di antara kata.
"""
import itertools
import re

from studiozai.pipeline import subtitle

HIGHLIGHT = {"mode": "highlight", "highlight": "#abff66"}
HIGHLIGHT_HEX = "66ffab"  # #abff66 dalam format ASS &HBBGGRR&


def _seconds(stamp: str) -> float:
    hours, minutes, rest = stamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(rest)


def _events(*captions) -> list[dict]:
    rows = []
    for line in subtitle.to_ass(list(captions)).splitlines():
        if not line.startswith("Dialogue:"):
            continue
        head, _, body = line.partition(",,0,0,0,,")
        fields = head.split(",")
        rows.append({"start": _seconds(fields[1]), "end": _seconds(fields[2]), "text": body})
    return rows


def _plain(text: str) -> str:
    """Teks yang benar-benar terlihat, tanpa blok override ASS."""
    return re.sub(r"\{[^}]*\}", "", text)


def _shown_text(row: dict) -> str:
    """Kata yang diwarnai + kata sisanya, sebagai satu string rapi."""
    return _plain(row["text"])


def _chunks(*captions) -> list[str]:
    """Potongan yang tampil berurutan; satu potongan bisa punya banyak irisan."""
    texts = [_shown_text(row) for row in _events(*captions)]
    return [text for index, text in enumerate(texts) if index == 0 or text != texts[index - 1]]


def _words(count: int, step: float = 0.5) -> list[dict]:
    return [
        {"word": token, "start": index * step, "end": index * step + 0.45}
        for index, token in enumerate(count)
    ]


def test_slices_are_contiguous_and_never_below_the_minimum_duration():
    """Irisan dalam satu potongan tidak boleh menyisakan jeda kosong.

    Versi lama memakai timing kata mentah, jadi jeda antar kata membuat teks
    hilang sejenak lalu muncul lagi. cheat-clip-pro memaksa irisan yang saling
    menyambung dan memaksa panjang minimum 0.16 detik per kata.
    """
    caption = subtitle.Caption(0, 2, "a b c", words=[
        {"word": "a", "start": 0.0, "end": 0.05},
        {"word": "b", "start": 0.06, "end": 0.10},
        {"word": "c", "start": 0.11, "end": 2.0},
    ], style=dict(HIGHLIGHT))
    rows = _events(caption)
    assert len(rows) == 3
    assert rows[0]["start"] == 0.0
    for previous, current in itertools.pairwise(rows):
        assert previous["end"] == current["start"], rows
    for row in rows:
        # 0.16 detik; toleransi 0.01 karena cap ASS hanya dua desimal.
        assert row["end"] - row["start"] >= 0.15, rows


def test_only_the_active_word_is_coloured_and_q2_is_set():
    caption = subtitle.Caption(0, 3, "halo teman semua", words=[
        {"word": "halo", "start": 0.0, "end": 1.0},
        {"word": "teman", "start": 1.0, "end": 2.0},
        {"word": "semua", "start": 2.0, "end": 3.0},
    ], style=dict(HIGHLIGHT))
    rows = _events(caption)
    assert [_shown_text(row) for row in rows] == ["halo teman semua"] * 3
    for index, row in enumerate(rows):
        assert row["text"].count(f"&H{HIGHLIGHT_HEX}&") == 1, row["text"]
        active = re.search(rf"\{{[^}}]*\\c&H{HIGHLIGHT_HEX}&[^}}]*\}}(\S+)", row["text"])
        assert active, row["text"]
        assert active.group(1) == ["halo", "teman", "semua"][index]
        # \q2 menahan teks tetap satu baris, persis resep cheat-clip-pro.
        assert r"\q2" in row["text"]


def test_chunks_stay_within_three_words_and_twenty_two_characters():
    tokens = ["halo", "semua", "ini", "adalah", "contoh", "kalimat", "yang", "panjang"]
    caption = subtitle.Caption(0, 3.95, " ".join(tokens), words=_words(tokens),
                               style=dict(HIGHLIGHT))
    rows = _events(caption)
    assert len(rows) > 1
    for row in rows:
        assert len(_shown_text(row).split()) <= 3, row["text"]
        assert len(_shown_text(row)) <= 22, row["text"]
    # Delapan kata yang tersambung tetap pecah menjadi beberapa potongan.
    assert len({_shown_text(row) for row in rows}) == 3


def test_chunk_breaks_on_sentence_end_and_on_a_long_pause():
    sentence = subtitle.Caption(0, 3, "dua kata. lanjut", words=[
        {"word": "dua", "start": 0.0, "end": 0.3},
        {"word": "kata.", "start": 0.4, "end": 0.7},
        {"word": "lanjut", "start": 0.8, "end": 1.1},
    ], style=dict(HIGHLIGHT))
    assert _chunks(sentence) == ["dua kata.", "lanjut"]

    paused = subtitle.Caption(0, 3, "dua kata lanjut", words=[
        {"word": "dua", "start": 0.0, "end": 0.3},
        {"word": "kata", "start": 0.4, "end": 0.7},
        {"word": "lanjut", "start": 1.5, "end": 1.8},
    ], style=dict(HIGHLIGHT))
    rows = _events(paused)
    assert _chunks(paused) == ["dua kata", "lanjut"]
    # Teks berhenti sebelum jeda bicara 0.7 -> 1.5 dan baru muncul kembali
    # setelah jeda itu; tidak ada yang menggantung di atas keheningan.
    gaps = [(a["end"], b["start"]) for a, b in itertools.pairwise(rows) if b["start"] > a["end"]]
    assert gaps
    assert max(gap[0] for gap in gaps) <= 1.0
    assert max(gap[1] for gap in gaps) >= 1.4


def test_last_event_never_runs_past_the_caption_boundary():
    """cheat-clip-pro menambah ekor 0.12 detik; caption kita berdampingan.

    Tanpa clamp, potongan terakhir akan menabrak Dialogue pertama caption
    berikutnya dan dua baris teks tampil bersamaan.
    """
    closing = subtitle.Caption(0, 2, "akhir kalimat", words=[
        {"word": "akhir", "start": 0.0, "end": 1.0},
        {"word": "kalimat", "start": 1.1, "end": 2.0},
    ], style=dict(HIGHLIGHT))
    opening = subtitle.Caption(2, 3, "mulai lagi", words=[
        {"word": "mulai", "start": 2.0, "end": 2.5},
        {"word": "lagi", "start": 2.6, "end": 3.0},
    ], style=dict(HIGHLIGHT))

    rows = _events(closing, opening)
    first = [row for row in rows if row["end"] <= 2.0]
    assert first and first[-1]["end"] == 2.0
    assert not [row for row in rows if 2.0 < row["end"] < 3.0 and row["start"] < 2.0]


def test_line_mode_is_left_alone():
    """Mode default tetap satu Dialogue, tanpa potongan maupun sorotan."""
    caption = subtitle.Caption(0, 2, "halo dunia", words=[
        {"word": "halo", "start": 0.0, "end": 1.0},
        {"word": "dunia", "start": 1.0, "end": 2.0},
    ], style={"mode": "line"})
    rows = _events(caption)
    assert len(rows) == 1
    assert rows[0]["start"] == 0.0 and rows[0]["end"] == 2.0
    assert r"\q2" not in rows[0]["text"]
