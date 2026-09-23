# Validasi Studio ZAI 1.8.0

Tanggal: 23 September 2026. Artefak: satu ZIP Windows x64, satu APK universal Android, dan `SHA256SUMS.txt`. Semua data uji baru berada di `build/`, terpisah dari proyek pengguna.

## Perubahan utama

- Editor desktop memakai pemutar langsung, panel pengaturan samping, dan timeline bawah dengan penggaris waktu, playhead, seret blok/tepi, dan drop berkas. Dialog tipografi serta tombol Batal/Hapus mengikuti desain aplikasi.
- Subtitle awal berasal dari ASR lokal, bukan caption link. Tombol subtitle editor menyimpan tanpa menutup editor; jika proyek belum punya transkrip, ASR hanya membaca rentang klip sehingga video panjang tidak perlu ditranskripsi ulang untuk satu edit.
- APK memisahkan teks TTS dan kloning, mengimpor berkas contoh dari penyedia dokumen Android sebagai stream lalu menormalkan 30 detik pertama. Editor memberi status ASR dan mempertahankan caption lama saat tidak ada ucapan.
- Katalog model suara menampilkan izin komersial dan sumber lisensinya. Supertonic 3 disarankan untuk TTS Indonesia/English, Piper LJSpeech untuk English. Pilihan lama yang nonkomersial atau hak datanya belum jelas tidak disarankan. ZipVoice tetap untuk kloning English/Mandarin; Chatterbox Indonesia adalah opsi desktop source yang berat.

## Bukti pengujian

| Pemeriksaan | Hasil |
|---|---|
| Core Python | 128 tes lulus; Ruff dan pemeriksaan sintaks JavaScript bersih. |
| Flutter | `analyze --no-pub` tanpa isu; 24 tes lulus. |
| Android | APK release 1.8.0 (code 13), 146,3 MB, min SDK 26, ARM64/ARMv7/x86_64. Signature v2 valid dan `zipalign -P 16` lolos. Sertifikat sideload SHA-256 `b699b1bbabf442cc30302164aec22f5818ad613adca7ac4bb036bdac328426af` sama dengan rilis sebelumnya. |
| Paket Windows | ZIP 176 MB. EXE memberi versi 1.8.0, membuat gambar SDXS lokal, merender dua pratinjau berbeda dan video final, lalu menghapus proyek uji. |
| UI desktop | Playwright pada 1298×714 dan 390×844 tanpa galat halaman; seret teks, drop PNG, pemilih berkas media, dan subtitle editor diuji. Halaman Suara diuji untuk pilihan bahasa/model, label lisensi, unggah contoh audio dan pratinjau. Screenshot/GIF README diambil dari workspace demo sintetis v1.8. |
| Suara lokal | Supertonic membuat WAV Indonesia dan English nyata. ZipVoice dengan contoh English 10,4 detik menghasilkan suara baru 4,16 detik. Referensi MP3, M4A, FLAC, OGG dinormalisasi ke WAV pada tes FFmpeg. |
| Video panjang nyata | Sumber [78,1 menit dengan track Indonesia](https://youtu.be/kIB-ypmiIzo) yang sudah tersimpan dari uji sebelumnya dipakai ulang: subtitle AI untuk klip pada detik 3650–3662 selesai dan menghasilkan 7 baris bertiming tanpa membaca ulang seluruh video. Uji awal topik pada [review speaker 80,5 menit](https://youtu.be/4WvlolSYqjU) terdokumentasi pada [rilis 1.7.0](RELEASE-1.7.0.md). |

## Batas yang tetap ada

Tidak ada perangkat di `adb devices`, jadi instalasi, mikrofon, unduhan, ASR, render, Supertonic, ZipVoice, dan gambar native belum diuji pada ponsel fisik dalam rilis ini. Chatterbox Indonesia membutuhkan checkpoint tambahan sekitar 2,13 GB, model dasar dan PyTorch, sehingga tidak tersedia di APK/EXE ringan dan belum diuji sintesisnya di sini. Kloning lokal Indonesia di HP belum didukung. Supertonic adalah **open weights** dengan syarat OpenRAIL-M untuk komersial, bukan lisensi open source OSI; hak data Piper Indonesia belum terverifikasi. Lihat [audit model dan tautan lisensi](MODELS.md).

Alamat video privat, terbatas wilayah, berubah aturan akses, atau membutuhkan login masih bisa gagal. TikTok/Instagram langsung di Android belum didukung; impor berkas yang telah disimpan. Pengujian ini tidak mencakup layanan cloud berbayar secara live.
