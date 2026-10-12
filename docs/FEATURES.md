# Fitur Studio ZAI 1.12

[Creator: podcast, kata, crop, terjemahan, galeri dan batch di Windows/Android](CREATOR.md).

| Fitur | Windows | Android |
|---|---|---|
| Video lokal | Ya | Ya |
| Link online | Situs yang didukung yt-dlp | YouTube dan URL file langsung |
| TikTok/Instagram | Tautan publik yang didukung yt-dlp | Impor file video yang sudah disimpan |
| Dub audio YouTube | Track yang tersedia | Track yang tersedia, retry terbatas tetap mempertahankan bahasa |
| Video sumber tersimpan | Ya | Ya |
| Trim, split, kanvas asli/9:16/1:1/16:9 | Ya | Ya |
| Portrait default, split facecam/gameplay | Ya | Ya |
| Judul pembuka dan watermark teks/gambar | Ya | Ya |
| Multi-kata, highlight/kotak kata aktif | Ya | Ya |
| Deteksi bahasa transkripsi otomatis | Ya, model multilingual | Ya, model multilingual |
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
| Mode default | Hybrid, caption dahulu dan LLM lokal terpilih; fallback heuristik berlabel | Caption dahulu, ASR on-device, heuristik berlabel |
| Full Offline | Sumber lokal dan model terpasang; loopback LLM | Sumber/model di HP; tidak memerlukan PC |
| LLM lokal nyata | Ollama, API loopback compatible, atau GGUF yang sudah ada melalui runtime CPU bundel | Belum diaktifkan; perlu pengujian HP fisik |
| AI online opsional | OpenAI, Anthropic, Groq, Gemini, DeepSeek, compatible | Provider cloud yang dipilih pengguna |
| Deteksi & saran model dari akun provider | Ya | Ya |
| Pelacakan wajah dengan jangkar X/Y | YuNet; Haar pada source tanpa bobot | ML Kit accurate + tracking |
| ZIP klip/format terpilih yang sudah dirender | Unduh ZIP | Bagikan ZIP |
| Gambar / suara online | OpenAI | OpenAI |
| Gambar lokal | SDXS-512, mesin SD.cpp CPU dalam paket | SDXS-512 CPU native pada ARM64; ARM32 belum didukung |
| Duplikat proyek independen | Ya | Belum ada tombol duplikat |
| Hapus proyek / cache terpisah | Ya | Ya |

Preview normal memutar sumber asli/segmen lokal dengan subtitle overlay tersinkron playback. Edit caption tidak menjalankan encoded preview otomatis. Tombol draf terenkode memeriksa komposisi final, termasuk crop, judul, watermark, overlay media dan audio tracks. Preview normal belum menggantikan compositor final untuk semua track. Tangkapan layar README berasal dari demo sintetis.

Caption hasil render tidak ditimpa track pemutar kedua. Teks yang sudah menyatu dengan sumber tidak dapat dihapus otomatis; posisi/off membantu mencegah tambahan teks bertumpuk.

Impor lokal mereferensikan file asli. Sumber unduhan disimpan di proyek. Hapus proyek membuang hasil miliknya; file asal eksternal dipertahankan. Cache memiliki versi dan checksum; cache rusak tidak dipakai.

HP fisik, mikrofon perangkat, gambar native Android, dan layanan cloud live belum diuji end-to-end pada sesi ini. Tidak ada iOS, sinkronisasi cloud proyek, atau publikasi langsung ke media sosial. [Validasi 1.12](RELEASE-1.12.0.md).
