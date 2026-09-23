# AI lokal dan online

Buka Pengaturan → AI opsional (Android: AI lokal & online). Pilih fungsi teks, gambar, atau suara, lalu isi provider, nama model yang tersedia di akun, alamat API, dan API key. Editor lokal tidak membutuhkan akun cloud.

| Fungsi | Penyedia | Alamat bawaan |
|---|---|---|
| Teks / pemilihan momen | OpenAI | https://api.openai.com/v1 |
| Teks / pemilihan momen | Anthropic | https://api.anthropic.com/v1 |
| Teks / pemilihan momen | DeepSeek | https://api.deepseek.com |
| Teks lokal / kompatibel | Ollama / chat completions | http://127.0.0.1:11434/v1 |
| Gambar online | OpenAI | https://api.openai.com/v1 |
| Gambar lokal | stable-diffusion.cpp | http://127.0.0.1:1234/v1 |
| Suara online | OpenAI | https://api.openai.com/v1 |

Model teks diisi sendiri sesuai akses akun. Gambar OpenAI memakai gpt-image-1-mini secara bawaan (1024 × 1024, kualitas rendah); suara memakai gpt-4o-mini-tts. Ini pilihan hemat yang didukung, bukan klaim model terbaru. API dapat berbayar; langganan ChatGPT/Claude aplikasi tidak menyediakan API key atau kredit API.

## Gambar lokal

Pasang server [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp/tree/master/examples/server) dan bobot kompatibel sesuai RAM/VRAM. Jalankan sesuai dokumentasi build server, lalu hubungkan alamat dengan akhiran /v1 di pengaturan gambar. Studio ZAI mengirim permintaan /images/generations: 512 × 512, 4 langkah, CFG 1, keluaran PNG base64.

[SD-Turbo](https://huggingface.co/stabilityai/sd-turbo) memakai sedikit langkah tetapi bobot distribusi penuhnya tetap besar. Kuantisasi dan kebutuhan memori bergantung pada server/model. Tidak ada unduhan model gambar otomatis atau mesin difusi native di APK. Android dapat memakai layanan online atau server sendiri melalui HTTPS; localhost hanya untuk server yang berjalan pada perangkat itu sendiri. Tidak ada jaminan difusi lokal berjalan ringan di semua HP.

## Suara dan privasi

Piper memiliki karakter tetap ID/EN. ZipVoice mendukung English/Mandarin, membutuhkan rekaman contoh 6–30 detik beserta teks yang persis diucapkan. Kloning Indonesia belum tersedia di paket standar. Rekam mikrofon atau pilih berkas; gunakan suara sendiri atau yang diizinkan.

Windows memakai DPAPI akun pengguna untuk kunci; Android memakai secure storage. Source Linux memakai izin berkas privat. Transkrip dikirim ke provider hanya ketika pemilihan momen online dipilih. Prompt gambar dan teks suara dikirim saat fitur online itu dijalankan. Sampel ZipVoice diproses lokal.

Tes integrasi memakai server fixture untuk protokol provider, respons PNG/WAV, dan penanganan error. API berbayar live serta server difusi nyata belum diuji pada rilis ini.

Referensi: [OpenAI images](https://developers.openai.com/api/docs/guides/image-generation), [OpenAI TTS](https://developers.openai.com/api/docs/guides/text-to-speech), [Anthropic API](https://platform.claude.com/docs/en/api/overview), [DeepSeek API](https://api-docs.deepseek.com/).
