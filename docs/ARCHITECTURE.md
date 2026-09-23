# Arsitektur Studio ZAI

Dua runtime melayani alur yang sama. Windows memakai Python/FastAPI dengan UI web lokal dan pywebview. Android adalah aplikasi Flutter mandiri; tidak memerlukan server Python untuk editor, subtitle, atau suara lokal.

| Bagian | Desktop | Android |
|---|---|---|
| Download | yt-dlp, track bahasa eksplisit | youtube_explode + transfer range terbatas, refresh stream mempertahankan track |
| ASR | faster-whisper, chunk 90 detik | sherpa-onnx, WAV streaming + worker isolate |
| Video | FFmpeg + ASS/libass | FFmpegKit + ASS/libass |
| TTS / clone | Piper / sherpa-onnx ZipVoice | sherpa-onnx VITS / ZipVoice |
| Penyimpanan | JSON per proyek, folder sumber/klip/aset | JSON proyek dan direktori aplikasi |
| AI opsional | studiozai/ai.py | services/cloud_ai.dart |
| Kunci | Windows DPAPI; izin berkas pada Linux | flutter_secure_storage |
| Progress | Job queue, SSE terbaru + heartbeat | ChangeNotifier, byte download / detik audio / tahap render |

## Editor

Clip menyimpan waktu sumber, kanvas, framing, caption, template, audio, dan timeline. Timeline memiliki track video, media, teks, audio. Pemutar membuka media yang sudah ada segera. Perubahan dijeda singkat, disimpan dan menghasilkan draf baru di belakang layar; file pratinjau unik menghindari overwrite berkas yang masih diputar. Permintaan diserialkan di editor, hasil usang tidak mengganti video terbaru. Pemutar ditutup/dijeda saat keluar.

Ekspor akhir memakai timeline dan gaya yang sama dengan pratinjau. Subtitle yang dibakar ke MP4 tidak juga dipasang sebagai track teks HTML default. Template buatan pengguna dipersistenkan terpisah agar bisa digunakan lintas proyek.

## Siklus data

Sumber unduhan dimiliki proyek, sehingga bisa dipotong kembali tanpa unduhan baru. Berkas lokal eksternal tidak dihapus ketika proyek dihapus. Duplikat desktop menyalin media milik proyek dan memperbarui referensi. ID penyimpanan klip desktop stabil terhadap urutan; indeks folder Android dipertahankan saat klip lain dihapus. Cache transkripsi dan draf dibersihkan terpisah dari sumber/model.

## AI

Teks cloud mengembalikan rentang momen yang divalidasi terhadap durasi sumber. Gambar dan suara dikirim sebagai prompt/teks ke provider pilihan pengguna dan hasil PNG/WAV disimpan lokal. Koneksi gambar lokal adalah integrasi HTTP ke server terpisah, bukan runtime difusi yang dibundel. API key tidak ditampilkan oleh GET settings dan tidak diteruskan melalui redirect.

Lihat [fitur per platform](FEATURES.md) dan [cakupan pengujian](RELEASE-1.8.0.md).
