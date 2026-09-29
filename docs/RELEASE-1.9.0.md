# Validasi Studio ZAI 1.9.0

Tanggal: 29 September 2026. Paket: Windows x64 dan APK universal Android 1.9.0 (version code 14). Data uji terpisah dari proyek pengguna di `build/`.

## Cakupan rilis

Mode podcast dan jumlah klip otomatis, review sebelum render, judul/hook editable, caption per kata dan animasi, crop/keyframe, pelacakan wajah lokal, terjemahan dengan versi bahasa tersimpan, galeri lintas proyek, dan ekspor batch tiga rasio. Groq dan Gemini tersedia sebagai penyedia ranking opsional. Lihat [matriks fitur](CREATOR.md) dan [changelog](CHANGELOG.md).

## Bukti pengujian

| Pemeriksaan | Hasil |
|---|---|
| Python | 150 tes lulus; mencakup ranking podcast, transkrip panjang, subtitle, crop, trim/split, batch, pembatalan, dan perubahan klip saat batch berjalan. Ruff bersih. |
| Flutter | 28 tes lulus. `flutter analyze` tanpa isu. Mencakup ranking podcast, penyimpanan gaya/keyframe/versi bahasa, trim/split, dan timestamp kata. |
| UI desktop dan FFmpeg | Browser mengunggah video sintetis, mengedit caption per kata dan hook, menyimpan crop dengan dua keyframe, lalu merender enam MP4 dari dua klip ke 9:16, 1:1, dan 16:9. FFprobe memeriksa rasio dan audio. Galeri, pencarian, filter, pengurutan, putar, tautan unduh/edit, serta layout lebar 390 px lulus. |
| Terjemahan Windows | Model resmi Argos Indonesia ↔ English diunduh dan dijalankan dengan CTranslate2. Hasil nyata mencakup “Halo, apa kabar?” → “Hello, how are you?” dan arah sebaliknya. Model lokal digunakan ulang tanpa unduhan berikutnya. |
| Pelacakan wajah Windows | OpenCV 4.14 membaca video uji dan menghasilkan posisi wajah bertiming. OpenCV 5 tidak digunakan karena API Haar yang dibutuhkan sudah dihapus. |
| Runtime EXE | EXE hasil PyInstaller dijalankan dengan profil data terisolasi; endpoint melaporkan 1.9.0, render caption/crop menghasilkan MP4, terjemahan menghasilkan “Hello world” dan VTT, serta pelacakan wajah menghasilkan keyframe. |
| Android | APK 1.9.0 (code 14), 166,4 MiB; min SDK 26, ARM64/ARMv7/x86_64. Signature v2 valid dan `zipalign -c -P 16 4` lolos. |

Script pengujian integrasi: `tools/smoke_batch_ui.py` dan `tools/smoke_creator_exe.py`. Smoke EXE memakai model terjemahan dan video wajah dari pengujian lokal sebelumnya; aset uji/model tidak dimasukkan ke Git. Checksum artefak disertakan sebagai `SHA256SUMS.txt` pada rilis GitHub.

## Batas pengujian dan kemampuan

- Tidak ada perangkat Android fisik maupun emulator yang tersambung. Instalasi, ML Kit, tracking wajah, ASR, dan render native di HP belum diuji end-to-end dalam sesi ini.
- Pengujian ini tidak memakai API key cloud pengguna; Groq/Gemini dan penyedia lain belum diuji live dalam rilis ini.
- Skor lokal memakai pola editorial Indonesia/English, bukan jaminan viral. Tracking wajah mengikuti posisi, bukan identifikasi pembicara aktif. Timing kata terjemahan diperkirakan dan dapat diedit.
- Impor Android mendukung YouTube dan URL media langsung; TikTok/Instagram memerlukan berkas lokal. Windows memakai yt-dlp dan tetap mengikuti pembatasan sumber.
- APK memakai sertifikat sideload yang sama dengan rilis sebelumnya. Distribusi Play Store dengan signing produksi bukan bagian rilis ini.
- Model ASR/terjemahan/suara/gambar diunduh terpisah; kecepatan dan kebutuhan RAM bergantung perangkat. Batas suara/gambar sebelumnya tetap dijelaskan di [model dan lisensi](MODELS.md).
