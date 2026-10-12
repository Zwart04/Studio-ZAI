"""Fetch the pinned Windows CPU runtime, never model weights."""
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "b11429"
NAME = f"llama-{TAG}-bin-win-cpu-x64.zip"
SHA256 = "1283323272b04cd07905816a597a0da810918102de958f4ff6f7bbaa70ed2efe"
URL = f"https://github.com/ggml-org/llama.cpp/releases/download/{TAG}/{NAME}"


def main():
    target = ROOT / "vendor" / "llama-cpu"
    target.mkdir(parents=True, exist_ok=True)
    archive = ROOT / "build" / NAME
    urllib.request.urlretrieve(URL, archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError("llama.cpp checksum mismatch")
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            name = Path(info.filename).name
            if not name or not (name == "llama-server.exe" or name.endswith(".dll") or name.lower().startswith("license")):
                continue
            destination = (target / name).resolve()
            if destination.parent != target.resolve():
                raise RuntimeError("Archive path outside runtime folder")
            destination.write_bytes(bundle.read(info))
    license_target = ROOT / "docs" / "licenses" / "LLAMA-CPP-LICENSE.txt"
    urllib.request.urlretrieve(f"https://raw.githubusercontent.com/ggml-org/llama.cpp/{TAG}/LICENSE", license_target)
    manifest = {"tag": TAG, "url": URL, "sha256": SHA256, "model_weights_included": False}
    (ROOT / "vendor" / "llama-runtime.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive.unlink()
    print(f"CPU runtime verified: {TAG}; no model download")


if __name__ == "__main__":
    main()
