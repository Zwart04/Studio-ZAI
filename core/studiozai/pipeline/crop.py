"""9:16 framing filters (center crop and blurred background)."""

from __future__ import annotations

from dataclasses import dataclass

TARGET_RATIO = 9 / 16
DEFAULT_HEIGHT = 1920
DEFAULT_WIDTH = 1080
MIN_SOURCE_HEIGHT = 720


def even(value: float) -> int:
    result = round(value)
    return result if result % 2 == 0 else result - 1


def target_size(
    src_w: int,
    src_h: int,
    ratio: float = TARGET_RATIO,
    max_height: int = DEFAULT_HEIGHT,
) -> tuple[int, int]:
    """Default vertical canvas (1080x1920); falls back to source height for tiny media."""
    if src_w <= 0 or src_h <= 0:
        return DEFAULT_WIDTH, DEFAULT_HEIGHT
    if src_h >= MIN_SOURCE_HEIGHT:
        height = min(max_height, DEFAULT_HEIGHT)
    else:
        height = even(src_h)
    return even(height * ratio), even(height)


@dataclass
class CropPlan:
    mode: str
    out_w: int
    out_h: int
    simple_chain: str | None = None
    complex_graph: str | None = None

    @property
    def is_complex(self) -> bool:
        return self.complex_graph is not None


def center_crop_chain(src_w: int, src_h: int, out_w: int, out_h: int) -> str:
    ratio = out_w / out_h
    crop_w = max(2, even(src_w))
    crop_h = max(2, even(src_h))
    if crop_w / crop_h > ratio:
        crop_w = max(2, even(crop_h * ratio))
    else:
        crop_h = max(2, even(crop_w / ratio))
    x = max(0, (src_w - crop_w) // 2)
    y = max(0, (src_h - crop_h) // 2)
    return f"crop={crop_w}:{crop_h}:{x}:{y},scale={out_w}:{out_h}:flags=lanczos,setsar=1"


def fit_chain(out_w: int, out_h: int) -> str:
    """Tampilkan SELURUH frame tanpa memotong; sisa kanvas diisi hitam.

    Dipakai kalau konten punya teks penting di tepi kiri/kanan yang hilang bila
    di-crop 9:16 (mis. rekaman layar, slide presentasi). Kebalikan dari
    `center_crop_chain` yang memang membuang sisi luar.
    """
    return (
        f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,"
        f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    )


def blur_background_graph(src_w: int, out_w: int, out_h: int, sigma: int = 24) -> str:
    return (
        f"split=2[bg][fg];"
        f"[bg]scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
        f"crop={out_w}:{out_h},gblur=sigma={sigma}[bgb];"
        f"[fg]scale={out_w}:{out_h}:force_original_aspect_ratio=decrease[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2[vout]"
    )


CANVAS_SHAPES = ("portrait", "original", "square", "landscape")
CANVAS_LABELS = {
    "portrait": "Potrait 9:16",
    "original": "Ukuran asli video",
    "square": "Kotak 1:1",
    "landscape": "Landscape 16:9",
}


def canvas_size(shape: str, src_w: int, src_h: int) -> tuple[int, int]:
    """Ukuran kanvas keluaran sesuai pilihan pengguna.

    - portrait  : 1080x1920 (default, TikTok/Reels/Shorts)
    - original  : mengikuti ukuran video sumber (dibatasi sisi terpanjang 1920)
    - square    : 1080x1080 (feed Instagram)
    - landscape : 1920x1080 (YouTube)
    Semua dimensi dibuat genap karena encoder H.264 mensyaratkannya.
    """
    if shape == "original":
        width = max(2, src_w - src_w % 2)
        height = max(2, src_h - src_h % 2)
        longest = max(width, height)
        if longest > 1920:
            ratio = 1920 / longest
            width = max(2, int(width * ratio) // 2 * 2)
            height = max(2, int(height * ratio) // 2 * 2)
        return width, height
    if shape == "square":
        return 1080, 1080
    if shape == "landscape":
        return 1920, 1080
    return target_size(src_w, src_h)


def plan(mode: str = "center", src_w: int = 1920, src_h: int = 1080, out_size: tuple[int, int] | None = None) -> CropPlan:
    """Build the ffmpeg plan for the requested framing mode."""
    mode = (mode or "center").lower()
    # "fit" dan "none" sama-sama menampilkan seluruh frame (letterbox), jadi tidak
    # ada teks di tepi yang terpotong. Dulu "none" men-stretch gambar hingga
    # gepeng, sekarang konsisten dengan "fit".
    if mode in {"none", "fit"}:
        out_w, out_h = (out_size or target_size(src_w, src_h))
        return CropPlan("fit", out_w, out_h, simple_chain=fit_chain(out_w, out_h))

    out_w, out_h = out_size or target_size(src_w, src_h)
    if mode == "blur":
        return CropPlan("blur", out_w, out_h, complex_graph=blur_background_graph(src_w, out_w, out_h))
    return CropPlan("center", out_w, out_h, simple_chain=center_crop_chain(src_w, src_h, out_w, out_h))
