"""Capture README media from the isolated, synthetic demo workspace.

Start `tools/demo_workspace.py --serve` first. This script only controls its
own Playwright browser; it never loads the user's Studio ZAI projects.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps
from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
BASE = "http://127.0.0.1:8752"


def ready(page: Page) -> None:
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(500)
    page.evaluate("() => { const el = document.getElementById('wizardOverlay'); if (el) el.hidden = true; }")


def navigate(page: Page, name: str) -> None:
    page.locator(f'#nav button[data-page="{name}"]').click()
    page.locator(f"#page-{name}.active").wait_for()
    page.wait_for_timeout(500)


def capture(page: Page, name: str, *, full: bool = False) -> None:
    target = OUT / f"{name}.jpg"
    page.screenshot(path=str(target), type="jpeg", quality=88, full_page=full)
    print(f"saved {target.relative_to(ROOT)}", flush=True)


def editor(page: Page) -> None:
    navigate(page, "projects")
    page.locator("#projectList [data-open]").first.click()
    page.locator("#clipGrid [data-edit]").first.click()
    page.locator(".editor-overlay #tlVideo").wait_for()
    page.wait_for_timeout(8000)  # allow the automatic draft render to settle
    try:
        page.wait_for_function(
            "() => !document.querySelector('#tlPreviewStatus')?.textContent?.trim()",
            timeout=45000,
        )
    except Exception:
        # The source video remains playable while a draft render is underway.
        pass
    page.locator(".editor-overlay #tlVideo").evaluate(
        "el => {el.pause(); if (el.readyState > 0) el.currentTime = Math.min(3, Math.max(0, el.duration - 0.2));}"
    )
    page.wait_for_function(
        "() => { const el = document.querySelector('#tlVideo'); return el && el.readyState >= 2 && !el.seeking; }",
        timeout=20000,
    )
    page.wait_for_timeout(800)


def make_gif() -> None:
    names = ["01-home", "04-editor", "03-voice", "07-images"]
    frames = []
    for name in names:
        with Image.open(OUT / f"{name}.jpg") as image:
            # The same top-left viewport is used for every frame so the tour
            # shows real, reproducible UI states rather than stitched mockups.
            frame = ImageOps.fit(image.convert("RGB"), (960, 600), method=Image.Resampling.LANCZOS,
                                 centering=(0, 0))
            frames.append(frame.quantize(colors=96, method=Image.Quantize.FASTOCTREE))
    target = OUT / "studio-zai-demo.gif"
    frames[0].save(target, save_all=True, append_images=frames[1:], loop=0,
                   duration=[2000, 2100, 1900, 2100], optimize=True)
    print(f"saved {target.relative_to(ROOT)}", flush=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        ready(desktop)
        capture(desktop, "01-home")
        navigate(desktop, "models")
        capture(desktop, "02-models")
        navigate(desktop, "voice")
        capture(desktop, "03-voice")
        navigate(desktop, "images")
        capture(desktop, "07-images")
        navigate(desktop, "settings")
        capture(desktop, "08-settings")
        editor(desktop)
        capture(desktop, "04-editor")

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        ready(mobile)
        capture(mobile, "05-mobile-home")
        editor(mobile)
        capture(mobile, "09-mobile-editor")
        brand = browser.new_page(viewport={"width": 1200, "height": 280})
        brand.goto((ROOT / "assets" / "brand-banner.svg").as_uri())
        brand.screenshot(path=str(ROOT / "build" / "brand-banner-preview.png"))
        browser.close()
    make_gif()


if __name__ == "__main__":
    main()
