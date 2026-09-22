# BUILD — Studio ZAI
### Cara Build & Menjalankan

> **EN TL;DR** — Prereqs: Python 3.11-3.13, FFmpeg in PATH; for Android: Flutter 3.47+, JDK 17 and Android SDK platform `android-37.0`. Desktop dev: `pip install -e .[dev]` then `studiozai serve`. Windows: PyInstaller one-folder with FFmpeg bundled. Android: `flutter build apk --release --split-per-abi` (targetSdk 37 = Android 17). Publish artifacts with `gh release create`.

---

## 0. Toolchain yang sudah diverifikasi

Konfigurasi ini yang dipakai untuk membangun artefak rilis (Windows 10 x64, September 2026):

| Kebutuhan | Versi terverifikasi | Pasang di Windows |
|---|---|---|
| Python (build EXE) | **3.12.10** | `winget install Python.Python.3.12` |
| FFmpeg (dibundel ke EXE) | 8.1.1 (Gyan build) | `winget install Gyan.FFmpeg` |
| Flutter SDK | **3.47.5 stable** | unduh `flutter_windows_3.47.5-stable.zip` dari storage.googleapis.com/flutter_infra_release |
| JDK | **17.0.20** (Microsoft OpenJDK) | `winget install Microsoft.OpenJDK.17` |
| Android cmdline-tools | 15859902 (`latest`) | dl.google.com/android/repository/commandlinetools-win-15859902_latest.zip |
| Android SDK platform | **`platforms;android-37.0`** (Android 17) | `sdkmanager --sdk_root=C:\Android\Sdk "platforms;android-37.0"` |
| Android build-tools | **37.0.0** | `sdkmanager ... "build-tools;37.0.0"` |
| GitHub CLI | 2.91+ | `winget install GitHub.cli` |

> **Catatan penamaan SDK Android:** sejak API 36/37 platform memakai **versi minor** (`android-37.0`, `android-37.1`, …). Paket `platforms;android-37` tanpa suffix **tidak ada** — selalu pakai `android-37.0`.
> **Python 3.14** belum punya wheel lengkap untuk ctranslate2/piper → gunakan 3.12/3.13 untuk build EXE.

---

## 1. Menjalankan Mode Dev (Desktop)

```bash
cd core
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux: source .venv/bin/activate
pip install -e ".[dev]"          # inti + test
pip install -e ".[media,asr,tts]"  # yt-dlp, faster-whisper, Piper
pip install -e ".[clone]"        # opsional: torch + chatterbox (~2GB)

studiozai doctor                  # cek ffmpeg, GPU, disk, model
studiozai serve                   # http://127.0.0.1:8737 (UI terbuka)
```

Atau langsung dari CLI tanpa UI:

```bash
studiozai clip "https://youtube.com/watch?v=..." --count 5 --lang id
studiozai clip D:\video\podcast.mp4 --no-transcribe        # mode ffmpeg murni
studiozai transcribe video.mp4 --model small --lang id
studiozai tts "Halo, ini narasi promosi." --lang id --out narasi.wav
studiozai clone --sample suara-saya.wav --text "Halo dunia" --out clone.wav   # butuh [clone]
studiozai models list
studiozai models download whisper-small-int8 piper-id_ID-news_tts-medium
```

## 2. Paket Windows (EXE)

```bat
cd desktop\packaging
build_windows.bat
```
Menghasilkan **`dist\StudioZAI\StudioZAI.exe`** (one-folder). Script otomatis memakai Python 3.12 + PyInstaller.

Yang ikut dibundel:
- `ui/` (web UI), `core/studiozai/models/registry.json`
- `ctranslate2`, `faster_whisper`, `av`, `onnxruntime`, `tokenizers`, `piper`, `yt_dlp` (via `collect_all`)
- **FFmpeg + FFprobe** — script mengisi `STUDIOZAI_FFMPEG_DIR` dari PATH sehingga EXE **mandiri tanpa instal ffmpeg terpisah**. Aplikasi mencari binary itu lebih dulu (`utils/ffmpeg.py: bundled_bin_dir()`), baru PATH.

