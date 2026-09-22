# SECURITY — Studio ZAI
### Privasi & Keamanan

> **EN TL;DR** — 100% local by default: no telemetry, no uploads. Network is used only to download the source video (user action) and model files (one-time, from official hosts). Secrets stay in local config; the local server binds to 127.0.0.1 only. Voice cloning requires explicit consent and outputs are watermarked (PerTh).

---

## 1. Model Ancaman (ringkas)

| Aset | Ancaman | Mitigasi |
|---|---|---|
| Video & hasil klip user | Kebocoran ke pihak ketiga | Tidak ada upload; semua file lokal |
| Suara user (sampel cloning) | Penyalahgunaan identitas | Konfirmasi izin, watermark PerTh, tidak dikirim keluar |
| Konfigurasi (cookies.txt, API key LLM) | Terbaca pihak lain | Simpan di folder data user dengan izin file ketat; tidak pernah dicatat ke log |
| Server lokal | Diakses dari jaringan | Bind `127.0.0.1` saja; tanpa autentikasi longgar apa pun |

## 2. Prinsip

1. **Offline-first** — tidak ada telemetri, analytics, crash reporter, atau auto-update yang memanggil rumah.
2. **Jaringan hanya untuk:**
   - unduh video sumber (perintah eksplisit user, via yt-dlp);
   - unduh model dari host resmi (HuggingFace/rilis), dengan verifikasi sha256;
   - panggilan LLM opsional **hanya jika** user mengisi endpoint sendiri (mis. Ollama lokal).
3. **Least privilege** — server lokal hanya loopback; Android meminta izin sesedikit mungkin (storage/notifikasi saat dibutuhkan).

## 3. Penanganan Rahasia

- `cookies.txt` & API key disimpan di `%LOCALAPPDATA%\StudioZAI\` / `~/.local/share/studiozai/` dengan izin `600` (Linux/macOS) atau setara (Windows).
- Nilai sensitif **diredaksi** dari log (`***`), tidak pernah dikirim ke UI kecuali masked.
- Dokumentasikan di UI: "cookie setara akses login — jangan bagikan file config."

## 4. Voice Cloning — Etika & Kepatuhan

- **Konfirmasi izin wajib** (sekali) sebelum fitur aktif: hanya suara sendiri / berizin.
- Semua audio Chatterbox **ber-watermark PerTh** secara default (MIT, bawaan model) — tahan kompresi MP3/Opus & editing ringan.
- Library deteksi PerTh open source memungkinkan verifikasi downstream.
- UI menampilkan peringatan saat mengkloning suara tokoh publik? Tidak — kebijakan: tolak jika teks prompt mengandung klaim impersonasi tokoh nyata (daftar sederhana + pesan edukasi).
- Catatan regulasi: EU AI Act Art. 50 & TAKE IT DOWN Act mendorong provenance marking — fitur watermark justru membantu kepatuhan kreator.

## 5. Keamanan Media & File

- Nama file hasil selalu disanitasi (blok `..`, karakter path berbahaya) — mencegah path traversal.
- Command ffmpeg dijalankan dengan argumen array (tanpa `shell=True`) — mencegah command injection.
- Unduhan model: hanya HTTPS + verifikasi sha256 di registry; gagal verifikasi → file dihapus.
- Ekstraksi subtitle dari sumber eksternal tidak dieksekusi sebagai kode; hanya teks.

## 6. Pelaporan Kerentanan

Buka *security advisory* privat/issue di repo `Zwart04/Studio-ZAI`, atau email pemilik repo. Sertakan: versi, platform, langkah reproduksi. Perbaikan akan masuk patch release dengan catatan CHANGELOG.

## 7. Checklist Rilis

- [ ] Tidak ada endpoint jaringan baru selain yang didokumentasikan §2.
- [ ] Semua panggilan subprocess memakai argumen array.
- [ ] File rahasia berizin ketat + redaksi log teruji.
- [ ] Konfirmasi izin cloning tampil di web & Android.
- [ ] Model registry HTTPS + sha256 lengkap.

## 8. Penguatan 1.3.3 (hasil audit)

Audit menyeluruh pada 2026-09-22 menemukan dan menutup hal berikut. Semua ada tes regresinya di `core/tests/test_security.py` (20 tes).

| Temuan | Dampak | Perbaikan |
|---|---|---|
| `project_id` dari URL dipakai langsung sebagai nama folder | `DELETE /api/projects/..` bisa menghapus **seluruh folder data** (model, suara, proyek) | `_project_root()` memvalidasi id dengan `^[A-Za-z0-9_-]{1,64}$` dan memastikan hasil `resolve()` tepat di dalam `projects/` |
| Ekstraksi arsip model tanpa filter (`tarfile.extractall`) | Arsip berbahaya dari internet bisa menulis file di luar folder tujuan | `_validate_members()` menolak path absolut/`..`/keluar tujuan, menolak symlink/hardlink, dan memakai `filter="data"` di Python 3.12+ |
| Server lokal bisa disalahgunakan dari LAN | Orang lain di jaringan bisa memicu render/unduhan | Bind default `127.0.0.1` (desktop launcher & `serve --host`), tanpa `CORSMiddleware` |
| `/api/media` menerima path bebas | Membaca berkas sembarang di disk | Hanya berkas yang `resolve()`-nya di dalam folder data (403 jika di luar) |
| Android: backup cloud & transfer perangkat aktif | Proyek, model, dan rekaman suara ikut tercadangkan ke Google | `android:allowBackup="false"`, `data_extraction_rules` mengecualikan domain root |
| Android: lalu lintas HTTP polos diizinkan | Unduhan bisa dibajak/downgrade ke HTTP | `network_security_config` menolak cleartext, semua unduhan HTTPS |

Hasil audit lain: tidak ada rahasia ter-hardcode di repo, tidak ada berkas sensitif (keystore/`key.properties`/`cookies.txt`) yang ter-commit, APK **tidak** `debuggable`, dan Windows Defender tidak menemukan ancaman pada EXE/APK hasil build.

> Catatan: APK rilis ditandatangani dengan **debug key** agar bisa langsung di-*sideload*. Untuk distribusi luas, buat keystore rilis sendiri (lihat `docs/BUILD.md`) — debug key tidak boleh dipakai untuk update publik.
