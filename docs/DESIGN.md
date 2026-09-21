# DESIGN — Studio ZAI
### Design System

> **EN TL;DR** — One design language for web (desktop) and Flutter (Android): dark-first, one accent color, 12px radii, 4/8 spacing scale, Inter typography, line icons (Lucide), 150ms micro-animations, grayscale + single accent. Tokens live in ui/tokens.css and android/lib/theme/tokens.dart — keep them in sync.

---

## 1. Prinsip

1. **Satu aksi utama per layar** — tombol besar, jelas, tanpa kompetisi visual.
2. **Tenang** — latar gelap, sedikit garis, tanpa gradient ramai, tanpa shadow tebal.
3. **Terang informasi** — status model, progress, dan alasan skor clip selalu terlihat.
4. **Konsisten lintas platform** — komponen yang sama (kartu clip, progress tipis, panel edit) di web & Flutter.
5. **Aksesibel** — kontras teks ≥ 4.5:1, target sentuh ≥ 44px, fokus keyboard terlihat.

## 2. Token Warna

| Token | Nilai | Pemakaian |
|---|---|---|
| `--bg` | `#0B0E14` | Latar aplikasi |
| `--surface` | `#141824` | Kartu, panel |
| `--surface-2` | `#1C2230` | Elemen di atas surface (hover/input) |
| `--border` | `#252C3B` | Garis pemisah 1px |
| `--text` | `#E8EAF0` | Teks utama |
| `--text-dim` | `#9AA3B5` | Teks sekunder |
| `--accent` | `#6C5CE7` | Aksi utama, fokus, progress |
| `--accent-press` | `#5A4BD1` | State pressed |
| `--success` | `#2ECC71` | Selesai |
| `--warn` | `#F1C40F` | Peringatan (RTF lambat, model besar) |
| `--danger` | `#E74C3C` | Hapus, error |

## 3. Tipografi

- Font: **Inter** (fallback system-ui / Roboto di Android), angka tabular untuk statistik.
- Skala: `12 / 13 / 14 (body) / 16 (subtitle) / 20 (judul) / 28 (hero)`.
- Berat: 400 body, 500 tombol, 600 judul. Tanpa italic dekoratif.

## 4. Spacing, Radius, Elevasi

- Spacing scale: `4, 8, 12, 16, 24, 32, 48`.
- Radius: `8` (input kecil), `12` (kartu/tombol utama), `999` (pill/chip).
- Elevasi: **hanya border 1px + surface bertingkat**; shadow hanya untuk popover (`0 8px 24px rgba(0,0,0,.4)`).

## 5. Komponen Inti

| Komponen | Deskripsi |
|---|---|
| **Nav** | Sidebar kiri (desktop, ikon+label, aktif = accent 8% bg) / Bottom nav (Android, maks 5 item) |
| **Prompt utama** | Input besar dengan placeholder "Tempel link YouTube / TikTok atau pilih file…" + tombol utama |
| **Clip card** | Thumbnail 9:16, durasi, badge skor + alasan singkat, menu (Edit, Export, Hapus) |
| **Progress bar** | Garis tipis 3px, warna accent, dengan label tahap ("Menranskripsi 42%") |
| **Model card** | Nama, ukuran, badge platform, tombol Unduh/Hapus, bar indikator terpasang |
| **Panel Edit** | Slide-in kanan/ bawah: trim slider, daftar caption (edit teks per baris), pilihan crop, volume, tombol Render |
| **Toast** | Kiri-bawah, 1 baris pesan + aksi opsional ("Buka folder") |
| **Empty state** | Ikon garis 48px + 1 kalimat + 1 aksi |

## 6. Ikon & Gerak

- Ikon garis 1.5px (set **Lucide**), konsisten 18/20/24px.
- Animasi: transisi 150ms `ease-out`; progress indeterminate 1.2s loop; tanpa animasi dekoratif lain.
- Haptic ringan di Android untuk aksi selesai (opsional).

## 7. Tata Letak

```
DESKTOP (≥1024px)                 ANDROID
┌────────┬────────────────────┐   ┌────────────────┐
│ Nav    │  Konten (maks      │   │  AppBar ringkas│
│ 220px  │  1100px, tengah)   │   │                │
│        │                    │   │  Konten        │
│        │  [Prompt utama]    │   │                │
│        │  [Progress]        │   │                │
│        │  [Grid clip 3-4]   │   │  [Clip list]   │
└────────┴────────────────────┘   ├────────────────┤
                                   │ Bottom nav     │
                                   └────────────────┘
```

## 8. Lokasi Token

| Platform | File | Catatan |
|---|---|---|
| Web | `ui/tokens.css` | `:root { --bg: …; }` |
| Flutter | `android/app/lib/theme/tokens.dart` | `class Tokens { static const bg = Color(0xFF0B0E14); }` |

> ⚠️ Mengubah warna/tipe wajib di dua tempat sekaligus. Dokumentasikan perubahan di CHANGELOG.
