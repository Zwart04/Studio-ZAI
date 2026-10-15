# Studio ZAI 1.16.0

## Beranda Windows

- Pilihan Transkrip saja dihapus dari beranda. Transkrip tetap dibuat untuk memilih momen dan subtitle; API lama tetap kompatibel.
- Semua klip tampil di beranda, masing-masing dengan frame, skor, rentang waktu, transkrip, dan tombol edit. Teks panjang dapat digulir dalam kartu.
- Provider, model online, dan prioritas menggunakan dropdown. Logo provider terpilih, panduan API, dan penanda kuota tetap terlihat. Model terdeteksi dikelompokkan menjadi Pilihan utama dan Model lain di akun.
- Preview edit 360p/24 fps disiapkan di latar belakang satu klip per tahap. Sumber online diunduh saat diperlukan. Tombol hentikan menghentikan antrean; preview selesai tetap tersimpan. Muat ulang dapat mencoba lagi.
- Preview adalah salinan ringan untuk mengedit, bukan ekspor final. Ekspor tetap membaca media sumber. Perubahan trim membatalkan cache yang tidak sesuai; perubahan teks/gaya tidak mengunduh atau mengodekan ulang media dasar.

## Editor Windows

- Embed YouTube diganti pemutar media lokal. Unduhan awal masih memerlukan waktu; setelah preview siap, membuka editor memakai media tersimpan.
- Mengubah kanvas, teks, template, font, atau menambah gambar mempertahankan elemen video yang sama. Teks, gambar, video tambahan, dan audio timeline ditampilkan/disinkronkan langsung.
- Crop manual, keyframe, split, dan latar blur ditampilkan melalui canvas dengan satu decoder sumber. Preview dibatasi sekitar 24 fps untuk mengurangi pekerjaan browser.
- Transkrip dapat diedit per baris. Klik waktu untuk mencari ucapan. Mengubah teks menghapus timing kata lama pada baris tersebut dan menandai timing pengganti sebagai perkiraan.
- Panel kanan dikelompokkan menjadi Klip, Subtitle, dan Elemen; kontrol font/ukuran, galeri gaya, dan transkrip memiliki bagian tersendiri.
- 30 template teks dengan lima keluarga font yang tersedia, serta 12 pilihan animasi subtitle. Enam pilihan animasi sederhana juga tersedia untuk teks overlay. Pemilihan gaya sekarang benar-benar memengaruhi preview dan ekspor.

## Perangkat dengan RAM terbatas

- Pilihan Hemat RAM memilih Whisper tiny dan analisis tanpa LLM. Pengguna dapat memilih GGUF terkecil yang sudah ada; model hingga 1.200 MB diberi label Ringan. Ukuran berkas tidak sama dengan total pemakaian RAM.
- Thread CPU dibatasi: mode hemat menggunakan satu thread pada CPU hingga empat inti, dua thread pada CPU lebih besar. Pengaturan digunakan untuk FFmpeg, faster-whisper, runtime GGUF, dan permintaan Ollama yang dikelola aplikasi.
- Pekerjaan FFmpeg dan inferensi tetap berbagi pembatas pekerjaan berat. Tidak menjalankan banyak render sekaligus hanya untuk mempercepat angka progres.
- Jalur encoder GPU NVIDIA yang sudah tersedia tetap dipilih setelah pemeriksaan; CPU menjadi cadangan. Rilis ini tidak menambahkan akselerasi Intel/AMD atau membuktikan dukungan setiap GPU.

## Android

Android mendapat 30 template dan 12 preset animasi bersama. Perombakan beranda, antrean proxy, dan editor browser di atas berlaku untuk Windows; antarmuka native Android tidak disamakan dalam rilis ini.

## Validasi dan batas

- Tes Python mencakup cache proxy, perubahan trim, audio/dimensi proxy, batas thread, dan gaya overlay dalam ASS.
- 288 tes Python dan 60 tes Flutter lulus. Analisis Dart untuk dua berkas layanan yang berubah tidak menemukan masalah; pemeriksaan penuh juga dijalankan oleh CI.
- EXE 1.16.0 diuji dengan data terisolasi: berkas UI cocok dengan sumber, 30 template termuat, proxy edit dibuat dan dapat dibaca, transkrip/SRT, momen, preview, serta ekspor 1440×1080 berhasil.
- Browser Edge diperiksa pada 320–1440 piksel. Kartu klip, template/font, edit transkrip, penambahan teks/gambar, crop, dan kanvas diuji. Pemutar dipastikan tidak diganti untuk perubahan biasa; tidak ada permintaan encode draf otomatis saat mengedit.
- Semua 12 animasi dirender melalui FFmpeg/libass dan frame hasilnya dibaca kembali.
- Pengujian memakai video sintetis. Belum diuji pada setiap laptop lama, GPU, koneksi internet, provider berbayar, atau perangkat Android fisik. Preview browser dan hasil libass dapat memiliki sedikit perbedaan ukuran/antialiasing font.

Unduhan awal tidak bisa dihilangkan. Video tanpa format sumber yang didukung dapat gagal disiapkan; gunakan berkas lokal sebagai alternatif. Cache preview menambah pemakaian penyimpanan. Proyek, API key, cookie, dan model pengguna tidak dihapus oleh pembaruan ini.
