"""Exercise the voice picker and browser file upload against the isolated demo server."""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "build" / "readme-demo-v18-release"
SAMPLE = next((DEMO / "projects").glob("*/source/narration.wav"))


def main() -> None:
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:8752", wait_until="networkidle")
        page.locator('#nav button[data-page="voice"]').click()
        page.wait_for_function("() => document.querySelector('#ttsVoice')?.value === 'supertonic-3-int8:0'")
        assert page.locator("#ttsVoice").input_value() == "supertonic-3-int8:0"
        assert "OpenRAIL-M" in page.locator("#ttsModelHint").inner_text()

        page.locator("#cloneLang").select_option("en")
        assert page.locator("#cloneModel").input_value() == "zipvoice-zh-en"
        assert page.locator("#cloneReferenceWrap").is_visible()
        page.locator("#cloneFileInput").set_input_files(str(SAMPLE))
        page.wait_for_function("() => document.querySelector('#cloneSampleName')?.textContent === 'narration.wav'")
        uploaded = page.locator("#cloneSample").input_value()
        assert Path(uploaded).is_file()
        assert page.locator("#cloneSamplePlayer").is_visible()
        assert not errors, errors
        browser.close()
    print("Voice UI smoke passed: model, language, license, audio upload, preview")


if __name__ == "__main__":
    main()