Model AI tetap diunduh saat dipakai (lihat MODELS.md §4), jadi folder aplikasi tetap ~400–600 MB.

Distribusi: ZIP-kan `dist\StudioZAI` → `StudioZAI-1.0.0-windows-x64.zip` (lihat §5), atau buat installer dengan Inno Setup.

## 3. Paket Linux

```bash
cd desktop/packaging
chmod +x build_linux.sh && ./build_linux.sh
```
Menghasilkan `dist/studio-zai.tar.gz`; jika `linuxdeploy` tersedia → `StudioZAI-x86_64.AppImage`.

## 4. Android (APK, target Android 17 / API 37)

```bash
cd android/app
flutter pub get
flutter build apk --release --split-per-abi
# hasil (terverifikasi):
#   app-arm64-v8a-release.apk     42.5 MB  <- untuk HP modern (Android 17)
#   app-armeabi-v7a-release.apk   60.4 MB
#   app-x86_64-release.apk        44.7 MB
```

> **Jangan** menambahkan `ndk { abiFilters }` di `build.gradle.kts` — Flutter sudah mengaturnya dari
> `--split-per-abi`/`--target-platform`, dan Gradle menolak keduanya sekaligus
> (*"Conflicting configuration … cannot be present when splits abi filters are set"*).
> APK arm64 di atas sudah **hanya** berisi `arm64-v8a`.

Jika folder `android/` belum ada (clone bersih), generate dulu lalu salin override:

```powershell
# Windows
flutter create --platforms=android --org com.zwart04 --project-name studiozai C:\dev\wrapper\studiozai
Copy-Item -Recurse C:\dev\wrapper\studiozai\android .\android
Copy-Item -Recurse -Force .\android_overrides\* .\android\
```
> `android_overrides/` berisi `MainActivity.kt` (channel `studiozai/device` untuk RAM/disk) dan `AndroidManifest.xml` (izin internet + baca media, label "Studio ZAI").

konfigurasi penting di `android/app/android/app/build.gradle.kts` (sudah di-set di repo):
`compileSdk = 37`, **`compileSdkMinor = 0`** (wajib: platform Android 17 bernama `android-37.0`, tanpa minor AGP mencari `android-37` dan gagal), `targetSdk = 37`, `minSdk = 26`, `jniLibs.useLegacyPackaging = true` (untuk ffmpeg-kit & sherpa-onnx).

- Kalau Flutter belum terpasang, `python tools\check_dart_refs.py` memeriksa dua kesalahan yang paling
  mahal tanpa perlu SDK: `Tokens.<nama>` yang tidak ada di `theme/tokens.dart` dan `translate('<kunci>')`
  yang tidak ada di `i18n/strings.dart` (penyebab teks mentah seperti "voice.text" muncul di aplikasi).
  `flutter analyze` tetap pemeriksa utama begitu Flutter tersedia.
- APK **tidak berisi model** (diunduh dari halaman Model) → tetap ringan.
- Uji cepat ke HP: `flutter run --release` (HP dengan USB debugging).
- **Signing**: rilis default memakai debug key agar bisa langsung di-*sideload*. Untuk kunci rilis sendiri:
  `keytool -genkey -v -keystore studiozai.jks -keyalg RSA -keysize 2048 -validity 10000 -alias studiozai`
  lalu buat `key.properties` + `signingConfigs { create("release") { … } }` dan ganti `signingConfig` di `buildTypes.release`. **Jangan commit** keystore/`key.properties`.

## 5. Push kode & publikasi artefak ke GitHub

