# v1.17.1 — 15 Oktober 2026

- Palet ulang gaya editor video: latar arang, permukaan bertingkat, kartu radius besar. Aksen biru hanya untuk tombol utama dan merah hanya untuk tombol hapus; tab aktif, seleksi, fokus, progress, playhead, dan preset memakai netral.
- Beranda disusun ulang jadi dua kolom yang mengalir sendiri, sehingga bagian dengan tinggi berbeda tidak meninggalkan lubang kosong. "Kinerja laptop" dilipat, judul dan keterangan diringkas.
- Tombol Hapus pada proyek, model, kunci API, dan klip kini konsisten merah. Strip merah dekoratif di bawah app bar Android dihapus mengikuti penghapusan strip serupa di web.
- Token warna Android disinkronkan dengan web dan `docs/DESIGN.md` diperbarui mengikuti kebijakan aksen baru.

[Pengujian dan batas](RELEASE-1.17.1.md).

---

# v1.17.0 — 15 Oktober 2026

- Workspace editor Windows memenuhi jendela, dengan preview penuh yang tetap memuat subtitle dan overlay.
- Animasi dipilih langsung di editor; subtitle panjang dibagi mengikuti ucapan dan dapat pindah baris dalam frame.
- Perbaikan pop, fade, posisi, dan karaoke saat ekspor; tata letak beranda serta kontrol bersama diperbarui.
- Paket Windows kini menyertakan teks lisensi SIL OFL dan catatan asal empat font subtitle yang dibundel.

[Cakupan, validasi, dan batas](RELEASE-1.17.0.md) · [Laporan penerapan antislop](ANTISLOP-1.17.0.md).

---

# v1.16.0 — 15 Oktober 2026

- Beranda Windows menampilkan semua klip beserta transkrip; pilihan Transkrip saja dihapus.
- Preview 360p disiapkan bertahap, pemutar editor dipertahankan saat mengedit, dan overlay tampil langsung.
- Transkrip per baris, panel editor terkelompok, 30 template teks dan 12 animasi.
- Mode Hemat RAM, pilihan GGUF terkecil, serta pembatas thread CPU.

[Cakupan, validasi, dan batas](RELEASE-1.16.0.md).

---

# v1.15.0 — 14 Oktober 2026

- Kelompok analisis, transkrip, subtitle, dan hasil klip terlihat langsung di beranda Windows.
- Tombol GGUF lebih besar dengan status proses dan perlindungan klik berulang.
- Ikon resmi provider, panduan API, penanda kuota gratis, dan pilihan model berdasarkan prioritas di Windows dan Android.

[Validasi dan batas saran model](RELEASE-1.15.0.md).

---

# v1.14.0 — 14 Oktober 2026

- Pilihan cepat animasi subtitle: Sorot + Pop, Lentur, Karaoke, Muncul per kata, Satu kata, Tanpa gerak.
- Beranda Windows dua kolom, kontrol GGUF ringkas, contoh animasi yang dapat diputar.
- Samakan kurva pop/lentur pada preview dengan ekspor; hanya kata aktif yang bergerak pada highlight.

[Validasi](RELEASE-1.14.0.md).

---

# v1.10.0 — 8 Oktober 2026

- Perbaiki default portrait pada klip manual dan tampilan kanvas; sinkronkan rasio timeline dan klip, serta buang hasil lama setelah perubahan.
- Windows/Android: split gaming dengan crop facecam/gameplay independen, proporsi, zoom, keyframe dan tracking posisi wajah.
- Judul pembuka dengan saran lokal/preset dan watermark teks/gambar dengan ukuran, posisi dan opasitas.
- Caption: seleksi beberapa kata, mode kata/highlight/kotak aktif, dan pratinjau video draft melalui jalur ekspor tanpa menyimpan draft.
- Bahasa transkripsi otomatis dan 11 bahasa pilihan; bahasa ASR Android disimpan untuk caption berikutnya.
- Audit ulang fitur publik SocialVisuals, rapikan paket lama dan hasil tes, serta kumpulkan source/paket terbaru dalam satu folder Studio ZAI.

[Validasi](RELEASE-1.10.0.md) · [Cakupan dan batas fitur](CREATOR.md).

---

# v1.9.0 — 29 September 2026

- Windows dan Android: mode podcast lokal dengan alasan skor, target jumlah otomatis, draf untuk review sebelum render, dan judul/hook editable.
- Caption per kata, timing, font, ukuran, warna, tebal, posisi X/Y, serta animasi pop/fade/rise/zoom/type. Android membaca timestamp token Whisper ketika tersedia.
- Crop manual yang dapat diseret, zoom, keyframe, dan pelacakan posisi wajah lokal. Trim/split ikut menyesuaikan kata dan keyframe.
- Terjemahan lokal dengan unduhan model, versi subtitle per bahasa, serta ekspor subtitle terpisah tanpa render ulang video.
- Galeri lintas proyek, pencarian/filter/skor, preview, akses editor, dan batch multi-format 9:16/1:1/16:9 di kedua platform.
- Groq dan Gemini ditambahkan; input transkrip panjang dipecah sebelum ranking AI dan hasil tumpang tindih dibuang.
- Upload berkas dan drag/drop pada Beranda browser desktop diperbaiki. Output per format disimpan terpisah.

