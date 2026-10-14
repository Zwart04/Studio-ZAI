# Studio ZAI 1.14.0

## Subtitle bergerak

- Enam pilihan cepat: Sorot + Pop, Lentur, Karaoke, Muncul per kata, Satu kata, dan Tanpa gerak.
- Windows: pilih animasi di beranda sebelum mencari momen. Tombol Putar contoh memperlihatkan efek tanpa suara dan tanpa render. Di editor, buka Gaya subtitle, pilih animasi dan warna aktif, lalu Terapkan ke semua subtitle. Simpan perubahan sebelum menutup editor.
- Android: pilihan cepat tersedia di editor caption. Simpan caption setelah memilih gaya. Beranda Android tidak memiliki pemilih animasi baru pada versi ini.
- Teks, posisi, font khusus per kata, dan timestamp dipertahankan saat menerapkan gaya. Animasi per kata sebelumnya diganti dengan pilihan baru.
- Efek pop dan lentur pada preview disesuaikan dengan kurva ekspor. Pada highlight, hanya kata aktif yang mendapat animasi.
- Timing mengikuti timestamp kata dari transkrip. Jika hanya tersedia teks per kalimat, timing kata diperkirakan; hasilnya bisa dikoreksi di editor. Muncul per kata menampilkan kata utuh, bukan morphing huruf atau perubahan bentuk font.

## Beranda Windows

Model dan hasil klip berdampingan di desktop, lalu menjadi satu kolom pada layar kecil. Kontrol GGUF dan RAM diletakkan dalam bagian yang dapat dibuka. Pemilih kanvas tetap menampilkan bentuk rasio. Contoh animasi diputar atas permintaan pengguna.

## Validasi

- 274 tes Python lulus; enam preset mempertahankan teks/timestamp dan menghasilkan tag ekspor yang sesuai.
- 52 tes Flutter lulus. Dart analyzer tidak menemukan masalah.
- Browser Edge: enam pilihan animasi, contoh putar/jeda, perubahan subtitle di editor, seek, rasio preview, transkrip/SRT, provider, dan keyboard. Tidak ada page error; tidak ada overflow beranda pada 320–1440 piksel. Edit biasa tidak memicu encode otomatis.
- EXE 1.14.0 diuji sebelum dan setelah dipasang ke `dist/StudioZAI`: seluruh UI cocok dengan sumber, transkrip/SRT, pembuatan momen dengan animasi lentur, preview, dan ekspor 1440×1080 lulus.
- Keenam efek dirender melalui FFmpeg/libass dan frame hasil video dibaca kembali. Efek pop/lentur menghasilkan perubahan antarframe; pergantian kata dan warna terlihat pada hasil render sintetis.

Pengujian memakai data sintetis dan proyek terisolasi. Akurasi timing podcast nyata bergantung pada hasil transkripsi. Belum diuji pada perangkat Android fisik atau provider berbayar. Hasil tes tidak menjamin semua video dan perangkat bebas bug.
