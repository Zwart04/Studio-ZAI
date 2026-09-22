"""Uji pemilihan track audio multi-bahasa (video YouTube dengan dub resmi)."""

from __future__ import annotations

from studiozai.pipeline import download


def _info() -> dict:
    return {
        "formats": [
            {"format_id": "137", "vcodec": "avc1", "acodec": "none"},                       # video saja
            {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "language": "en", "format_note": "original"},
            {"format_id": "140-dub", "vcodec": "none", "acodec": "mp4a", "language": "id", "format_note": "dubbed"},
            {"format_id": "140-dub2", "vcodec": "none", "acodec": "mp4a", "language": "id", "format_note": "dubbed"},
            {"format_id": "18", "vcodec": "avc1", "acodec": "mp4a"},                          # video+audio: dilewati
        ]
    }


def test_audio_tracks_hanya_audio_murni_dan_unik() -> None:
    tracks = download.audio_tracks(_info())
    assert [t["lang"] for t in tracks] == ["en", "id"]
    assert tracks[1]["label"].startswith("dubbed")


def test_audio_tracks_kosong_bila_tidak_ada() -> None:
    assert download.audio_tracks({"formats": [{"format_id": "18", "vcodec": "avc1", "acodec": "mp4a"}]}) == []
