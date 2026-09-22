"""Uji posisi subtitle dan template tipografi.

Ekspektasi margin diambil dari konstanta modul (bukan angka mati) supaya
penyetelan default berikutnya tidak membuat tes gagal tanpa alasan.
"""

from __future__ import annotations

from pathlib import Path

from studiozai.pipeline import subtitle

# play_res default tinggi 1920 -> skala 1.0, jadi nilai preset dipakai apa adanya.
MARGIN_H = subtitle.DEFAULT_MARGIN_H
BOTTOM_MARGIN = int(subtitle.PRESETS["clean"]["margin_v"])


def _captions() -> list[subtitle.Caption]:
    return [
        subtitle.Caption(0.0, 2.0, "Halo dunia"),
        subtitle.Caption(2.5, 4.0, "Baris kedua"),
    ]


def test_posisi_bawah_alignment_2() -> None:
    ass = subtitle.to_ass(_captions(), position="bottom")
    assert f",2,{MARGIN_H},{MARGIN_H},{BOTTOM_MARGIN},1" in ass  # alignment 2 + margin bawah
    assert "Dialogue:" in ass


def test_posisi_tengah_alignment_5_tanpa_margin() -> None:
    ass = subtitle.to_ass(_captions(), position="middle")
    assert f",5,{MARGIN_H},{MARGIN_H},0,1" in ass


def test_posisi_atas_alignment_8_margin_kecil() -> None:
    ass = subtitle.to_ass(_captions(), position="top")
    assert f",8,{MARGIN_H},{MARGIN_H},150,1" in ass


def test_posisi_off_tidak_ada_dialogue() -> None:
    ass = subtitle.to_ass(_captions(), position="off")
    assert "Dialogue:" not in ass
    assert "[Events]" in ass  # struktur ASS tetap valid


def test_posisi_tidak_dikenal_jatuh_ke_bawah() -> None:
    ass = subtitle.to_ass(_captions(), position="ngawur")
    assert f",2,{MARGIN_H},{MARGIN_H},{BOTTOM_MARGIN},1" in ass


def test_write_subtitles_menerima_position(tmp_path) -> None:
    """Regresi: service memanggil write_subtitles(position=...) sehingga parameter
    ini wajib ada, kalau tidak seluruh render klip gagal dengan TypeError."""
    files = subtitle.write_subtitles(_captions(), tmp_path, "subs", position="top")
    assert set(files) == {"srt", "ass", "vtt"}
    ass = Path(files["ass"]).read_text(encoding="utf-8")
    assert f",8,{MARGIN_H},{MARGIN_H},150,1" in ass


def test_write_subtitles_mode_off_tanpa_dialogue(tmp_path) -> None:
    files = subtitle.write_subtitles(_captions(), tmp_path, "subs", position="off")
    ass = Path(files["ass"]).read_text(encoding="utf-8")
    assert "Dialogue:" not in ass
    assert Path(files["srt"]).read_text(encoding="utf-8").strip()  # SRT tidak berubah


def test_delapan_template_tersedia() -> None:
    ids = [preset["id"] for preset in subtitle.preset_list()]
    assert len(ids) == 8
    for expected in ("clean", "bold_highlight", "tiktok_pop", "karaoke_fill", "title_card",
                     "minimal_lower", "neon", "subtitle_box"):
        assert expected in ids


def test_semua_template_bisa_dirender() -> None:
    """Setiap template harus menghasilkan baris Style yang valid."""
    for preset in subtitle.preset_list():
        ass = subtitle.to_ass(_captions(), preset=preset["id"])
        assert "Style: Default," in ass
        assert "Dialogue:" in ass


def test_item_teks_timeline_menambah_style_dan_pos() -> None:
    items = [
        {"start": 0.5, "end": 2.0, "text": "Judul", "template": "tiktok_pop", "x": 0.5, "y": 0.8},
        {"start": 2.0, "end": 3.0, "text": "Sub", "template": "minimal_lower", "x": 0.2, "y": 0.1},
    ]
    ass = subtitle.to_ass(_captions(), text_items=items)
    # Satu style per template yang dipakai + style Default untuk caption.
    assert "Style: Tpl_tiktok_pop," in ass
    assert "Style: Tpl_minimal_lower," in ass
    assert r"{\an5\pos(540,1536)}" in ass  # x=0.5*1080, y=0.8*1920
    assert "Judul" in ass and "Sub" in ass


def test_item_teks_template_tidak_dikenal_jatuh_ke_default() -> None:
    items = [{"start": 0, "end": 1, "text": "X", "template": "tidak-ada", "x": 0.5, "y": 0.5}]
    ass = subtitle.to_ass(_captions(), text_items=items)
    assert "Style: Tpl_clean," in ass