```powershell
# 1. Kode
cd "C:\Users\Zwart\Downloads\Coding AI\Studio ZAI"
powershell -ExecutionPolicy Bypass -File scripts\push_github.ps1

# 2. Rilis + unggah EXE & APK (repo private)
gh auth switch --user Zwart04          # pastikan akun benar
gh release create v1.0.0 `
  "dist\StudioZAI-1.0.0-windows-x64.zip" `
  "android\app\build\app\outputs\flutter-apk\app-release.apk#StudioZAI-1.0.0-android-arm64.apk" `
  --title "Studio ZAI 1.0.0" `
  --notes "EXE Windows mandiri (ffmpeg terbundel) + APK Android 17 (API 37, arm64). Model diunduh dari dalam aplikasi."
```

---

## 6. Struktur Artefak

| Platform | Artefak | Ukuran terverifikasi |
|---|---|---|
| Windows | `StudioZAI-1.0.0-windows-x64.zip` (one-folder, ffmpeg ikut) | **213 MB** (511 MB setelah diekstrak) |
| Linux | `studio-zai.tar.gz` / AppImage | ~200 MB (ffmpeg dari sistem) |
| Android | `app-arm64-v8a-release.apk` | **42.5 MB** |

Model tersimpan di folder data pengguna (MODELS.md §4), bukan di artefak.

## 7. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| PyInstaller: `script '…launcher.py' not found` | Spec dipindah dari struktur repo → spec kini mencari root otomatis (folder yang punya `core/` dan `ui/`) |
| `Failed to find package 'platforms;android-37'` | Nama paket benar: **`platforms;android-37.0`** (versi minor) |
| `Failed to find target with hash string 'android-37'` | Set `compileSdkMinor = 0` di `build.gradle.kts` (platform Android 17 = `android-37.0`) |
| Gradle: `Android SDK file not found: adb` | `sdkmanager ... "platform-tools"` belum jalan |
| APK gagal di plugin yt-dlp Android | Plugin `flutter_yt_dlp` belum kompatibel dengan AGP 9/Gradle 9 → di repo ini sudah dilepas; TikTok/IG diunduh dari desktop |
| PyInstaller EXE: server tidak listen | Lihat `%LOCALAPPDATA%\StudioZAI\launcher.log` (launcher menulis traceback ke sana) |
| Aplikasi jalan di port lain (8738/8739), UI terasa lama | Ada proses `Studio ZAI`/`python` lama yang masih memegang 8737. Tutup lewat Task Manager — kalau prosesnya berjalan sebagai Administrator, Task Manager juga harus dibuka *as Administrator*. Cek cepat: `Get-NetTCPConnection -LocalPort 8737` |
| Folder `StudioZAI-…` tidak bisa dihapus / "file in use" | Aplikasi masih berjalan. Sejak 1.3.2 menutup jendela = proses keluar dan semua anak `ffmpeg` dihentikan (Job Object `KILL_ON_JOB_CLOSE`). Bila sudah di-*End task* dan masih terkunci, akhiri proses `StudioZAI.exe`/`ffmpeg.exe` yang tersisa |
| Gradle lambat pertama kali | Normal: AGP 9.1 + Kotlin 2.4 + dependensi plugin diunduh sekali |
| `ffmpeg not found` (mode dev) | Instal ffmpeg; EXE hasil build sudah membawa ffmpeg sendiri |
| `pip install` gagal (ctranslate2/piper) | Python terlalu baru → pakai 3.12/3.13 |
| Transkrip lambat | Turunkan model ASR di halaman Model (tiny/base) atau pakai GPU (CUDA) |
| Cloning desktop lambat di CPU | Normal (RTF 1–3×). Pakai GPU, teks pendek, atau Piper (tanpa cloning) |
| TikTok gagal diunduh (desktop) | Isi `cookies.txt` (Pengaturan) atau `pip install -U yt-dlp` |
| Halaman Model: unduhan 404 | Model dipindah di upstream → perbarui URL di `core/studiozai/models/registry.json` & `android/app/lib/services/model_registry.dart` |
| UI blank di desktop | Jalankan `studiozai serve` lalu buka `http://127.0.0.1:8737` |
