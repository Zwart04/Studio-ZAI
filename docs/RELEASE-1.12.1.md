# Studio ZAI 1.12.1

Perbaikan Windows untuk laporan preview dan kartu klip, 12 Oktober 2026.

- Kartu klip, galeri dan proyek mengikuti portrait 9:16, square 1:1 atau landscape 16:9. Galeri memakai rasio output yang sedang ditampilkan.
- Badge skor 0–100 tampil di kanan atas. Warna membedakan skor rendah, sedang dan tinggi. Skor menunjukkan kekuatan rekomendasi dari analisis; belum dikalibrasi terhadap jumlah penonton atau peluang viral.
- Thumbnail sumber YouTube tersedia sebelum render, termasuk untuk proyek lama. Ini gambar sumber, bukan frame setiap klip. Setelah render, thumbnail hasil klip digunakan. Full Offline tidak menampilkan URL thumbnail sumber.
- Jika unduhan audio CDN gagal, aplikasi mencoba downloader native yt-dlp dengan metadata/link baru, header extractor, cookie yang dipilih dan pilihan bahasa yang sama. Jalur cadangan tetap audio-only.
- Error jaringan mempertahankan kode HTTP tanpa menampilkan signed URL. Kandidat heuristik diberi badge; mode Online AI memberi petunjuk pengaturan provider, bukan menyarankan model lokal.

Klip, trim, caption dan setting pengguna tidak diubah. Klip panjang pada laporan berasal dari mode Otomatis berbasis topik; pilih preset durasi bila ingin klip pendek.

## Pengujian

257 tes Python lolos, Ruff bersih dan versi konsisten. Browser Edge dengan API terisolasi memeriksa tiga rasio kartu, badge skor, thumbnail publik nyata, overflow 360–1440, editor, seek dan subtitle. Tidak ada page error atau encode otomatis ketika caption diedit.

Sumber publik yang dilaporkan pengguna (`oPZY7nKtUTc`) diuji langsung: unduhan audio standar dan native berhasil sekitar 30 MB. Segmen video untuk rentang 20–32 detik berhasil diunduh dan dimux dengan audio; FFprobe mencatat video 1280×640, audio tersedia dan berkas sekitar 30 detik karena padding segmen. Ini tidak membuktikan semua jaringan, video atau kondisi cookies akan berhasil.

EXE final diuji dengan LOCALAPPDATA terisolasi: versi, metadata rasio/thumbnail, UI sesuai sumber, source preview, render dan ekspor. Paket dan history sumber dipindai sebelum upload. Laporan 1.12 masih berlaku untuk ASR, LLM dan subtitle lainnya: [1.12.0](RELEASE-1.12.0.md).

Perubahan ini pada desktop/web Windows. APK Android dibangun ulang sebagai 1.12.1/build 18; fitur native tetap mengikuti baseline 1.12. Tidak ada pengujian HP fisik atau provider berbayar pada patch ini. Lisensi noncommercial Studio ZAI dan lisensi dependensi tetap berlaku.
