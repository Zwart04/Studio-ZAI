# Alur beranda Studio ZAI

Dicek dari kode pada 14 Oktober 2026. Pada 1.16.0, pilihan Transkrip saja dihapus dari beranda Windows dan diganti alur klip. Lihat [perubahan beranda/editor 1.16.0](RELEASE-1.16.0.md); penjelasan API transkrip di bawah tetap berlaku untuk API lama.

## Dari sumber sampai klip

1. Pilih berkas lokal atau masukkan link. Untuk link, yt-dlp membaca judul, durasi, pilihan kualitas, track audio, gambar sampul, dan heatmap jika sumber menyediakannya. Berkas lokal diperiksa dengan FFprobe.
2. Aplikasi mencoba caption sumber terlebih dahulu: yt-dlp, kemudian youtube-transcript-api. Caption berisi teks dan timestamp. Berkas subtitle lokal juga dapat digunakan. Jika tidak tersedia, audio ditranskrip memakai faster-whisper di perangkat.
3. Pilih **Hanya transkrip** untuk menghasilkan teks/SRT, atau **Cari momen** untuk menghasilkan kandidat klip. Keduanya tidak membutuhkan Supadata: integrasi Supadata tidak ada pada versi ini.
4. Pemilih momen lokal memakai model yang dipilih pada runtime/GGUF, jika tersedia. Tanpa LLM, algoritme menilai ciri teks, batas kalimat, suara, dan heatmap yang tersedia. Model online menerima transkrip untuk menyarankan momen dan timestamp; alur ini tidak mengirim video penuh kepada model pemilih momen.
5. Tinjau judul, timestamp, skor, subtitle, dan framing. Render mengunduh bagian video yang diperlukan pada proyek online, kemudian FFmpeg membuat hasil klip di komputer.

## Kontrol yang terlihat di beranda

| Kelompok | Fungsi dan mesin yang digunakan |
|---|---|
| Sumber dan kualitas | Berkas atau link; kualitas mengikuti pilihan sumber. Gambar di pratinjau link adalah sampul sumber, bukan frame klip. |
| Cari momen / Hanya transkrip | Memilih hasil: kandidat klip, atau teks/SRT saja. |
| Lokal / AI online | Memilih tempat analisis momen. Lokal memakai runtime/model lokal; online memakai provider dan API key pilihan pengguna. |
| GGUF | Format berkas model LLM, bukan nama model. Muat menjalankan model; Lepaskan dari RAM menghentikan model, tidak menghapus berkasnya dari penyimpanan. |
| Deteksi model | Meminta daftar model yang bisa diakses akun/runtime. Tidak berarti semua model gratis atau sudah diunduh. |
| Rekomendasi / Termurah / Paling pintar | Memilih dari model hasil deteksi. Termurah memakai subset harga tercatat dengan asumsi token; paling pintar memakai urutan keluarga model, bukan benchmark. |
| Jenis konten | Otomatis/ulasan atau podcast. Mode podcast menyesuaikan pemilihan batas percakapan/cerita. |
| Jumlah dan durasi | Jumlah otomatis menargetkan 3–10 momen; hasil dapat lebih sedikit. Preset 15/30/60 detik memakai rentang 10–20/20–40/45–75 detik, supaya kalimat tidak selalu terpotong tepat pada angka preset. |
| Kanvas dan framing | Rasio 9:16, 1:1, 4:3, 16:9, letterbox, atau ukuran sumber sesuai pilihan; crop memenuhi kanvas, fit mempertahankan gambar dalam kanvas. Bukan peningkatan kualitas sumber. |
| Kecepatan transkrip | Cepat = Whisper tiny INT8; Seimbang = base INT8; Akurat = small INT8, melalui faster-whisper lokal. Model lebih besar memerlukan lebih banyak RAM/waktu; akurasi tetap bergantung suara. |
| Bahasa dan audio | Bahasa membantu transkripsi, bukan menerjemahkan suara. Track audio memilih bahasa/suara sumber yang tersedia; hasil tetap memakai suara asli. |
| Subtitle | Posisi bawah/tengah/atas/nonaktif, warna dan animasi kata. Timing kata mengikuti transkrip; jika hanya timing kalimat tersedia, timing kata diperkirakan. Preview browser; ekspor FFmpeg/libass. |
| Tinjau sebelum render | Membuat kandidat terlebih dahulu agar pengguna bisa mengoreksi. Jika dimatikan, proses melanjutkan render sesuai pengaturan. |
| Cek perangkat | Memeriksa perangkat, RAM, model, FFmpeg, dan dependensi. Bukan jaminan semua video dapat diproses. |
| Proyek terakhir | Membuka pekerjaan tersimpan. Skor adalah rekomendasi relatif, bukan persentase kemungkinan viral. |

Deteksi/framing wajah pada mesin Windows menggunakan OpenCV YuNet dengan Haar sebagai cadangan. Ini terpisah dari LLM pemilih momen; jangan menganggap model teks otomatis melihat atau mengenali pembicara dalam video.

## Cookie, API, metadata, dan data yang keluar

- **Metadata** adalah informasi tentang video. Judul, durasi, dan heatmap membantu proses; metadata saja tidak cukup untuk memahami seluruh isi percakapan.
- **Cookie** opsional untuk permintaan sumber melalui downloader ketika situs membutuhkan sesi login. Cookie tidak menjamin lolos blokir/izin video dan tidak dipakai sebagai API key model. Perlakukan cookie seperti akses akun; jangan unggah ke GitHub atau kirim kepada orang lain.
- **API key** dipakai untuk provider online pilihan pengguna. Transkrip dikirim ke provider saat analisis online; mode ini tetap memiliki biaya/kuota sesuai akun. Badge gratis tidak berarti tanpa batas. Pengaturan mengembalikan nilai key yang disamarkan ke UI.
- **Lokal tidak selalu berarti tanpa internet**: mengambil link atau mengunduh model masih memerlukan jaringan. Full Offline memerlukan sumber dan model sudah tersedia di perangkat.
- **Supadata tidak digunakan**; tidak ada kuota Supadata yang terpakai.
- **Cache** menghindari pengambilan ulang. Metadata sumber disimpan sementara selama 30 menit, caption platform diperiksa dengan batas usia cache 24 jam. Cache/model/media tetap memakai penyimpanan lokal.

## Thumbnail klip

Kartu klip draft dan galeri mengambil frame pada waktu mulai klip, bukan memakai sampul YouTube yang sama untuk semua klip. Sumber lokal/segmen tersimpan dipakai terlebih dahulu. Jika perlu, proyek online mengambil rentang video singkat dengan kualitas maksimum 360p; segmen HLS dapat lebih panjang dari satu detik. Maksimum dua permintaan frame diproses bersamaan dan JPG disimpan sebagai cache. Perubahan awal klip menghasilkan cache berbeda.

Jika jaringan atau format HLS tidak tersedia, kartu menampilkan pemberitahuan frame belum tersedia. Klip yang sudah dirender memakai thumbnail hasil render. Thumbnail draft memperlihatkan frame sumber; crop, subtitle, dan efek final dinilai melalui preview/render editor.
