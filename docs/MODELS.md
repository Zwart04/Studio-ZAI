# Model lokal dan izin penggunaan

Model diunduh saat diperlukan. Katalog desktop berada di `core/studiozai/models/registry.json`, katalog APK di `android/app/lib/services/model_registry.dart`. Ukuran di layar adalah perkiraan; unduhan, ekstraksi, dan runtime dapat memakai ruang tambahan.

Status **boleh komersial** berarti lisensi upstream mengizinkannya dengan syarat yang tertulis. **Belum terverifikasi** berarti hak bobot atau data suara belum cukup jelas untuk direkomendasikan bagi konten komersial. **Terbatas** berarti ada ketentuan riset atau nonkomersial; model lama ini disembunyikan dari pilihan suara baru, tetapi instalasi yang sudah ada tetap dapat dilihat dan dihapus. Label lisensi repositori tidak otomatis mencakup setiap suara dan data latihnya.

| Kebutuhan | Pilihan | Perangkat dan batasan |
|---|---|---|
| Subtitle Indonesia | Whisper Small int8 | Lebih akurat, lebih berat dari Base/Tiny. Desktop dan APK memakai format bobot berbeda. |
| Subtitle English / perangkat menengah | Whisper Base int8 | Kompromi ukuran dan waktu. |
| Perangkat lemah | Whisper Tiny int8 | Cepat; hasil transkrip lebih sering perlu koreksi. |
| Suara Indonesia dan English | [Supertonic 3 int8](https://huggingface.co/Supertone/supertonic-3) | Sepuluh preset dalam satu model CPU sekitar 123 MB. **OpenRAIL-M:** komersial diizinkan sesuai [syarat penggunaan dan pemberitahuan konten AI](https://huggingface.co/Supertone/supertonic-3/blob/main/LICENSE). Bobot terbuka, tetapi lisensinya bukan open source OSI. Bukan kloning dari rekaman. |
| Suara English ringan | [Piper LJSpeech](https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ljspeech/medium/MODEL_CARD) | Sekitar 63 MB, dilatih dari awal pada dataset public domain; repositori bobot MIT. Pilihan English yang paling jelas asal datanya. |
| Suara Indonesia paling ringan | [Piper News](https://huggingface.co/rhasspy/piper-voices/blob/main/id/id_ID/news_tts/medium/MODEL_CARD) | Satu suara sekitar 63 MB. Repositori bertanda MIT, tetapi model card tidak menjelaskan hak komersial data suara Indonesia; **belum terverifikasi**. |
| Kloning English / Mandarin | [ZipVoice int8](https://github.com/k2-fsa/ZipVoice) | Apache-2.0; CPU desktop/APK. Perlu rekaman jelas 6–30 detik dan teks persis rekaman. **Tidak mendukung Indonesia.** |
| Kloning Indonesia | [Chatterbox Indonesian](https://huggingface.co/grandhigh/Chatterbox-TTS-Indonesian/raw/main/README.md) | Apache-2.0; opsional **desktop dari source**. Checkpoint tambahan sekitar 2,13 GB, model dasar/PyTorch menambah beberapa GB; perlu RAM besar dan runtime `core[clone]`. Tidak tersedia di APK atau EXE ringan. |
| Gambar offline | [SDXS-512 Q8](https://huggingface.co/concedo/sdxs-512-tinySDdistilled-GGUF) | 512 × 512, bobot sekitar 683 MB; OpenRAIL++. [Rincian pemasangan](LOCAL_IMAGE.md). |

Whisper mengenali ucapan dan membuat transkrip/subtitle; memasangnya tidak menambah karakter TTS. Sintesis dan kloning hanya tersedia bila model **dan** runtime yang sesuai terpasang. Untuk Chatterbox Indonesia, status bobot “terpasang” saja belum berarti paket desktop ringan siap menjalankannya. Contoh suara untuk kloning dapat dipilih dari format audio yang dibaca FFmpeg, termasuk WAV, MP3, M4A, FLAC, dan OGG; aplikasi mengubahnya sementara menjadi WAV yang diperlukan model.

## Suara lama dan hasil riset Indonesia

| Sumber | Temuan dan keputusan |
|---|---|
| [Piper Lessac](https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/lessac/medium/MODEL_CARD), [Ryan](https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ryan/medium/MODEL_CARD) | Lessac menunjuk [data berlisensi untuk riset saja](https://www.cstr.ed.ac.uk/projects/blizzard/2013/lessac_blizzard2013/license.html); Ryan memakai data CC BY-NC-SA 4.0. Keduanya bertanda **terbatas** dan tidak dipilih untuk penggunaan komersial. |
| Piper Alba, Amy, Joe | Model card masing-masing menyatakan diturunkan dari Lessac. Status komersial **belum terverifikasi**; disembunyikan dari pilihan baru. |
| [drat/TTS-Indonesia-Gratis](https://github.com/drat/TTS-Indonesia-Gratis), [Wikidepia/indonesian-tts](https://github.com/Wikidepia/indonesian-tts) | README melarang penggunaan komersial, meskipun repo drat juga menyebut MIT. Bobotnya tidak diintegrasikan. |
| [F5-TTS-INDO-FINETUNE-V2](https://huggingface.co/Eempostor/F5-TTS-INDO-FINETUNE-V2) | Bobot CC BY-NC 4.0; tidak diintegrasikan. |
| [bagustris/tts-bahasa](https://github.com/bagustris/tts-bahasa) | Kode memakai Meta MMS; [checkpoint MMS Indonesia](https://huggingface.co/facebook/mms-tts-ind) CC BY-NC 4.0. Lisensi kode MIT tidak mengubah batasan bobot. |
| [X-lord/Dataset-Text-To-Speech-Indonesia](https://huggingface.co/datasets/X-lord/Dataset-Text-To-Speech-Indonesia/raw/main/README.md) | Dataset berlabel MIT, **bukan model siap pakai**; asal hak rekamannya tidak dijelaskan di card. Tidak ditambahkan sebagai pilihan suara. |
| [Siomdo TTS](https://raw.githubusercontent.com/nuzulul/nuzulul.github.io/master/siomdo.md) | Halaman freeware Windows lama; tidak menyediakan source, bobot, atau lisensi model terbuka untuk integrasi. |

## Pemasangan dan sumber

Setup menyarankan model sesuai perangkat. Model tambahan dapat diunduh dan dihapus di halaman Model. Desktop memakai `faster-whisper`, Android memakai `sherpa-onnx`; bobot ASR keduanya tidak dapat dipertukarkan. Model tersimpan di `%LOCALAPPDATA%/StudioZAI/models` pada Windows dan direktori data aplikasi pada Android. Menghapus cache tidak menghapus model atau video sumber. Arsip Supertonic dan bobot SDXS divalidasi dengan SHA-256; sebagian bobot lama belum menyediakan checksum upstream dalam katalog.

Kode dan bobot memiliki lisensi yang berbeda: [OpenAI Whisper](https://github.com/openai/whisper) dan [faster-whisper](https://github.com/SYSTRAN/faster-whisper) MIT; [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) Apache-2.0; [Piper voices](https://huggingface.co/rhasspy/piper-voices) perlu dicek per voice; [ZipVoice](https://github.com/k2-fsa/ZipVoice/blob/master/LICENSE) Apache-2.0; [Supertonic](https://huggingface.co/Supertone/supertonic-3/blob/main/LICENSE) OpenRAIL-M; [Chatterbox Indonesian](https://huggingface.co/grandhigh/Chatterbox-TTS-Indonesian/raw/main/README.md) Apache-2.0. Model cloud bersifat opsional dan tidak diunduh sebagai model lokal; lihat [panduan AI](AI.md).
