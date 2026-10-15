import copy

import pytest

from studiozai.pipeline import caption_style, subtitle
from studiozai.server import ProcessRequest


@pytest.mark.parametrize("name", caption_style.MOTION_STYLES)
def test_motion_survives_export_without_changing_transcript(name):
    rows = [{"start": 0, "end": 2, "text": "halo dunia", "words": [
        {"word": "halo", "start": 0, "end": 1, "style": {"animation": "fade", "font": "Anton"}},
        {"word": "dunia", "start": 1, "end": 2}], "style": {"y": .8}}]
    before = copy.deepcopy(rows)
    request = ProcessRequest(source="fixture.mp4", caption_motion=name)
    caption_style.apply_motion(rows, request.caption_motion)
    assert rows[0]["text"] == before[0]["text"]
    assert [(w["start"], w["end"]) for w in rows[0]["words"]] == [(0, 1), (1, 2)]
    assert rows[0]["style"]["y"] == .8
    assert rows[0]["words"][0]["style"] == {"font": "Anton"}
    ass = subtitle.to_ass([subtitle.Caption(**rows[0])])
    assert "halo" in ass and "dunia" in ass
    expected = {"pop": r"\fscx75", "elastic": r"\fscy70", "karaoke": r"\kf100",
                "typewriter": r"\t(1000,1001,\alpha&H00&)", "word": r"\fscx75"}
    if name in expected:
        assert expected[name] in ass


def test_highlight_only_animates_current_word():
    row = subtitle.Caption(0, 2, "halo dunia", words=[
        {"word": "halo", "start": 0, "end": 1},
        {"word": "dunia", "start": 1, "end": 2}],
        style={"mode": "highlight", "animation": "pop"})
    events = caption_style.events(row, {}, 1080, 1920)
    for event in events:
        assert event.count(r"\fscx75") == 1


def test_long_caption_pages_preserve_words_and_time():
    tokens = ["terus", "di", "sini", "kayak", "ada", "tekstur-teksturnya", "dan", "tulisan", "panjang", "tetap", "terbaca", "di", "dalam", "video"]
    row = subtitle.Caption(0, len(tokens), " ".join(tokens),
                           words=[{"word": word, "start": i, "end": i+1} for i, word in enumerate(tokens)],
                           style={"mode": "line", "animation": "typewriter"})
    events = caption_style.events(row, {}, 1080, 1920)
    import re
    displayed = [re.sub(r"\{[^}]*\}", "", event.split(",", 9)[9]) for event in events]
    assert " ".join(displayed).split() == tokens
    assert all(len(text.split()) <= 6 for text in displayed)
    assert len(events) > 1
    assert events[0].startswith("Dialogue: 0,0:00:00.00,")
    assert f",0:00:{len(tokens):02d}.00," in events[-1]


def test_rise_export_respects_selected_top_position():
    row = subtitle.Caption(0, 2, "halo dunia", style={"mode": "line", "animation": "rise"})
    ass = subtitle.to_ass([row], position="top")
    assert r"\move(540,365,540,288,0,220)" in ass
    assert "x" not in row.style


def test_plain_selection_disables_preset_karaoke_and_box_uses_highlight():
    words = [{"word": "halo", "start": 0, "end": 1}]
    plain = subtitle.Caption(0, 1, "halo", words=words, style={"mode": "line", "animation": "none"})
    assert r"\kf" not in subtitle.to_ass([plain], preset="bold_highlight")
    box = subtitle.Caption(0, 1, "halo", words=words, style={"mode": "box", "highlight": "#12ab34"})
    assert r"\c&H34ab12&" in subtitle.to_ass([box])
