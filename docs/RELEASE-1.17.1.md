# Studio ZAI 1.17.1

Romboak tampilan Windows, Android, dan web ke palet arang bergaya editor video, 15 Oktober 2026.

## Palet warna

`ui/tokens.css` memakai latar arang `#141417` (bukan hitam pekat), permukaan bertingkat `#202024` / `#2A2A2F` / `#36363C`, dan teks putih lembut `#F5F5F7`. Token netral baru `--sel`, `--sel-strong`, dan `--ring` menggantikan biru pada keadaan non-aksi.

Kebijakan aksen tertulis di komentar `ui/tokens.css` dan `docs/DESIGN.md`: `--accent` / `--action` hanya untuk tombol utama, `--red` hanya untuk tombol hapus. Tab aktif, seleksi, focus ring, progress, berita, playhead, timeline, tab batch, tautan unduh, dan preset kanvas seluruhnya netral. Strip gradient merah `#app::after` dihapus; padanan Flutter-nya, `bottom: PreferredSize` di bawah app bar `main.dart`, ikut dihapus.

Kontras dihitung ulang sebelum rilis: `--text-dim` di atas `--surface` 6,73:1, teks putih di atas `--action` 4,78:1, `--red` di atas latar tombol hapus 5,66:1, dan `--separator-strong` sebagai batas nonteks 3,49:1.

## Beranda

`ui/home_guide.js` memasang dua wadah `.home-col` yang masing-masing mengalir sendiri. Grid baris 2 kolom sebelumnya mengikat tinggi dua bagian pada baris yang sama sehingga kolom kanan berlubang sekitar 600 px ketika kolom kiri jauh lebih tinggi. Multikolom CSS sempat dicoba dan dibuang karena merusak grid kanvas: hanya 1 dari 6 pilihan kanvas yang tergambar di Chromium.

Pembagian kolom kiri = "Model untuk memilih momen" + "Transkrip & audio", kanan = "Hasil klip" + "Subtitle & animasi". Selisih tinggi kedua kolom di bawah 100 px pada lebar 1440. Bagian "Kinerja laptop" menjadi `<details>`; `#performanceMode`, `#pickSmallGguf`, dan `#pickNoLlm` tetap ada dan tetap berfungsi. Tidak ada ID, atribut `name`, atau elemen `<p>` penyangga yang dihapus — seluruh pemeriksaan `tools/verify_hybrid_ui.js` tetap lulus.

Tombol "Muat model GGUF" diturunkan dari biru ke netral agar hanya ada satu tombol utama per layar.

## Android

`android/app/lib/theme/tokens.dart` mengikuti palet baru dan `Tokens.accent2` dihapus bersama satu-satunya pemakaiannya. `Tokens.sel`, `Tokens.selStrong`, `Tokens.ring`, dan `Tokens.separatorStrong` sempat ditambahkan lalu dibuang kembali karena tidak dipakai kode mana pun; `tools/check_dart_refs.py` melaporkan sisa konstanta mati sebagai info.

## Pengujian

291 tes Python lolos. Enam puluh tes Flutter lolos, `flutter analyze` tanpa temuan. `ruff check core/studiozai` bersih, `tools/check_i18n.py` 184/184 kunci, `scripts/check_version.py` konsisten, dan `tools/check_dart_refs.py` cocok. Sembilan berkas `ui/*.js` lolos parser `node --check`.

Browser Edge dengan API terisolasi memeriksa 14 kelompok pemeriksaan pada lebar 320, 360, 390, 540, 680, 768, 1024, dan 1440 tanpa overflow dan tanpa page error. Tangkapan layar seluruh tujuh halaman navigasi dan editor diperiksa manual.

## Batas

Perubahan ini tampilan saja: alur kerja, API, dan format render tidak berubah. Penyedia berbayar, perangkat Android fisik, dan aksesibilitas per pembaca layar tidak diuji pada patch ini. Rilis 1.17.0 masih berlaku untuk face-track crop (mediapipe), Chatterbox Q4 Android, dan publishing ke sosmed yang belum tersedia. Lisensi noncommercial Studio ZAI dan lisensi dependensi tetap berlaku.
