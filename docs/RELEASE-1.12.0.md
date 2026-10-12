# Studio ZAI 1.12.0

Pemeriksaan lokal: 12 Oktober 2026. Windows x64 dan APK Android 1.12.0, build 17. Rilis ini melanjutkan perubahan pengguna pada proyek yang sama.

## Memakai aplikasi

1. Windows: ekstrak seluruh ZIP, lalu jalankan `StudioZAI.exe`. Simpan folder `_internal` di samping EXE. Android: pasang APK; sertifikatnya cocok dengan APK 1.11 lokal yang diperiksa.
2. Pilih **Hybrid** untuk mencari caption lebih dahulu dan memakai AI lokal. Pilih **Offline** untuk video lokal tanpa akses jaringan oleh jalur pemrosesan. **Online AI** memakai provider yang Anda pilih secara eksplisit.
3. Windows, LLM lokal: deteksi model dari server lokal yang sudah berjalan, atau pilih GGUF yang sudah ada dan tekan muat. Runtime CPU disertakan; bobot GGUF tidak disertakan dan tidak diunduh otomatis. Model dimuat saat diminta, satu pekerjaan berat berjalan pada satu waktu.
4. Online: pilih provider, masukkan API key, ambil daftar model lalu pilih model. Pergantian provider membersihkan key/model pada formulir dan mengabaikan hasil discovery lama. Pengujian provider pada rilis ini memakai fixture, tanpa memanggil layanan berbayar.
5. Jika caption tersedia, kandidat klip berasal dari teks terlebih dahulu. Jika tidak, pasang model ASR yang diperlukan. Tiny dan Small yang sudah ada diuji; Base tidak tersedia pada komputer pengujian. Heuristik diberi label bila LLM tidak tersedia. Android belum mengaktifkan LLM on-device.
6. Editor memakai portrait 9:16 secara default; square, landscape dan ukuran asli tetap dapat dipilih. Metadata rotasi video ponsel diperhitungkan sebelum crop. Subtitle langsung mengikuti playback, seek dan timing kata. **Draf terenkode** memeriksa komposisi akhir, termasuk lapisan media, judul dan audio.
7. Video lokal tetap dirujuk dari lokasi aslinya. Bila dipindah, gunakan **Tautkan ulang video** dan pilih video yang sama. Durasi/ukuran diperiksa; pemeriksaan tersebut bukan identifikasi isi video. Trim, subtitle dan ekspor tetap disimpan.

## Perubahan yang diperiksa

- Pemrosesan caption dahulu, cache berchecksum/TTL, chunk ASR yang dapat dilanjutkan, CPU INT8, pilihan CPU dan fallback CUDA.
- Ranking LLM lokal nyata dengan shortlist, batas konteks, schema timestamp dan validasi durasi. Request memakai snapshot setting/key agar perubahan formulir tidak mengubah pekerjaan yang sedang berjalan.
- Preview subtitle tanpa encode ulang setiap perubahan, animasi kata/box/highlight/karaoke/pop/bounce/fade/rise/zoom/typewriter, serta clock Android di antara laporan posisi native.
- Simpan proyek atomik dan merge perubahan independen; konflik tidak menimpa suntingan diam-diam. Output render unik, validasi FFprobe dan retry CPU saat encoder GPU gagal.
- Antrean terbatas, cancellation saat menunggu slot inferensi/encoder, timeout FFmpeg dan progress batch per hasil. Batch seluruhnya gagal berstatus error.
- Runtime llama.cpp CPU, QuickJS dan yt-dlp EJS dibundel untuk Windows. Model, `.env`, API key dan data proyek pribadi tidak dimasukkan ke paket.

## Cakupan fitur referensi

