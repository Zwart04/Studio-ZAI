# Studio ZAI: rencana Hybrid Local AI

Tanggal pemeriksaan: 12 Oktober 2026. Rencana disetujui pengguna melalui instruksi lanjut. Implementasi dan bukti pengujian dicatat di [laporan 1.12](RELEASE-1.12.0.md).

## Dasar pengerjaan

Rencana ini mengikuti lampiran Fast Hybrid Local AI Architecture dari pengguna dan pilihan antislop `during` untuk sesi ini. Pengguna meminta semua tahap dilanjutkan sampai selesai. Inventaris dan selisih berikut mencatat kondisi sebelum implementasi.

Workspace yang diperiksa: `C:\Users\Zwart\Downloads\Coding AI\Studio ZAI`, branch `main`, HEAD `83df30ef7638ef1ff3724395bce0638056dc00a3`, remote `Zwart04/Studio-ZAI`. Ada 34 file tracked berubah dan 10 file baru. Semua perubahan tersebut tetap menjadi dasar pengerjaan. Rencana ini tidak meminta reset, clone ulang, atau penggantian komponen yang masih bekerja.

Referensi lokal `cheat-clip-pro` berada di folder Coding AI, HEAD `40948a53ab77bd3af775a77462692a00531b0eb7`. Pemeriksaan hanya membaca sumber. Pola yang berguna: timestamp kata dari audio klip terpilih, pemuatan model secara lazy, dan output subtitle yang stabil. Discovery Gemini dan fallback model referensi tidak membuktikan analisis LLM lokal. Implementasi Studio ZAI akan memakai komponen yang sudah ada, dengan mempertahankan lisensi pihak ketiga bila ada kode yang digunakan.

Audit bug sebelumnya tetap berlaku: [laporan 16 temuan](../build/AUDIT-2026-10-12.md). Rencana ini memasukkan semuanya ke tahap perbaikan dan menambahkan selisih terhadap arsitektur baru.

## Bukti lingkungan saat ini

| Pemeriksaan langsung | Hasil |
|---|---|
| CPU | AMD Ryzen 5 5500U, 12 logical CPU |
| RAM yang dilaporkan Windows | Sekitar 11,4 GiB |
| Adapter grafis | AMD Radeon Graphics |
| Runtime CTranslate2 di `.venv-build` | CPU: float32, int8, int8_float32; CUDA device count: 0 |
| Runtime Faster-Whisper | Terpasang di `.venv-build` |
| Pemeriksaan file model ASR | Tiny dan Small tersedia; Base tidak lolos `manager.is_installed` |
| Ollama pada localhost:11434 | Endpoint `/api/tags` belum merespons saat pemeriksaan |
| Android melalui ADB | Tidak ada perangkat terhubung |

Ini bukan benchmark inferensi. Pengecekan file model tidak membuktikan kualitas hasil ASR. Tidak ada model yang diunduh, cloud inference yang dipanggil, atau key pengguna yang dicetak. Pengecekan ADB menyalakan daemon lokal ADB ketika belum berjalan.

Hasil tes pada kondisi lokal yang sama dari audit sebelumnya: 221 tes Python dan 36 tes Flutter lulus; Flutter analyze menemukan satu info lint. Hash inventaris awal digunakan lagi untuk memeriksa bahwa sumber aplikasi belum berubah. Kelulusan tes tersebut belum mencakup selisih arsitektur di bawah.

## Selisih kode terhadap kebutuhan

