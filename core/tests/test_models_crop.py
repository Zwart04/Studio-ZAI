import pytest

from studiozai import models
from studiozai.pipeline import crop


def test_registry_integrity():
    registry = models.manager.load_registry()
    assert registry
    ids = [m["id"] for m in registry]
    assert len(ids) == len(set(ids))
    for model in registry:
        assert {"id", "kind", "size_mb", "license", "download"} <= set(model)
        assert model["kind"] in {"asr", "tts", "clone", "image"}


def test_get_model_unknown():
    with pytest.raises(KeyError):
        models.manager.get_model("tidak-ada")


def test_resolve_tier_android_low_ram():
    tier = models.manager.resolve_tier({"android": True, "ram_gb": 4.0}, "id")
    assert tier["asr"] == "whisper-tiny-int8"
    assert tier["clone"] is None
    assert tier["tts"].startswith("piper-id")


def test_resolve_tier_android_capable():
    tier = models.manager.resolve_tier({"android": True, "ram_gb": 8.0}, "en")
    assert tier["asr"] == "whisper-base-int8"
    assert tier["clone"] == "zipvoice-zh-en"
    assert tier["tts"].startswith("piper-en")


def test_resolve_tier_desktop():
    desktop = models.manager.resolve_tier({"android": False, "ram_gb": 16.0, "gpu": {"name": "RTX 4060", "vram_gb": 8}}, "id")
    assert desktop["asr"] == "whisper-small-int8"
    assert desktop["clone"] == "zipvoice-zh-en"
    weak = models.manager.resolve_tier({"android": False, "ram_gb": 4.0}, "id")
    assert weak["asr"] == "whisper-base-int8"


def test_status_and_kinds():
    rows = models.manager.status()
    expected = [m for m in models.manager.load_registry() if not m.get('experimental') or models.manager.is_installed(m['id'])]
    assert {r['id'] for r in rows} == {m['id'] for m in expected}
    assert models.manager.models_by_kind("tts")
    assert models.manager.models_by_kind("clone")


def test_archive_checksum_blocks_corrupt_model(monkeypatch, tmp_path):
    model = {
        "id": "sample",
        "download": {"type": "archive", "name": "sample.tar.bz2",
                     "url": "https://example.invalid/sample.tar.bz2", "sha256": "0" * 64},
    }
    monkeypatch.setattr(models.manager, "get_model", lambda _model_id: model)
    monkeypatch.setattr(models.manager, "model_dir", lambda _model_id: tmp_path)

    def fake_download(_url, target, _progress, _base, _span):
        target.write_bytes(b"corrupt archive")

    monkeypatch.setattr(models.manager, "_download_file", fake_download)
    with pytest.raises(RuntimeError, match="checksum tidak cocok"):
        models.manager.download("sample")
    assert not (tmp_path / "sample.tar.bz2").exists()
    assert not (tmp_path / ".installed").exists()


def test_crop_target_size_is_even_and_vertical():
    width, height = crop.target_size(1920, 1080)
    assert width % 2 == 0 and height % 2 == 0
    assert height > width
    assert abs(width / height - 9 / 16) < 0.02


def test_crop_center_chain_stays_inside_source():
    chain = crop.center_crop_chain(1920, 1080, 1080, 1920)
    assert chain.startswith("crop=")
    parts = chain.split(",")[0].replace("crop=", "").split(":")
    crop_w, crop_h, x, y = (int(p) for p in parts)
    assert crop_w <= 1920 and crop_h <= 1080
    assert x >= 0 and y >= 0


def test_crop_blur_graph_uses_overlay():
    plan = crop.plan("blur", 1920, 1080)
    assert plan.is_complex
    assert "overlay=" in plan.complex_graph
    assert "gblur" in plan.complex_graph


def test_crop_none_plan():
    plan = crop.plan("none", 1920, 1080)
    assert plan.simple_chain and plan.simple_chain.startswith("scale=")
