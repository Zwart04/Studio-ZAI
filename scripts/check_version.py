"""Pengecek versi: satu sumber kebenaran untuk semua artefak.

Versi aplikasi (EXE, APK, UI, dokumen) harus sama dengan versi yang dirilis di
GitHub. Skrip ini membandingkan semua tempat versi ditulis dan gagal bila ada
yang berbeda, supaya "kode 1.0.0 tapi rilis 1.3.x" tidak terulang.

    python scripts/check_version.py           # periksa saja
    python scripts/check_version.py --tag v1.3.2   # bandingkan dengan tag rilis
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "core" / "studiozai" / "__init__.py"

PATTERNS = {
    "core/studiozai/__init__.py": re.compile(r'__version__\s*=\s*"([^"]+)"'),
    "core/pyproject.toml": re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE),
    "android/app/pubspec.yaml": re.compile(r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)", re.MULTILINE),
    "ui/index.html": re.compile(r'studiozai-v([0-9]+\.[0-9]+\.[0-9]+)'),
}


def read_version(path: Path, pattern: re.Pattern[str]) -> str | None:
    if not path.is_file():
        return None
    match = pattern.search(path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Cek konsistensi versi Studio ZAI")
    parser.add_argument("--tag", help="tag rilis yang dibandingkan, mis. v1.3.2")
    args = parser.parse_args()

    if not SOURCE.is_file():
        print(f"gagal: {SOURCE} tidak ditemukan")
        return 2

    source_version = read_version(SOURCE, PATTERNS[str(SOURCE.relative_to(ROOT)).replace("\\", "/")])
    if not source_version:
        print("gagal: __version__ tidak ditemukan di core/studiozai/__init__.py")
        return 2

    print(f"sumber kebenaran : {source_version}  (core/studiozai/__init__.py)")
    failures: list[str] = []

    for relative, pattern in PATTERNS.items():
        if relative == "core/studiozai/__init__.py":
            continue
        found = read_version(ROOT / relative, pattern)
        if found is None:
            print(f"  dilewati       : {relative} (pola tidak ketemu)")
            continue
        status = "sama" if found == source_version else "BEDA"
        print(f"  {status:<14} : {relative} -> {found}")
        if found != source_version:
            failures.append(relative)

    if args.tag:
        tag_version = args.tag.lstrip("v")
        status = "sama" if tag_version == source_version else "BEDA"
        print(f"  {status:<14} : tag rilis -> {tag_version}")
        if tag_version != source_version:
            failures.append(f"tag {args.tag}")

    if failures:
        print("\nHASIL: versi tidak konsisten di " + ", ".join(failures))
        return 1
    print("\nHASIL: semua versi konsisten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
