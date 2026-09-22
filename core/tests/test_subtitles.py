"""Uji posisi subtitle (termasuk mode "off" untuk video yang sudah punya subtitle)."""

from __future__ import annotations

from pathlib import Path

from studiozai.pipeline import subtitle


def _captions() -> list[subtitle.Caption]:
    return [
        subtitle.Caption(0.0, 2.0, "Halo dunia"),
        subtitle.Caption(2.5, 4.0, "Baris kedua"),
    ]


def test_posisi_bawah_alignment_2() -> None:
    ass = subtitle.to_ass(_captions(), position="bottom")
    assert ",2,60,60,240,1" in ass  # alignment 2 + margin bawah standar
    assert "Dialogue:" in ass


def test_posisi_tengah_alignment_5_tanpa_margin() -> None:
    ass = subtitle.to_ass(_captions(), position="middle")
    assert ",5,60,60,0,1" in ass


def test_posisi_atas_alignment_8_margin_kecil() -> None:
    ass = subtitle.to_ass(_captions(), position="top")
    assert ",8,60,60,150,1" in ass


def test_posisi_off_tidak_ada_dialogue() -> None:
    ass = subtitle.to_ass(_captions(), position="off")
    assert "Dialogue:" not in ass
    assert "[Events]" in ass  # struktur ASS tetap valid


def test_posisi_tidak_dikenal_jatuh_ke_bawah() -> None:
    ass = subtitle.to_ass(_captions(), position="ngawur")
    assert ",2,60,60,240,1" in ass


def test_write_subtitles_menerima_position(tmp_path) -> None:
    """Regresi: service memanggil write_subtitles(position=...) sehingga parameter
    ini wajib ada, kalau tidak seluruh render klip gagal dengan TypeError."""
    files = subtitle.write_subtitles(_captions(), tmp_path, "subs", position="top")
    assert set(files) == {"srt", "ass", "vtt"}
    ass = Path(files["ass"]).read_text(encoding="utf-8")
    assert ",8,60,60,150,1" in ass


def test_write_subtitles_mode_off_tanpa_dialogue(tmp_path) -> None:
    files = subtitle.write_subtitles(_captions(), tmp_path, "subs", position="off")
    ass = Path(files["ass"]).read_text(encoding="utf-8")
    assert "Dialogue:" not in ass
    assert Path(files["srt"]).read_text(encoding="utf-8").strip()  # SRT tidak berubah
