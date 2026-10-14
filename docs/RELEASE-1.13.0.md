# Studio ZAI 1.13.0

Beranda sekarang memisahkan pekerjaan, model, dan kanvas. Kode bahasa regional seperti `en-US` dinormalkan menjadi `en` sebelum dikirim ke Whisper.

## Windows

- Pilih **Cari momen untuk klip** atau **Transkrip saja**. Transkrip saja tidak memanggil pemilih momen dan tidak membuat atau merender klip. Hasil teks bertimestamp dan unduhan SRT tersedia di proyek.
- Model offline memakai runtime di komputer. Model online memakai provider dan API key untuk membaca transkrip serta memilih momen. Whisper adalah model transkrip lokal yang terpisah. Caption sumber diprioritaskan jika tersedia.
- Pilihan Hybrid dihapus dari beranda. Mode lama masih dapat dibaca untuk kompatibilitas proyek dan klien terdahulu.
- Pilihan visual kanvas: portrait 9:16, kotak 1:1, standar 4:3, letterbox dalam portrait, landscape 16:9, atau rasio sumber. Pilih crop penuh, margin hitam, atau latar buram. Kotak dan 4:3 menghasilkan kanvas dengan rasio tersebut, bukan konten di dalam kanvas portrait.
- Render otomatis mengikuti kanvas yang dipilih. Pilihan model otomatis menghapus model spesifik yang sebelumnya tersimpan. Tombol Mulai mencegah pengiriman ganda selama persiapan.

## Android

Pilihan Hybrid diganti dengan penjelasan offline/online. Transkrip saja menampilkan teks bertimestamp tanpa ranking atau render. Pilihan kanvas berupa tombol dengan bentuk rasio; pilihan Android tetap portrait, kotak, landscape, dan asli. SRT serta preset 4:3/letterbox pada rilis ini tersedia di Windows. Android masih memakai heuristik untuk memilih momen lokal; LLM on-device belum diaktifkan.

## Validasi

- 267 tes Python lulus, termasuk regresi bahasa regional, transkrip saja yang mempertahankan edit klip, batas jaringan inference lokal, ekspor SRT, dan render nyata 4:3 tanpa distorsi bentuk.
- Whisper tiny INT8 asli berhasil mentranskrip rekaman sintetis berbahasa Inggris dengan parameter `en-US`; hasilnya `en`, dua segmen. Ini memvalidasi penanganan bahasa, bukan tolok ukur akurasi podcast.
- Browser Edge: alur transkrip melalui API sebenarnya sampai SRT; perpindahan tugas/provider; pembersihan API key saat provider berubah; enam preset kanvas; preview rasio; subtitle saat seek; tidak ada encode otomatis saat mengedit. Tidak ada page error atau overflow beranda pada 320, 360, 390, 540, 680, 768, 1024, dan 1440 piksel.
- 46 tes Flutter lulus dan analyzer tidak menemukan masalah. Tes widget mencakup perpindahan tugas dan pemilihan kanvas pada layar 320 piksel.
- EXE hasil build dan EXE setelah dipasang di `dist/StudioZAI` lulus: versi 1.13.0, semua HTML/CSS/JS identik dengan sumber, transkrip saja, SRT, momen, preview, serta video 1440×1080.

Pengujian menggunakan proyek terisolasi. Data proyek asli, model, cookie, dan API key pengguna tidak dipindahkan. Belum ada pengujian di perangkat Android fisik atau panggilan inference ke provider berbayar. Gangguan jaringan/platform video tetap bisa menyebabkan unduhan gagal; hasil pengujian tidak menjamin seluruh kombinasi video dan perangkat bebas bug.

## Pemeriksaan tampilan antislop

- Hard Gate PASS untuk alur yang diubah: browser tanpa page error/overflow, pilihan native mendukung keyboard, fokus terlihat, loading/error memakai status pekerjaan, dan tidak ada angka penghematan tanpa bukti pada formulir baru.
- Purpose Gate PASS: diagram rasio menunjukkan bentuk keluaran; garis biru menandai pilihan aktif; latar gelap dan font sistem mengikuti `docs/DESIGN.md`.
- Liveliness PASS: ENERGY 1 / RHYTHM 2 / MOTION 1. Formulir dipisahkan menurut sumber, tugas, model, dan hasil; satu tombol proses utama.
- Craftsmanship PASS dalam cakupan perubahan: setiap pilihan terhubung ke payload proses; transkrip, rasio, preview, serta render diverifikasi. Perbedaan fitur Windows/Android dijelaskan di atas.