| Kebutuhan | Kondisi kode lokal | Perubahan yang diperlukan |
|---|---|---|
| Metadata/caption sebelum media | `service.ingest` langsung download audio; caption baru dicoba di `generate_clips` | Tahap metadata dan caption harus selesai sebelum keputusan unduh audio |
| Analisis caption tanpa audio | `generate_clips` menolak media kosong; `analyze_media` selalu decode PCM | Jalur kandidat dari transkrip murni, audio features opsional |
| File lokal tanpa salinan besar | Import desktop dan Android menyalin file; desktop menghapus subtitle embedded dari salinan | Referensi sumber asli, impor caption sebelum perubahan media, ownership jelas |
| LLM lokal default | `use_llm=False`; form baru menghubungkan AI ke provider cloud; model global dapat mengalahkan model job | Kebijakan mode eksplisit dan konfigurasi LLM lokal terpisah |
| Ranking hanya shortlist | `rank_with_llm` membagi seluruh transkrip menjadi chunk sekitar 18.000 karakter | Pilih kandidat lebih dulu, batasi context dan jumlah panggilan |
| Structured semantic result | JSON start/end/title/reason/score; belum ada hook/context completeness | Schema, identitas kandidat, validasi batas/durasi dan metadata eksekusi |
| Offline tanpa download model | `transcribe.load_model` dapat menjalankan `models.manager.download` | Model yang belum terpasang harus meminta setup; tidak download dari job |
| ASR adaptif dan reuse | Cache model desktop ada; device memakai PyTorch; Android membuat worker baru setiap tugas | Deteksi CTranslate2, CPU fallback, cache terikat budget dan worker lifecycle |
| Hindari decode berulang | ASR decode sendiri, analisis audio decode lagi; chunk WAV sementara | Reuse PCM/features yang diperlukan, bounded streaming, hasil transkrip valid tersimpan |
| Caption Android sebelum ASR | `AppState.process` download, extract WAV, lalu ASR; tidak ada caption-first flow | Adapter caption terpisah, tidak menganggap yt-dlp desktop berlaku di Android |
| Preview overlay | Desktop `schedulePreview` memanggil encoded preview setelah debounce; creator Android memakai `previewClip` | Overlay tersinkron playback sebagai normal preview; draft encode hanya atas permintaan |
| Render hemat dan aman | Batch desktop menetapkan 3 worker; Project.save menulis JSON langsung | Mulai 1 worker, budget global, transaksi proyek, snapshot dan finalisasi atomik |
| Cache lengkap dan versioned | Project menyimpan transcript/segments; belum ada key semua tahap; cache save dapat menimpa state | Key berbasis sumber/parameter/versi; entry lengkap saja, merge aman |
| LLM on-device Android | ASR lokal ada; ranking AI lewat layanan HTTP | Label heuristik yang jujur; penelitian native LLM opsional dan gate perangkat nyata |

## Kontrak mode yang akan dipakai

1. **Hybrid Local AI**, default untuk proyek baru: URL boleh mengambil metadata/caption/audio/segmen yang dibutuhkan. Analisis semantic diarahkan ke runtime LLM lokal yang dipilih. Key/provider cloud tersimpan tidak mengubah mode ini. Bila runtime/model belum siap, tampilkan setup atau pilihan heuristik secara eksplisit.
2. **Full Offline**: hanya sumber lokal dan model terpasang. Larang network media/cloud/model download. Runtime desktop untuk LLM boleh loopback di komputer yang sama; endpoint LAN tidak memenuhi mode ini. Android memakai perangkat sendiri, bukan server LAN, untuk klaim on-device.
3. **Online AI**, opsional: cloud ASR/ranking hanya untuk capability yang diaktifkan pengguna; provider/model/key terikat pada job. Tidak mengirim data hanya karena key tersimpan.

Akuisisi media, ASR, ranking, animasi, format output, dan concurrency memiliki pengaturan terpisah. Field `online` lama tetap bisa dibaca sebagai strategi media, bukan diam-diam ditafsirkan sebagai izin cloud. Proyek lama, timeline, caption variants, storage_id, dan output format harus tetap kompatibel.

Status hasil akan mencatat asal transcript, ASR runtime/model/device, ranking engine/model, kualitas timestamp (measured/platform/estimated), sumber media preview, dan encoder yang benar-benar dipakai. Tidak ada fallback cloud otomatis. Heuristik tidak diberi label LLM.

