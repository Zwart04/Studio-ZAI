"""Cek referensi Dart tanpa perlu Flutter SDK.

`flutter analyze` adalah pemeriksa terbaik, tetapi butuh Flutter terpasang.
Skrip ringan ini menangkap dua kesalahan yang paling sering terjadi dan paling
mahal (baru ketahuan saat build):

1. `Tokens.<nama>` yang dipakai di UI tapi tidak ada di `theme/tokens.dart`.
2. `translate('<kunci>')` yang tidak ada di `i18n/strings.dart` — jebakan ini
   membuat teks mentah seperti "voice.text" muncul di aplikasi.

Jalankan dari mana saja:

    python tools/check_dart_refs.py

Keluar dengan kode 1 kalau ada yang tidak cocok.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "android" / "app" / "lib"

# Konstanta di tokens.dart yang sah-sah saja tidak dipakai langsung di layar
# (dipakai di dalam tokens.dart sendiri atau sebagai alias).
IGNORED_UNUSED = {
    "bg", "space5", "space8", "rowHeight", "motion", "fill", "separator",
    "surface3", "accentPress", "text2", "radiusPill", "success", "warn",
    "danger",
}


def main() -> int:
    if not LIB.is_dir():
        print(f"folder tidak ditemukan: {LIB}")
        return 1

    tokens_src = (LIB / "theme" / "tokens.dart").read_text(encoding="utf-8")
    tokens_defined = set(re.findall(r"static const ([A-Za-z0-9_]+)", tokens_src))

    strings_src = (LIB / "i18n" / "strings.dart").read_text(encoding="utf-8")
    keys = set(re.findall(r"'([a-zA-Z0-9_.]+)':", strings_src))

    problems: list[str] = []
    used_tokens: set[str] = set()
    used_keys: set[str] = set()

    for path in sorted(LIB.rglob("*.dart")):
        if path.name == "tokens.dart":
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(LIB)
        for name in re.findall(r"Tokens\.([A-Za-z0-9_]+)", text):
            used_tokens.add(name)
            if name not in tokens_defined:
                problems.append(f"{rel}: Tokens.{name} tidak ada di tokens.dart")
        for key in re.findall(r"translate\('([^']+)'\)", text):
            used_keys.add(key)
            if key not in keys:
                problems.append(f"{rel}: translate('{key}') tidak ada di strings.dart")

    unused = sorted(tokens_defined - used_tokens - IGNORED_UNUSED)

    print(f"Tokens    : dipakai {len(used_tokens)}, didefinisikan {len(tokens_defined)}")
    print(f"Kunci i18n: dipakai {len(used_keys)}, tersedia {len(keys)}")
    if unused:
        print(f"Tokens tidak terpakai (info): {', '.join(unused)}")

    if problems:
        print("\nMASALAH:")
        for item in problems:
            print(f" - {item}")
        return 1

    print("\nSemua referensi Tokens & i18n cocok.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
