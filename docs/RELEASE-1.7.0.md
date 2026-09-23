# Validasi Studio ZAI 1.7.0

Tanggal: 23 September 2026. Rilis: Windows x64 dan satu APK universal Android. Pengujian memakai direktori `build/` terpisah dari proyek pengguna.

## Perubahan yang diperiksa

- Android: ekstraksi model, ASR, dan TTS menggunakan worker isolate top-level dengan pesan yang dapat dikirim; checksum diperiksa sebelum model dinyatakan terpasang. Kegagalan ASR/ekstraksi audio kini mengarah ke draf yang dapat diedit, dan pekerjaan tanpa klip tidak dilaporkan sukses palsu.
- Klip: pemilihan durasi adaptif mencari awal topik/ulasan produk lalu akhir pada batas ucapan. Sumber video tetap tersimpan agar rentang lain bisa diambil tanpa unduhan ulang.
- Audio: pemilihan track sumber mempertimbangkan bitrate, AAC asli disalin saat tidak ada efek, dan audio yang harus dicampur diekspor AAC 256 kbps/48 kHz.
- UI: pengaturan bahasa, track, dan audio didekatkan; editor langsung menampilkan pemutar; kontrol dan jarak layar desktop/mobile dirapikan dalam palet gelap netral.
- Gambar: SDXS-512 Q8 lokal pada Windows x64 dan APK ARM64, bobot terpisah 682.847.200 byte dengan SHA-256. Mode online tetap pilihan.
- Suara: Supertonic 3 int8 menambah sepuluh karakter ID/EN. ZipVoice tetap khusus kloning English/Mandarin.

## Bukti pengujian

| Pemeriksaan | Hasil |
| :-- | :-- |
| Python | 121 tes lulus; dua peringatan deprecation FastAPI `on_event` tanpa kegagalan. |
| Flutter | `analyze --no-pub` tanpa isu; 20 tes lulus. |
| APK | Build release berhasil: `com.zwart04.studiozai`, 1.7.0 (code 12), min SDK 26, ARM64/ARMv7/x86_64. Signature v2 valid, satu APK, alignment native 16 KB lolos `zipalign`. |
| Paket Windows | EXE 1.7.0 berjalan dari paket PyInstaller; smoke mencakup health, UI/timeline, dua draf unik, ekspor FFmpeg, penghapusan proyek, dan pembuatan gambar SDXS lokal. |
| SDXS lokal | Model 683 MB diperiksa SHA-256; gambar PNG 512×512 berhasil dibuat tanpa layanan cloud, termasuk dari EXE hasil paket. Library APK ARM64 terpaket dan selaras 16 KB. |
| Supertonic | Sepuluh sid Indonesia menghasilkan WAV nyata dan berbeda; sid 6 English juga berhasil. Empat keluaran Indonesia dan satu English ditranskripsikan balik dan isi kalimat terbaca. Arsip Android 128.774.318 byte lolos SHA-256 dan ekstraksi model. |
| UI | Screenshot desktop dan lebar 390 px diambil dari aplikasi berjalan dengan media demo. Tidak ada overflow horizontal pada pemeriksaan browser; GIF berasal dari keadaan UI tersebut. |

APK memakai sertifikat sideload yang sama dengan v1.6.0 (SHA-256 `b699b1bbabf442cc30302164aec22f5818ad613adca7ac4bb036bdac328426af`), sehingga jalur pembaruan instalasi lama terjaga. Sertifikat ini adalah kunci debug proyek, bukan signing key produksi Play Store.

## Video nyata yang diberikan pengguna

[Review speaker 80,5 menit](https://youtu.be/4WvlolSYqjU) diperiksa melalui metadata, track audio, caption Indonesia, dan sampel media 15 menit pertama. Pada transkrip tersebut, tiga hasil adaptif pertama dimulai saat pengantar produk: **1:23–4:02** (158 detik), **5:39–8:09** (149 detik), dan **10:28–13:11** (163 detik). Mode otomatis tidak memakai batas 15–60 detik tetap. Format produksi yang dipilih sumber adalah 1280×640 (720p nominal); sampel media uji sengaja diambil 640×320 agar unduhan lebih singkat.

Render QA terpisah atas ulasan produk pertama sepanjang 254,8 detik selesai dalam 15,7 detik, menghasilkan H.264 dengan AAC stereo 48 kHz sekitar 253 kbps. Rata-rata level audio sumber/hasil sekitar −23,8/−23,9 dB, puncak keduanya −0,6 dB. Setelah pembatas adaptif terakhir, pemilihan segmen diulang; render QA 254,8 detik tersebut menguji jalur ekspor/audio, bukan klaim bahwa semua segmen akhir telah diekspor.

Pada Android, parser metadata video tersebut dan transfer parsial 1 MiB video serta audio melalui downloader Dart berhasil. **Unduhan penuh, transkripsi, render, mikrofon, Supertonic native, dan SDXS native pada ponsel fisik belum diuji** karena tidak ada perangkat pada `adb devices`. Tes Flutter memeriksa jalur logika dan arsip, sementara APK release berhasil dikompilasi. Kegagalan jaringan akibat video privat, login, wilayah, atau perubahan YouTube masih mungkin terjadi. URL TikTok/Instagram langsung di Android belum didukung; impor video yang telah disimpan di perangkat. Desktop memakai situs publik yang didukung yt-dlp.

Layanan cloud berbayar belum diuji live. Kinerja model gambar 683 MB dan pemrosesan video panjang sangat bergantung pada RAM/CPU perangkat. APK ARM32 tidak menyertakan mesin gambar lokal; mode online tersedia sebagai pilihan.

Artefak rilis hanya Windows ZIP, satu APK universal, dan `SHA256SUMS.txt`. Tidak ada demo MP4 atau beberapa varian APK yang membingungkan.
