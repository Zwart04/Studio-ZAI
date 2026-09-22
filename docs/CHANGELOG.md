# CHANGELOG — Studio ZAI

Format mengikuti [Keep a Changelog](https://keepachangelog.com/) dan [Semantic Versioning](https://semver.org/).

## [1.5.0] — 2026-09-22

### Added
- **Editor timeline multi-track** (Android + Desktop): track Video, Media (overlay gambar/video),
  Teks, dan Audio. Blok bisa digeser (ubah waktu) dan ditarik tepinya (ubah durasi).
  Data timeline disimpan di `clip.timeline` dan dirender lewat graf FFmpeg yang sama di kedua platform
  (`core/studiozai/pipeline/timeline.py` ↔ `android/.../services/timeline_render.dart`).
- **8 template tipografi** — Clean, Bold highlight, TikTok pop, Karaoke fill, Title card,
  Minimal lower, Neon, Subtitle box. Berlaku untuk caption otomatis maupun item track teks
  (`GET /api/subtitle-presets`).
- **Pratinjau cepat** (540×960) di editor — `POST /api/projects/{id}/clips/{index}/preview`,
  tanpa menimpa hasil render final.
- **Tambah media**: `POST /api/projects/{id}/assets` menyalin gambar/video/audio pilihan pengguna
  ke folder proyek agar timeline tetap valid.
- Mode framing **`fit`** (letterbox — seluruh frame tampil, tidak ada yang terpotong) dan pilihan
  **ukuran klip** (potrait/asli/kotak/landscape) kini juga ada di Android.

### Fixed
- **"Ruang penyimpanan kurang … tersedia 0 MB" saat unduh model**: perhitungan ruang bebas di Dart
  memakai `FileStat.stat()` pada sebuah FOLDER, yang di Android selalu bernilai 0. Sekarang memakai
  `StatFs` lewat MethodChannel (`freeDiskMb`), dan bila ruang tidak diketahui pemeriksaan dilewati.
  (Bukan masalah izin — model ditulis ke penyimpanan internal aplikasi.)
- **"Unduhan gagal (HTTP 416)"**: unduhan yang sudah selesai tetapi gagal diekstrak membuat percobaan
  berikutnya mengirim `Range` dari posisi akhir → server membalas 416. Sekarang 416 dengan berkas
  lokal yang ada diperlakukan sebagai "sudah lengkap" dan langsung masuk tahap ekstraksi; berkas
  parsial yang rusak dibuang lalu diunduh ulang sekali.
- **Tombol/teks berantakan di kartu klip (desktop)**: `.icon-btn` dikunci 34 px padahal berisi label
  teks, sehingga tombol meluber dan tombol Hapus tampak hilang. Sekarang lebar otomatis + ikon SVG
  diberi ukuran; judul klip dibatasi 2 baris.
- **Teks kepotong di klip**: caption diperpendek (28 karakter / 5 kata) dan margin diperlebar,
  plus mode `fit`/`blur` agar teks milik video sumber tidak ikut terbuang oleh crop 9:16.
- **Tombol hapus klip**: kini ada konfirmasi (Android & Desktop), menghapus berkas hasil render,
  merapikan indeks, dan menampilkan umpan balik.
- **Kunci terjemahan yang hilang** (`voice.text`, `voice.lang`, `voice.model`) tidak lagi tampil
  sebagai teks mentah; versi aplikasi di layar Pengaturan disamakan dengan pubspec.

### Changed
- Ekstraksi arsip model memakai `rename` (bukan salin) sehingga puncak pemakaian disk lebih kecil
  dan ekstraksi lebih cepat.
- Aksen utama tetap biru; merah dipakai hemat untuk rekam/hapus/peringatan.
- Versi: core `1.5.0`, APK `1.5.0+9`.

### Tests & tooling
- 86 tes lulus, termasuk `core/tests/test_timeline_render.py` — render timeline **sungguhan** dengan
  FFmpeg (video + overlay gambar + teks ber-template + musik, sumber tanpa audio, perintah pratinjau)
  yang dilewati otomatis kalau ffmpeg tidak ada.
- `tools/check_dart_refs.py` — pemeriksa `Tokens.<nama>` dan `translate('<kunci>')` tanpa perlu Flutter,
  menangkap kesalahan yang biasanya baru ketahuan saat build.
- `flutter analyze` bersih (No issues found).

## [1.4.0] — 2026-09-22

### Fixed
- **Aplikasi Android tertutup sendiri saat unduh model**: ekstraksi `.tar.bz2` dulu memuat seluruh
  arsip ke memori (`readAsBytesSync` + `decodeBytes`) — ZipVoice 350 MB butuh ~1 GB RAM sehingga
  Android membunuh aplikasi. Sekarang bz2 didekompresi streaming ke berkas `.tar` sementara, lalu
  `.tar` dibaca per blok 64 KB (memori tetap kecil) + cek ruang disk sebelum ekstrak.
- **Layar selalu tampak kusam/terhalang**: wizard setup muncul terus selama model inti belum lengkap.
  Sekarang wizard layar penuh hanya saat pertama kali; kalau model kurang, muncul banner kecil di
  Beranda dengan tombol "Siapkan"/"Nanti".
- **Subtitle dobel dengan subtitle bawaan video**: berkas kerja kini dibersihkan dari track
  subtitle/data bawaan (remux stream-copy), dan posisi subtitle bisa dipilih —
  Bawah / Tengah / Atas / Tanpa subtitle (untuk video yang sudah punya subtitle sendiri).

### Changed
- **UI dirombak (gaya Apple)**: stylesheet ditulis ulang — hitam pekat, judul putih tegas, kartu
  "inset grouped" dengan garis rambut, toggle iOS, segmented control, tombol biru iOS, sheet panel,
  toast, dan gerak 200 ms; tata letak mobile memakai tab bar bawah.
- **Daftar model Android lengkap**: ditambah whisper-small, whisper-medium, dan suara Inggris
  (en_GB alba) sehingga semua model yang tersedia tampil dengan tombol unduh/hapus.

### Tests
- 68 tes lulus (5 tes baru untuk posisi subtitle), `ruff` bersih, `flutter analyze` 0 error.

## [1.3.3] — 2026-09-22

### Security
- `project_id` dari URL kini divalidasi (`^[A-Za-z0-9_-]{1,64}$`) sebelum dipakai sebagai nama folder —
  sebelumnya `DELETE /api/projects/..` dapat menghapus seluruh folder data aplikasi.
- Ekstraksi arsip model (`tar`/`zip`) memakai validasi anggota: menolak path absolut, `..`, keluar
  folder tujuan, dan symlink/hardlink; memakai `filter="data"` pada Python 3.12+.
- Android: `allowBackup=false` + aturan ekstraksi data (proyek/model/rekaman tidak ikut backup cloud),
  dan `network_security_config` menolak lalu lintas HTTP polos.
- 20 tes keamanan baru di `core/tests/test_security.py` (total 63 tes lulus).

### Verified
- Audit: tidak ada rahasia ter-hardcode, tidak ada berkas sensitif ter-commit, APK tidak `debuggable`,
  Windows Defender tidak menemukan ancaman pada artefak hasil build.

## [1.3.2] — 2026-09-22

### Fixed
- **Aplikasi tidak bisa ditutup / folder tidak bisa dihapus**: fallback jendela Chrome/Edge dulu
  loop selamanya sehingga proses EXE tetap hidup setelah jendela ditutup. Sekarang launcher
  menunggu jendela ditutup lalu keluar.
- **Satu instance saja**: membuka aplikasi dua kali tidak lagi membuat server/jendela ganda
  (dipakai `instance.json` + pengecekan PID & port); jendela kedua menyambung ke instance yang jalan.
- **Proses ffmpeg tidak tertinggal**: semua proses anak dilacak (`utils/proc.py`) dan dihentikan
  saat keluar, plus Job Object Windows `KILL_ON_JOB_CLOSE` supaya ikut mati walau aplikasi di-End task.
- **Unduhan model gagal (404)**: entri `chatterbox-gguf-q4` dan `mms-tts-ind` dihapus dari registry
  desktop & Android (URL-nya sudah tidak ada / modelnya tidak punya berkas ONNX). Tersisa 10 model
  yang seluruh URL-nya sudah diverifikasi HTTP 200.
- **Versi tidak sinkron**: kode masih 1.0.0 padahal rilis GitHub sudah 1.3.1. Versi kini 1.3.2 di
  `__init__.py`, `pyproject.toml`, dan `pubspec.yaml`, dijaga oleh `scripts/check_version.py`.
- **Tes gagal karena PermissionError**: folder `%TEMP%\pytest-*` bisa punya ACL rusak setelah sesi
  mati paksa; pytest kini memakai basetemp lokal (`.tmp-pytest`).
- **Lint bersih**: 15 temuan ruff diperbaiki, termasuk bug closure variabel loop di `transcribe.py`.

## [1.3.1] — 2026-09-22
- UI tanpa emoji, nama model lebih natural, perbaikan penamaan aset rilis.

## [1.3.0] — 2026-09-22
- UI overhaul: ikon SVG navigasi, toggle gaya iOS, skeleton, progress monoton, wizard setup awal.

## [1.2.0] — 2026-09-22
- Klip muncul kembali, transkrip lebih cepat (chunk 10 menit), progress lebih jelas.

## [1.0.0] — 2026-09-21

### Added
- **Core engine (Python)**: pipeline download (yt-dlp), transkripsi (faster-whisper), auto-clip heuristik (RMS + silence + scene, tanpa AI) dan berbasis transkrip, subtitle SRT/ASS (2 preset), crop 9:16 (center/blur), render ffmpeg (nvenc auto), TTS Piper ID/EN, voice cloning Chatterbox (ID fine-tune + EN, lazy/extra), dubbing & ducking.
- **CLI**: `doctor`, `serve`, `download`, `probe`, `transcribe`, `clip`, `tts`, `clone`, `models`.
- **Model Manager**: registry `registry.json`, deteksi hardware (RAM/GPU/disk), tier otomatis per platform, unduh resume + verifikasi sha256, benchmark RTF untuk model cloning.
- **Desktop UI**: FastAPI + SSE, web UI vanilla minimalis (Beranda, Proyek, Editor, Suara, Model, Pengaturan), bilingual ID/EN, dark theme.
- **Editor sederhana**: trim, split, urutkan ulang, edit teks subtitle, crop per klip, volume, re-render.
- **Android (Flutter)**: app on-device penuh — YouTube via `youtube_explode_dart` (pure Dart), TikTok/IG via `flutter_yt_dlp`, unduhan langsung via HTTP; sherpa-onnx (ASR Whisper int8, TTS VITS Piper ID/EN, VAD, **ZipVoice cloning EN**), ffmpeg_kit_flutter_new, Manajer Model tier Android, tujuan **Android 17 (compileSdk/targetSdk 37, minSdk 26)**.
- **Packaging**: PyInstaller spec (membundel FFmpeg/FFprobe + ctranslate2/onnxruntime/av/piper/yt-dlp) + script Windows/Linux, script build APK, `scripts/push_github.ps1`, panduan rilis `gh release create`.
- **UI Apple-style**: palet iOS dark (accent `#0A84FF`), kartu *inset grouped* dengan garis rambut, segmented control ID/EN, sheet translusen, tab bar bawah di layar kecil — diterapkan di web UI dan Flutter dengan token identik.
- **Dokumentasi**: PRD, PLAN, FEATURES, ARCHITECTURE, TECH_STACK, MODELS, DESIGN, BUILD, SECURITY, CONTRIBUTING, README bilingual.

### Notes
- Model tidak dibundel; diunduh on-demand dari sumber resmi (HuggingFace/rilis) via Manajer Model.
- Voice cloning: Chatterbox (MIT) untuk desktop (ID + EN); ZipVoice (Apache-2.0) untuk EN di Android (on-device, butuh rekaman contoh + transkripnya).
- Semua output Chatterbox mengandung watermark PerTh (bawaan model).
- Toolchain rilis terverifikasi: Python 3.12.10, Flutter 3.47.5, JDK 17, Android SDK `platforms;android-37.0` + `build-tools;37.0.0`.

### Known Limitations
- Face-track crop (mediapipe) masih tahap uji (P1).
- Chatterbox di CPU bisa lebih lambat dari realtime (RTF 1–3× pada CPU modern).
- Chatterbox Q4 di Android **belum diimplementasikan** (butuh integrasi native llama.cpp) — di HP, kloning tersedia untuk Bahasa Inggris via ZipVoice.
- Belum ada publishing langsung ke sosmed (roadmap P2).
