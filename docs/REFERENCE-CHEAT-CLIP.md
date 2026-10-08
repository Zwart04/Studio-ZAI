# Tinjauan Cheat Clip Pro

Referensi: https://github.com/galihjuansaputra/cheat-clip-pro. Clone pengguna dipindahkan dengan perubahan lokal tetap terjaga ke `C:\Users\Zwart\Downloads\Coding AI\cheat-clip-pro`.

| Alur referensi | Studio ZAI |
|---|---|
| Provider/key dan penemuan model | Katalog akun, saran, otomatis/manual pada Windows dan Android; tidak mengarang daftar jika provider gagal |
| Clip Studio, portrait/square, split facecam | Editor, crop/keyframe, split facecam/gameplay dan tiga rasio sudah tersedia |
| Subtitle per kata, judul, logo, musik | Editor kata, overlay judul/watermark dan track audio sudah tersedia |
| Unduh beberapa klip sebagai ZIP | ZIP MP4 pilihan pada Windows; berbagi ZIP pada Android |
| Crop mengikuti wajah | Implementasi independen: YuNet Windows, ML Kit accurate Android; jangkar X/Y dan crop ditahan saat kehilangan wajah |
| YouTube/upload | Sumber tersimpan dan impor file tersedia |
| Google Drive, cookies UI, target 15/30/60, heatmap most replayed, pilihan GPU AMD/Intel | Belum semuanya tersedia sebagai alur tersendiri; perlu pengembangan lanjutan |

Most replayed/heatmap publik YouTube bukan analitik retention privat dan tidak tersedia pada semua video. Pelacakan wajah bukan identifikasi pembicara aktif; tinjau video dengan beberapa wajah atau pergantian adegan.

Tidak menyalin source Cheat Clip ke Studio ZAI. README upstream menyatakan MIT tetapi clone yang diperiksa tidak menyertakan LICENSE; lisensi Studio ZAI tidak diterapkan ke clone. Perbaikan clone tetap lokal, tidak dikirim ke remote galihjuansaputra.

## Clone lokal

Virtualenv diperbaiki setelah pemindahan, termasuk jalur aktivasi dan launcher pip. Import FastAPI/PyTorch/OpenCV/Google GenAI berhasil. `concurrently` diperbarui ke 10.0.5 dan override `shell-quote` ke ^1.12.0. Build Vite berhasil; audit npm melaporkan 0 kerentanan pada pemeriksaan sesi ini. Virtualenv/node_modules tetap disimpan supaya clone dapat dijalankan.
