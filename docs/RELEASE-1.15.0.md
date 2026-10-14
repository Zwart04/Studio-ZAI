# Studio ZAI 1.15.0

## Beranda dan kontrol model

- Pengaturan analisis, hasil klip, transkrip, dan subtitle dikelompokkan dalam bagian yang terlihat langsung pada beranda Windows.
- Tombol Muat model GGUF dan Lepaskan dari RAM lebih besar, tersusun sejajar di desktop dan vertikal di ponsel. Status memuat/melepas terlihat, dan tombol dinonaktifkan selama permintaan berjalan. Pelepasan ditolak ketika pekerjaan sedang aktif.
- Provider online memakai ikon resmi yang disimpan lokal, petunjuk mendapatkan API key, serta tautan panduan dan harga/batas akun. Sumber ikon tercatat dalam `ui/assets/providers/sources.json`; merek tetap milik penyedia masing-masing.
- Gemini dan Groq diberi penanda kuota/paket gratis dengan penjelasan batasnya. Gratis tidak berarti tanpa batas atau semua model gratis.
- Setelah deteksi model, pilih Rekomendasi, Termurah, atau Paling pintar dari model yang tersedia pada akun. Pergantian provider atau key membatalkan pilihan hasil deteksi sebelumnya.
- Android mendapatkan ikon provider, petunjuk API, tombol menyalin tautan resmi, dan prioritas model pada pengaturan cloud.

## Batas saran model

Harga diperiksa 14 Oktober 2026 dan kedaluwarsa setelah 30 hari. Termurah membandingkan hanya model dengan harga yang diketahui, memakai asumsi 5.000 token input dan 1.000 output. Tarif standar konteks pendek tidak mencakup diskon, cache, pajak, atau kuota gratis. Paling pintar memakai urutan keluarga model, bukan hasil benchmark atau jaminan kualitas. Endpoint kompatibel tidak diberi harga milik provider lain.

Sumber: [OpenAI](https://developers.openai.com/api/docs/pricing), [Anthropic](https://platform.claude.com/docs/en/about-claude/pricing), [Gemini](https://ai.google.dev/gemini-api/docs/pricing), [Groq](https://console.groq.com/docs/models), [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/).

## Validasi

- 277 tes Python dan 54 tes Flutter lulus; Dart analyzer tidak menemukan masalah.
- Browser Edge: beranda pada delapan ukuran 320–1440 piksel; bagian subtitle/analisis terlihat, tombol GGUF, ikon resmi, tautan API, pergantian provider, prioritas model, keyboard, animasi caption, transkrip/SRT, dan rasio preview. Tidak ada page error atau overflow beranda.
- EXE 1.15.0 diuji sebelum dan setelah pemasangan ke `dist/StudioZAI`. UI dan ikon cocok dengan sumber. Transkrip/SRT, pencarian momen, preview, dan render 1440×1080 lulus dengan data terisolasi.

Deteksi provider dan pelepasan GGUF pada tes browser memakai fixture. Belum ada pengujian API berbayar, pemuatan GGUF nyata pada perubahan ini, atau perangkat Android fisik. Pengujian ini tidak menjamin semua video dan perangkat bebas bug.
