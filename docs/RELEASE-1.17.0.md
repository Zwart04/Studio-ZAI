# Studio ZAI 1.17.0

## Editor dan preview Windows

- Workspace memenuhi jendela. Preview menjadi area utama, kontrol pemutar berada di luar frame, panel Klip / Subtitle / Elemen di kanan, dan timeline di bawah.
- Tombol Layar penuh memperbesar preview ke seluruh area aplikasi, termasuk subtitle dan elemen tambahan. Tombol Kembali ke editor atau Escape mengembalikan panel tanpa memuat ulang video.
- Tombol Edit subtitle membuka pengaturan animasi. Mengganti animasi atau warna aktif langsung berlaku; tombol Putar animasi pada klip memutar ucapan yang sedang dipilih. Simpan menyimpan perubahan ke proyek.
- Kata subtitle dapat pindah baris. Ukuran teks mengikuti skala video, tanpa batas minimum piksel yang membuat preview kecil meluber. Kata panjang dapat terpecah dalam ruang yang tersedia.
- Kalimat panjang ditampilkan dalam bagian maksimal enam kata / 38 karakter, mengikuti waktu ucapan. Mode sorot tetap memakai bagian pendek tiga kata. Preview dan ASS menggunakan batas bagian yang sama.
- Pop hasil ekspor hanya membesarkan kata aktif. Efek naik bekerja pada satu baris, fade masuk secara bertahap, dan pilihan Tanpa gerak menghentikan karaoke bawaan preset.
- Keterangan waktu kata perkiraan berada di luar gambar. Posisi subtitle standar pada ekspor diselaraskan dengan preview.
- Pengaturan beranda dipisahkan dengan ruang dan judul sesuai fungsi. Dropdown provider/model tetap tersedia. Struktur navigasi, beranda, galeri, dan panel menggunakan palet proyek yang sama.

## Cakupan Android

APK mengikuti versi 1.17.0, dengan label gerak naik dan transisi fade yang diperbarui. Perombakan workspace dan preview layar penuh dalam rilis ini berlaku pada editor Windows/web. Tidak ada klaim pengujian perangkat Android fisik.

## Berkas yang disertakan

Paket Windows memuat teks lisensi SIL Open Font License 1.1 untuk keempat font subtitle yang dibundel (Anton, Barlow Condensed, DM Serif Display, Kalam) beserta catatan asalnya, berdampingan dengan lisensi llama.cpp, stable-diffusion.cpp, QuickJS, LLVM, dan YuNet yang sudah ada. Berkas ini sebelumnya tidak ikut terbundel.

## Pemeriksaan

- Browser Edge: beranda pada 320 sampai 1440 piksel; subtitle panjang pada 360, 768, dan 1440 piksel, termasuk preview penuh; video yang sama dipertahankan saat mengubah teks, animasi, kanvas, dan media.
- Animasi diganti langsung dari editor, disimpan, dan dibaca kembali lewat API. Putar/jeda, scrub, Escape, fokus keyboard, serta tujuh tujuan navigasi diperiksa.
- Semua 12 pilihan animasi dirender menggunakan FFmpeg/libass dan frame dibaca kembali.
- Tes otomatis mencakup pembagian kalimat, kata aktif, posisi animasi atas, cache preview, dan ekspor. 291 tes Python dan 60 tes Flutter lulus; Ruff pada `core` bersih, `dart analyze --fatal-infos` tanpa temuan, dan sembilan berkas JS UI lolos parser.
- EXE 1.17.0 diuji dengan data terisolasi dua kali, yaitu hasil build langsung dan folder `dist/StudioZAI` yang dikemas ulang: berkas UI cocok dengan sumber, 30 template termuat, proxy edit dibuat, transkrip/SRT, momen, preview, dan ekspor 1440×1080 berhasil.
- Audit privasi kedua arsip rilis menemukan 0 temuan pada 361 berkas ter-track dan 1052 blob riwayat.
- Pemeriksaan visual menggunakan video sintetis berlabel fixture. Perbedaan antialiasing font antara browser dan libass masih mungkin terlihat. Unduhan pertama tetap perlu selesai sebelum video lokal dapat diputar.

Laporan penerapan keenam skill: [pemeriksaan antislop](https://github.com/Zwart04/Studio-ZAI/blob/v1.17.0/docs/ANTISLOP-1.17.0.md).
