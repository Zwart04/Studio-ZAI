# CHANGELOG — Studio ZAI

Format mengikuti [Keep a Changelog](https://keepachangelog.com/) dan [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-09-21

### Added
- **Core engine (Python)**: pipeline download (yt-dlp), transkripsi (faster-whisper), auto-clip heuristik (RMS + silence + scene, tanpa AI) dan berbasis transkrip, subtitle SRT/ASS (2 preset), crop 9:16 (center/blur), render ffmpeg (nvenc auto), TTS Piper ID/EN, voice cloning Chatterbox (ID fine-tune + EN, lazy/extra), dubbing & ducking.
- **CLI**: `doctor`, `serve`, `download`, `probe`, `transcribe`, `clip`, `tts`, `clone`, `models`.
- **Model Manager**: registry `registry.json`, deteksi hardware (RAM/GPU/disk), tier otomatis per platform, unduh resume + verifikasi sha256, benchmark RTF untuk model cloning.
- **Desktop UI**: FastAPI + SSE, web UI vanilla minimalis (Beranda, Proyek, Editor, Suara, Model, Pengaturan), bilingual ID/EN, dark theme.
- **Editor sederhana**: trim, split, urutkan ulang, edit teks subtitle, crop per klip, volume, re-render.
- **Android (Flutter)**: app on-device penuh — youtubedl_android, sherpa-onnx (ASR whisper int8, TTS VITS Piper ID/EN, VAD, ZipVoice EN), ffmpeg_kit_flutter_new, Manajer Model tier Android, UI dengan token desain sama.
- **Packaging**: PyInstaller spec + script Windows/Linux, script build APK, `scripts/push_github.ps1`.
- **Dokumentasi**: PRD, PLAN, FEATURES, ARCHITECTURE, TECH_STACK, MODELS, DESIGN, BUILD, SECURITY, CONTRIBUTING, README bilingual.

### Notes
- Model tidak dibundel; diunduh on-demand dari sumber resmi (HuggingFace/rilis) via Manajer Model.
- Voice cloning: Chatterbox (MIT) untuk desktop; ZipVoice (Apache-2.0) untuk EN di Android; Chatterbox Q4 Android = eksperimental dengan auto-benchmark.
- Semua output Chatterbox mengandung watermark PerTh (bawaan model).

### Known Limitations
- Face-track crop (mediapipe) masih tahap uji (P1).
- Chatterbox di CPU bisa lebih lambat dari realtime (RTF 1–3× pada CPU modern).
- Chatterbox Q4 Android belum divalidasi di perangkat fisik.
- Belum ada publishing langsung ke sosmed (roadmap P2).
