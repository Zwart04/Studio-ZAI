# Studio ZAI — Android

Aplikasi Android mandiri (Flutter). Baca [app/README.md](app/README.md) untuk detail arsitektur dan [app/android_overrides/README.md](app/android_overrides/README.md) untuk langkah build.

## Ringkas

```bash
# Linux/macOS
./build_apk.sh

# Windows
build_apk.bat
```

Hasil: `app/build/app/outputs/flutter-apk/app-arm64-v8a-release.apk` (~60-120MB, tanpa model).

## Perbedaan dengan desktop

| Aspek | Desktop (Python) | Android (Flutter) |
|---|---|---|
| ASR | faster-whisper (CTranslate2) | sherpa-onnx Whisper int8 |
| TTS | piper-tts | sherpa-onnx VITS (Piper) |
| Render | FFmpeg sistem | ffmpeg-kit fork (AAR) |
| Unduh video | yt-dlp (Python) | youtubedl_android |
| Voice cloning | Chatterbox (ID + EN) — produksi | ZipVoice (EN) — **eksperimental, belum diverifikasi** |

Skoring momen, aturan subtitle, dan token desain sengaja dibuat identik dengan versi desktop supaya hasil klip konsisten.
