# 🎬 Studio ZAI

**Aplikasi cross-platform untuk mengubah video panjang menjadi klip pendek (shorts) secara otomatis — 100% jalan di komputer/HP-mu sendiri.**

Studio ZAI mengambil video dari **YouTube / TikTok / Instagram / file lokal**, mencari momen terbaik secara otomatis, memotongnya menjadi klip 9:16, menambahkan **subtitle otomatis (Indonesia & Inggris)**, dan bisa membuat **voiceover otomatis** — bahkan **mengkloning suaramu sendiri**.

Tersedia untuk **Windows, Linux, dan Android**.

> 🇬🇧 English version: [README.en.md](README.en.md)

---

## ✨ Fitur Utama

| Fitur | Keterangan |
|---|---|
| 🔗 **Input fleksibel** | Link YouTube, TikTok, Instagram, atau file video lokal |
| ✂️ **Auto-clip pintar** | Deteksi momen terbaik tanpa AI (loudness + silence + scene) atau dengan transkrip |
| 💬 **Auto subtitle** | Subtitle kata-per-kata, gaya burned-in, ekspor SRT/VTT. Indonesia & Inggris |
| 📱 **Crop vertikal 9:16** | Mode center & blur-background untuk TikTok/Reels/Shorts |
| 🎙️ **Voiceover otomatis** | TTS Bahasa Indonesia & Inggris (Piper — super ringan, realtime di CPU) |
| 🧬 **Voice cloning** | Kloning suara dari sampel 10-30 detik (Chatterbox 0.5B — Indonesia & Inggris) |
| 🎛️ **Editor sederhana** | Trim, split, urutkan ulang, edit teks subtitle, atur volume, export |
| 🤖 **Manajer Model** | Deteksi otomatis hardware → rekomendasi & unduh model yang pas |
| 🔌 **Offline-first** | Setelah model terunduh, semua proses jalan tanpa internet |
| 🌗 **UI minimalis** | Dark theme bersih, Bahasa Indonesia + English |

## 🪶 Kenapa Ringan?

- Tanpa AI sekalipun tetap bisa bikin klip (mode heuristik murni ffmpeg).
- Semua model dipilih yang paling kecil & efisien: **Whisper kecil** (75-250MB), **Piper TTS** (~60MB/suara), bukan model raksasa.
- Model **tidak dibundel** di installer/APK — diunduh hanya saat dibutuhkan.
- UI tanpa framework berat (vanilla HTML/CSS/JS di desktop).

## 🚀 Mulai Cepat

### Desktop (Windows / Linux)

```bash
# 1. Clone & install
git clone https://github.com/Zwart04/Studio-ZAI.git
cd Studio-ZAI/core
pip install -e .[dev]

# 2. Cek lingkungan (deteksi ffmpeg, GPU, model yang cocok)
studiozai doctor

# 3. Jalankan aplikasi
studiozai serve        # buka http://127.0.0.1:8737
```

### Android

```bash
cd android/app
flutter pub get
flutter build apk --release --split-per-abi
# APK ada di build/app/outputs/flutter-apk/
```

Panduan lengkap: [docs/BUILD.md](docs/BUILD.md)

## 📖 Dokumentasi

| Dokumen | Isi |
|---|---|
| [PRD](docs/PRD.md) | Kebutuhan produk & target pengguna |
| [PLAN](docs/PLAN.md) | Roadmap & milestone (M0–M5) |
| [FEATURES](docs/FEATURES.md) | Daftar fitur lengkap + prioritas |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | Desain sistem & alur data |
| [TECH_STACK](docs/TECH_STACK.md) | Teknologi & lisensi |
| [MODELS](docs/MODELS.md) | Registry model + logika auto-deteksi |
| [DESIGN](docs/DESIGN.md) | Design system (token, komponen) |
| [BUILD](docs/BUILD.md) | Cara build per platform |
| [SECURITY](docs/SECURITY.md) | Privasi & keamanan |
| [CONTRIBUTING](docs/CONTRIBUTING.md) | Cara berkontribusi |
| [CHANGELOG](docs/CHANGELOG.md) | Riwayat versi |

## 🗂️ Struktur Repo

```
Studio ZAI/
├─ core/       # Engine Python (desktop): pipeline, CLI, server, model manager
├─ ui/         # Web UI statis (dipakai aplikasi desktop)
├─ desktop/    # Launcher pywebview + packaging (PyInstaller/AppImage)
├─ android/    # Aplikasi Flutter (full on-device)
├─ scripts/    # Script dev & deploy
└─ docs/       # Semua dokumentasi
```

## ⚖️ Lisensi & Atribusi

Kode Studio ZAI: **MIT** — lihat [LICENSE](LICENSE).
Model pihak ketiga: Piper (MIT), Whisper (MIT), Chatterbox (MIT), Chatterbox-TTS-Indonesian (Apache-2.0), ZipVoice (Apache-2.0). Detail: [docs/MODELS.md](docs/MODELS.md).

> ⚠️ Voice cloning hanya untuk suara milikmu sendiri atau yang kamu punya izin eksplisit. Semua output Chatterbox otomatis mengandung watermark PerTh (bawaan model, MIT).
