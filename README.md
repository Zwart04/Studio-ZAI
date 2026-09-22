<p align="center">
  <img src="assets/logo-banner.png" alt="Studio ZAI — Auto Clip • Subtitle • Voiceover" width="720" />
</p>

<h1 align="center">Studio ZAI</h1>

<p align="center">
  <strong>Ubah video panjang jadi klip viral 9:16 — otomatis, lokal, tanpa cloud.</strong><br />
  Auto-clip pintar · subtitle ID/EN · voiceover & cloning suara · 100% di perangkatmu.
</p>

<p align="center">
  <a href="https://github.com/Zwart04/Studio-ZAI/releases/latest"><img alt="Download" src="https://img.shields.io/github/v/release/Zwart04/Studio-ZAI?label=unduh&logo=github" /></a>
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Android-blue" />
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green" />
  <img alt="Offline" src="https://img.shields.io/badge/offline--first-100%25%20lokal-orange" />
</p>

<p align="center">
  <a href="#-unduh--coba-2-menit"><strong>⬇️ Unduh & coba (2 menit)</strong></a> ·
  <a href="#-tangkapan-layar">📸 Tangkapan layar</a> ·
  <a href="#-fitur">✨ Fitur</a> ·
  <a href="#-cara-kerja">⚙️ Cara kerja</a> ·
  <a href="README.en.md">🇬🇧 English</a>
</p>

---

## 🎬 Lihat cara kerjanya

Tempel link YouTube / TikTok / Instagram (atau pilih file lokal) → Studio ZAI mengunduh, mencari momen terbaik, memotong jadi klip 9:16, dan membakar subtitle otomatis — semuanya di komputermu sendiri.

| Beranda — tempel link, pilih kualitas, mulai | Manajer Model — deteksi perangkat, unduh sekali |
|---|---|
| ![Beranda](docs/screenshots/01-home.png) | ![Model](docs/screenshots/02-models.png) |

| Suara — TTS Indonesia/Inggris + cloning | Tampilan HP — tab bawah, 1 tangan |
|---|---|
| ![Suara](docs/screenshots/03-voice.png) | ![Mobile](docs/screenshots/05-mobile-home.png) |

## ⬇️ Unduh & coba (2 menit)

