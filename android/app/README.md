# Studio ZAI — Android app

Aplikasi Android **mandiri (full on-device)**: unduh video, transkripsi, auto-clip, subtitle, crop 9:16, dan TTS — semuanya jalan di HP, tanpa server.

## Komponen

| Fungsi | Paket |
|---|---|
| UI | Flutter 3.x (Material 3, tema = `ui/tokens.css`) |
| Unduh video | `youtubedl_android` (yt-dlp) |
| ASR & TTS | `sherpa_onnx` — Whisper int8 (ASR), VITS/Piper (TTS ID/EN), silero VAD |
| Render media | `ffmpeg_kit_flutter_new` (fork maintained ffmpeg-kit) |
| Izin & berkas | `permission_handler`, `file_picker`, `path_provider` |
| Bagikan hasil | `share_plus` |

## Struktur

```
lib/
├─ main.dart                 # entry + navigasi bawah
├─ models.dart               # Project / Clip / ModelInfo / DeviceReport
├─ theme/tokens.dart         # token desain (sinkron dengan web UI)
├─ i18n/strings.dart         # teks ID/EN
├─ state/app_state.dart      # state global + penyimpanan proyek (JSON)
├─ services/
│  ├─ model_registry.dart    # katalog model Android (URL + ukuran + lisensi)
│  ├─ model_manager.dart     # deteksi perangkat + unduh/resume/ekstrak/hapus
│  ├─ media_tools.dart       # ffmpeg/ffprobe + WAV reader/writer
│  ├─ downloader.dart        # yt-dlp (YouTube/TikTok/Instagram)
│  ├─ speech.dart            # sherpa-onnx: ASR whisper, TTS Piper, (ZipVoice stub)
│  ├─ subtitle_builder.dart  # SRT + ASS (burn-in), port dari core Python
│  └─ pipeline.dart          # scoring heuristik + render klip + export
├─ screens/                  # home, clips, editor, voice, models, settings
└─ widgets/common.dart       # komponen bersama (kartu, badge, progress, clip tile)
```

## Build

Lihat [android_overrides/README.md](android_overrides/README.md) (langkah `flutter create` + timpa berkas native), atau langsung:

```bash
./build_apk.sh          # Linux/macOS
build_apk.bat           # Windows
```

## Catatan penting

- **APK tidak berisi model.** Model diunduh dari halaman *Model* (mis. Whisper base ~190MB, Piper Indonesia ~63MB).
- **Kloning suara di Android masih eksperimental.** `SpeechService.cloneWithZipVoice` sengaja mengembalikan `UnsupportedError` sampai konfigurasi ZipVoice diverifikasi di perangkat nyata; untuk kualitas produksi pakai desktop (Chatterbox ID/EN). Ini tercatat di `docs/FEATURES.md` (F-24) dan `docs/MODELS.md`.
- Nama simbol `sherpa_onnx` bisa berbeda antar versi paket. Jika `flutter analyze` menemukan ketidakcocokan, sesuaikan konstruktor di `lib/services/speech.dart` dengan versi di `pubspec.yaml`.
- `DropdownButtonFormField(initialValue:)` mengikuti Flutter terbaru; pada Flutter lama ganti menjadi `value:`.
