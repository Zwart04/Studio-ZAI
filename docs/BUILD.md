# Build Studio ZAI 1.8

## Desktop

Gunakan Python 3.12, FFmpeg/FFprobe pada PATH, dan virtualenv. Dependensi media/AI lokal terpisah dari bobot model.

```powershell
python -m venv .venv-build
.venv-build/Scripts/python.exe -m pip install -e "core[media,asr,tts,desktop,dev]" pyinstaller
.venv-build/Scripts/python.exe -m pytest core/tests
.venv-build/Scripts/python.exe -m studiozai serve
```

Build Windows dari root repo:

```powershell
$env:STUDIOZAI_FFMPEG_DIR = Split-Path (Get-Command ffmpeg).Source
.venv-build/Scripts/python.exe -m PyInstaller desktop/packaging/studiozai.spec --noconfirm
.venv-build/Scripts/python.exe tools/smoke_exe.py
.venv-build/Scripts/python.exe tools/zip_exe.py
```

Paket one-folder memuat FFmpeg/FFprobe, faster-whisper, Piper, sherpa-onnx/ZipVoice/Supertonic, yt-dlp, UI, font, dan arsip CPU stable-diffusion.cpp. PyTorch/Chatterbox tidak dibundel. Semua file folder diperlukan; distribusikan ZIP seluruh folder. Bobot model tetap di direktori data pengguna.

## Android

Toolchain yang dipakai: Flutter 3.47.5, JDK 17, platform SDK android-37.0, build-tools 37.0.0. Minimum Android 8/API 26. Verifikasi dengan flutter doctor dan SDK lokal; versi alat bukan persyaratan yang dijamin selalu terbaru.

```powershell
cd android/app
flutter pub get
flutter analyze
flutter test
flutter build apk --release
```

Hasil: build/app/outputs/flutter-apk/app-release.apk. Rilis 1.8 memakai satu APK universal agar pengguna tidak perlu memilih ABI. Library gambar native CPU hanya disertakan untuk ARM64; fitur lain tetap memakai ABI yang didukung paket. Jika membangun untuk penggunaan sendiri, --split-per-abi dapat menghasilkan paket lebih kecil per arsitektur.

Konfigurasi proyek saat ini menggunakan kunci debug untuk sideload dan kontinuitas pembaruan rilis sebelumnya. Produksi/Play Store membutuhkan keystore release milik pengembang. Jangan commit keystore, key.properties, atau rahasia API. Mengganti signing key akan memengaruhi jalur upgrade instalasi lama.

## Rilis

Periksa versi di core/studiozai/__init__.py, core/pyproject.toml, android/app/pubspec.yaml dan layar Tentang Android. Jalankan tes, uji EXE, verifikasi versi/signature APK, lalu hash artefak. Publikasikan tiga file: Windows ZIP, satu APK, SHA256SUMS.txt. Media README berada di docs/screenshots, tidak menjadi aset unduhan MP4.

## Data pengembangan

`tools/demo_workspace.py --serve` membuat media demo sintetis dan membuka server 127.0.0.1:8752 dengan direktori build/readme-demo-v18-release. Model diambil dari direktori model lokal, sedangkan proyek pengguna tidak dipakai untuk screenshot. Script memerlukan Supertonic 3 dan Whisper Tiny terpasang. GIF README merupakan tur screenshot UI, bukan video hasil milik pihak lain.

[Validasi rilis](RELEASE-1.8.0.md) · [Integrasi AI](AI.md)
