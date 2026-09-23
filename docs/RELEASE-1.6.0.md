# Validasi Studio ZAI 1.6.0

Tanggal: 23 September 2026. Paket: Windows x64 + satu APK universal Android. Data pengujian berada di build/, terpisah dari proyek pengguna.

## Perubahan utama

- Android: transfer YouTube range 1 MiB, timeout dan retry terbatas, refresh URL stream tetap menggunakan track yang dipilih. Profil klien yang berhasil pada pengujian menggantikan jalur yang mengembalikan 403 / page needs to be reloaded.
- Video panjang: SSE mengirim event terbaru meskipun histori dibatasi; heartbeat dan laporan detik/chunk membuat tahap transkripsi terlihat bergerak. Chunk desktop 90 detik.
- Editor langsung menampilkan pemutar. Tombol Pratinjau cepat dihapus; perubahan otomatis menyiapkan draf di belakang layar. File draf unik tidak menimpa file yang sedang diputar, hasil permintaan lama tidak menggantikan edit yang lebih baru, dan draf lama dibatasi.
- Trim/split, kanvas per bagian, sumber tersimpan untuk potongan baru, custom typography, posisi/off subtitle, serta pemutar tanpa caption ganda.
- Suara lokal tambahan, ZipVoice beserta vocoder di Windows/Android, mikrofon untuk referensi, dan koneksi AI teks/gambar/suara opsional.
- Logo berkontras, README baru, screenshot aktual dan GIF tur UI. Rilis hanya memuat Windows ZIP, APK universal, dan checksum.

## Bukti pengujian

| Pemeriksaan | Hasil |
|---|---|
| Python engine | 108 tes lulus; 2 peringatan deprecation FastAPI on_event. |
| Flutter | analyze tanpa issue; 13 tes lulus; build APK release berhasil. |
| APK | applicationId com.zwart04.studiozai, versionName 1.6.0, versionCode 11, minimum SDK 26, ARM64/ARMv7/x86_64. |
| Signing APK | SHA-256 sertifikat b699b1bbabf442cc30302164aec22f5818ad613adca7ac4bb036bdac328426af, sama dengan paket sebelumnya. |
| EXE hasil build | Health 1.6.0, runtime Piper dan ZipVoice tersedia, API AI terdaftar; ingest sumber, dua pratinjau unik, ekspor FFmpeg, penghapusan proyek berhasil. |
| Editor web | Video siap putar dengan kontrol; tidak ada tombol Pratinjau cepat; kanvas berubah otomatis 960×960 lalu kembali 960×540; track caption HTML tambahan = 0. Menutup editor menjeda video dan melepas src. |
| Responsif | Desktop 1280×800 dan layar kecil 390×844; lebar konten tidak melebihi viewport. Pemutar dan tombol editor tersedia pada layar kecil. |
| Tipografi | Preset custom disimpan dan digunakan dalam render; split menjaga gaya dan menyesuaikan waktu caption. |
| Proyek | Rentang baru memakai sumber tersimpan. Tes duplikat memastikan sumber/hasil salinan tetap ada setelah proyek asli dihapus. |
| Audio panjang Android | Fixture WAV 65 menit dibaca dalam chunk memori terbatas; audio terpotong ditolak. |
| ZipVoice CPU | Sintesis dari contoh suara Piper milik pengujian menghasilkan WAV 2,36 detik. |
| AI online | Tes protokol provider dengan server fixture dan validasi PNG/WAV, redirect, error, serta penyimpanan kredensial. |

## Video nyata yang diminta

Sumber: https://youtu.be/kIB-ypmiIzo. Downloader Dart yang digunakan Android dijalankan pada Windows untuk transfer nyata, termasuk bagian setelah batas 4 MiB yang sebelumnya gagal. Video dan audio selesai diunduh dan dimux:

- Durasi FFprobe: 4.685,447 detik (78 menit 5 detik).
- H.264 854×480 + AAC dengan tag bahasa ind.
- Ukuran hasil: 456.164.891 byte.
- Audio 200 detik mulai detik 3.650 diuji dengan Whisper Tiny ID: 79 segmen, 87 pembaruan progres, melewati tiga chunk dan menghasilkan segmen setelah detik 180.

Pengujian lengkap transkripsi 1.874 segmen dan ekspor awal/setelah menit 60/akhir dari sumber ini juga dicatat pada [validasi 1.5.1](RELEASE-1.5.1.md). Hasil lama tersebut adalah regresi historis, bukan klaim bahwa seluruh transkripsi 78 menit diulang pada build 1.6.0.

## Batas pengujian

Tidak ada HP fisik terhubung: perbaikan Android sudah dibangun dan diuji pada Dart/Flutter, tetapi pemrosesan end-to-end, izin mikrofon, batas memori, serta perilaku background Vivo Android 16 belum diverifikasi di perangkat itu. Aplikasi mempertahankan layar aktif selama pekerjaan; tetap buka aplikasi selama proses panjang.

Video pada screenshot error terpisah (ID y9QtM6qnG50) juga tidak tersedia dari pengujian desktop; tidak ada klaim bahwa video terbatas/dihapus bisa dipaksa tersedia. Akses YouTube dapat berubah.

Cloud berbayar dan server difusi nyata tidak diuji live karena tidak ada kredensial/server yang dikonfigurasi. Gambar lokal adalah koneksi server terpisah, bukan model native universal pada HP. Kloning Indonesia belum tersedia di paket standar.
