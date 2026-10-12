"""Cek konsistensi tabel i18n di ui/app.js dengan kunci yang benar-benar dipakai.

Laporan:
  - kunci yang ada di id tapi hilang di en (dan sebaliknya)
  - kunci yang dipakai lewat t("...") tapi belum didefinisikan
  - kunci yang didefinisikan tapi tidak pernah dipakai

Jalankan: python tools/check_i18n.py  (keluar 1 bila ada kunci hilang)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"


def table_keys(source: str, lang: str) -> set[str]:
    match = re.search(rf"\b{lang}\s*:\s*\{{", source)
    if not match:
        return set()
    start = source.index("{", match.start())
    depth, index = 0, start
    while index < len(source):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                break
        index += 1
    block = source[start : index + 1]
    return set(re.findall(r'"([A-Za-z0-9_.]+)"\s*:', block))


def main() -> int:
    app = (UI / "app.js").read_text(encoding="utf-8")
    id_keys, en_keys = table_keys(app, "id"), table_keys(app, "en")

    used: set[str] = set()
    for path in sorted(UI.glob("*.js")):
        source = path.read_text(encoding="utf-8")
        used.update(re.findall(r'\bt\(\s*[\'"]([^\'"]+)[\'"]', source))

    problems: list[str] = []
    for key in sorted(id_keys - en_keys):
        problems.append(f"kunci hilang di en : {key}")
    for key in sorted(en_keys - id_keys):
        problems.append(f"kunci hilang di id : {key}")
    for key in sorted(used - id_keys):
        problems.append(f"dipakai tapi belum didefinisikan: {key}")
    unused = sorted(id_keys - used)

    print(f"id={len(id_keys)} en={len(en_keys)} used={len(used)}")
    for line in problems:
        print(line)
    if unused:
        print("didefinisikan tapi tidak dipakai:")
        for key in unused:
            print(f"  - {key}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
