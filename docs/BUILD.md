# BUILD — Studio ZAI
### Cara Build & Menjalankan

> **EN TL;DR** — Prereqs: Python 3.11-3.13, FFmpeg in PATH. Desktop dev: `pip install -e .[dev]` then `studiozai serve`. Windows package: PyInstaller (one-folder). Linux: PyInstaller + AppImage. Android: Flutter SDK + Android SDK, `flutter build apk`. Troubleshooting table at the end.

---

## 0. Prasyarat Umum

| Kebutuhan | Windows | Linux | Cek |
|---|---|---|---|
| Python 3.11–3.13 *(disarankan)* | python.org / `winget install Python.Python.3.12` | `apt install python3 python3-venv` | `python --version` |
| FFmpeg ≥ 6 | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` | `ffmpeg -version` |
| Git | `winget install Git.Git` | `apt install git` | `git --version` |
| GitHub CLI *(untuk push)* | `winget install GitHub.cli` | `apt install gh` | `gh --version` |
| Flutter 3.x + Android SDK *(khusus Android)* | lihat flutter.dev | idem | `flutter doctor` |

> Python 3.14+: didukung **jika** semua wheel (ctranslate2, piper, dll.) tersedia. Jika ada kegagalan instalasi, pakai 3.12/3.13 lalu buat venv.

---

## 1. Menjalankan Mode Dev (Desktop)

```bash
cd core
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux: source .venv/bin/activate
pip install -e ".[dev]"          # inti + test
pip install -e ".[clone]"        # opsional: torch + chatterbox (~2GB)
pip install -e ".[face]"         # opsional: mediapipe untuk face-track (uji)

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

## 2. Paket Windows

```bat
cd desktop\packaging
build_windows.bat
```
Menghasilkan `dist\StudioZAI\StudioZAI.exe` (one-folder, tanpa model). Opsional: kompres ZIP atau buat installer dengan Inno Setup (script di folder yang sama).

Isi build:
- PyInstaller spec sudah termasuk `ui/`, `core/studiozai/models/registry.json`.
- FFmpeg **tidak** dibundel (biar ringan & legal) — app mendeteksi ffmpeg di PATH; jika tidak ada, tampilkan instruksi instalasi di UI (`doctor`).

## 3. Paket Linux

```bash
cd desktop/packaging
chmod +x build_linux.sh && ./build_linux.sh
```
Menghasilkan `dist/studio-zai.tar.gz`; jika `linuxdeploy` tersedia → `StudioZAI-x86_64.AppImage`.

## 4. Android

```bash
cd android/app
flutter pub get
flutter doctor                      # pastikan Android toolchain OK
flutter build apk --release --split-per-abi
# hasil: build/app/outputs/flutter-apk/app-arm64-v8a-release.apk
```
- APK **tidak berisi model** (diunduh dari dalam app).
- Debug cepat ke perangkat: `flutter run --release`.
- Jika butuh mendowngrade ABI ffmpeg-kit: edit `android/app/android/app/build.gradle` (paket `ffmpeg_kit_flutter_new`).

## 5. Push ke GitHub (private)

```powershell
cd "C:\Users\Zwart\Downloads\Coding AI\Studio ZAI"
powershell -ExecutionPolicy Bypass -File scripts\push_github.ps1
```
Script akan: `git init` → commit → cek login `gh` → `gh repo create Zwart04/Studio-ZAI --private --source . --push`.
Jika akun aktif bukan Zwart04: `gh auth switch --user Zwart04` (script menawarkan otomatis).

---

## 6. Struktur Artefak

| Platform | Artefak | Ukuran perkiraan (tanpa model) |
|---|---|---|
| Windows | `dist/StudioZAI/` one-folder + ZIP | 150–250MB |
| Linux | `studio-zai.tar.gz` / AppImage | 150–250MB |
| Android | APK arm64 (split-per-abi) | 60–120MB |

Model tersimpan di folder data pengguna (lihat MODELS.md §4), bukan di artefak.

## 7. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `ffmpeg not found` | Instal ffmpeg dan pastikan di PATH; jalankan `studiozai doctor` |
| `pip install` gagal (ctranslate2/piper) | Kamu memakai Python versi terlalu baru → pakai 3.12/3.13 |
| Transkrip lambat | Turunkan model ASR di halaman Model (tiny/base) atau aktifkan GPU bila ada CUDA |
| Cloning sangat lambat di CPU | Normal (RTF bisa 1–3×). Gunakan GPU (CUDA) atau teks pendek; mode Piper tetap tersedia |
| TikTok gagal diunduh | Coba `cookies.txt` (Pengaturan → Download) atau update yt-dlp (`pip install -U yt-dlp`) |
| Build Android gagal di ffmpeg-kit | Ganti varian paket (`ffmpeg_kit_flutter_new` ↔ `_full`) dan `flutter clean` lalu ulangi |
| APK tidak bisa unduh model | Izin jaringan/storage; cek koneksi & ruang kosong ≥ 2GB |
| UI blank di desktop | Jalankan `studiozai serve` lalu buka manual `http://127.0.0.1:8737` |
