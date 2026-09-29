# Fitur Studio ZAI 1.9

[Creator: podcast, kata, crop, terjemahan, galeri dan batch di Windows/Android](CREATOR.md).

| Fitur | Windows | Android |
|---|---|---|
| Video lokal | Ya | Ya |
| Link online | Situs yang didukung yt-dlp | YouTube dan URL file langsung |
| TikTok/Instagram | Tautan publik yang didukung yt-dlp | Impor file video yang sudah disimpan |
| Dub audio YouTube | Track yang tersedia | Track yang tersedia, retry terbatas tetap mempertahankan bahasa |
| Video sumber tersimpan | Ya | Ya |
| Trim, split, kanvas asli/9:16/1:1/16:9 | Ya | Ya |
| Timeline video, media, teks, audio | Seret blok, tepi, dan berkas ke track | Potong/atur klip dan overlay |
| Pemutar langsung + pratinjau otomatis | Ya | Ya |
| Subtitle AI dari audio ID/EN | faster-whisper; editor menranskripsi rentang klip bila proyek belum punya transkrip | sherpa-onnx Whisper; hasil lama dipertahankan saat ASR hening |
| Durasi klip adaptif/topik produk | Ya | Ya, dengan fallback bila transkrip kosong |
| Template bawaan + gaya buatan sendiri | Ya | Ya |
| Piper News ID / LJSpeech EN | Ya; hak data News ID belum terverifikasi untuk komersial | Ya; label lisensi tampil |
| Supertonic 3, 10 suara ID/EN | Ya | Ya; sintesis native belum diuji di HP fisik |
| Rekaman mikrofon | Browser/WebView | Izin mikrofon Android |
| ZipVoice English/Mandarin | Runtime dibundel | Runtime dibundel |
| Chatterbox kloning Indonesia | Opsional dari source + PyTorch, bobot >2 GB di luar model dasar | Belum tersedia pada paket ringan |
| AI teks / pemilihan momen | OpenAI, Anthropic, DeepSeek, compatible | Sama |
| Gambar / suara online | OpenAI | OpenAI |
| Gambar lokal | SDXS-512, mesin SD.cpp CPU dalam paket | SDXS-512 CPU native pada ARM64; ARM32 belum didukung |
| Duplikat proyek independen | Ya | Belum ada tombol duplikat |
| Hapus proyek / cache terpisah | Ya | Ya |

Video langsung tersedia di editor. Perubahan digabung setelah jeda singkat dan dirender otomatis; video sebelumnya tetap dapat diputar selama pembaruan. Ekspor tetap tindakan terpisah. Ini editor sederhana, bukan compositor GPU real-time setara CapCut. Tangkapan layar README berasal dari demo sintetis, bukan proyek pengguna.

Caption hasil render tidak ditimpa track pemutar kedua. Teks yang sudah menyatu dengan sumber tidak dapat dihapus otomatis; posisi/off membantu mencegah tambahan teks bertumpuk.

Sumber unduhan disimpan di proyek. Hapus proyek membuang sumber dan hasil miliknya; file asal eksternal dipertahankan. Cache hanya data sementara.

HP fisik, mikrofon perangkat, gambar native Android, dan layanan cloud live belum diuji end-to-end pada sesi rilis ini. Tidak ada iOS, sinkronisasi cloud proyek, atau publikasi langsung ke media sosial. [Validasi rilis](RELEASE-1.9.0.md).
