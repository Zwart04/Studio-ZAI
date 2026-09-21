import pytest

from studiozai.utils.text import (
    ass_timestamp,
    clock,
    human_size,
    sanitize_filename,
    srt_timestamp,
    vtt_timestamp,
)


def test_sanitize_blocks_traversal():
    traversal = sanitize_filename("../../etc/passwd")
    assert ".." not in traversal
    assert "/" not in traversal and "\\" not in traversal
    assert traversal == "etc_passwd"
    assert sanitize_filename("") == "clip"
    assert sanitize_filename("  ...  ") == "clip"


def test_sanitize_keeps_readable_names():
    assert sanitize_filename("Podcast Bapak Budi #1") == "Podcast-Bapak-Budi-#1"
    assert len(sanitize_filename("x" * 200, max_length=20)) == 20


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (0, "00:00:00,000"),
        (1.5, "00:00:01,500"),
        (3661.25, "01:01:01,250"),
    ],
)
def test_srt_timestamp(seconds, expected):
    assert srt_timestamp(seconds) == expected


def test_vtt_and_ass_timestamps():
    assert vtt_timestamp(1.5) == "00:00:01.500"
    assert ass_timestamp(1.5) == "0:00:01.50"
    assert ass_timestamp(65.999) == "0:01:06.00"


def test_clock_and_human_size():
    assert clock(75) == "1:15"
    assert clock(3725) == "1:02:05"
    assert human_size(1024) == "1 KB"
    assert human_size(1536 * 1024).endswith("MB")
