"""Uji pilihan ukuran kanvas klip (potrait/asli/kotak/landscape)."""

from __future__ import annotations

from studiozai.pipeline import crop


def test_potrait_default_1080x1920() -> None:
    assert crop.canvas_size("portrait", 1920, 1080) == (1080, 1920)


def test_original_mengikuti_sumber() -> None:
    assert crop.canvas_size("original", 1920, 1080) == (1920, 1080)
    assert crop.canvas_size("original", 1280, 720) == (1280, 720)


def test_original_dibatasi_1920_dan_genap() -> None:
    width, height = crop.canvas_size("original", 3840, 2160)
    assert max(width, height) == 1920
    assert width % 2 == 0 and height % 2 == 0


def test_kotak_dan_landscape() -> None:
    assert crop.canvas_size("square", 1920, 1080) == (1080, 1080)
    assert crop.canvas_size("landscape", 1080, 1920) == (1920, 1080)


def test_plan_memakai_out_size_yang_diminta() -> None:
    plan = crop.plan("center", 1920, 1080, out_size=crop.canvas_size("landscape", 1920, 1080))
    assert (plan.out_w, plan.out_h) == (1920, 1080)
    assert "scale=1920:1080" in plan.simple_chain
