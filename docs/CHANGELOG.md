# CHANGELOG — Studio ZAI

Format mengikuti [Keep a Changelog](https://keepachangelog.com/) dan [Semantic Versioning](https://semver.org/).

## [1.3.2] — 2026-09-22

### Fixed
- **Aplikasi tidak bisa ditutup / folder tidak bisa dihapus**: fallback jendela Chrome/Edge dulu
  loop selamanya sehingga proses EXE tetap hidup setelah jendela ditutup. Sekarang launcher
  menunggu jendela ditutup lalu keluar.
- **Satu instance saja**: membuka aplikasi dua kali tidak lagi membuat server/jendela ganda
  (dipakai `instance.json` + pengecekan PID & port); jendela kedua menyambung ke instance yang jalan.
- **Proses ffmpeg tidak tertinggal**: semua proses anak dilacak (`utils/proc.py`) dan dihentikan
  saat keluar, plus Job Object Windows `KILL_ON_JOB_CLOSE` supaya ikut mati walau aplikasi di-End task.
- **Unduhan model gagal (404)**: entri `chatterbox-gguf-q4` dan `mms-tts-ind` dihapus dari registry
  desktop & Android (URL-nya sudah tidak ada / modelnya tidak punya berkas ONNX). Tersisa 10 model
  yang seluruh URL-nya sudah diverifikasi HTTP 200.
- **Versi tidak sinkron**: kode masih 1.0.0 padahal rilis GitHub sudah 1.3.1. Versi kini 1.3.2 di
  `__init__.py`, `pyproject.toml`, dan `pubspec.yaml`, dijaga oleh `scripts/check_version.py`.
- **Tes gagal karena PermissionError**: folder `%TEMP%\pytest-*` bisa punya ACL rusak setelah sesi
  mati paksa; pytest kini memakai basetemp lokal (`.tmp-pytest`).
- **Lint bersih**: 15 temuan ruff diperbaiki, termasuk bug closure variabel loop di `transcribe.py`.

## [1.3.1] — 2026-09-22
- UI tanpa emoji, nama model lebih natural, perbaikan penamaan aset rilis.

## [1.3.0] — 2026-09-22
- UI overhaul: ikon SVG navigasi, toggle gaya iOS, skeleton, progress monoton, wizard setup awal.

## [1.2.0] — 2026-09-22
- Klip muncul kembali, transkrip lebih cepat (chunk 10 menit), progress lebih jelas.

## [1.0.0] — 2026-09-21

### Added
- **Core engine (Python)**: pipeline download (yt-dlp), transkripsi (faster-whisper), auto-clip heuristik (RMS + silence + scene, tanpa AI) dan berbasis transkrip, subtitle SRT/ASS (2 preset), crop 9:16 (center/blur), render ffmpeg (nvenc auto), TTS Piper ID/EN, voice cloning Chatterbox (ID fine-tune + EN, lazy/extra), dubbing & ducking.
- **CLI**: `doctor`, `serve`, `download`, `probe`, `transcribe`, `clip`, `tts`, `clone`, `models`.
- **Model Manager**: registry `registry.json`, deteksi hardware (RAM/GPU/disk), tier otomatis per platform, unduh resume + verifikasi sha256, benchmark RTF untuk model cloning.
- **Desktop UI**: FastAPI + SSE, web UI vanilla minimalis (Beranda, Proyek, Editor, Suara, Model, Pengaturan), bilingual ID/EN, dark theme.
- **Editor sederhana**: trim, split, urutkan ulang, edit teks subtitle, crop per klip, volume, re-render.
- **Android (Flutter)**: app on-device penuh — YouTube via `youtube_explode_dart` (pure Dart), TikTok/IG via `flutter_yt_dlp`, unduhan langsung via HTTP; sherpa-onnx (ASR Whisper int8, TTS VITS Piper ID/EN, VAD, **ZipVoice cloning EN**), ffmpeg_kit_flutter_new, Manajer Model tier Android, tujuan **Android 17 (compileSdk/targetSdk 37, minSdk 26)**.
- **Packaging**: PyInstaller spec (membundel FFmpeg/FFprobe + ctranslate2/onnxruntime/av/piper/yt-dlp) + script Windows/Linux, script build APK, `scripts/push_github.ps1`, panduan rilis `gh release create`.
- **UI Apple-style**: palet iOS dark (accent `#0A84FF`), kartu *inset grouped* dengan garis rambut, segmented control ID/EN, sheet translusen, tab bar bawah di layar kecil — diterapkan di web UI dan Flutter dengan token identik.
- **Dokumentasi**: PRD, PLAN, FEATURES, ARCHITECTURE, TECH_STACK, MODELS, DESIGN, BUILD, SECURITY, CONTRIBUTING, README bilingual.

### Notes
- Model tidak dibundel; diunduh on-demand dari sumber resmi (HuggingFace/rilis) via Manajer Model.
- Voice cloning: Chatterbox (MIT) untuk desktop (ID + EN); ZipVoice (Apache-2.0) untuk EN di Android (on-device, butuh rekaman contoh + transkripnya).
- Semua output Chatterbox mengandung watermark PerTh (bawaan model).
- Toolchain rilis terverifikasi: Python 3.12.10, Flutter 3.47.5, JDK 17, Android SDK `platforms;android-37.0` + `build-tools;37.0.0`.

### Known Limitations
- Face-track crop (mediapipe) masih tahap uji (P1).
- Chatterbox di CPU bisa lebih lambat dari realtime (RTF 1–3× pada CPU modern).
- Chatterbox Q4 di Android **belum diimplementasikan** (butuh integrasi native llama.cpp) — di HP, kloning tersedia untuk Bahasa Inggris via ZipVoice.
- Belum ada publishing langsung ke sosmed (roadmap P2).