Halaman publik [SocialVisuals](https://socialvisuals.pro/) diperiksa sebagai referensi. Studio ZAI menyediakan workspace/proyek, deteksi klip podcast, pilihan rentang klip, editor kata dan bahasa, gaya/font subtitle, judul pembuka, watermark teks/gambar, crop/keyframe, split facecam/gameplay, preview, galeri dan ekspor batch beberapa rasio. Deteksi wajah Windows menggunakan YuNet dan Android menggunakan ML Kit; hasil crop perlu ditinjau pada video pengguna. Aplikasi berbayar di balik login tidak diuji, sehingga laporan ini tidak menyatakan semua fitur internal SocialVisuals identik.

## Hasil pengujian

| Pemeriksaan | Bukti dan batas |
|---|---|
| Python | 251 tes lolos; mencakup cache, mode offline, konflik proyek, batch, cancellation, timeout, CPU fallback, relink dan metadata rotasi |
| Flutter | 44 tes lolos; live subtitle, clock playback, caption/cache, audio, transfer dan rotasi. Analisis statis tidak menemukan masalah setelah perbaikan |
| Sumber | Ruff, konsistensi versi dan tabel ID/EN lolos. Audit pola rahasia memeriksa sumber serta blob Git; hasil terpisah dicatat sebelum upload |
| UI browser nyata | Edge dan API terisolasi; lebar 320 sampai 1440, tiga rasio, seek/kata aktif, keyboard, offline URL, provider swap dan zero encode otomatis. Tidak ada page error |
| MP4 subtitle nyata | Sepuluh efek diuji dengan frame hasil decode: tampil, berubah selama cue, lalu hilang setelah cue; output 360×640 |
| Video ponsel | MP4 640×360 dengan display matrix 90° dibaca sebagai 360×640; crop/encode aktual menghasilkan 360×640 |
| LLM nyata | Qwen3 1.7B Q6 CPU: load 24,867 detik, RSS 1.911,7 MiB; Indonesia 43,836 detik, Inggris 32,830 detik, masing-masing dua hasil tervalidasi dan tidak memilih iklan fixture |
| ASR nyata | Tiny CPU: cold ID 4,438 detik / EN 1,307 detik; Small: ID 7,041 / EN 7,084. RSS puncak sekitar 250–580 MiB. Fixture TTS sekitar 14–15 detik; ini bukan skor kualitas podcast |
| EXE nyata | Health 1.12, runtime suara, preview/export, GGUF lokal dan inferensi gambar lokal diuji dengan LOCALAPPDATA terisolasi. ASR paket diuji terpisah tanpa download model |
| Android | Build release, package/build number dan signature diperiksa. Tidak ada HP terhubung: penggunaan RAM, kamera, izin dan kualitas pada perangkat fisik belum dibuktikan |

Benchmark memakai model yang sudah terpasang, tanpa download model atau inferensi cloud. Angka ini berlaku untuk Ryzen 5 5500U dengan RAM sekitar 11,4 GiB, bukan janji waktu untuk semua perangkat atau durasi podcast.

## Penerimaan rencana A–K

| Skenario | Status bukti |
|---|---|
| A, caption YouTube | Kontrak caption dahulu diuji tanpa download/decode/ASR; tidak ada klaim download akun YouTube live berhasil |
| B, tanpa caption | Jalur audio-only dan ASR diuji; ASR dan ranking lokal juga dijalankan nyata secara terpisah. Satu podcast YouTube publik penuh belum diuji end-to-end |
| C, offline lokal | Guard jaringan, sumber lokal, preview/render dan inferensi CPU diuji; mode tetap memerlukan model lokal yang sudah terpasang |
| D, LLM lokal | Runtime CPU/GGUF dan schema hasil benar-benar dijalankan |
| E, tanpa LLM | Status setup/unavailable dan heuristik jelas; tidak diberi label LLM |
| F, subtitle animasi | Browser/widget dan frame MP4 untuk sepuluh efek lolos |
| G, batch | Validasi output, hasil parsial, seluruhnya gagal dan perubahan state diuji |
| H, perangkat lemah | Batas slot/memory, benchmark CPU/RSS dan interaksi browser diuji. Pengujian beban panjang pada HP belum tersedia |
| I, EXE | Binary rilis dijalankan, bukan hanya import Python sumber |
| J, APK | Build/signature/tes Flutter lolos; pengujian perangkat fisik belum tersedia |
| K, regresi | Suite Python/Flutter memeriksa proyek lama, import, editor, galeri dan multi-format; smoke EXE memeriksa voice/image. Tidak semua kombinasi voice/image pada HP diuji |

Gate UI berlaku pada alur yang diuji dan warna kontrol yang diubah: putih pada tombol biru 5,25:1, teks redup pada surface 5,25:1, aksen pada surface 4,91:1. Tidak mengklaim seluruh layar lama, semua kombinasi zoom/screen reader dan semua perangkat telah lulus.

## Lisensi, data dan batas

Kode Studio ZAI memakai **Studio ZAI Noncommercial License 1.0**, bukan MIT: boleh digunakan publik, perangkat lunaknya tidak boleh dijual. Monetisasi video hasil karya diperbolehkan sesuai LICENSE. Lisensi dependensi tetap disertakan, termasuk pemberitahuan runtime tambahan.

Audit rahasia mencari pola kredensial dan nama file privat pada sumber, history dan isi arsip. Hasil nol temuan tidak menjamin semua bentuk rahasia dapat dikenali. API key Windows disimpan melalui mekanisme lokal yang ada; aplikasi tidak menyertakan key pengguna pada rilis.

Warning toolchain Android mengenai plugin Kotlin/format SDK masih ada meskipun build berhasil. Tidak ada uji provider berbayar atau perangkat Android fisik. Kualitas deteksi wajah, ASR, ranking dan timestamp tetap perlu ditinjau pada materi pengguna. Tidak ada klaim kode bebas semua bug.

Artefak publik: [rilis GitHub v1.12.0](https://github.com/Zwart04/Studio-ZAI/releases/tag/v1.12.0). Checksum berada pada `SHA256SUMS.txt` di rilis tersebut. Bukti lokal tersimpan dalam folder `build` dengan nama `hybrid-*`; file media uji dan cache build sementara dapat dibersihkan setelah validasi.
