# FEATURES — Studio ZAI
### Daftar Fitur Lengkap

> **EN TL;DR** — Complete feature catalog with priority (P0 must-have, P1 next, P2 experimental) and status. P0 ships in v1.0 on all three platforms (with platform-specific limits documented). Each AI feature has a no-AI fallback.

**Status legend:** ✅ ada di repo · 🟡 ada, butuh pengujian perangkat nyata · 🔵 rencana pasca-v1

---

## P0 — Wajib v1 (semua platform)

| ID | Fitur | Desktop | Android | Status |
|---|---|---|---|---|
| F-01 | **Input link** YouTube/TikTok/Instagram via yt-dlp | ✅ | ✅ (youtubedl_android) | 🟡 |
| F-02 | **Input file lokal** (drag-drop di desktop, file picker di Android) | ✅ | ✅ | 🟡 |
| F-03 | **Probe media** (durasi, resolusi, audio) + validasi | ✅ | ✅ | 🟡 |
| F-04 | **Auto transkrip ID/EN** dengan word timestamps + deteksi bahasa | ✅ | ✅ | 🟡 |
| F-05 | **Auto clip mode tanpa AI** — skor dari loudness RMS, gap silence, perubahan scene (transkripsi opsional) | ✅ | ✅ | 🟡 |
| F-06 | **Auto clip mode transkrip** — momen padat kata & kalimat utuh, 15-60 dtk | ✅ | ✅ | 🟡 |
| F-07 | **Subtitle otomatis**: word-level, 2 preset gaya (Clean, Bold-Highlight), burn-in + ekspor SRT/VTT | ✅ | ✅ | 🟡 |
| F-08 | **Crop 9:16**: center & blur-background | ✅ | ✅ | 🟡 |
| F-09 | **TTS ID/EN** (Piper) dari teks bebas atau transkrip klip | ✅ | ✅ | 🟡 |
| F-10 | **Mix audio**: ganti audio asli / narasi + original dikecilkan (ducking) | ✅ | ✅ | 🟡 |
| F-11 | **Editor sederhana**: trim, split, urutkan, judul klip, volume, edit teks subtitle, re-render | ✅ | ✅ | 🟡 |
| F-12 | **Manajer Model**: deteksi hardware, rekomendasi tier, unduh/resume/verifikasi/hapus, tampil ukuran | ✅ | ✅ | 🟡 |
| F-13 | **Proyek tersimpan**: daftar proyek, lanjutkan, duplikat, hapus | ✅ | ✅ | 🟡 |
| F-14 | **UI bilingual ID/EN**, dark minimalis, responsif | ✅ | ✅ | 🟡 |
| F-15 | **Progress realtime** (SSE di desktop, ChangeNotifier di Android) + log ringkas | ✅ | ✅ | 🟡 |
| F-16 | **Doctor**: cek ffmpeg/gpu/disk/model + saran perbaikan (CLI & UI) | ✅ | ✅ | 🟡 |

## P1 — Setelah v1 stabil

| ID | Fitur | Catatan | Status |
|---|---|---|---|
| F-17 | **Voice cloning desktop** (Chatterbox): ID (fine-tune) & EN, sampel 10-30 dtk | Auto-detect CUDA; peringatan RTF di CPU | ✅ kode, 🟡 uji |
| F-18 | **Voice cloning Android EN** (ZipVoice via sherpa-onnx) | Butuh reference audio + teksnya | ✅ kode |
| F-19 | **Highlight dengan LLM lokal opsional** (Ollama/LM Studio/OpenRouter, kirim transkrip saja) | Mati default; UI input base URL + model | ✅ |
| F-20 | **Face-track crop** (mediapipe, extra opsional desktop) | Kunci ke `object` di FFmpeg | 🔵 |
| F-21 | **Hook title overlay** (teks pembuka 2 dtk) | Preset + edit manual | ✅ |
| F-22 | **Kirim hasil ke HP via LAN** (QR code + server statis sementara) | Satu folder shared | 🔵 |
| F-23 | **cookies.txt** untuk video yang butuh login | Desktop setting | ✅ |

## P2 — Eksperimental / roadmap

| ID | Fitur | Catatan | Status |
|---|---|---|---|
| F-24 | **Chatterbox Q4 di Android** (ID/EN) | Auto-benchmark; jika RTF > 8 → tidak ditampilkan | ✅ kode, 🔵 uji HP nyata |
| F-25 | **Voice Pack**: fine-tune VITS kecil di desktop dari sampel user → sync ke Android | Inference super ringan semua platform | 🔵 |
| F-26 | **Batch & folder watch** | Antrean multi-video | 🔵 |
| F-27 | **Publish langsung** ke TikTok/YouTube | Butuh API pihak ketiga (Upload-Post dsb.) | 🔵 |
| F-28 | **Terjemahan subtitle** ID⇄EN untuk dubbing lintas bahasa | Tahap 1: subtitle; tahap 2: dubbing | 🔵 |
| F-29 | **iOS** | Butuh mesin macOS untuk build | 🔵 |

---

## Detail Perilaku Fitur Kunci

### Auto-clip heuristik (tanpa AI)
1. Ekstrak audio → hitung RMS per 0.5 dtk (numpy).
2. Deteksi silence (ffmpeg `silencedetect`) → batas kalimat alami.
3. (Opsional) skor perubahan scene via `select=gt(scene,0.4)` untuk momen visual.
4. Skor window: loudness ternormalisasi × kepadatan kata (jika ada transkrip) × penalti silence panjang.
5. Pilih top-N window 15-60 dtk, snap ke batas kalimat, hindari overlap.
6. Setiap clip menyimpan "alasan skor" agar transparan di UI.

### Subtitles
- Sumber: word timestamps (whisper) → grup 3-7 kata per caption, jeda > 0.6 dtk memecah caption.
- Preset **Clean**: putih, shadow halus, bawah tengah. **Bold-Highlight**: kata aktif kuning tebal (ASS karaoke).
- Burn-in via libass (`subtitles=` filter), plus file `.srt` + `.vtt` di folder output.

### TTS & dubbing
- Mode **Replace**: audio narasi menggantikan audio asli.
- Mode **Mix**: narasi + original audio dikecilkan (`sidechaincompress`/volume manual).
- Panjang narasi tidak sinkron? TTS di-*time-stretch* ringan (atempo dalam rentang wajar 0.9–1.15) atau dipotong dengan peringatan.

### Voice cloning (etika & batas)
- Konfirmasi izin satu kali sebelum aktif.
- Desktop: Chatterbox base (EN) + checkpoint ID; sampel ≥ 6 dtk (disarankan 10-30 dtk bersih).
- Android: ZipVoice (EN) stabil; Chatterbox Q4 ID hanya jika benchmark lulus.
- Semua output ber-watermark PerTh (bawaan model).
