# PRD — Studio ZAI
### Product Requirements Document

> **EN TL;DR** — Studio ZAI is a cross-platform (Windows/Linux/Android), offline-first app that turns long videos (YouTube/TikTok/Instagram links or local files) into 9:16 short clips with automatic highlight detection, subtitles (ID/EN), TTS voiceover (ID/EN), voice cloning, and a simple built-in editor. It must stay lightweight: works without AI (pure ffmpeg heuristics) and uses only small models when AI is enabled.

---

## 1. Latar Belakang

Kreator konten Indonesia butuh alat untuk mengubah video panjang (podcast, livestream, webinar, vlog) menjadi klip pendek siap posting ke TikTok/Reels/Shorts. Solusi yang ada (Opus Clip, dll.) berbasis cloud, berlangganan, dan data harus diunggah. Referensi open-source seperti [openshorts](https://github.com/mutonby/openshorts) dan [OpenCreator](https://github.com/krillinai/OpenCreator) menunjukkan permintaan pasar nyata, tetapi:

- openshorts berat (Docker + stack besar), wajib Gemini untuk fitur pintar.
- OpenCreator butuh Codex + API cloud untuk generasi media.

**Peluang:** aplikasi lokal yang **ringan**, **jalan di 3 OS**, **tanpa wajib AI**, dengan dukungan **Bahasa Indonesia kelas satu** (subtitle & suara).

## 2. Tujuan Produk

| # | Tujuan | Metrik sukses |
|---|---|---|
| G1 | Bikin klip 9:16 dari video panjang dalam < 10 menit untuk video 1 jam (mode heuristik, laptop CPU i5/Ryzen 5) | Waktu proses & rasio keberhasilan ≥ 95% |
| G2 | Subtitle ID/EN otomatis yang layak posting tanpa edit berat | WER transkrip ID < 15% (model small) |
| G3 | Voiceover ID/EN natural tanpa cloud | RTF < 1.0 di CPU untuk Piper |
| G4 | Voice cloning ID/EN tersedia di Windows & Linux; Android tier terbatas yang jujur | Clone dari sampel 10-30 dtk terdengar mirip (uji manual) |
| G5 | Installer desktop < 300MB (tanpa model), APK < 120MB | Ukuran rilis |
| G6 | Semua fitur inti jalan **offline** setelah model terunduh | Mode pesawat test |

**Non-goals (v1):** publishing langsung ke sosmed, kolaborasi multi-user, transkripsi > 2 bahasa UI, iOS, server cloud.

## 3. Pengguna Sasaran

1. **Kreator faceless / clipper** — potong podcast/streamer lain menjadi shorts. Butuh cepat & batch.
2. **Content creator lokal** — punya video sendiri (webinar/vlog), butuh subtitle & versi vertikal.
3. **UMKM / agensi** — bikin konten promosi dari video produk, butuh voiceover Indonesia.

## 4. User Stories Utama

- **US-1:** Sebagai clipper, saya paste link YouTube podcast 1 jam → aplikasi otomatis membuat 5-15 klip 9:16 dengan subtitle, siap diunduh.
- **US-2:** Sebagai kreator, saya drop file MP4 lokal → pilih mode crop blur → subtitle ID dibakar → hasil langsung bisa di-share.
- **US-3:** Sebagai UMKM, saya tulis script promosi → generate voiceover Indonesia → aplikasi mix dengan video saya.
- **US-4:** Sebagai kreator, saya rekam suara saya 20 detik → aplikasi mengkloning → semua narasi memakai suara saya.
- **US-5:** Sebagai pengguna HP, saya paste link TikTok di Android → klip + subtitle langsung di HP tanpa internet setelah model terunduh.
- **US-6:** Sebagai pengguna hemat kuota, saya ingin tahu ukuran model sebelum mengunduh dan bisa memilih tier yang cocok dengan HP/laptop saya.

## 5. Kebutuhan Fungsional (ringkas — detail di FEATURES.md)

| ID | Fitur | Prioritas |
|---|---|---|
| F-01 | Input link (yt-dlp) & file lokal | P0 |
| F-02 | Transkripsi ID/EN otomatis (word timestamps) | P0 |
| F-03 | Auto-clip heuristik (tanpa AI) & berbasis transkrip | P0 |
| F-04 | Auto subtitle burned-in + ekspor SRT/VTT | P0 |
| F-05 | Crop vertikal 9:16 (center/blur) | P0 |
| F-06 | TTS ID/EN (Piper) | P0 |
| F-07 | Manajer model + auto-deteksi hardware | P0 |
| F-08 | Editor sederhana (trim/split/reorder/subtitle/volume/render) | P0 |
| F-09 | UI bilingual ID/EN, dark, minimalis | P0 |
| F-10 | Voice cloning desktop (Chatterbox ID/EN) | P1 |
| F-11 | Highlight dengan LLM lokal opsional | P1 |
| F-12 | Face-track crop | P1 |
| F-13 | Cloning EN di Android (ZipVoice) | P1 |
| F-14 | Cloning ID eksperimental di Android (Chatterbox GGUF Q4, auto-benchmark) | P2 |
| F-15 | Voice Pack (fine-tune VITS dari sampel user) | P2 |

## 6. Kebutuhan Non-Fungsional

- **Ringan:** idle RAM < 300MB desktop; APK tanpa model; model diunduh on-demand dengan tampilan ukuran.
- **Offline-first:** tidak ada telemetri; tidak ada panggilan jaringan selain unduh video (perintah user) & unduh model (sekali).
- **Privasi:** semua file proyek di folder data lokal user; tidak ada upload.
- **Portabilitas:** Windows 10+, Linux (x86_64, AppImage), Android 8.0+ (arm64 utama).
- **Ketahanan:** kegagalan model/AI tidak memblokir pipeline dasar (degradasi bertingkat).
- **i18n:** semua string UI punya kunci ID/EN.

## 7. Batasan & Asumsi

- ASR & TTS jalan di CPU; GPU (CUDA) hanya mempercepat model cloning, bukan syarat.
- Android tidak bisa menjalankan Python — pipeline diimplementasikan ulang dengan komponen native (Flutter + sherpa-onnx + ffmpeg-kit fork).
- Voice cloning hanya boleh untuk suara sendiri/berizin (ditampilkan sebagai konfirmasi satu kali di UI).

## 8. Kriteria Rilis v1.0

1. Ketiga platform ter-build dari repo ini (Windows exe, Linux AppImage, Android APK).
2. Smoke test lulus: link YouTube + file lokal → klip 9:16 + subtitle + TTS (ID) di tiap platform.
3. `studiozai doctor` dan Manajer Model akurat di hardware low-end & mid-end.
4. Docs lengkap (folder `docs/`), README bilingual, CHANGELOG terisi.
5. Repo private `Zwart04/Studio-ZAI` berisi source + docs + build script.