**Rilis terbaru: [github.com/Zwart04/Studio-ZAI/releases/latest](https://github.com/Zwart04/Studio-ZAI/releases/latest)**

| Platform | Berkas | Ukuran |
|---|---|---|
| 🪟 Windows 10/11 (x64) | `StudioZAI-*-windows-x64.zip` — ekstrak, jalankan `StudioZAI.exe` (FFmpeg sudah di dalam) | ±215 MB |
| 🤖 Android 8+ (arm64) | `StudioZAI-*-android-arm64.apk` — target Android 17 (API 37) | ±42 MB |

Model AI **tidak** ikut di dalam paket. Saat pertama dibuka, wizard setup akan mengunduh yang kamu butuhkan (mis. suara Indonesia ±63 MB). Setelah itu semua jalan **offline**.

> 💡 Windows SmartScreen mungkin muncul karena EXE belum bersertifikat → *More info → Run anyway*.
> Android: izinkan *Install unknown apps* dari browser/file manager.

## ✨ Fitur

- 🔗 **Input apa pun** — link YouTube (dengan pilihan kualitas 480p → 4K / audio saja), TikTok, Instagram, atau file video lokal. Progress unduhan realtime (MB/s + sisa waktu).
- ✂️ **Auto-clip yang benar-benar pintar** — skor energi + kepadatan kata + jeda alami (belajar dari [openshorts](https://github.com/mutonby/openshorts)): potongan selalu jatuh di jeda bicara, tidak pernah di tengah kata. Bisa tanpa AI sama sekali (murni ffmpeg) atau dibantu transkrip/LLM lokal.
- 💬 **Subtitle otomatis** — kata-per-kata → caption rapi, dibakar ke video (gaya Clean / Bold-Highlight), plus ekspor SRT/VTT. Indonesia & Inggris.
- 📱 **Klip 9:16 siap posting** — crop center atau blur-background, 1080×1920, cocok untuk TikTok / Reels / Shorts.
- 🎙️ **Voiceover otomatis** — ketik teks → suara Indonesia/Inggris natural (Piper, realtime di CPU).
- 🧬 **Kloning suara** — dari rekaman 10–30 detik (desktop: Chatterbox ID+EN; Android: ZipVoice EN, on-device). Hanya untuk suaramu / yang kamu punya izin.
- 🎛️ **Editor timeline (ala CapCut, ringkas)** — track Video, Media (tambah gambar/video), Teks, dan Audio. Geser blok untuk mengatur waktu, tarik tepinya untuk durasi, pratinjau cepat sebelum render. Ada di Android dan desktop.
- 🔤 **8 template tipografi** — Clean, Bold highlight, TikTok pop, Karaoke fill, Title card, Minimal lower, Neon, Subtitle box. Bisa dipakai untuk caption otomatis maupun teks tambahan.
- 🖼️ **Framing aman** — selain crop center 9:16 ada **Fit** (letterbox) dan **Blur background** supaya teks milik video sumber tidak terpotong, plus pilihan kanvas 9:16 / asli / 1:1 / 16:9.
- 🌗 **UI gelap minimalis** — Bahasa Indonesia + English, bisa dipakai satu tangan di HP.

## ⚙️ Cara kerja

```
link / file lokal
   │  yt-dlp (dengan pilihan kualitas + progress MB/s)
   ▼
video sumber ──► transkrip Whisper (word timestamps, ID/EN)
   │                  │
   │                  ▼
   │           skor momen: energi + kepadatan kata + jeda alami
   │           potong selalu di jeda bicara (snap-to-pause)
   ▼
klip 9:16 ──► subtitle dibakar ──► (opsional) voiceover/TTS/kloning ──► MP4 siap posting
```

Semua proses lokal. Tidak ada telemetri, tidak ada upload — video dan suaramu tidak pernah keluar dari perangkat. Detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🪶 Kenapa ringan?

| Keputusan | Dampak |
|---|---|
| Bisa jalan **tanpa AI** (heuristik ffmpeg + skor audio) | Laptop kentang pun bisa bikin klip |
| Model terkecil di kelasnya: Whisper tiny–small (75–250 MB), Piper (~60 MB/suara) | Unduhan kecil, CPU-only, realtime |
| Model **tidak dibundel** — unduh on-demand via Manajer Model | Installer/APK tetap kecil |
| UI vanilla (desktop) + Flutter ramping (Android) | RAM idle kecil, startup cepat |

## 🚀 Untuk developer

```bash
# Desktop: jalankan dari source
git clone https://github.com/Zwart04/Studio-ZAI.git
cd Studio-ZAI/core
pip install -e .[dev]
studiozai doctor     # cek ffmpeg, GPU, rekomendasi model
studiozai serve      # buka http://127.0.0.1:8737
```

```bash
# Android: build APK (butuh Flutter + Android SDK 37)
cd android/app
flutter pub get
flutter build apk --release --split-per-abi
```

```bash
# Tes
cd core && pytest -q        # 40 tes unit
flutter analyze             # di android/app
```

Panduan build lengkap (Windows EXE via PyInstaller, AppImage, signing APK):
[docs/BUILD.md](docs/BUILD.md) · Arsitektur: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) ·
Model: [docs/MODELS.md](docs/MODELS.md) · Fitur lengkap: [docs/FEATURES.md](docs/FEATURES.md)

## 🗂️ Struktur repo

```
Studio ZAI/
├─ core/       # Engine Python: pipeline, CLI, server, manajer model
├─ ui/         # Web UI statis (desktop)
├─ desktop/    # Launcher pywebview + packaging (PyInstaller/AppImage)
├─ android/    # Aplikasi Flutter (full on-device)
├─ assets/     # Logo resmi
├─ docs/       # Dokumentasi + screenshots
├─ scripts/    # Script dev & deploy
└─ tools/      # Utilitas (generator icon, screenshot)
```

## ⚖️ Lisensi & atribusi

Kode Studio ZAI: **MIT** — lihat [LICENSE](LICENSE).

Model pihak ketiga: Piper (MIT) · Whisper / faster-whisper (MIT) · Chatterbox (MIT) ·
Chatterbox-TTS-Indonesian (Apache-2.0) · ZipVoice via sherpa-onnx (Apache-2.0).
Detail & link resmi: [docs/MODELS.md](docs/MODELS.md).
Inspirasi pipeline: [openshorts](https://github.com/mutonby/openshorts) (snap-to-pause, scoring) &
[OpenCreator](https://github.com/krillinai/OpenCreator) (workspace kreator lokal).

> ⚠️ Kloning suara hanya untuk suaramu sendiri atau yang kamu punya izin eksplisit.
> Output Chatterbox otomatis mengandung watermark PerTh (bawaan model, MIT).