## Tahap implementasi dan penerimaan

### 1. Keamanan state dan source ingestion

File utama: `core/studiozai/service.py`, `projects.py`, `server.py`, `pipeline/download.py`, `pipeline/captions.py`, `utils/probe.py`; Android `state/app_state.dart`, `models.dart`, `services/downloader.dart`, `services/youtube_source.dart`.

- Sebelum edit, simpan manifest/hash dan checkpoint kecil untuk file sumber yang berubah. Jangan mengarsipkan model, media besar, key, atau env ke Git.
- Pisahkan persiapan sumber menjadi metadata, transcript cache/caption, lalu audio fallback. Pertahankan API ingest lama melalui adapter jika dibutuhkan; tambahkan descriptor sumber untuk proyek yang belum punya file media.
- Izinkan generator berjalan dengan transcript valid tanpa `audio_media_path`. Acoustic scoring tidak wajib jika caption sudah cukup.
- Validasi host/URL yang didukung, bahasa caption, finite timing, urutan, durasi, teks dan duplikasi. Perbaiki pencocokan suffix bahasa dan audio fallback yang mengganti bahasa diam-diam.
- Untuk lokal, baca FFprobe/sidecar/embedded subtitle dahulu. Referensikan sumber asli secara default; pilihan salin tetap tersedia. Tandai media eksternal sehingga cleanup/delete proyek tidak menghapusnya. Sumber yang pindah diberi alur relink.
- Perbaiki transaksi cache/project sebagai prasyarat pipeline: reload terbaru lalu merge hanya cache fields di bawah lock per proyek; temp JSON unik dan atomic replace. Preview draft tidak boleh tersimpan melalui cache save. Nilai offset 0 tetap valid.
- Android URL langsung memakai downloader yang sesuai; fallback video mempertahankan audio pilihan. Tracking online resolve video segmen dahulu.

Uji penerimaan: caption YouTube fixture menghasilkan kandidat dengan 0 download audio/video dan 0 panggilan ASR; caption tak layak menjalankan satu audio-only fallback; impor lokal tidak menyalin atau mengubah sumber; proyek tanpa caption/media speech punya manual clipping yang jujur. Reproduksi audit 2, 4, 5, 9, 10, 11, 12, 13 menjadi tes regresi.

### 2. Mode eksekusi dan penghapusan pekerjaan berulang

File utama: `core/studiozai/config.py`, `server.py`, `service.py`, `pipeline/highlight.py`; tambahan kecil `core/studiozai/execution_policy.py`; Android `models.dart`, `state/app_state.dart`, `services/pipeline.dart`.

- Tambahkan enum/kontrak mode, validasi request, dan migrasi settings yang kompatibel. Jalur offline menolak sumber URL dan endpoint remote sebelum job berjalan.
- Kandidat transcript-first memakai sentence/topic windows; acoustic features hanya bila dibutuhkan. Reuse features, hindari decode media yang sudah tersedia sebagai PCM pada tahap ASR.
- Pisahkan shortlist dari ranking akhir. Terapkan min/max durasi, jumlah klip, non-overlap dan sentence boundaries sebelum/sesudah ranking.
- Cache transcript dan kandidat dengan versi algoritma, identitas/stat sumber, digest transcript, bahasa, model, dan parameter. Jangan menggunakan entry partial atau cache dari source/model berbeda. Hash saat data memang dibaca; hindari membaca ulang file besar hanya untuk setiap edit UI.

Uji penerimaan: transport spy menolak setiap network request di Full Offline kecuali loopback LLM yang diizinkan; cache hit tidak decode/ASR ulang; perubahan sumber/bahasa/model/durasi membuat miss yang tepat. Analisis tanpa ucapan tidak membuat transcript palsu.

### 3. Ranking semantic LLM lokal yang nyata

