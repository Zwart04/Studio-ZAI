# Privasi dan keamanan Studio ZAI 1.11

## Jaringan
Editor dan model lokal memproses media pada perangkat. Unduh video/model memerlukan jaringan. Studio ZAI tidak menambahkan telemetri sendiri. SDK ML Kit Android untuk wajah/terjemahan dapat mengirim informasi perangkat/aplikasi, identifier instalasi dan diagnostik pemakaian melalui HTTPS, sesuai [disclosure Google](https://developers.google.com/ml-kit/android-data-disclosure). Karena itu aplikasi tidak diklaim bebas dari seluruh telemetri dependensi.

AI online opsional: deteksi model mengirim API key ke provider untuk meminta katalog; analisis momen mengirim transkrip; gambar online mengirim prompt; suara online mengirim teks. Pengguna memilih provider dan menjalankan fitur tersebut. Provider mempunyai aturan penyimpanan/kuota sendiri. Sampel ZipVoice diproses lokal. Model terjemahan diunduh saat diperlukan.

## Kunci dan konfigurasi
- Windows menyimpan API key dengan DPAPI akun Windows pada folder data pengguna, di luar repo dan ekspor proyek. Penulisan kredensial dilakukan atomik. Source Linux/macOS memakai berkas privat berizin 600; bukan vault terenkripsi.
- Android memakai secure storage/Keystore; bukan SharedPreferences biasa. Backup aplikasi dimatikan.
- Respons pengaturan hanya menampilkan penanda ***, bukan isi key. Key untuk deteksi tidak disimpan sebelum tombol Simpan ditekan.
- Mengganti provider/alamat API menghapus key lama kecuali key baru diberikan. Deteksi menolak penggunaan key tersimpan pada tujuan lain.
- Provider resmi dibatasi ke host HTTPS resmi. Endpoint sendiri memakai compatible. Key tidak dikirim melalui HTTP remote; redirect API ditolak, termasuk pada koneksi LLM lama.
- .env, cookies, kredensial, keystore, dan konfigurasi lokal diabaikan Git. Jangan memaksa git add -f untuk berkas tersebut.

## Server dan media
Server desktop mengikat 127.0.0.1. Middleware menolak host asing, Origin berbeda, dan permintaan browser cross-site. Ini bukan autentikasi untuk server publik; jangan mengekspos server lokal ke internet.

/api/media hanya melayani jenis video/audio/gambar/subtitle/ZIP di folder data pengguna. Path di luar folder data dan konfigurasi, key, log, JSON atau database ditolak. ZIP klip hanya berisi MP4 yang dipilih, tanpa konfigurasi/cookies/JSON proyek.

UI paket Windows dibatasi ke aset web; folder data pengguna tidak disalin. Android menyertakan aset aplikasi, bukan konfigurasi perangkat.

## Pemeriksaan rilis
[Audit rilis](../tools/audit_release_privacy.py) memeriksa nama berkas privat dan pola token umum pada source terlacak, blob riwayat Git, dan arsip rilis. Nilai temuan tidak dicetak. Fingerprint token publik bawaan extractor yt-dlp dibandingkan dengan source upstream resmi; token lain tetap dilaporkan. Tidak ditemukannya pola bukan jaminan untuk semua jenis rahasia atau akses malware pada perangkat.

Tes regresi mencakup penyimpanan/redaksi key, penggantian tujuan API, katalog model, host/Origin, dan media privat. Provider diuji dengan fixture tanpa key/kuota pengguna. [Hasil rilis](RELEASE-1.11.0.md).

## Lisensi dan laporan
Kode baru memakai [Studio ZAI Noncommercial](../LICENSE): publik boleh menggunakan dan membagikan; menjual aplikasi atau layanan berbasis aplikasi memerlukan izin Zwart04. Pengguna boleh memonetisasi hasil. Izin MIT pada salinan lama tidak dicabut. Komponen pihak ketiga mempertahankan lisensi masing-masing.

Laporkan masalah melalui security advisory privat di repo Zwart04/Studio-ZAI. Sertakan versi dan langkah reproduksi tanpa API key atau .env.
