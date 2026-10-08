# Validasi Studio ZAI 1.10.0

Tanggal: 8 Oktober 2026. Windows x64 dan APK universal Android (version code 15).

## Perubahan dan audit

Klip manual dan viewport kini portrait secara default, dengan sinkronisasi canvas timeline/klip serta invalidasi hasil lama. Tambahan Windows dan Android: crop facecam/gameplay independen, proporsi split, judul pembuka dengan saran lokal dan empat preset, watermark teks/gambar dengan opasitas, seleksi beberapa kata, mode kata/highlight/kotak aktif, pratinjau caption draft, serta deteksi bahasa otomatis. Fitur podcast, review, keyframe, tracking posisi wajah, terjemahan, galeri dan batch sebelumnya tetap tersedia.

Pemetaan diperiksa terhadap daftar publik [SocialVisuals](https://socialvisuals.pro/) pada 8 Oktober 2026. Ini bukan pengujian akses aplikasi berbayarnya. [Matriks fitur dan batas kemampuan](CREATOR.md).

## Bukti pengujian

| Pemeriksaan | Hasil |
|---|---|
| Python | 156 tes lulus, Ruff bersih. Termasuk sinkronisasi kanvas, mode kata aktif, serta render split nyata dua area warna berbeda. |
| Flutter | 30 tes lulus; analyzer tanpa isu. Split/keyframe, ASS ActiveBox dan serialisasi ukuran/opasitas tercakup. |
| Browser + FFmpeg | Enam ekspor 9:16/1:1/16:9 dengan audio diperiksa FFprobe; galeri, pencarian/filter, putar/edit/unduh dan layout 390 px lulus. Tambahan split/title/watermark teks/multiselect/box dan preview caption draft lulus. |
| Runtime EXE | Paket 1.10.0 dengan profil terisolasi: render split/title/upload watermark gambar/box lulus, draft preview tidak menyimpan perubahan, Argos menghasilkan Hello world + VTT, tracking wajah menghasilkan 2 keyframe. Smoke umum lulus untuk runtime Piper/ZipVoice, gambar lokal nyata, preview unik, ekspor dan hapus proyek uji. |
| Windows ZIP | 384.8 MiB; archive CRC integrity lulus, StudioZAI.exe dan UI finishing terbundel. |
| APK | 1.10.0 code 15, 166.5 MiB, min SDK 26; ARM64/ARMv7/x86_64. Signature v2 dan zipalign 16 KB lolos; sertifikat sideload sama. |
| Pemeriksaan visual | Kanvas editor portrait dan frame ekspor split 1080×1920 dengan judul, watermark dan kotak kata aktif dilihat langsung. |

[Editor portrait](screenshots/creator-portrait.png) · [Frame hasil ekspor](screenshots/creator-export.png).

Script integrasi yang dipelihara: `tools/smoke_batch_ui.py`, `tools/smoke_creator_exe.py`. Media, profil aplikasi dan model pengujian terisolasi dari data pengguna. Checksum paket disertakan pada rilis GitHub.

## Susunan folder dan pembersihan

Seluruh pengerjaan dikumpulkan di `C:\Users\Zwart\Downloads\Coding AI\Studio ZAI`. Source, dokumentasi dan bukti visual disimpan; paket terakhir berada di `releases/1.10.0/`. Build lama, virtualenv duplikat, skrip/media temporer, fixture dan keluaran tes dibersihkan setelah paket diperiksa. Source Python aplikasi dan tes yang dipelihara tetap diperlukan untuk pengembangan.

Sekitar 7 GB artefak lama dibersihkan sebelum build baru. Angka ini ukuran logis perkiraan, bukan pengukuran tepat blok disk: sebagian fixture memakai hardlink. Tiga direktori cache lama (`.pytest_cache`, `core/.pytest_cache` dan `.tmp-pytest`) tetap terkunci oleh izin Windows. Pembersihan massal sempat ditolak pemeriksaan otomatis; pembersihan dilanjutkan dengan target artefak yang diverifikasi melalui `flutter clean` dan `git clean` scoped. Data/model/proyek pengguna di LOCALAPPDATA tetap tersimpan.

## Batas validasi

- Tidak ada perangkat Android fisik atau emulator tersambung. Build, tes dan signature tidak membuktikan render/ASR/ML Kit/tracking native end-to-end di HP.
- API cloud tidak diuji menggunakan key pengguna. Saran judul lokal mengambil ucapan/hook, bukan generasi cloud.
- Deteksi bahasa memerlukan model multilingual. Skor podcast memakai heuristik ID/EN lokal; tracking mengikuti posisi wajah, bukan diarization pembicara aktif.
- Android YouTube/URL media langsung didukung; TikTok/Instagram memakai impor file lokal. Windows memakai situs yang didukung yt-dlp.
- APK memakai kunci sideload yang sama dengan rilis sebelumnya, bukan signing produksi Play Store.