File utama: `core/studiozai/pipeline/highlight.py`, `ai.py`, `service.py`, `config.py`, `server.py`; tambahan `core/studiozai/local_llm.py` untuk adapter lokal/discovery/capability.

- Discovery hanya model yang sudah tersedia di runtime pilihan. Jangan menjalankan pull otomatis. Pisahkan model LLM lokal dari provider cloud serta model ASR.
- Kirim shortlist beserta context terbatas, identitas kandidat, dan opsi refinement dalam batas kandidat. Batasi jumlah request, context dan output; cancellation/timeout tidak menjalankan retry tanpa batas.
- Schema hasil memuat candidate ID, start, end, title, reason, semantic score, hook assessment dan context completeness. Validasi JSON tipe/finite number, source boundaries, durasi pilihan, dan overlap secara independen dari model.
- Gunakan structured output sesuai capability runtime. Cache hasil dengan model identity, prompt/schema version, transcript digest dan shortlist parameters. Pertahankan model job eksplisit; jangan membaca settings global yang berubah saat job berjalan.
- Laporkan model/engine yang benar-benar menerima request. Empty/invalid output, model hilang dan runtime down memberi setup/fallback heuristik dengan label jelas.

Uji penerimaan: tes kontrak memeriksa request benar-benar berisi shortlist dan model job; response rusak/out-of-range ditolak; model override tidak diabaikan; pilihan max 20 detik tidak menghasilkan 30 detik. Uji nyata harus menunjukkan runtime lokal menerima kandidat dan menghasilkan schema valid, bukan hanya mock response.

Model dari lampiran (`qwen3:1.7b`, `qwen3.5:2b-q4_K_M`, `qwen3:4b-instruct`) menjadi kandidat benchmark bila benar-benar terpasang/tersedia pada runtime. Tidak menetapkan model terbaik berdasarkan nama atau ukuran file. Saat ini Ollama belum merespons, jadi benchmark ketiga model masih menunggu runtime/model yang tersedia.

### 4. ASR adaptif, cache dan lifecycle model

File utama: `core/studiozai/pipeline/transcribe.py`, `models/manager.py`, `service.py`, `config.py`; Android `services/speech.dart`, `services/wav_chunks.dart`, `services/media_tools.dart`, `services/model_manager.dart`.

- Hapus download otomatis dari pemuatan ASR; bedakan paket runtime tersedia dan model file siap. Model Tiny/Small yang sudah ada dapat dipakai tanpa instalasi tambahan.
- Gunakan kemampuan CTranslate2 untuk device/compute type; inisialisasi/inferensi CUDA yang gagal turun ke CPU dengan status nyata. Override tetap tersedia.
- Reuse model sesuai budget: satu instance aktif per konfigurasi dan bounded idle eviction. Android evaluasi persistent speech isolate dengan reset/cancellation/memory recovery; jangan mempertahankan banyak model hanya untuk menghindari reload.
- Cache transcript selesai/hasil chunk tervalidasi untuk resume. Fingerprint chunk harus memasukkan source revision, bahasa, model, chunk boundaries dan versi engine. Temporary PCM tidak diperlakukan sebagai hasil selesai.
- Word timing prioritas: existing genuine words, selected-range alignment yang didukung, atau ASR klip terpilih. Timestamp perkiraan selalu ditandai.

Uji penerimaan: missing model tidak memanggil download; cache model digunakan ulang; CPU fallback diuji; perubahan source/model tidak menghidupkan stale transcript. Ukur Tiny/Base/Small dengan audio Indonesia/Inggris yang punya referensi nyata, jika model tersedia; Base saat ini dicatat unavailable, bukan diunduh otomatis.

### 5. Subtitle dan preview langsung

File utama: `ui/timeline.js`, `creator.js`, `studio.css`, `core/studiozai/pipeline/caption_style.py`, `subtitle.py`, `service.py`; Android `screens/editor_screen.dart`, `screens/creator_screen.dart`, `services/creator_tools.dart`, `services/subtitle_builder.dart`; komponen overlay kecil baru bila diperlukan.

