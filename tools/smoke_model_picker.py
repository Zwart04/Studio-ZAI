"""Exercise provider/key/model UX with fixture catalog and isolated app data."""
import socket
import threading
import time
import uuid
from pathlib import Path

import uvicorn
from playwright.sync_api import expect, sync_playwright
from studiozai import config, credentials, server


def main():
    out = Path(__file__).resolve().parents[1] / 'build' / f'model-ui-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True)
    config._base_dir = lambda: out
    config.save_settings({'setup_version': 2, 'setup_done': True, 'lang': 'id'})
    server.ai.request = lambda *args, **kwargs: {'data': [{'id': 'fixture-flash-2'}, {'id': 'fixture-pro-2'}]}
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    app = uvicorn.Server(uvicorn.Config(server.app, host='127.0.0.1', port=port, log_level='error'))
    worker = threading.Thread(target=app.run, daemon=True)
    worker.start()
    for _ in range(150):
        if app.started: break
        time.sleep(.1)
    assert app.started
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1440, 'height': 980})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{port}', wait_until='networkidle')
            expect(page.locator('#homeProjects .empty')).to_have_count(1)
            page.locator('#nav [data-page="settings"]').click()
            card = page.locator('.ai-profile[data-kind="ai"]')
            card.locator('[data-ai="ai_provider"]').select_option('groq')
            card.locator('[data-ai="ai_api_key"]').fill('fixture-only')
            card.locator('[data-model="ai"]').focus()
            expect(card.locator('[data-model="ai"]')).to_have_value('fixture-flash-2')
            page.locator('#saveAiSettings').click()
            expect(card.locator('[data-ai="ai_api_key"]')).to_have_value('')
            expect(card.locator('[data-model="ai"]')).to_have_value('fixture-flash-2')
            expect(card.locator('[data-ai="ai_model"]')).to_be_hidden()
            assert credentials.read()['ai_api_key'] == 'fixture-only'
            assert 'fixture-only' not in (out / 'credentials.json').read_text()
            page.screenshot(path=str(out / 'provider-desktop.png'), full_page=True)
            page.set_viewport_size({'width': 393, 'height': 852})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out / 'provider-mobile.png'), full_page=True)
            card.locator('[data-ai="ai_provider"]').select_option('openai')
            page.locator('#saveAiSettings').click()
            expect(card.locator('[data-ai="ai_api_key"]')).to_have_value('')
            expect(card.locator('[data-model="ai"]')).to_have_value('auto')
            assert not credentials.read()['ai_api_key']
            assert not errors, errors
            browser.close()
        print(f'Model UI, saved selection, key removal and responsive layout passed: {out}')
    finally:
        app.should_exit = True
        worker.join(timeout=10)


if __name__ == '__main__':
    main()
