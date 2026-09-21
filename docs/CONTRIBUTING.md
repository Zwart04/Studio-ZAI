# CONTRIBUTING — Studio ZAI

> **EN TL;DR** — PR small & focused; run `pytest` + `ruff` before pushing; keep the design tokens in sync between `ui/tokens.css` and Flutter; all user-facing strings must have ID + EN; no telemetry.

---

## Alur Kerja

1. Fork / branch dari `main`: `git checkout -b feat/nama-fitur`.
2. Ikuti struktur & gaya yang ada. Tanpa dependency baru tanpa diskusi di issue.
3. Jalankan pemeriksaan lokal:
   ```bash
   cd core
   ruff check .
   pytest -q
   ```
4. Commit dengan pesan jelas: `feat: …` / `fix: …` / `docs: …` / `refactor: …`.
5. Buka Pull Request + isi: apa, kenapa, cara uji, screenshot (jika UI).

## Aturan Kode

- **Python:** stdlib-first; import berat (torch, faster-whisper) wajib *lazy* (di dalam fungsi) agar `doctor` cepat & degradasi mulus.
- **UI web:** tanpa framework; akses DOM lewat helper kecil; semua string lewat kamus i18n (`app.js`).
- **Flutter:** state sederhana (ChangeNotifier); jangan tambah state library baru.
- **Desain:** perubahan warna/tipe → update `ui/tokens.css` **dan** `android/.../theme/tokens.dart` bersamaan.
- **Dokumentasi fitur baru wajib**, minimal di FEATURES.md + CHANGELOG.md.

## Yang Tidak Diterima

- Telemetri/analytics/panggilan cloud tersembunyi.
- Model/biner besar di dalam repo (gunakan Manajer Model + registry).
- Fitur yang tidak punya jalur fallback non-AI.
- Perubahan lisensi model tanpa catatan.

## Struktur Commit Rapi (disarankan)

```
feat(core): heuristic highlight scoring
fix(android): ffmpeg-kit variant build error
docs(build): add Linux AppImage notes
```

## Menjalankan Tes

| Perintah | Cakupan |
|---|---|
| `pytest -q` (di `core/`) | unit: highlight, subtitle, registry, utils |
| `studiozai doctor` | integrasi lingkungan |
| `studiozai clip samples/… --no-transcribe` | smoke pipeline tanpa AI |
| `flutter analyze` (di `android/app`) | lint Dart |

Terima kasih sudah berkontribusi! 🎬