[Panduan fitur dan batas kemampuan](CREATOR.md) · [Validasi](RELEASE-1.9.0.md).

---

# v1.8.0 — 23 September 2026

- Editor desktop kini menempatkan pemutar dan panel pengaturan di atas timeline dengan penggaris/playhead, drag blok/tepi, dan impor berkas ke track. Tombol dialog mengikuti gaya aplikasi.
- Subtitle otomatis di editor desktop tidak menutup panel saat pekerjaan berjalan; klip tanpa transkrip proyek ditranskripsi hanya pada rentang yang dipilih. Alur awal menjelaskan bahwa subtitle dibuat Whisper lokal dari audio, bukan caption tautan.
- APK memperjelas pembuatan subtitle dan menjaga caption lama bila audio hening. Pemilih contoh kloning menerima dokumen audio dari penyimpanan Android, mengubahnya ke WAV, serta memakai teks kloning terpisah dari formulir TTS.
- Katalog suara diaudit per lisensi suara dan data. Supertonic 3 menjadi rekomendasi Indonesia, Piper LJSpeech untuk English; suara lama yang nonkomersial atau haknya belum jelas ditandai dan tidak ditawarkan sebagai pilihan baru.
- Model kloning Indonesia Chatterbox Apache-2.0 tersedia sebagai opsi desktop dari source yang berat, dengan kegagalan runtime/checkpoint yang jelas; APK tetap memakai ZipVoice English/Mandarin. Formulir desktop dapat memilih model, mengimpor format audio yang dibaca FFmpeg, atau merekam mikrofon.
- Perbarui README, tangkapan layar, tur GIF, dokumen model, dan paket rilis.

[Validasi dan batasan](RELEASE-1.8.0.md).

---

# v1.7.0 — 23 September 2026

- Perbaiki jalur model Android yang mengirim objek Flutter ke isolate, validasi arsip/checksum, serta fallback pembuatan klip ketika hasil transkripsi tidak menghasilkan rekomendasi.
- Mode klip adaptif mengutamakan awal topik/ulasan produk dan memilih akhir pada batas ucapan; opsi durasi minimum/maksimum yang membingungkan dihapus dari alur utama.
- Pertahankan kualitas audio sumber saat tidak ada efek tambahan dan naikkan kualitas AAC ketika audio harus dicampur.
- Tata ulang beranda, formulir sumber/bahasa/track/audio, editor dengan pemutar langsung, dan jarak antarkontrol dalam palet gelap netral.
- Tambahkan gambar lokal SDXS-512 pada Windows dan Android ARM64, model terpisah dengan SHA-256; mode cloud tetap opsional.
- Tambahkan Supertonic 3 int8 dengan sepuluh karakter suara ID/EN di desktop dan Android, tanpa mengubah cakupan kloning ZipVoice.
- Perbarui logo README, tangkapan layar, GIF UI, dan dokumentasi batas fitur per platform.

[Validasi dan batasan](RELEASE-1.7.0.md).

---

# v1.6.0 — 23 September 2026

- Unduhan Android dengan profil stream baru, retry terbatas, progres byte, dan track bahasa tetap.
- Progres transkripsi panjang diperbaiki; SSE tidak macet setelah banyak segmen.
- Pemutar langsung, pembaruan otomatis, trim/split, sumber tersimpan, tipografi custom, dan subtitle tanpa track ganda.
- Duplikat proyek independen dan cache Android tidak menghapus video sumber.
- 7 pilihan Piper, ZipVoice CPU Windows/Android, rekaman mikrofon, 13 suara OpenAI opsional.
- AI teks OpenAI/Anthropic/DeepSeek/compatible, gambar OpenAI/SD.cpp server, kunci terlindungi.
- Beranda ringkas, logo kontras, README dan screenshot baru.
- Satu APK universal, Windows ZIP dan checksum; tidak ada demo MP4.

[Validasi dan batasan](RELEASE-1.6.0.md).

---

# CHANGELOG — Studio ZAI

Format mengikuti [Keep a Changelog](https://keepachangelog.com/) dan [Semantic Versioning](https://semver.org/).

## 1.5.1 — 2026-09-22

- Perbaiki track audio Indonesia, rasio kanvas asli/kotak, preview, subtitle otomatis, dan penerapan perubahan editor.
- Tambah 24 template dengan font OFL lokal, preset posisi 3 × 3, serta input persentase; pertahankan palet Apple-style yang ada.
- Perjelas pilihan sumber dan pengaturan, perbaiki layout responsif dan sinkronisasi daftar setelah penghapusan.
- Wajibkan setup awal yang memverifikasi model; pindahkan ekstraksi dan ASR Android dari UI thread, serta baca audio panjang secara bertahap.
- Perbaiki visibilitas logo dan area aman ikon Android. Sertakan paket sumber model desktop yang sebelumnya terabaikan oleh aturan Git.
- Perbarui README ID/EN, screenshot, GIF, dan MP4. Uji video nyata 78 menit dengan audio Indonesia hingga ekspor; lihat [validasi](RELEASE-1.5.1.md).


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
