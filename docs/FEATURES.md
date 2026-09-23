# Fitur Studio ZAI 1.6

| Fitur | Windows | Android |
|---|---|---|
| Video lokal | Ya | Ya |
| Link online | Situs yang didukung yt-dlp | YouTube dan URL file langsung |
| Dub audio YouTube | Track yang tersedia | Track yang tersedia, retry terbatas tetap mempertahankan bahasa |
| Video sumber tersimpan | Ya | Ya |
| Trim, split, kanvas asli/9:16/1:1/16:9 | Ya | Ya |
| Timeline video, media, teks, audio | Ya | Ya |
| Pemutar langsung + pratinjau otomatis | Ya | Ya |
| Subtitle ID/EN | faster-whisper | sherpa-onnx Whisper |
| Template bawaan + gaya buatan sendiri | Ya | Ya |
| Piper ID/EN + karakter suara | Ya | Ya |
| Rekaman mikrofon | Browser/WebView | Izin mikrofon Android |
| ZipVoice English/Mandarin | Runtime dibundel | Runtime dibundel |
| AI teks / pemilihan momen | OpenAI, Anthropic, DeepSeek, compatible | Sama |
| Gambar / suara online | OpenAI | OpenAI |
| Gambar lokal | Server SD.cpp terpisah | Koneksi server, bukan mesin difusi native |
| Duplikat proyek independen | Ya | Belum ada tombol duplikat |
| Hapus proyek / cache terpisah | Ya | Ya |

Video langsung tersedia di editor. Perubahan digabung setelah jeda singkat dan dirender otomatis; video sebelumnya tetap dapat diputar selama pembaruan. Ekspor tetap tindakan terpisah. Ini editor sederhana, bukan compositor GPU real-time setara CapCut.

Caption hasil render tidak ditimpa track pemutar kedua. Teks yang sudah menyatu dengan sumber tidak dapat dihapus otomatis; posisi/off membantu mencegah tambahan teks bertumpuk.

Sumber unduhan disimpan di proyek. Hapus proyek membuang sumber dan hasil miliknya; file asal eksternal dipertahankan. Cache hanya data sementara.

HP fisik, mikrofon perangkat, dan layanan cloud live belum diuji. Belum ada iOS, sinkronisasi cloud proyek, publikasi langsung ke media sosial, atau difusi gambar native universal. [Validasi rilis](RELEASE-1.6.0.md).
