# PLAN — Studio ZAI
### Roadmap & Milestone

> **EN TL;DR** — Delivery plan in 6 milestones (M0–M5): docs/scaffold → core engine CLI → desktop UI & editor → model manager & cloning → Android app → packaging & release. Every milestone has concrete deliverables and a verification gate.

---

## Ringkasan Milestone

| Milestone | Fokus | Status |
|---|---|---|
| **M0** | Scaffold repo + seluruh dokumen | ✅ |
| **M1** | Core engine Python (pipeline + CLI) | ✅ |
| **M2** | Server FastAPI + Web UI + editor | ✅ |
| **M3** | Manajer Model + TTS + cloning desktop | ✅ |
| **M4** | Aplikasi Android (Flutter, on-device) | ✅ |
| **M5** | Packaging + rilis + push GitHub | ✅ |

> Tanda ✅ = deliverable kode/dokumen sudah ada di repo. Pengujian perangkat keras nyata (GPU/HP) dilakukan bertahap oleh pemilik repo — lihat bagian Verifikasi.

---

## M0 — Scaffold & Dokumen ✅

**Deliverable:** struktur repo, `README.md` (ID), `README.en.md`, LICENSE, `.gitignore`, `.editorconfig`, seluruh `docs/*.md` (PRD, PLAN, FEATURES, ARCHITECTURE, TECH_STACK, MODELS, DESIGN, BUILD, SECURITY, CONTRIBUTING, CHANGELOG), script push GitHub.

**Gate:** semua dokumen saling konsisten; perintah di BUILD.md dapat dijalankan.

## M1 — Core Engine (Python) ✅

**Deliverable:**
- `core/studiozai/`: `config.py` (path data per-OS), `utils/ffmpeg.py` (finder + progress), `utils/text.py`.
- `pipeline/`: `download.py` (yt-dlp), `probe.py`, `transcribe.py` (faster-whisper), `highlight.py` (heuristik + LLM opsional), `subtitle.py` (SRT/ASS), `crop.py`, `render.py`, `voice.py` (Piper + Chatterbox).
- `models/`: `registry.json` + `manager.py` (auto-deteksi + unduh + verifikasi).
- `projects.py`, `jobs.py` (antrean + progress), `cli.py`.
- `tests/` pytest.

**Gate:** `studiozai doctor` akurat; `studiozai clip <file> --no-transcribe` menghasilkan klip tanpa model AI apa pun (ffmpeg saja); `pytest` hijau.

## M2 — Desktop UI + Editor ✅

**Deliverable:** `server.py` (FastAPI + SSE), `ui/` (index.html, tokens.css, styles.css, app.js) dengan halaman: Beranda, Proyek, Editor, Suara, Model, Pengaturan. `desktop/launcher.py` (pywebview).

**Gate:** buka `studiozai serve` → alur End-to-End dari UI: paste link → progress realtime → klip muncul → edit subtitle → export.

## M3 — Manajer Model + Voice ✅

**Deliverable:** halaman Model di UI (deteksi hardware, rekomendasi tier, unduh/hapus), `voice.py` lengkap (Piper list voice ID/EN, dubbing/mix/duck), integrasi Chatterbox (base EN + fine-tune ID) dengan lazy import & auto-device (CUDA/CPU).

**Gate:** unduh model Piper dari UI → generate narasi ID; unduh Chatterbox → clone dari `samples/`.

## M4 — Android (Flutter) ✅

**Deliverable:** `android/app` lengkap: tema token sama dengan web, i18n ID/EN, layar Home/Proses/Klip/Editor/Suara/Model/Pengaturan, service: `youtubedl_android`, `sherpa_onnx` (ASR whisper int8 + TTS VITS Piper ID/EN + VAD), `ffmpeg_kit_flutter_new` (potong/crop/burn), Model Manager tier Android (termasuk benchmark ZipVoice; Chatterbox Q4 = flag eksperimental).

**Gate (butuh Flutter SDK, dijalankan pemilik repo):** `flutter build apk` sukses; alur lokal 1 menit → klip + subtitle + TTS offline; benchmark tercatat di layar Model.

## M5 — Packaging & Rilis ✅

**Deliverable:** `desktop/packaging/` (PyInstaller spec, `build_windows.bat`, `build_linux.sh` + AppImage), `android/app/build_apk.bat|sh`, `scripts/push_github.ps1`, CHANGELOG v1.0.0, git tag.

**Gate:** artefak terbentuk dari clean checkout (instruksi BUILD.md), push ke `Zwart04/Studio-ZAI` (private) berhasil.

---

## Verifikasi Berkala

| Level | Cara |
|---|---|
| Unit | `cd core && pytest -q` |
| Smoke CLI | `studiozai doctor`; `studiozai clip samples/demo.mp4 --no-transcribe` |
| Smoke UI | `studiozai serve` → alur lengkap dari browser |
| Smoke Android | Build APK di mesin ber-Flutter, uji mode pesawat |
| Rilis | Cek ukuran artefak & CHANGELOG |

## Prinsip Pengembangan

1. **Degradasi bertingkat** — setiap fitur AI punya jalur fallback non-AI.
2. **Model on-demand** — tidak ada model di installer; semua lewat Manajer Model.
3. **Satu desain** — token warna/tipe sama di web & Flutter.
4. **Docs-first** — fitur yang tidak terdokumentasi dianggap belum selesai.

## Ide Pasca-v1 (backlog)

- Fine-tune "Voice Pack" VITS dari sampel user → inference ringan semua platform.
- Batch queue + folder watch.
- Publish langsung (Upload-Post API) seperti openshorts.
- Terjemahan subtitle otomatis (translate transkrip) untuk dubbing lintas bahasa.
- iOS (butuh mesin macOS).
