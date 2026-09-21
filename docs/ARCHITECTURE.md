# ARCHITECTURE — Studio ZAI
### Desain Sistem

> **EN TL;DR** — Two runtimes share one product: a Python desktop engine (yt-dlp → faster-whisper → heuristic/LLM highlight → ffmpeg render → Piper/Chatterbox voice) behind a local FastAPI server that serves a vanilla web UI, and a standalone Flutter Android app reimplementing the same pipeline on-device (youtubedl-android → sherpa-onnx ASR/TTS → ffmpeg-kit fork render). A Model Manager auto-detects hardware on every platform and downloads only the matching model tier.

---

## 1. Gambaran Umum

```
┌──────────────────────────── DESKTOP (Windows/Linux) ────────────────────────────┐
│                                                                                  │
│  ┌──────────────┐    HTTP/SSE    ┌─────────────────────────────────────────┐    │
│  │  Web UI      │◄──────────────►│  FastAPI Server (server.py)             │    │
│  │  ui/ (vanilla)│               │  /api/jobs /api/models /api/projects …  │    │
│  └──────────────┘                └───────────────┬─────────────────────────┘    │
│         ▲                                        │                               │
│  ┌──────┴───────┐                    ┌───────────▼──────────┐                   │
│  │ pywebview    │                    │  Job Queue (threads)  │                   │
│  │ launcher.py  │                    └───────────┬──────────┘                   │
│  └──────────────┘                                │                               │
│                                       ┌──────────▼──────────┐                   │
│                                       │  Pipeline (Python)   │                   │
│                                       │ ┌──────────────────┐ │                   │
│  ┌────────────────┐                   │ │ download (yt-dlp)│ │                   │
│  │ Model Manager  │◄─────────────────►│ │ transcribe       │ │   ┌───────────┐  │
│  │ registry.json  │   tier & model    │ │ highlight        │ │──►│ ffmpeg    │  │
│  │ detect+download│                   │ │ subtitle/crop    │ │   │ (sistem)  │  │
│  └────────────────┘                   │ │ voice (TTS/clone)│ │   └───────────┘  │
│                                       │ │ render           │ │                   │
│                                       │ └──────────────────┘ │                   │
│                                       └──────────────────────┘                   │
└──────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────── ANDROID (Flutter, on-device) ──────────────────────┐
│  Flutter UI (tema token sama)                                                    │
│    │                                                                             │
│    ├─ youtubedl-android ─────────► unduh YT/TikTok/IG                            │
│    ├─ sherpa_onnx ────────────────► ASR whisper int8 (subtitle)                  │
│    │                                TTS VITS Piper id/en  + VAD                  │
│    │                                ZipVoice (cloning EN, opsional)              │
│    ├─ ffmpeg_kit_flutter_new ─────► potong / crop 9:16 / burn subtitle / mix     │
│    ├─ ModelManager (Dart) ────────► tier Android + benchmark + unduh on-demand   │
│    └─ MediaStore/share ───────────► simpan hasil ke galeri                       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Prinsip Desain

1. **Pipeline sebagai fungsi murni bertahap** — tiap tahap punya input/output file di folder proyek, bisa di-resume, bisa dilewati (degradasi bertingkat).
2. **AI opsional** — transkripsi & highlight heuristik berjalan tanpa model LLM. Model hanya "menambah".
3. **Satu registry model** (`models/registry.json`) — deskriptif (id, bahasa, platform, tier, ukuran, URL, sha256); manager & UI membaca registry yang sama.
4. **Frontend sebagai klien tipis** — UI tidak menyimpan logika pipeline; semua aksi lewat API/SSE.
5. **Android = implementasi ulang pipeline**, bukan emulasi Python. Kontrak perilaku sama (stage, artefak), teknologi native.

## 3. Komponen Desktop

| Modul | Tanggung jawab | Teknologi |
|---|---|---|
| `config.py` | Path data per-OS (`%LOCALAPPDATA%/StudioZAI`, `~/.local/share/studiozai`), settings JSON | stdlib |
| `utils/ffmpeg.py` | Cari ffmpeg sistem, jalankan perintah + parse progress | subprocess |
| `pipeline/download.py` | URL → file media; cookies opsional; info metadata | yt-dlp |
| `pipeline/probe.py` | Durasi/resolusi/audio streams | ffprobe |
| `pipeline/transcribe.py` | Audio → segmen + word timestamps, deteksi bahasa | faster-whisper |
| `pipeline/highlight.py` | Skor momen: RMS loudness, silence, kepadatan kata, scene cut; mode LLM opsional (OpenAI-compatible) | numpy + ffmpeg |
| `pipeline/subtitle.py` | Segmen → SRT/ASS (2 preset gaya), util waktu | stdlib |
| `pipeline/crop.py` | Filter 9:16: center, blur-background | ffmpeg filter graph |
| `pipeline/render.py` | Cut presisi, concat, burn subtitle, ducking audio, export h264 (nvenc auto) | ffmpeg |
| `pipeline/voice.py` | Piper TTS (id/en), Chatterbox cloning (lazy), mix/dubbing | piper-tts / chatterbox-tts (extra) |
| `jobs.py` | Antrean job background + event progress (dipakai SSE) | threading |
| `projects.py` | Store proyek JSON + clip list + editan + riwayat | stdlib |
| `server.py` | REST + SSE + static UI | FastAPI/uvicorn |
| `cli.py` | `doctor`, `serve`, `download`, `transcribe`, `clip`, `tts`, `clone`, `models` | argparse |

### Alur data (desktop)

```
url/input.mp4
   └─► download ─► media.mp4
          └─► probe (durasi dll)
          └─► extract audio ─► audio.wav ─► transcribe ─► transcript.json
                    │                                        │
                    └─► highlight(transcript?) ─► clips[] (start,end,skor,alasan)
                              └─► cut ─► crop ─► subtitle burn ─► (voice mix) ─► mp4
                                                        │
                                              projects/<id>/project.json + clips/
