# AI lokal dan online

Buka Pengaturan → AI opsional (Android: AI lokal & online) hanya jika ingin memakai penyedia eksternal. Pembuatan klip, editor, subtitle, suara dasar, dan gambar SDXS-512 berjalan lokal setelah model yang diperlukan terpasang.

| Fungsi | Penyedia | Alamat bawaan |
|---|---|---|
| Teks / pemilihan momen | OpenAI | https://api.openai.com/v1 |
| Teks / pemilihan momen | Anthropic | https://api.anthropic.com/v1 |
| Teks / pemilihan momen | Groq | https://api.groq.com/openai/v1 |
| Teks / pemilihan momen | Gemini | https://generativelanguage.googleapis.com/v1beta/openai |
| Teks / pemilihan momen | DeepSeek | https://api.deepseek.com |
| Teks lokal / kompatibel | Ollama / chat completions | http://127.0.0.1:11434/v1 |
| Gambar online | OpenAI | https://api.openai.com/v1 |
| Gambar lokal bawaan | SDXS-512 + stable-diffusion.cpp | Langsung di perangkat, tanpa server |
| Gambar lokal lanjutan | Server stable-diffusion.cpp milikmu | http://127.0.0.1:1234/v1 |
| Suara online | OpenAI | https://api.openai.com/v1 |

Pilih provider, masukkan API key, lalu tekan **Deteksi & sarankan model**. Daftar berasal dari akun provider; model nonaktif dan model untuk tugas lain disaring. Model kosong/otomatis memakai saran saat analisis berjalan. Nama model tetap dapat diisi manual. Saran memakai jenis/nama model, bukan jaminan harga, kuota, atau kualitas. Gambar OpenAI memakai gpt-image-1-mini secara bawaan (1024 × 1024, kualitas rendah); suara memakai gpt-4o-mini-tts. Ini pilihan hemat yang didukung, bukan klaim model terbaru. API dapat berbayar; langganan ChatGPT/Claude aplikasi tidak menyediakan API key atau kredit API.

## Gambar lokal

Unduh **SDXS-512** sekali dari halaman Model. Bobot 683 MB terpisah dari APK/EXE dan diverifikasi SHA-256. Model menghasilkan gambar 512 × 512 dalam satu langkah menggunakan CPU [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp); prompt dan gambar tetap di perangkat. Mesin bawaan tersedia di Windows x64 dan APK Android arm64. Kebutuhan RAM serta waktu pemrosesan bergantung pada perangkat; Android arm32 belum mempunyai mesin ini. [Detail model, sumber, dan lisensi](LOCAL_IMAGE.md).

Untuk bobot yang lebih besar atau GPU/server sendiri, pilihan lama **stable-diffusion.cpp server** tetap ada di Pengaturan. Gunakan alamat `/v1` yang dapat dijangkau perangkat. Android yang terhubung ke server di komputer lain memerlukan alamat komputer tersebut; `127.0.0.1` berarti ponselnya sendiri.

## Suara dan privasi

Piper memiliki karakter tetap ID/EN. ZipVoice mendukung English/Mandarin, membutuhkan rekaman contoh 6–30 detik beserta teks yang persis diucapkan. Kloning Indonesia belum tersedia di paket standar. Rekam mikrofon atau pilih berkas; gunakan suara sendiri atau yang diizinkan.

Windows memakai DPAPI akun pengguna untuk kunci; Android memakai secure storage. Source Linux memakai izin berkas privat. Transkrip dikirim ke provider hanya ketika pemilihan momen online dipilih. Prompt gambar dan teks suara dikirim saat fitur online itu dijalankan. Sampel ZipVoice diproses lokal.

Tes integrasi memakai server fixture untuk protokol provider, respons PNG/WAV, dan penanganan error. SDXS-512 sudah diuji menghasilkan PNG sungguhan pada mesin Windows pengembangan; pengujian inferensi pada ponsel fisik masih diperlukan. API berbayar live serta server difusi eksternal belum diuji pada rilis ini.

Referensi: [OpenAI images](https://developers.openai.com/api/docs/guides/image-generation), [OpenAI TTS](https://developers.openai.com/api/docs/guides/text-to-speech), [Anthropic API](https://platform.claude.com/docs/en/api/overview), [DeepSeek API](https://api-docs.deepseek.com/).

Deteksi model tidak mengunggah video/transkrip. Key yang belum disimpan hanya dipakai untuk deteksi. Host provider resmi wajib HTTPS; alamat lain memakai compatible. Key tersimpan tidak dipakai ulang setelah provider/alamat berubah. Redirect API diblokir. Daftar dicache dalam memori lima menit, terpisah per provider/alamat/key.
