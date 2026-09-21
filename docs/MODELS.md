# MODELS — Studio ZAI
### Registry Model & Logika Auto-Deteksi

> **EN TL;DR** — Studio ZAI ships no models. A single registry (core/studiozai/models/registry.json) describes every downloadable model with size, language, platform tier and license. A Model Manager detects the device (OS, RAM, GPU, storage) and downloads only the smallest set that fits. Voice cloning: Chatterbox 0.5B (desktop, ID via community fine-tune + EN) and ZipVoice (Android, EN) — XTTS-v2 and PocketTTS are excluded because they do not support Indonesian.

---

## 1. Kategori Model

| Kind | Fungsi | Dipakai kapan |
|---|---|---|
| `asr` | Speech-to-text (subtitle & highlight dari transkrip) | Mode transkrip |
| `tts` | Text-to-speech (voiceover ID/EN) | Fitur Suara |
| `clone` | Zero-shot voice cloning | Fitur cloning (butuh sampel suara) |
| `llm` | (opsional) pemilih momen cerdas | Hanya jika user set endpoint |

## 2. Daftar Model

### ASR — Whisper (MIT)

| ID | Ukuran | Catatan |
|---|---|---|
| `whisper-tiny-int8` | ~75MB | Paling cepat, akurasi dasar — perangkat sangat lemah |
| `whisper-base-int8` | ~150MB | Seimbang untuk EN |
| `whisper-small-int8` | ~250MB | **Default untuk Indonesia** (rekomendasi) |
| `whisper-medium-int8` | ~750MB | Opsional, akurasi terbaik di kelas ringan |

Desktop: `faster-whisper` (CTranslate2). Android: `sherpa-onnx` whisper int8 (format ONNX). Model berasal dari rilis Systran (faster-whisper) dan k2-fsa (sherpa-onnx) di HuggingFace.

### TTS — Piper (MIT) — ringan, semua platform

| ID | Bahasa | Ukuran |
|---|---|---|
| `piper-id_ID-news_tts-medium` | Indonesia | ~60MB |
| `piper-en_US-lessac-medium` | Inggris (US) | ~60MB |
| `piper-en_GB-alba-medium` *(opsional)* | Inggris (UK) | ~60MB |

Desktop memakai `piper-tts`; Android memakai model VITS yang sama via `sherpa-onnx` (format yang sudah dikonversi, tersedia di model zoo sherpa-onnx: `vits-piper-id_ID-news_tts-medium`).

### Voice Cloning

| ID | Bahasa | Ukuran | Platform | Lisensi | Catatan |
|---|---|---|---|---|---|
| `chatterbox-base` | EN | ~1.5GB | Desktop | MIT | Zero-shot clone, watermark PerTh otomatis |
| `chatterbox-id-finetune` | ID | +~600MB (di atas base) | Desktop | Apache-2.0 | [grandhigh/Chatterbox-TTS-Indonesian](https://huggingface.co/grandhigh/Chatterbox-TTS-Indonesian) — checkpoint `t3_cfg.safetensors` |
| `zipvoice-zh-en` | EN (+zh) | ~250–400MB | Android/Desktop | Apache-2.0 | Via sherpa-onnx; butuh reference audio + teksnya |
| `chatterbox-gguf-q4` *(eksperimental)* | ID/EN | ~400–700MB | Android | MIT | [calcuis/chatterbox-gguf](https://huggingface.co/calcuis/chatterbox-gguf) + S3Gen ONNX; hanya tampil jika benchmark RTF ≤ 8 |

### Fallback tambahan

| ID | Fungsi | Lisensi | Catatan |
|---|---|---|---|
| `mms-tts-ind` | TTS ID tanpa cloning (VITS) | CC-BY-NC-4.0 | Hanya jika Piper gagal/diinginkan user; non-komersial |
| `kokoro-82m` *(opsional desktop EN)* | TTS EN alternatif | Apache-2.0 | 82M, kualitas bagus untuk EN |

### Yang TIDAK dipakai (dan alasannya)

| Model | Alasan tidak dipakai |
|---|---|
| XTTS-v2 (Coqui) | **Tidak mendukung Bahasa Indonesia** (17 bahasa, tanpa ID) |
| PocketTTS (sherpa-onnx) | Language pack hanya EN/DE/IT/PT/ES/FR — tanpa ID |
| ZipVoice untuk ID | Fokus zh/en; kualitas ID tidak terjamin |
| Model difusi video (Wan/LTX) | Bukan fungsi produk ini; berat (GPU besar) |

## 3. Tabel Tier & Auto-Deteksi

`resolve_tier()` memilih kombinasi berdasarkan hasil deteksi:

| Perangkat terdeteksi | ASR | TTS | Cloning |
|---|---|---|---|
| Desktop RAM < 8GB, tanpa GPU | whisper-base | Piper | — (disarankan off) |
| Desktop RAM ≥ 8GB CPU-only | whisper-small | Piper | Chatterbox (peringatan: lambat, RTF bisa > 1) |
| Desktop + CUDA ≥ 6GB VRAM | whisper-small | Piper | Chatterbox (nyaman) |
| Android RAM < 6GB | whisper-tiny | Piper VITS | — |
| Android RAM ≥ 6GB, arm64 | whisper-base | Piper VITS | ZipVoice (EN) |
| Android flagship (benchmark lulus) | whisper-base | Piper VITS | + Chatterbox Q4 (eksperimental, hidden default) |

Deteksi teknis:

```
Desktop:  platform.system/machine, psutil.virtual_memory, nvidia-smi (CUDA), shutil.disk_usage
Android:  Build.SUPPORTED_ABIS, ActivityManager.MemoryInfo, StatFs, benchmark sintesis lokal
```

Output deteksi ditampilkan di halaman **Model**: nama perangkat, RAM, GPU, storage, dan rekomendasi tier + ukuran unduhan.

## 4. Kebijakan Unduhan

1. Model diunduh **hanya saat fitur pertama dipakai** atau dari halaman Model.
2. Unduhan mendukung **resume** (HTTP Range) dan **verifikasi sha256** setelah selesai.
3. Lokasi penyimpanan:
   - Windows: `%LOCALAPPDATA%\StudioZAI\models`
   - Linux: `~/.local/share/studiozai/models`
   - Android: `filesDir/models` (bisa dipindah ke SD via SAF)
4. Bisa dihapus per model dari UI; status (terpasang/rusak/versi) selalu terlihat.
5. Benchmark RTF dijalankan sekali per model cloning (1 kalimat sintesis), disimpan di settings.

## 5. Watermark & Etika

- Chatterbox menyematkan watermark **PerTh** ke setiap output audio secara default (fitur model, MIT). Ini membantu kepatuhan regulasi (EU AI Act Art. 50) dan tidak menghilangkan kualitas.
- UI menampilkan konfirmasi satu kali: *"Saya hanya mengkloning suara milik saya atau yang saya punya izin."* sebelum fitur cloning aktif.
- Library deteksi PerTh bersifat open source (permissive) untuk verifikasi downstream.
