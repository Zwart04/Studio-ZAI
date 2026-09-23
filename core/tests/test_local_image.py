import subprocess
import sys

import pytest

from studiozai import ai, config, local_image


def test_image_defaults_to_offline_model_without_http(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    output = tmp_path / "offline.png"
    output.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    monkeypatch.setattr(local_image, "generate", lambda prompt: output)
    monkeypatch.setattr(ai, "request", lambda *args, **kwargs: pytest.fail("unexpected HTTP"))

    assert ai.image("Speaker on a desk") == output
    assert '"provider": "sdxs_local"' in output.with_suffix(".json").read_text(encoding="utf-8")


def test_cloud_selection_requires_configured_online_provider(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    with pytest.raises(ValueError, match="Atur penyedia gambar online"):
        ai.image("Speaker on a desk", provider="cloud")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows CPU bundle")
def test_packaged_local_engine_starts_offline(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    cli = local_image._engine()
    result = subprocess.run([str(cli), "--help"], cwd=cli.parent,
                            capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 0
    assert "--steps" in result.stdout + result.stderr
