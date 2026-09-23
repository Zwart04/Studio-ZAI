# Model dan lisensi

Bobot diunduh terpisah sesuai kebutuhan. Katalog desktop ada di core/studiozai/models/registry.json, Android di android/app/lib/services/model_registry.dart. Ukuran katalog adalah perkiraan; ukuran unduh dan ekstraksi dapat berbeda.

| Kebutuhan | Rekomendasi | Pertimbangan |
|---|---|---|
| Subtitle Indonesia | Whisper Small int8 | Lebih akurat dari Tiny/Base, lebih banyak waktu dan RAM. |
| Subtitle Inggris / perangkat menengah | Whisper Base int8 | Kompromi kecepatan dan ukuran. |
| Coba cepat / perangkat lemah | Whisper Tiny int8 | Cepat, tetapi lebih banyak koreksi teks. |
| Akurasi tambahan desktop | Whisper Medium int8 | Opsional, lebih berat. |
| Suara Indonesia | Piper News | Satu karakter Indonesia pada katalog terintegrasi. |
| Suara English | Piper Lessac, Alba, Amy, Ryan, Joe, LJ | Unduh hanya karakter yang diperlukan. |
| Banyak karakter suara ID/EN | Supertonic 3 int8 | Sepuluh karakter dalam satu unduhan sekitar 129 MB; sintesis CPU lokal. Bukan kloning. |
| Kloning English/Mandarin | ZipVoice int8 | CPU Windows/Android, perlu encoder, decoder, vocoder, kamus, audio contoh dan transkripnya. |
| Gambar offline | SDXS-512 Q8 | 512 × 512, satu langkah; bobot 683 MB. Windows x64 dan Android ARM64. |

Desktop memakai faster-whisper; Android memakai sherpa-onnx Whisper. Format bobot berbeda dan tidak dapat dipertukarkan. Model Whisper multibahasa adalah model pengenalan ucapan, bukan kumpulan karakter TTS; memasangnya tidak menambah pilihan suara.

## Model eksperimental

Chatterbox, fine-tune Indonesia komunitas, GGUF eksperimental, MMS dan jalur runtime yang belum teruji tidak menjadi rekomendasi utama. Entri lama dipertahankan untuk kompatibilitas/pengelolaan instalasi. Paket Windows tidak membawa PyTorch/Chatterbox. Pengaturan lama Chatterbox tanpa runtime dimigrasikan ke ZipVoice. Kloning Indonesia belum tersedia di paket standar; gunakan Piper ID atau suara online.

## Pemasangan

Setup memasang kebutuhan dasar dan memeriksa hasilnya. Supertonic dan SDXS dipasang bila dibutuhkan, agar setup tetap ringan. Android mengekstrak arsip dalam worker isolate, dan ZipVoice memerlukan unduhan vocoder terpisah. Model dapat dihapus dari halaman Model; pembersihan cache tidak menghapus model/video sumber. Arsip Supertonic dan bobot SDXS diperiksa dengan SHA-256 sebelum ditandai terpasang; tidak semua model lama memiliki checksum upstream di katalog.

Penyimpanan: Windows %LOCALAPPDATA%/StudioZAI/models, Linux direktori data pengguna, Android direktori aplikasi.

## Lisensi

| Komponen | Sumber dan ketentuan |
|---|---|
| Whisper | [OpenAI Whisper](https://github.com/openai/whisper), [faster-whisper](https://github.com/SYSTRAN/faster-whisper): MIT. |
| Piper voices | [Bobot resmi dan model card](https://huggingface.co/rhasspy/piper-voices), [arsip sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models). Lisensi setiap suara/dataset berbeda; jangan menganggap seluruh bobot MIT. |
| ZipVoice | [Panduan sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/tts/zipvoice.html), Apache-2.0 untuk ZipVoice; komponen tambahan mengikuti upstream. |
| Font | Anton, Barlow Condensed, DM Serif Display, Kalam: OFL, disertakan bersama font. |
| Supertonic 3 | [Model card Supertone](https://huggingface.co/Supertone/supertonic-3), OpenRAIL-M. Runtime [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) mengikuti lisensi Apache-2.0. |
| Gambar lokal | [SDXS-512 GGUF](https://huggingface.co/concedo/sdxs-512-tinySDdistilled-GGUF), OpenRAIL++. Mesin desktop [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) MIT; mesin APK ARM64 dari [Local Diffusion](https://github.com/rmatif/Local-Diffusion) Apache-2.0. [Rincian file dan hash](LOCAL_IMAGE.md). |

Model cloud bukan unduhan lokal. [Panduan AI](AI.md).
