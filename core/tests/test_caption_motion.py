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
        # One base override and exactly one active-word override.
        assert event.count(r"\fscx75") == 2
