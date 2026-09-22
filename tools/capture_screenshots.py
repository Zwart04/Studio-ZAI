"""Capture professional screenshots of the Studio ZAI web UI for the README."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8737"

SHOTS = [
    # (name, url-hash-or-action, width, height, extra-wait)
    ("01-home", None, 1440, 900, 1.5),
    ("02-models", "models", 1440, 900, 2.0),
    ("03-voice", "voice", 1440, 900, 1.5),
    ("04-editor", "editor", 1440, 900, 1.5),
]


def dismiss_wizard(page):
    try:
        page.evaluate(
            "() => { const o = document.getElementById('wizardOverlay'); if (o) o.hidden = true; }"
        )
    except Exception:
        pass


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(1500)
        dismiss_wizard(page)

        for name, action, width, height, wait in SHOTS:
            page.set_viewport_size({"width": width, "height": height})
            if action == "models":
                page.click('button[data-page="models"]')
            elif action == "voice":
                page.click('button[data-page="voice"]')
            elif action == "editor":
                page.click('button[data-page="models"]')
            page.wait_for_timeout(int(wait * 1000))
            dismiss_wizard(page)
            page.screenshot(path=str(OUT / f"{name}.png"))
            print("saved", OUT / f"{name}.png")

        # Mobile view of home
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(1500)
        dismiss_wizard(page)
        page.screenshot(path=str(OUT / "05-mobile-home.png"))
        print("saved", OUT / "05-mobile-home.png")
        browser.close()


if __name__ == "__main__":
    main()
