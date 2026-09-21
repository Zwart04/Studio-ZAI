# DESIGN — Studio ZAI
### Design System (Apple-style, minimalis)

> **EN TL;DR** — One design language for the web UI (desktop) and the Flutter app (Android), modelled on Apple's dark UI: pure black canvas, grouped inset cards, hairline separators, iOS-blue accent, SF-like typography, translucent sheets, 220 ms motion, one clear primary action per screen. Tokens live in `ui/tokens.css` and `android/app/lib/theme/tokens.dart` — keep them in sync.

---

## 1. Prinsip

1. **Satu aksi utama per layar** — tidak ada dua tombol bersaing.
2. **Tenang dan lapang** — latar hitam, sedikit garis, tanpa gradient ramai, tanpa shadow tebal.
3. **Hierarki tipografi jelas** — judul besar, isi 15px, keterangan 13px.
4. **Konsisten lintas platform** — kartu klip, progress tipis, sheet edit yang sama di web & Android.
5. **Aksesibel** — kontras teks ≥ 4.5:1, target sentuh ≥ 44px, focus ring terlihat.

## 2. Token Warna (palet iOS dark)

| Token | Nilai | Pemakaian |
|---|---|---|
| `--bg` | `#000000` | Latar aplikasi |
| `--bg-elevated` | `#0B0B0D` | Sidebar / tab bar |
| `--surface` | `#1C1C1E` | Kartu "inset grouped" |
| `--surface-2` | `#2C2C2E` | Input, elemen di dalam kartu |
| `--surface-3` | `#3A3A3C` | Hover / thumb segmented |
| `--separator` | `rgba(255,255,255,.09)` | Garis rambut 1px |
| `--fill` | `rgba(120,120,128,.24)` | Tombol sekunder, chip |
| `--text` | `#FFFFFF` | Teks utama |
| `--text-dim` | `#8E8E93` | Teks sekunder (systemGray) |
| `--text-dim-2` | `#636366` | Placeholder/tersier |
| `--accent` | `#0A84FF` | Aksi utama, progress, fokus |
| `--green` | `#30D158` | Selesai/aktif |
| `--orange` | `#FF9F0A` | Peringatan (draft, model eksperimental) |
| `--red` | `#FF453A` | Hapus, error |

## 3. Tipografi

- Font: **system stack** — `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI Variable", Inter, Roboto` (tanpa unduh font → tetap ringan).
- Skala: `12 (caption) / 13 (footnote) / 15 (body) / 16 (callout) / 20 (title3) / 24 (title2) / 30 (title1)`.
- Berat: 400 body, 500 tombol, 600 subjudul, 700 judul besar; letter-spacing negatif tipis pada judul.
- Angka tabular pada tabel/statistik.

## 4. Bentuk, Jarak, Gerak

- Radius: `10` (input/tombol), `14` (kartu), `18` (sheet), `999` (pill/chip).
- Spacing skala 4: `4, 8, 12, 16, 20, 24, 32, 40`; tinggi baris daftar 48px.
- Elevasi: **border rambut + surface bertingkat**; shadow hanya toast/sheet (`0 12px 32px rgba(0,0,0,.5)`).
- Blur translusen untuk sidebar/tab bar/sheet: `backdrop-filter: saturate(180%) blur(20px)`.
- Motion: 220ms `cubic-bezier(.25,.1,.25,1)`; muncul `opacity + translateY(4px)`.

## 5. Komponen Inti

| Komponen | Deskripsi |
|---|---|
| **Sidebar / Tab bar** | Desktop: sidebar 240px, item 36px, aktif = accent 16%. Mobile: tab bar bawah translusen, ikon 22px + label 11px |
| **Kartu grup (inset grouped)** | `--surface`, radius 14, baris 48px + separator rambut, tanpa border luar |
| **Prompt utama** | Input besar + tombol "Pilih berkas" sejajar, placeholder satu baris |
| **Kartu klip** | Thumbnail 9:16 radius atas, judul 15px semibold, meta 13px dim, aksi pill kecil |
| **Pill/badge** | Tinggi 22px, latar tinted 12–16%, teks 12px (ok/warn/info) |
| **Progress** | Bar 4px, track `--surface-3`, isi accent + label tahap 13px |
| **Sheet panel** | Desktop 460px dari kanan (blur + separator kiri); mobile memenuhi layar |
| **Toast** | Tengah bawah, kartu 14px, hilang otomatis 4.5s (error 9s) |
| **Segmented control** | Track `--fill`, thumb `--surface-3`, teks 13px — untuk ganti bahasa ID/EN |
| **Empty state** | Garis putus-putus + satu kalimat + satu aksi |

## 6. Ikon & Interaksi

- Ikon garis, 18–24px, mengikuti warna teks sekunder.
- Feedback tekan: `scale(0.985)` pada tombol utama; tanpa animasi dekoratif lain.
- Fokus keyboard: outline accent 2px, offset 2px.

## 7. Tata Letak

```
DESKTOP (≥820px)                    ANDROID
┌────────┬──────────────────────┐   ┌────────────────────┐
│ Sidebar│  Konten (maks 920px) │   │  AppBar ringkas    │
│ 240px  │  Judul besar         │   │  Kartu grup        │
│        │  Kartu grup          │   │  Daftar klip       │
│        │  Grid klip ≥200px    │   │                    │
│ segmented + versi              │   │                    │
└────────┴──────────────────────┘   ├────────────────────┤
                                     │  Tab bar (5 item)  │
                                     └────────────────────┘
```

## 8. Lokasi Token

| Platform | Berkas | Catatan |
|---|---|---|
| Web | `ui/tokens.css` | variabel `:root` |
| Web komponen | `ui/styles.css` | kartu grup, pill, sheet, segmented |
| Flutter | `android/app/lib/theme/tokens.dart` | `class Tokens` + `buildTheme()` |
| Flutter komponen | `android/app/lib/widgets/common.dart` | `SectionCard`, `Pill`, `ProgressStrip`, `ClipTile` |

> ⚠️ Mengubah warna/tipe wajib di kedua tempat sekaligus dan dicatat di CHANGELOG.
