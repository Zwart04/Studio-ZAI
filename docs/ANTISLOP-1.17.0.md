# Pemeriksaan desain 1.17.0

Mode during meneruskan pilihan sesi. Arah berasal dari docs/DESIGN.md: editor video gelap, fokus pada konten, warna biru untuk tindakan dan fokus. ENERGY 1 / RHYTHM 2 / MOTION 1 untuk antarmuka. Animasi subtitle merupakan konten yang dipilih pengguna, bukan dekorasi antarmuka.

## Keputusan

- Preview mendapat ruang terbesar karena tugas utama editor adalah menilai video.
- Kontrol dan keterangan timing diletakkan di luar frame supaya pengguna melihat isi video tanpa label aplikasi di dalam gambar.
- Panel kanan memisahkan klip, subtitle, dan elemen agar jenis pengaturan dapat ditemukan berdasarkan pekerjaan.
- Layar sempit menumpuk preview dan inspector dalam area yang dapat digulir; layar menengah memakai inspector 320 piksel; layar besar 380 piksel.
- Hitam mengurangi gangguan saat menilai warna video; abu-abu membedakan panel; biru menandai fokus dan tindakan yang tersedia.
- Font sistem mempertahankan keterbacaan dan tidak menambah unduhan. Font subtitle tetap merupakan pilihan konten.
- Radius 8 sampai 12 piksel membedakan kontrol dari panel. Garis pemisah dan jarak antarkelompok menggantikan kartu bertumpuk.
- Tidak ada aset merek atau ilustrasi baru. Logo provider yang sudah tersedia tetap dipakai untuk identifikasi provider.

## Delivery gate

- PASS R-02, R-15, R-16: teks baru menyebut tindakan nyata: Edit subtitle, Layar penuh, Kembali ke editor, Putar animasi pada klip. Salinan baru tidak memakai em dash atau klaim promosi.
- PASS R-03, R-35: tools/verify_hybrid_ui.js memeriksa overflow pada delapan lebar beranda dan lima lebar editor; batas setiap kata subtitle diukur pada tiga lebar, dalam mode biasa dan penuh.
- PASS R-17, R-18, R-23, R-36, R-38: tidak menambah statistik/testimoni/aset orang; video tes sintetis ditandai fixture; skor klip dan daftar model tetap berasal dari data aplikasi.
- PASS R-24, R-26: tujuh tujuan navigasi dibuka; provider/model/prioritas, animasi, font, teks, crop, media, play/pause, scrub, layar penuh, kembali, dan Simpan diuji melalui browser. Animasi tersimpan diverifikasi lewat API.
- PASS R-25: teks sekunder #b0b0b5 pada #1c1c1e = 7.88:1; fokus #61afff = 7.36:1; batas input #747478 = 3.66:1 untuk komponen nonteks. Rasio dihitung dengan contrast-check.py dari antislop-human.
- PASS R-27, R-28: pesan persiapan, error preview, dan subtitle kosong tetap tersedia; tidak menambah FAQ.
- PASS R-32: fokus terlihat, dialog membatasi Tab pada kontrol aktif; Escape keluar dari preview penuh sebelum menutup editor. Tombol Edit subtitle memindahkan fokus ke pemilih animasi.
- PASS R-33, R-34: perubahan ditulis langsung dalam sumber; aplikasi memakai tema gelap tunggal yang diuji.
- PASS R-37: arah desain dan dials dinyatakan sebelum penyerahan, dengan alasan keputusan di atas.
- PASS Purpose gate R-01, R-04, R-06 sampai R-14, R-19, R-22: tidak menambah gradien, glow, ilustrasi, atau ikon dekoratif. Bayangan frame hanya membedakan batas gambar. Animasi konten dipicu pilihan/pemutaran pengguna.
- PASS Liveliness: video menjadi fokus; kelompok pengaturan memiliki jarak dan susunan berdasarkan fungsi; pola frame, scrub, dan timeline mengidentifikasi aplikasi sebagai editor klip.
- PASS C-1 sampai C-5, R-05, R-11, R-20, R-21, R-29 sampai R-31: komposisi mengikuti pekerjaan mengedit video; alasan warna, tipografi, jarak, dan panel tertulis; tidak mengarang data atau mengganti identitas produk.
- PASS antislop-code: komentar baru menjelaskan kontrak timeline dan alasan tata letak; banner komentar pembuka editor diganti satu baris. Perubahan logika dilakukan sesuai permintaan pengguna, bukan sebagai pembersihan komentar.

Bukti browser tersimpan lokal di build/hybrid-browser/results.json beserta editor.png dan full-preview.png. Pemeriksaan ini tidak menjamin semua kombinasi font, isi video, model berbayar, atau perangkat fisik bebas masalah.
