<p align="center"><img src="assets/brand-banner.svg" width="840" alt="Studio ZAI — Video, Suara, Gambar" /></p>

<p align="center">Studio video sederhana untuk Windows dan Android. Temukan momen dari video panjang, edit langsung, buat subtitle, suara, dan gambar dengan model lokal.</p>

<p align="center"><a href="https://github.com/Zwart04/Studio-ZAI/releases/latest"><strong>Unduh v1.10.0</strong></a> · <a href="#mulai">Mulai</a> · <a href="docs/FEATURES.md">Fitur per perangkat</a> · <a href="docs/MODELS.md">Model & lisensi</a> · <a href="README.en.md">English</a></p>

![Editor Studio ZAI: video dapat diputar langsung, subtitle dan timeline di satu layar](docs/screenshots/creator-portrait.png)

## Baru di 1.10

Kanvas editor dan klip manual kini portrait secara default. Windows dan Android mendapat split facecam/gameplay, judul pembuka, watermark teks/gambar, seleksi beberapa kata, kotak kata aktif, pratinjau perubahan caption, serta deteksi bahasa otomatis. Deteksi podcast, crop/keyframe, terjemahan, galeri, dan batch tiga rasio tetap tersedia. [Panduan lengkap dan batas fitur](docs/CREATOR.md) · [Pengujian rilis](docs/RELEASE-1.10.0.md).

## Buat video dari ide sampai siap ekspor

| Video | Suara | Gambar |
| :-- | :-- | :-- |
| Temukan klip dari transkrip, simpan sumber, potong lagi tanpa mengunduh ulang. | Narasi Indonesia/Inggris, sepuluh karakter Supertonic lokal, suara Piper yang terpilih, rekaman mikrofon, dan kloning suara. | SDXS-512 membuat gambar 512×512 di perangkat setelah model diunduh. Penyedia cloud tetap pilihan. |

**Klip otomatis yang mengikuti isi video.** Mode durasi adaptif mencari awal topik atau ulasan produk dan titik akhir kalimat yang masuk akal. Pilih track audio sumber sebelum memproses; bahasa transkripsi tidak mengubah atau menerjemahkan suara. Pengguna tetap bisa mengambil rentang waktu lain dari video sumber yang tersimpan.

**Editor dengan timeline.** Video langsung dapat diputar, panel pengaturan ada di samping, dan timeline ada di bawah. Geser blok untuk memindahkan teks/media, tarik tepinya untuk mengubah durasi, atau letakkan berkas ke track. Trim, split, ukuran asli/9:16/1:1/16:9, musik, dan subtitle ada di layar yang sama. Buat subtitle AI untuk satu klip tanpa perlu menranskripsi ulang seluruh video panjang; terapkan salah satu dari 24 gaya atau simpan tipografi buatanmu.

**Lokal lebih dulu.** File lokal, editor, transkripsi, subtitle, suara, dan gambar lokal berjalan tanpa API key setelah model dipasang. Model tidak dibundel dalam APK/EXE agar paket awal tetap lebih kecil. Unduhan model dan video dari tautan tentu membutuhkan internet. Groq, Gemini, OpenAI, Anthropic, DeepSeek, dan endpoint kompatibel tersedia sebagai pilihan untuk tugas AI yang mendukungnya.

## Unduh

| Perangkat | Paket | Catatan |
| :-- | :-- | :-- |
| Windows 10/11 x64 | [ZIP Windows](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.10.0/StudioZAI-1.10.0-windows-x64.zip) | Ekstrak seluruh folder, jalankan **StudioZAI.exe**. FFmpeg dan runtime AI ikut; bobot model diunduh saat dibutuhkan. |
| Android 8+ | [Satu APK universal](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.10.0/StudioZAI-1.10.0-android.apk) | Editor dan suara mendukung ABI paket; gambar native offline tersedia pada **ARM64**. |