- Normal preview memutar original/selected segment dengan subtitle overlay. Editor tidak menjalankan FFmpeg atau save draft setiap edit caption. Cache segmen online boleh diambil sekali sesuai kebutuhan playback.
- Sinkronkan cue/kata dengan seek, pause, trim dan source offset. Layout baris tetap stabil saat active word berubah. Request lama tidak boleh menimpa draft baru.
- Satukan vocabulary efek: word, highlight, box, karaoke, pop, bounce, fade, rise, zoom, typewriter; alias `type` lama tetap terbaca. Implementasikan efek yang belum ada pada live overlay dan export, bukan hanya menambah option.
- Draft encoded singkat tersedia sebagai aksi terpisah untuk mengecek efek final. Export memakai FFmpeg/libass yang ada. Preserve timeline, teks/media overlay dan audio tracks.

Uji penerimaan: edit subtitle biasa menghasilkan 0 request encoded preview/FFmpeg; playback/seeking menunjukkan kata yang tepat; estimated/measured label benar. Render fixture pendek, ambil frame sebelum/saat/setelah kata aktif untuk memverifikasi setiap efek pada MP4. Pemeriksaan frame bukan hanya pencarian tag ASS.

### 6. Render queue hemat dan hasil yang aman

File utama: `core/studiozai/jobs.py`, `server.py`, `projects.py`, `service.py`, `pipeline/render.py`, `pipeline/timeline.py`, `utils/ffmpeg.py`; Android `state/app_state.dart`, `services/pipeline.dart`, `services/timeline_render.dart`.

- Mulai satu render worker secara global, termasuk single render/preview/batch. Queued work dibatasi tanpa membuat thread/encoder tak terbatas; berbagi budget dengan ASR/LLM.
- Job per klip/format memakai snapshot immutable dan temp output unik. Validasi revision lagi sebelum attach. Cancellation/retry tidak menerbitkan stale/partial output atau menghapus output sukses sebelumnya.
- Terapkan watchdog FFmpeg yang tidak bergantung pada stderr; kill/reap saat timeout/cancel.
- Finalisasi atomik setelah FFprobe memvalidasi stream, duration, dimensi/canvas dan audio sesuai mode. Probe encoder tersedia tidak cukup: lakukan encode probe singkat dan CPU fallback jika akselerasi gagal.
- Tampilkan progres/result tiap klip; kegagalan total menjadi gagal, kegagalan sebagian tetap disebutkan. Jangan menampilkan “Selesai 0 video” sebagai sukses.

Uji penerimaan: regresi audit 2, 3, 6, 15; dua job/project berbeda tetap mematuhi budget global; cancel saat encoder diam selesai tepat waktu; crash/failure tidak merusak JSON/output sebelumnya. Hasil portrait benar 9:16. Worker tambahan hanya diaktifkan setelah benchmark nyata menunjukkan manfaat tanpa menurunkan respons UI atau menaikkan memory berlebihan.

### 7. Windows/Android dan UX yang menjelaskan proses nyata

File utama: `ui/index.html`, `app.js`, `studio.js`, `tokens.css`, `styles.css`, `studio.css`; Android `screens/home_screen.dart`, `screens/settings_screen.dart`, `screens/cloud_settings_screen.dart`, `state/app_state.dart`, `services/cloud_ai.dart`, `theme/tokens.dart`, `widgets/common.dart`.

