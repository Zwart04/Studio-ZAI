# Galeri klip dan ekspor beberapa format

Pembaruan Windows dan Android versi 1.9, September 2026. Alur ini mengikuti kebutuhan clipper pada [SocialVisuals](https://socialvisuals.pro/): cari hasil lama, pilih klip, lalu buat keluaran untuk beberapa platform. Lihat [panduan Creator](CREATOR.md) untuk fitur podcast, caption, crop, dan terjemahan.

## Cara memakai

1. Buat klip dari Beranda, lalu buka proyeknya.
2. Pada kartu klip, centang klip yang ingin diekspor.
3. Di **Ekspor banyak klip**, pilih **9:16**, **1:1**, dan/atau **16:9**. Ringkasan menunjukkan jumlah file yang akan dibuat.
4. Klik **Render pilihan**. Progres mengikuti setiap file. Pada desktop, tombol **Batal** menghentikan encoder dan sisa batch; file yang sudah selesai tetap tersedia.
5. Gunakan tautan **Unduh** di kartu klip atau buka **Galeri klip** untuk memutar hasil, mencari judul klip/proyek, menyaring hasil yang sudah dirender, dan mengurutkan skor momen.

**Edit** di galeri membuka editor klip yang sama. Proyek, sumber video, subtitle, dan timeline yang sudah tersimpan digunakan kembali.

## Perilaku hasil

- Setiap kombinasi klip dan rasio menghasilkan MP4 terpisah. Audio asli/narasi, caption, framing, dan overlay mengikuti jalur render editor yang sudah ada.
- Pengaturan kanvas editor dan render utama tidak diubah oleh batch. Ukuran portrait mengikuti kebijakan sumber aplikasi: 1080×1920 untuk sumber minimal 720p, lebih kecil untuk sumber beresolusi rendah. Square 1080×1080 dan landscape 1920×1080.
- Penggantian rasio menyesuaikan kanvas, bukan membuat komposisi manual baru. Periksa crop dan letak teks pada hasil tiap rasio sebelum publikasi.
- Perubahan pengaturan klip melalui editor menghapus referensi hasil lama agar tidak ditawarkan sebagai ekspor terbaru. Mengganti judul atau menyimpan nilai yang sama tetap mempertahankan hasil.
- Pada desktop, jika klip diubah saat batch menunggu atau berjalan, batch berhenti dengan pesan untuk mengulang ekspor. Perubahan judul tidak ditimpa oleh penyimpanan hasil render.
- File disimpan dalam folder proyek lokal. Render ulang memakai folder hasil baru; hasil sebelumnya tetap di disk sampai proyek dihapus.
- Skor momen berasal dari proses pemilihan klip yang sudah ada, bukan jaminan jumlah penonton atau viralitas.

## Verifikasi

Jalankan tes dengan folder sementara baru jika direktori pytest lama memiliki masalah izin Windows:

```powershell
$batchTestDir = Join-Path (Get-Location) ('build\batch-tests-' + [guid]::NewGuid().ToString('N'))
.\.venv-build\Scripts\python.exe -m pytest core/tests/test_batch_render.py core/tests/test_canvas.py core/tests/test_projects.py core/tests/test_timeline_render.py core/tests/test_studio_upgrade.py -q --basetemp="$batchTestDir" -p no:cacheprovider
.\.venv-build\Scripts\python.exe tools/smoke_batch_ui.py
```

Smoke test memakai proyek dan video sintetis terpisah di `build/batch-smoke-*`. Pengujian mencakup dua klip dengan dan tanpa timeline, enam hasil render, dimensi dan audio via FFprobe, pilihan klip/format, pencarian dan urutan galeri, pemutaran, unduhan, akses editor, bahasa Inggris, serta lebar layar 390 px. Model AI dan proyek pengguna tidak dipakai dalam smoke test ini.