[Catatan pengujian v1.10.0](docs/RELEASE-1.10.0.md) · [Checksum SHA-256](https://github.com/Zwart04/Studio-ZAI/releases/download/v1.10.0/SHA256SUMS.txt) · [Cara build](docs/BUILD.md)

## Mulai

1. Jalankan setup awal dan unduh model transkripsi sesuai perangkat. **Whisper Base** cukup untuk mulai; **Small** umumnya lebih baik untuk Indonesia jika RAM memadai. Pilihan suara Indonesia utama adalah **Supertonic 3** (sepuluh karakter, lisensi OpenRAIL-M); gambar dapat dipasang kemudian dari halaman **Model**.
2. Tempel tautan atau pilih video lokal. Letakkan **bahasa konten** dan **track audio sumber** yang benar sebelum memilih suara klip asli atau narasi. Pada Android, tautan YouTube publik dan URL berkas langsung didukung; untuk TikTok/Instagram, impor berkas video yang telah disimpan. Desktop memakai situs yang didukung yt-dlp.
3. Pilih jumlah klip dan tekan **Buat klip**. Jika **Subtitle AI dari audio** aktif, Whisper lokal mengenali ucapan; Studio ZAI tidak mengambil caption dari tautan. Aplikasi menyimpan sumber bersama proyek. Buka klip untuk memutar, memotong, mengubah kanvas, dan menata subtitle.
4. Ekspor hasil saat selesai. Untuk mengambil momen lain, buka **Ambil bagian dari video sumber**; tidak perlu mengunduh video itu lagi.

> **Transkrip** adalah teks ucapan yang dipakai untuk memilih momen. **Subtitle** adalah bagian teks tersebut yang diberi waktu dan ditampilkan pada video. Jika sumber sudah memiliki tulisan yang menyatu dengan gambar, nonaktifkan subtitle tambahan atau ubah posisinya agar tidak bertumpuk. ZipVoice mendukung kloning English/Mandarin; kloning Indonesia hanya tersedia sebagai opsi desktop dari source dengan Chatterbox/PyTorch yang jauh lebih berat, belum di APK/EXE ringan. Sepuluh suara Supertonic mendukung TTS Indonesia/Inggris, bukan kloning.

## Lihat aplikasinya

![Tur singkat antarmuka Studio ZAI](docs/screenshots/studio-zai-demo.gif)

| Beranda | Suara | Gambar |
| :--: | :--: | :--: |
| ![Beranda dan pengaturan klip](docs/screenshots/01-home.jpg) | ![Pilihan suara dan rekaman](docs/screenshots/03-voice.jpg) | ![Gambar lokal dan pilihan cloud](docs/screenshots/07-images.jpg) |

Gambar di atas diambil dari UI desktop dengan media demo yang dibuat untuk dokumentasi. [Beranda sempit](docs/screenshots/05-mobile-home.jpg) dan [editor sempit](docs/screenshots/09-mobile-editor.jpg) menguji web pada lebar ponsel dan bukan screenshot APK. GIF adalah tur UI; tidak ada berkas demo MP4 di rilis.

## Model, privasi, dan batasan

Bobot [SDXS-512](docs/LOCAL_IMAGE.md) sekitar 683 MB dan butuh RAM tambahan saat menghasilkan gambar. Performa bergantung pada perangkat; ponsel ARM32 belum memiliki mesin gambar offline native. Model lama dengan batas nonkomersial atau hak data yang belum jelas tetap diberi tanda dan tidak direkomendasikan. **Supertonic 3 adalah open-weights, bukan open source OSI**, dan izin komersialnya memiliki syarat. [Daftar model dan lisensinya](docs/MODELS.md) menjelaskan sumber dan batasan setiap pilihan.

Kunci API disimpan pada penyimpanan terlindungi sistem. Mode lokal tidak mengirim prompt atau media ke penyedia cloud. Mode online mengirim permintaan ke penyedia yang dipilih. Video privat, dihapus, dibatasi wilayah, atau meminta login bisa gagal diunduh; pilih berkas lokal sebagai alternatif.

Alur pemilihan klip diuji dengan [video review speaker nyata 80,5 menit](https://youtu.be/4WvlolSYqjU). Pemeriksaan editor, subtitle satu klip, paket desktop dan APK dijelaskan pada [laporan rilis](docs/RELEASE-1.8.0.md). Perangkat Android fisik belum tersedia untuk uji end-to-end dalam sesi ini.

## Kembangkan

**Galeri klip lintas proyek** dan **ekspor batch 9:16 / 1:1 / 16:9** tersedia dalam paket Windows dan Android v1.10.0. [Panduan penggunaan](docs/CLIP_GALLERY.md).

```powershell
git clone https://github.com/Zwart04/Studio-ZAI.git
cd Studio-ZAI
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e "core[media,asr,tts,face,translation,desktop,dev]"
.venv/Scripts/python.exe -m studiozai serve
```

```powershell
.venv/Scripts/python.exe -m pytest core/tests
cd android/app
flutter pub get
flutter analyze
flutter test
flutter build apk --release
```

[Arsitektur](docs/ARCHITECTURE.md) · [Fitur per platform](docs/FEATURES.md) · [Build dan signing](docs/BUILD.md) · [Changelog](docs/CHANGELOG.md)

Kode aplikasi berlisensi [MIT](LICENSE). Model, font, dan library native memakai lisensi masing-masing. Referensi alur kreator: [openshorts](https://github.com/mutonby/openshorts) dan [OpenCreator](https://github.com/krillinai/OpenCreator).