- Tiga mode processing memakai satu pilihan utama; subsetting terpisah untuk ASR, LLM lokal/cloud, subtitle, output, concurrency. Local model discovery menawarkan model terpasang atau setup; bukan klaim “otomatis terbaik” tanpa benchmark.
- Perbaiki key/provider swap: clear field/model/status bila provider berubah, invalidasi discovery lama, dan provider/key binding pada backend. Jangan mencatat key/token/prompt pribadi pada log benchmark.
- Pertahankan download media desktop dan pisahkan link eksternal dari link download. Tampilkan penyebab gagal dan aksi retry yang benar.
- Android basic tetap bekerja tanpa Ollama/PC. Bila belum ada LLM on-device, tampilkan heuristik secara eksplisit. LAN inference opsional diberi label server LAN dan tidak masuk Full Offline on-device.
- Penelitian optional on-device LLM memakai runtime native yang cocok, dengan build/JNI, model mapping, capability/memory checks. Fitur belum boleh diaktifkan umum sebelum uji memory/performance/stabilitas pada HP. Ketidaktersediaan HP saat ini membatasi bukti, bukan alasan memberi klaim palsu.

Uji penerimaan: regresi audit 1, 11, 12, 13, 14; provider switch tidak mengirim key lama; mode default tidak memanggil cloud yang tersimpan; setiap status dapat ditelusuri ke engine aktual. Keyboard Tab/Enter/Escape, empty/loading/error, zoom 200%, sentuh dan reflow desktop/tablet/phone diuji pada UI aktual.

### 8. Benchmark, regresi dan paket

File utama: `core/tests/`, `android/app/test/`, `tools/`, `desktop/packaging/build_windows.bat`, `studiozai.spec`, `.github/workflows/`, `docs/BUILD.md`.

- Ubah fixture audit menjadi tes regresi permanen yang memeriksa kegagalan nyata, bukan menyalin implementation detail. Pertahankan tes lama.
- Tambahkan runner benchmark opt-in dengan dataset Indonesia/Inggris yang provenance-nya jelas; catat unavailable dan error sebagai hasil, bukan angka dummy.
- Catat time-to-first-highlight, total time, model load, LLM latency, peak memory process/runtime terpisah, downloaded media bytes, render time, cache hit/miss, model/runtime/version dan hardware. Pisahkan cold/warm run. Ukuran download model bukan penggunaan RAM.
- Build scripts memasang extras face/translation yang benar dan berhenti jika dependency/build gagal. Paket tidak memasukkan model besar atau data user otomatis. Audit sumber/history dan arsip aktual sebelum rilis.
- Windows EXE smoke dengan LOCALAPPDATA terisolasi; APK release, signature dan package checks. Uji device fisik dicatat terpisah dari tes Flutter/build. Tidak push/release tanpa otorisasi untuk pekerjaan ini.

## Matriks penerimaan akhir

| Skenario lampiran | Bukti yang wajib dicatat |
|---|---|
| A: YouTube caption | Kandidat muncul; tidak ada download full video/audio atau ASR yang tidak diperlukan |
| B: YouTube tanpa caption | Audio-only, ASR lokal, lalu ranking LLM lokal nyata |
| C: Local offline | Network diblok; sumber lokal, ASR/LLM lokal, playback preview dan render berhasil |
| D: Local AI | Request/engine/model nyata dan output schema tervalidasi |
| E: No local LLM | Setup/heuristik berlabel jelas, tidak mengklaim sukses LLM |
| F: Animated subtitles | Per-word timing live dan frame MP4 untuk semua efek |
| G: Batch | Output per klip valid, state aman, snapshot/retry/cancel diuji |
| H: Weak hardware | Memory/CPU/concurrency diukur; UI tetap merespons selama pekerjaan |
| I: Windows EXE | Binary yang baru dibangun dijalankan dengan data uji terisolasi |
| J: Android APK | Build/signature pass; uji perangkat nyata hanya bila tersedia |
| K: Regression | Proyek lama, imports, editor, gallery, voice/image tools dan multi-format tetap bekerja |

## Arah antislop untuk tahap UI

Design Read: editor klip untuk pengguna Windows/Android, mengikuti arah dark workspace yang sudah ada di `docs/DESIGN.md`; ENERGY 1 / RHYTHM 2 / MOTION 1. Subtitle animation adalah konten video, bukan animasi dekoratif antarmuka.

