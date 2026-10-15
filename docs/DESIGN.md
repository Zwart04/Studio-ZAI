# DESIGN — Studio ZAI
### Design System (CapCut-style workspace, minimalis)

> **EN TL;DR** — One design language for the web UI (desktop) and the Flutter app (Android), modelled on CapCut's dark editor: charcoal canvas (not pure black), layered surfaces, hairline separators, rounded cards, SF-like typography, 220 ms motion, one clear primary action per screen. **Colour policy: blue accent is only for the primary button, red only for delete — every selected/focused/progress state is neutral.** Tokens live in `ui/tokens.css` and `android/app/lib/theme/tokens.dart` — keep them in sync.

---

## 1. Prinsip

1. **Satu aksi utama per layar** — tidak ada dua tombol bersaing. Hanya `--action` (biru) yang menonjol; sisanya netral.
2. **Aksen terbatas** — biru = tombol utama, merah = tombol hapus. Tab aktif, seleksi, focus ring, progress, dan berita selalu netral (putih bertingkat).
3. **Tenang dan lapang** — latar arang, sedikit garis, tanpa gradient dekoratif, tanpa glow, tanpa shadow tebal.
4. **Hierarki tipografi jelas** — judul besar, label seksi kecil, isi 15px, keterangan 12–13px.
5. **Konsisten lintas platform** — kartu klip, progress tipis, sheet edit yang sama di web & Android.
6. **Aksesibel** — kontras teks ≥ 4.5:1, target sentuh ≥ 44px, focus ring kontras tinggi.

## 2. Token Warna (palet arang / CapCut-style)

| Token | Nilai | Pemakaian |
|---|---|---|
| `--bg` | `#141417` | Latar aplikasi |
| `--bg-elevated` | `#1A1A1E` | Sidebar / tab bar |
| `--surface` | `#202024` | Kartu |
| `--surface-2` | `#2A2A2F` | Input, elemen di dalam kartu |
| `--surface-3` | `#36363C` | Hover / tombol sekunder |
| `--separator` | `rgba(255,255,255,.08)` | Garis rambut 1px |
| `--separator-strong` | `rgba(255,255,255,.15)` | Batas kartu/pilihan |
| `--fill` | `rgba(120,120,128,.26)` | Tombol sekunder, chip |
| `--sel` / `--sel-strong` | `rgba(255,255,255,.10)` / `.17` | Seleksi, tab aktif, chip terpilih |
| `--ring` | `rgba(255,255,255,.72)` | Focus ring, garis terpilih, playhead |
| `--text` | `#F5F5F7` | Teks utama |
| `--text-2` | `#E8E8ED` | Teks sekunder |
| `--text-dim` / `--text-dim-2` | `#A5A5AE` | Keterangan / placeholder |
| `--accent` | `#5AA9FF` | Tautan & sorotan biru (teks di atas gelap) |
| `--action` / `--accent-press` | `#1F6FE0` / `#1A5FC4` | **Hanya** latar tombol utama |
| `--green` | `#34C759` | Selesai/aktif (status) |
| `--orange` | `#FF9F0A` | Peringatan (draft, model eksperimental) |
| `--red` | `#FF8478` | **Hanya** tombol hapus & error |

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
| **Sidebar / Tab bar** | Desktop: sidebar 240px, item 44px, aktif = `--sel-strong` + garis bawah `--ring` (netral, bukan biru). Mobile: tab bar bawah, ikon 22px + label 11px |
| **Kartu grup** | `--surface`, radius 16 (beranda 20), baris 44–48px + separator rambut |
| **Prompt utama** | Input besar + tombol "Pilih berkas" sejajar, placeholder satu baris |
| **Beranda** | Kartu sumber tunggal; bagian pengaturan dibagi **dua wadah kolom** (`.home-col`) di JS, bukan grid baris — supaya tinggi bagian yang berbeda tidak meninggalkan lubang kosong. Bagian tinggi (mis. "Kinerja laptop") dilipat jadi `<details>` |
| **Kartu klip** | Thumbnail 9:16 radius atas, judul 15px semibold, meta 13px dim, aksi pill kecil |
| **Pill/badge** | Tinggi 22px, latar tinted netral, teks 12px (ok/warn) |
| **Progress** | Bar 4px, track `--surface-3`, isi **netral** `--ring` + label tahap 13px |
| **Tombol hapus** | Merah `--red` di atas latar `rgba(255,77,68,.16)` — satu-satunya tempat merah selain toast error |
| **Sheet panel** | Desktop 460px dari kanan (blur + separator kiri); mobile memenuhi layar |
| **Toast** | Tengah bawah, kartu 14px, hilang otomatis 4.5s (error 9s) |
| **Segmented control** | Track `--fill`, thumb `--surface-3`, teks 13px — untuk ganti bahasa ID/EN |
| **Empty state** | Garis putus-putus + satu kalimat + satu aksi |

## 6. Ikon & Interaksi

- Ikon garis, 18–24px, mengikuti warna teks sekunder.
- Feedback tekan: `scale(0.985)` pada tombol utama; tanpa animasi dekoratif lain.
- Fokus keyboard: outline `--ring` 2px, offset 2–3px (putih, kontras tinggi — bukan biru).

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
