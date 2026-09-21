from studiozai.pipeline import subtitle


def words(*pairs):
    return [{"word": w, "start": s, "end": e} for w, s, e in pairs]


def test_group_words_basic():
    captions = subtitle.group_words(
        words(("halo", 0.0, 0.4), ("dunia", 0.4, 0.9), ("kita", 0.9, 1.2)),
        max_words=6,
    )
    assert len(captions) == 1
    assert captions[0].text == "halo dunia kita"
    assert captions[0].start == 0.0
    assert captions[0].end == 1.2


def test_group_words_splits_on_gap_and_punctuation():
    captions = subtitle.group_words(
        words(("selesai.", 0.0, 0.5), ("lanjut", 2.0, 2.4)), max_words=6
    )
    assert len(captions) == 2
    assert captions[0].text == "selesai."
    assert captions[1].text == "lanjut"


def test_group_words_respects_limits():
    many = words(*[(f"kata{i}", i * 0.3, i * 0.3 + 0.25) for i in range(20)])
    captions = subtitle.group_words(many, max_words=4, max_chars=100)
    assert all(len(c.text.split()) <= 4 for c in captions)
    assert len(captions) >= 5


def test_to_srt_formatting():
    captions = [subtitle.Caption(start=0.0, end=1.5, text="Halo dunia")]
    srt = subtitle.to_srt(captions)
    assert srt.startswith("1\n00:00:00,000 --> 00:00:01,500\nHalo dunia")


def test_to_ass_has_style_and_dialogue():
    captions = [
        subtitle.Caption(
            start=0.0,
            end=1.0,
            text="Halo dunia",
            words=words(("Halo", 0.0, 0.5), ("dunia", 0.5, 1.0)),
        )
    ]
    ass = subtitle.to_ass(captions, preset="bold_highlight", play_res=(1080, 1920))
    assert "PlayResX: 1080" in ass
    assert "[V4+ Styles]" in ass
    assert "Dialogue: 0,0:00:00.00,0:00:01.00" in ass
    assert "{\\k" in ass


def test_captions_from_segments_without_word_timings():
    segments = [{"start": 0, "end": 2, "text": "satu dua tiga empat lima enam tujuh delapan"}]
    captions = subtitle.captions_from_segments(segments, max_words=4)
    assert captions
    assert all(c.end > c.start for c in captions)
    assert " ".join(c.text for c in captions).split() == segments[0]["text"].split()


def test_ass_escape():
    assert subtitle.ass_escape("a{b}c\\d") == "a\\{b\\}c\\\\d"