- Dark canvas dipertahankan untuk melihat video; system font menghindari unduhan font tambahan; aksen biru mengutamakan aksi analisis/render; warna status menyampaikan state nyata dengan teks.
- Form import/model, daftar kandidat, dan editor punya komposisi berbeda sesuai keputusan pengguna. Tidak menambah dashboard statistik atau cards promosi.
- Motion UI hanya feedback singkat; overlay subtitle mengikuti playback. Pengaturan tetap dapat dibaca tanpa mouse atau warna saja.
- Token web/Flutter harus konsisten; contrast dihitung, bukan ditebak; controls minimal 44px pada sentuh dan reflow diuji di rentang lebar kontinu.
- Direction lama menyebut blur sidebar/tab bar/sheet. Jika implementasi menampilkan lebih dari dua surface blur bersamaan, ini bertabrakan dengan R-10. Sebelum mengubah desain tersebut, konfirmasi elemen spesifik dengan pemilik sesuai R-37. Tidak membuat logo/aset/navigation baru tanpa arahan yang diperlukan.
- `antislop-code` hanya menangani komentar. Perbaikan logic berasal dari kebutuhan arsitektur, tidak diklaim sebagai pembersihan komentar. Pertahankan komentar API, concurrency, platform, privacy dan lisensi yang berguna.

Gate antislop UI lengkap menjadi penerimaan tahap 7: Hard Gate, Purpose-Gate, Liveliness, Quality Locks, serta checklist UI/human/mobile. Setiap PASS memerlukan bukti runtime/click-through yang tercatat. Rencana ini bukan UI yang telah dibangun dan tidak mengklaim gate UI selesai.

## Pemeriksaan dokumen sebelum implementasi

- R-02 PASS: dokumen baru tidak memakai em dash atau en dash.
- R-17/R-36/R-38 PASS: angka lingkungan berasal dari pemeriksaan lokal; benchmark yang belum dijalankan disebut belum tersedia; fitur baru ditulis sebagai pekerjaan yang akan dilakukan.
- R-31/C-1 PASS: alasan mode, layout, font, palette dan motion ditulis pada bagian kontrak/arah UI.
- antislop-code PASS untuk lingkup sesi: tidak ada komentar atau kode aplikasi yang diubah.
- C-5 PASS: tes audit sebelumnya dibedakan dari validasi arsitektur baru, mock contract dari inferensi nyata, dan build APK dari bukti perangkat.

## Sumber teknis yang diperiksa

- [Cheat Clip Pro](https://github.com/galihjuansaputra/cheat-clip-pro), serta sumber clone lokal yang disebut di atas.
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs): schema dan dukungan response_format pada API kompatibel; tidak menjamin kualitas pemilihan klip.
- [Ollama chat API](https://docs.ollama.com/api/chat): adapter runtime lokal mengikuti capability versi yang tersedia.
- [CTranslate2 compute types](https://opennmt.net/CTranslate2/python/ctranslate2.get_supported_compute_types.html): pemeriksaan compute capability, bukan hanya PyTorch CUDA.
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper): runtime ASR yang sudah dipakai; benchmark upstream bukan benchmark komputer pengguna.
- [llama.cpp Android](https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md): kandidat penelitian native, bukan bukti kompatibilitas semua HP.
- Katalog model [Qwen3 1.7b](https://ollama.com/library/qwen3:1.7b), [Qwen3.5 2b Q4](https://ollama.com/library/qwen3.5:2b-q4_K_M), [Qwen3 4b instruct](https://ollama.com/library/qwen3:4b-instruct): nama/tag harus diverifikasi lagi terhadap runtime sebelum benchmark.

Persetujuan rencana ini memulai implementasi tahap 1 dan melanjutkan tahap berikutnya sesuai hasil uji. Keputusan instalasi model besar, eksperimen hardware Android, dan publikasi tetap mengikuti arahan pengguna serta bukti yang tersedia.
