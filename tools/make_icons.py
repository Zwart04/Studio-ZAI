"""Generate all app icons + README assets from the Studio ZAI logo.

Usage: python tools/make_icons.py "<path-to-logo.png>" "<repo-root>"
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (255, 255, 255, 255)          # clean white background for icons
BG_DARK = (11, 11, 13, 255)        # dark variant if ever needed


LOGO_PAD = 0.03  # padding di sekitar konten logo (fraksi sisi terpanjang) — biar icon besar & jelas


def load_logo(logo_path: Path) -> Image.Image:
    """Muat logo dan crop ke bounding box kontennya (buang padding transparan)."""
    src = Image.open(logo_path).convert("RGBA")
    bbox = src.split()[-1].getbbox()
    if bbox:
        src = src.crop(bbox)
    return src


def with_background(src: Image.Image, size: int, background=BG, scale: float = 0.82, radius_ratio: float = 0.0) -> Image.Image:
    """Logo centered on a background, scaled up (padding tipis) for safe zones."""
    canvas = Image.new("RGBA", (size, size), background)
    if radius_ratio > 0:
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        radius = int(size * radius_ratio)
        draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
        canvas.putalpha(mask)
    side = int(size * scale)
    logo = src.resize((side, side), Image.LANCZOS)
    offset = (size - side) // 2
    canvas.alpha_composite(logo, (offset, offset))
    return canvas


def fit_logo(src: Image.Image, box: int, pad_ratio: float = LOGO_PAD) -> Image.Image:
    """Resize konten logo (non-square ok) agar memenuhi kotak `box` dengan padding tipis.

    Tidak dipaksa square: konten 833x617 tetap 833x617 proporsional, lalu
    ditempatkan di tengah kanvas transparan bila pemanggil butuh kanvas square.
    """
    longest = max(src.size)
    target_longest = int(box * (1 - pad_ratio * 2))
    scale = target_longest / longest
    new_size = (max(1, int(src.size[0] * scale)), max(1, int(src.size[1] * scale)))
    return src.resize(new_size, Image.LANCZOS)


def save_square(src: Image.Image, path: Path, size: int, background=BG, scale: float = 0.82) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with_background(src, size, background, scale).convert("RGB").save(path, "PNG", optimize=True)


def save_round(src: Image.Image, path: Path, size: int, background=BG, scale: float = 0.78) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    base = with_background(src, size, background, scale)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(base, (0, 0), mask)
    out.save(path, "PNG", optimize=True)


def main() -> None:
    logo_path = Path(sys.argv[1])
    root = Path(sys.argv[2])
    src = load_logo(logo_path)

    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    # ---- shared assets (README + web UI) ----
    # logo.png: konten asli yang sudah di-crop (proporsional, BUKAN square paksa)
    logo_full = fit_logo(src, 512)
    logo_full.save(assets / "logo.png", "PNG", optimize=True)
    with_background(Image.open(logo_path).convert("RGBA"), 512, BG, 0.86).convert("RGB").save(
        assets / "logo-icon.png", "PNG", optimize=True
    )
    # banner: robot BESAR di kiri + teks judul di kanan (proporsional, tanpa ruang kosong raksasa)
    bw, bh = 1200, 380
    banner = Image.new("RGBA", (bw, bh), BG)
    mark = fit_logo(src, int(bh * 0.92), pad_ratio=0.04)
    mark_x = 70
    mark_y = (bh - mark.size[1]) // 2
    banner.alpha_composite(mark, (mark_x, mark_y))
    draw = ImageDraw.Draw(banner)
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 118)
        font_sub = ImageFont.truetype("arial.ttf", 46)
    except OSError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    tx = mark_x + mark.size[0] + 60
    title = "Studio ZAI"
    sub = "Auto Clip  •  Subtitle  •  Voiceover"
    tb = draw.textbbox((0, 0), title, font=font_title)
    sb = draw.textbbox((0, 0), sub, font=font_sub)
    total_h = (tb[3] - tb[1]) + 18 + (sb[3] - sb[1])
    ty = (bh - total_h) // 2
    draw.text((tx, ty), title, fill=(20, 20, 20, 255), font=font_title)
    draw.text((tx, ty + (tb[3] - tb[1]) + 18), sub, fill=(110, 110, 110, 255), font=font_sub)
    banner.convert("RGB").save(assets / "logo-banner.png", "PNG", optimize=True)

    # ---- Windows ICO (multi-size, white background, logo BESAR) ----
    ico_canvas = with_background(Image.new("RGBA", (10, 10), (0, 0, 0, 0)), 512, BG, 1.0)
    ico_mark = fit_logo(src, 512, pad_ratio=0.06)
    ico_canvas.alpha_composite(ico_mark, ((512 - ico_mark.size[0]) // 2, (512 - ico_mark.size[1]) // 2))
    ico_src = ico_canvas.convert("RGB")
    ico_dir = root / "desktop" / "packaging" / "icons"
    ico_dir.mkdir(parents=True, exist_ok=True)
    ico_src.save(ico_dir / "studiozai.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    ico_src.resize((256, 256), Image.LANCZOS).save(ico_dir / "studiozai.png", "PNG", optimize=True)

    # ---- Android mipmaps ----
    res = root / "android" / "app" / "android" / "app" / "src" / "main" / "res"
    sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    for bucket, px in sizes.items():
        mipmap = res / f"mipmap-{bucket}"
        mipmap.mkdir(parents=True, exist_ok=True)
        save_square(Image.open(logo_path).convert("RGBA"), mipmap / "ic_launcher.png", px, BG, 0.84)
        save_round(Image.open(logo_path).convert("RGBA"), mipmap / "ic_launcher_round.png", px, BG, 0.80)

    # adaptive icon (API 26+): background + foreground layers
    adaptive = res / "mipmap-anydpi-v26"
    adaptive.mkdir(parents=True, exist_ok=True)
    (adaptive / "ic_launcher.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '  <background android:drawable="@drawable/ic_launcher_background"/>\n'
        '  <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
        '  <monochrome android:drawable="@mipmap/ic_launcher_monochrome"/>\n'
        '</adaptive-icon>\n',
        encoding="utf-8",
    )
    (adaptive / "ic_launcher_round.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '  <background android:drawable="@drawable/ic_launcher_background"/>\n'
        '  <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
        '  <monochrome android:drawable="@mipmap/ic_launcher_monochrome"/>\n'
        '</adaptive-icon>\n',
        encoding="utf-8",
    )

    drawable = res / "drawable"
    drawable.mkdir(parents=True, exist_ok=True)
    # background: subtle vertical white gradient
    bg = Image.new("RGBA", (432, 432), BG)
    grad = ImageDraw.Draw(bg)
    for y in range(432):
        shade = 255 - int(12 * (y / 432))
        grad.line([(0, y), (432, y)], fill=(shade, shade, min(255, shade + 4), 255))
    bg.save(drawable / "ic_launcher_background.png", "PNG", optimize=True)

    # foreground: logo BESAR di safe zone (padding tipis, bukan 60% kecil)
    fg = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    mark = fit_logo(src, 432, pad_ratio=0.08)
    off_x = (432 - mark.size[0]) // 2
    off_y = (432 - mark.size[1]) // 2
    fg.alpha_composite(mark, (off_x, off_y))
    for bucket, px in sizes.items():
        (res / f"mipmap-{bucket}").mkdir(parents=True, exist_ok=True)
        fg.resize((px, px), Image.LANCZOS).save(res / f"mipmap-{bucket}" / "ic_launcher_foreground.png", "PNG", optimize=True)

    # monochrome (Android 13+ themed icon): alpha silhouette of the logo
    mono = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    logo = fit_logo(src, 432, pad_ratio=0.08)
    alpha = logo.split()[-1].point(lambda a: 255 if a > 32 else 0)
    solid = Image.new("RGBA", logo.size, (255, 255, 255, 255))
    solid.putalpha(alpha)
    mono.alpha_composite(solid, ((432 - logo.size[0]) // 2, (432 - logo.size[1]) // 2))
    for bucket, px in sizes.items():
        mono.resize((px, px), Image.LANCZOS).save(res / f"mipmap-{bucket}" / "ic_launcher_monochrome.png", "PNG", optimize=True)

    # splash screen background used by the default Flutter template
    (drawable / "launch_background.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<layer-list xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '  <item android:drawable="@color/launch_background"/>\n'
        '  <item>\n'
        '    <bitmap android:gravity="center" android:src="@mipmap/ic_launcher_foreground"/>\n'
        '  </item>\n'
        '</layer-list>\n',
        encoding="utf-8",
    )
    values = res / "values"
    values.mkdir(parents=True, exist_ok=True)
    (values / "colors.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<resources>\n'
        '  <color name="launch_background">#FFFFFF</color>\n'
        '</resources>\n',
        encoding="utf-8",
    )

    # ---- web UI favicon + logo ----
    ui_assets = root / "ui" / "assets"
    ui_assets.mkdir(parents=True, exist_ok=True)
    ui_canvas = with_background(Image.new("RGBA", (10, 10), (0, 0, 0, 0)), 180, BG, 1.0)
    ui_mark = fit_logo(src, 180, pad_ratio=0.06)
    ui_canvas.alpha_composite(ui_mark, ((180 - ui_mark.size[0]) // 2, (180 - ui_mark.size[1]) // 2))
    ui_canvas.convert("RGB").save(ui_assets / "icon-180.png", "PNG", optimize=True)
    logo_full.resize((96, 54), Image.LANCZOS).save(ui_assets / "logo.png", "PNG", optimize=True)
    ico_src.resize((64, 64), Image.LANCZOS).save(ui_assets / "favicon.png", "PNG", optimize=True)

    print("Ikon dibuat:")
    print(f"  - {ico_dir}\\studiozai.ico (multi-size)")
    print(f"  - {res} mipmaps + adaptive + monochrome")
    print(f"  - {assets} (logo.png, logo-icon.png, logo-banner.png)")
    print(f"  - {ui_assets} (favicon + logo)")


if __name__ == "__main__":
    main()
