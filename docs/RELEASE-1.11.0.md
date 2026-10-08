# Studio ZAI 1.11.0 — 8 Oktober 2026

## Perubahan

- Lisensi aplikasi: publik boleh memakai, memodifikasi dan membagikan; aplikasi/layanan berbasis aplikasi tidak boleh dijual tanpa izin Zwart04. Hasil milik pengguna boleh dimonetisasi. Salinan MIT lama dan lisensi dependensi tidak dicabut.
- Provider + API key → deteksi katalog akun, saran model, pilihan otomatis/manual pada Windows dan Android. Tidak ada daftar palsu saat provider gagal. Key lama tidak diteruskan ke provider/alamat baru; redirect API diblokir.
- Endpoint media privat diperketat; JSON/config/kredensial/database tidak dilayani. Host/Origin asing dan browser cross-site diblokir.
- Windows memakai YuNet dan Android memakai ML Kit accurate/tracking; jangkar X/Y memilih subjek, crop ditahan ketika kehilangan wajah. Bukan identifikasi pembicara aktif.
- ZIP hanya berisi MP4 klip/format yang dipilih, dengan penulisan streaming dan penghapusan berkas parsial ketika gagal.
- Clone Cheat Clip dipindahkan ke Coding AI dan dependensinya diperbaiki, tanpa push ke repo pihak lain. [Perbandingan dan fitur yang belum lengkap](REFERENCE-CHEAT-CLIP.md).

## Validasi

| Pemeriksaan | Hasil |
|---|---|
| Python | 169 tes lulus |
| Flutter | 36 tes lulus; analyze tanpa temuan |
| Ruff core dan sintaks JS | Lulus |
| Browser + render FFmpeg | Enam MP4: portrait 1080×1920, square 1080×1080, landscape 1920×1080; ZIP enam video valid |
| Pemilih model desktop + layar 393 px | Deteksi fixture, pilihan tersimpan, field key kosong setelah simpan, pergantian provider menghapus key; tanpa error JS/overflow |
| EXE creator | Portrait 202×360 dari sumber kecil, split, judul, watermark gambar, active word box, draft preview; YuNet menghasilkan keyframe pada video uji |
| EXE umum | Startup 1.11.0, Piper/ZipVoice, pratinjau, render, gambar SDXS sungguhan dan cleanup proyek uji |
| APK | Universal Android 8+, versi 1.11.0/code16; signature v2 dan zipalign 16 KB valid |
| Audit privasi | Source, riwayat Git dan ZIP/APK: tidak ada temuan pola token pribadi/berkas privat; fingerprint token publik yt-dlp diverifikasi ke upstream |

Tes menggunakan profil data terisolasi; `.env`, konfigurasi dan proyek pengguna tidak dimasukkan ke paket. Model YuNet, UI dan lisensi dalam paket Windows dibandingkan hash dengan source. Lisensi aplikasi disertakan dalam kedua paket.

## Batas pengujian dan privasi

Provider memakai fixture, bukan key/kuota pengguna; akses API berbayar live belum diuji. Tidak ada HP fisik tersambung: deteksi native ML Kit dan berbagi ZIP Android belum dibuktikan pada perangkat. Uji terjemahan nyata tidak diulang karena model fixture telah dibersihkan; tes regresi terjemahan lulus dan validasi nyata versi sebelumnya tetap tercatat pada catatan 1.10.

Video uji wajah dibuat dari satu gambar contoh OpenCV untuk memeriksa runtime; bukan benchmark podcast banyak pembicara. Tinjau wajah saling melintas, occlusion dan pergantian adegan.

AI online mengirim transkrip/prompt sesuai tindakan pengguna. SDK ML Kit dapat mengirim diagnostik perangkat/pemakaian menurut [disclosure resmi](https://developers.google.com/ml-kit/android-data-disclosure); ini bukan klaim nol lalu lintas jaringan. Pemindaian pola token bukan jaminan untuk semua bentuk rahasia. [Privasi](SECURITY.md).

APK memakai signing key debug yang sama dengan rilis sebelumnya untuk kontinuitas sideload. Distribusi Play Store memerlukan keystore release sendiri; private key tidak disertakan.

## Artefak

| Berkas | SHA256 |
|---|---|
| StudioZAI-1.11.0-windows-x64.zip | `2524665822426068caa1ebc8c0c97f4ddff059429e039c51102a9dedbc8b78b2` |
| StudioZAI-1.11.0-android.apk | `c5dd1a8061303ff88d019015e0d3a4340505c860eaaecb9548dd8fa35656da73` |

Paket lokal: `releases/1.11.0/`. [GitHub Release](https://github.com/Zwart04/Studio-ZAI/releases/tag/v1.11.0).

Cache/build Studio dibersihkan setelah verifikasi. Pemeriksaan akhir memastikan empat cache lama yang sebelumnya terkunci sudah tidak ada. Penghapusan output kecil `dist`/JSON audit pada clone Cheat Clip ditolak pemeriksaan persetujuan otomatis dengan alasan `blocked by policy`; output itu dipertahankan. Virtualenv/node_modules clone tetap tersedia untuk menjalankan proyek.