```

## 4. Komponen Android

| Komponen | Paket | Catatan |
|---|---|---|
| UI | Flutter (Material 3 customized) | Token warna/tipe sama dengan `ui/tokens.css` |
| Download | `youtubedl_android` | yt-dlp ter-bundle untuk YT/TikTok/IG |
| ASR | `sherpa_onnx` (whisper tiny/base int8) | Offline, model diunduh on-demand |
| VAD | `sherpa_onnx` (silero VAD) | Untuk pemotongan heuristik tanpa ASR |
| TTS | `sherpa_onnx` (VITS Piper `id_ID`, `en_US`) | Super ringan |
| Cloning EN | `sherpa_onnx` ZipVoice | Model kecil, sudah ada contoh Android di repo sherpa-onnx |
| Cloning ID (eksperimental) | Chatterbox GGUF Q4 + S3Gen ONNX via llama.cpp bindings | Hanya ditampilkan jika benchmark lokal < ambang (RTF ≤ 8) |
| Render | `ffmpeg_kit_flutter_new` (fork maintained, full-gpl) | Fallback rencana: Media3 Transformer |
| Simpan | MediaStore / share sheet | Hasil masuk galeri |

## 5. Manajer Model & Auto-Deteksi

Deteksi (masing-masing platform):

| Sinyal | Desktop | Android |
|---|---|---|
| OS & arsitektur | `platform` | `Build` |
| RAM | psutil | ActivityManager |
| GPU | `nvidia-smi` (CUDA), Metal (macOS n/a v1) | SoC + `NNAPI` probe |
| Storage bebas | shutil.disk_usage | StatFs |
| Bahasa target | dari UI | dari UI |

Hasil → `resolve_tier()` memilih kombinasi model minimum yang memenuhi (ASR tier, TTS tier, cloning tier), lalu UI menampilkan: ukuran unduhan, RAM/VRAM terpakai, estimasi kecepatan. Unduhan: resume HTTP + verifikasi sha256 + marker `.installed`. Benchmark sekali per perangkat (sintesis 1 kalimat → RTF) disimpan di settings; dipakai untuk menyembunyikan/menampilkan fitur eksperimental.

## 6. Kontrak Data

- **Project** (`projects/<uuid>/project.json`): id, judul, sumber, bahasa, transkrip, daftar clip {index, start, end, judul, skor, crop_mode, subtitle_style, volume, voice_id}, path hasil.
- **Registry model** (`core/studiozai/models/registry.json`): array objek `{id, kind( asr|tts|clone ), langs, platform, tier, size_mb, url, sha256, license, note}`.
- **Event job** (SSE): `{job_id, stage, progress 0-100, message, artifact?}`.

## 7. Keputusan Teknis Kunci & Alasannya

| Keputusan | Alasan |
|---|---|
| Web UI vanilla (tanpa React) | Ringan, tanpa build step, mudah diaudit; desktop hanya butuh webview |
| Python untuk desktop | Ekosistem video/AI paling lengkap (yt-dlp, whisper, TTS) — waktu pengembangan tercepat |
| Flutter untuk Android | Satu basis kode UI, FFI matang ke sherpa-onnx & ffmpeg-kit fork |
| Piper sebagai TTS default | Realtime di CPU, 60MB/suara, MIT, tersedia voice Indonesia resmi |
| Chatterbox untuk cloning | Satu-satunya jalur cloning ID/EN berkualitas dengan lisensi MIT + fine-tune ID Apache-2.0; alternatif (XTTS-v2) tidak punya bahasa Indonesia |
| Heuristik default, LLM opsional | Memenuhi syarat "kalau bisa tanpa AI"; LLM hanya menambah kualitas |
| Model tidak dibundel | Installer/APK kecil; user memilih tier sesuai perangkat |
