# TECH_STACK — Studio ZAI
### Teknologi yang Dipakai

> **EN TL;DR** — Python 3.11–3.13 engine (FastAPI, yt-dlp, faster-whisper, numpy, Piper TTS, optional Chatterbox) + vanilla web UI (no framework) for desktop; Flutter + sherpa-onnx + ffmpeg-kit fork + youtubedl-android for Android. All permissive licenses; no cloud dependency.

---

## 1. Desktop (Windows / Linux)

| Lapisan | Teknologi | Versi | Lisensi | Catatan |
|---|---|---|---|---|
| Bahasa | Python | 3.11–3.13 (disarankan) | PSF | 3.14+ didukung jika semua wheel tersedia |
| Server | FastAPI + uvicorn | ≥0.115 / ≥0.30 | MIT/BSD | REST + SSE |
| Webview shell | pywebview | ≥5.0 | BSD-3 | Fallback: buka browser otomatis |
| Download | yt-dlp | ≥2025.x | Unlicense | YT/TikTok/IG; self-update channel |
| Media | FFmpeg (sistem) | ≥6.0 | LGPL/GPL | Wajib ada di PATH; dipakai untuk semua edit |
| ASR | faster-whisper | ≥1.1 | MIT | Model Systran whisper int8 |
| Numerik | numpy | ≥2.0 | BSD | Scoring highlight |
| TTS | piper-tts | ≥1.2 | MIT | Voice ID/EN ~60MB |
| Cloning (extra) | chatterbox-tts + torch (CPU atau CUDA) | terbaru | MIT | ~1.5–2GB download; lazy-import |
| LLM opsional | endpoint OpenAI-compatible (Ollama/LM Studio/OpenRouter) | - | - | Hanya kirim transkrip teks |
| Packaging | PyInstaller | ≥6.0 | GPL with exception | One-folder |

### Extras pip

```
pip install -e core            # inti: download, transcribe, clip, subtitle, TTS Piper
pip install -e "core[clone]"   # + Chatterbox (torch) untuk voice cloning
pip install -e "core[dev]"     # + pytest, ruff
```

## 2. Web UI

| Teknologi | Alasan |
|---|---|
| HTML + CSS + JS vanilla (ES modules) | Tanpa build step, muat instan, ringan |
| SSE (Server-Sent Events) | Progress realtime tanpa websocket (cukup 1 arah) |
| Design token di `ui/tokens.css` | Sumber tunggal warna/tipe, disinkronkan ke Flutter |
| i18n | Kamus JS sederhana ID/EN (`ui/app.js`) |

## 3. Android

| Lapisan | Paket | Lisensi | Catatan |
|---|---|---|---|
| UI | Flutter 3.x (Material 3) | BSD-3 | Satu basis kode |
| Download | `youtubedl_android` | MIT | yt-dlp di perangkat |
| ASR/TTS/VAD | `sherpa_onnx` | Apache-2.0 | Whisper int8, VITS Piper, ZipVoice, silero VAD |
| Render media | `ffmpeg_kit_flutter_new` | LGPL/GPL (full-gpl AAR) | Fork maintained dari ffmpeg-kit (di-retire 2025) |
| Izin/storage | plugin standard (permission_handler, shared_storage) | MIT | SAF/MediaStore |
| State | Provider/ChangeNotifier sederhana | BSD-3 | Tanpa state-framework berat |

## 4. Model (ringkasan — detail di MODELS.md)

| Model | Ukuran | Platform | Lisensi |
|---|---|---|---|
| Whisper tiny/base/small int8 | 75–250MB | Semua | MIT |
| Piper `id_ID-news_tts-medium`, `en_US-lessac-medium` | ~60MB/suara | Semua | MIT |
| Chatterbox base (EN) & `grandhigh/Chatterbox-TTS-Indonesian` | ~0.5B (~1–2GB total) | Desktop | MIT / Apache-2.0 |
| ZipVoice (sherpa-onnx) | ~200–400MB | Android/Desktop | Apache-2.0 |
| Chatterbox GGUF Q4 (eksperimental) | ~400–700MB | Android | MIT |

## 5. Toolchain Pengembangan

| Kebutuhan | Windows | Linux |
|---|---|---|
| Python | 3.11–3.13 (winget/python.org) | apt/dnf/python.org |
| FFmpeg | `winget install Gyan.FFmpeg` | `apt install ffmpeg` |
| Flutter (khusus Android) | Flutter SDK + Android Studio/JDK17 | idem |
| Git & GitHub CLI | git + `winget install GitHub.cli` | git + gh |
| Editor | VS Code (disarankan) | idem |

## 6. Prinsip Pemilihan Teknologi

1. **Lisensi permisif** — semua inti MIT/Apache/BSD; GPL hanya pada tool build (PyInstaller) & AAR ffmpeg (didokumentasikan).
2. **Tidak ada runtime berat** — tanpa Node.js, Docker, Electron, atau database eksternal (JSON + SQLite stdlib).
3. **CPU-first** — GPU opsional; tidak ada fitur yang wajib GPU.
4. **Bisa diganti** — setiap modul pipeline terisolasi; misal ffmpeg-kit fork → Media3 Transformer cukup ganti satu file.
