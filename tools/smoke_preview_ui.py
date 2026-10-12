"""Browser smoke test for the editor preview panel (aspect, loading, error).

Runs a real Chromium against an isolated synthetic workspace and proves the
three preview guarantees that used to be broken:

1. The preview frame always honours the canvas ratio the user picked
   (portrait / square / landscape / original) instead of distorting through
   independent min-width and min-height clamps.
2. The YouTube embed keeps its own 16:9 box and is *contained* inside that
   canvas frame (regression: the embed used to render at the browser default
   300x150 because no CSS targeted `.output-frame iframe`).
3. Loading and error are visually distinct: loading = veil + spinner +
   "Memperbarui pratinjau...", error = red pill + "Pratinjau belum
   diperbarui: ...". Neither ever looks like the other.

Run:  python tools/smoke_preview_ui.py
Artefacts (including a screenshot per stage) land in build/preview-ui-smoke-*.

Requires playwright + uvicorn, the same tooling as tools/smoke_batch_ui.py.
"""
from __future__ import annotations

import json
import logging
import re
import socket
import threading
import time
import uuid
from pathlib import Path

import uvicorn
from playwright.sync_api import Page, expect, sync_playwright

from studiozai import config, projects, server
from studiozai.pipeline import timeline
from studiozai.utils import ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / f"preview-ui-smoke-{uuid.uuid4().hex[:8]}"

# uvicorn mencatat ConnectionResetError tiap kali <video> diganti di tengah
# streaming media. Itu perilaku normal, bukan kegagalan — jangan membuang-buang
# sinyal asli di tengah ribut traceback.
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

# Rasio yang diminta pengguna lewat pemilih kanvas, vs rasio yang harus
# dihasilkan bingkai pratinjau. original mengikuti sumber 1280x720.
CANVAS_RATIO = {
    "portrait": 9 / 16,
    "square": 1.0,
    "landscape": 16 / 9,
    "original": 1280 / 720,
}

LOADING_TEXT = "Memperbarui pratinjau…"
PREPARE_TEXT = "Menyiapkan pratinjau…"
ERROR_PREFIX = "Pratinjau belum diperbarui"

# Diisi main() setelah uvicorn memilih port bebas.
BASE_URL = ""


def assert_ratio(box: dict, expected: float, label: str, tolerance: float = 0.03) -> float:
    """Bingkai harus berbanding expected; kesalahan lebih dari 3% dianggap pecah."""
    measured = box["width"] / box["height"]
    assert abs(measured / expected - 1) <= tolerance, (
        f"{label}: rasio seharusnya {expected:.4f}, terukur {measured:.4f} "
        f"({box['width']:.1f}x{box['height']:.1f})"
    )
    return measured


def goto_home(page: Page) -> None:
    """Muat ulang halaman.

    `renderProjects()` langsung kembali ke tampilan detail selama
    `state.project` masih terisi, sehingga daftar proyek tidak pernah muncul
    lagi tanpa memuat ulang. Muat ulang mereset state dan membuat kedua proyek
    tampil di daftar.
    """
    page.goto(BASE_URL, wait_until="networkidle")
    page.evaluate("() => { const el = document.getElementById('wizardOverlay'); if (el) el.hidden = true; }")


def open_editor(page: Page, project_id: str) -> None:
    page.locator('#nav [data-page="projects"]').click()
    page.locator(f'#projectList [data-open="{project_id}"]').click()
    page.locator("#clipGrid [data-edit]").first.click()
    expect(page.locator(".editor-overlay #tlStage .output-frame")).to_be_visible(timeout=15000)


def set_canvas(page: Page, value: str) -> None:
    page.locator('[data-inspector="clip"]').click()
    page.locator("#tlCanvas").select_option(value)
    expect(page.locator("#tlCanvas")).to_have_value(value)


def frame_box(page: Page) -> dict:
    box = page.locator("#tlStage .output-frame").bounding_box()
    assert box, "bingkai pratinjau tidak punya kotak tata letak"
    return box


def assert_frame_uses_stage(page: Page) -> None:
    """Bingkai harus memaksimalkan ruang stage di SATU sisi.

    `fitStage()` memakai `width = min(stageW - 16, (stageH - 45) * ratio)`,
    jadi bingkai yang sehat pasti mentok di lebar ATAU tinggi stage. Kalau tidak,
    bingkai menyusut sendiri — itulah keluhan "pratinjau salah ukuran".
    """
    stage = page.locator("#tlStage").bounding_box()
    frame = frame_box(page)
    assert stage, "stage pratinjau tidak punya kotak tata letak"
    avail_w = max(40, stage["width"] - 2 - 16)   # clientWidth = border-box - border
    avail_h = max(40, stage["height"] - 2 - 45)  # 45 = cadangan lencana + baris status
    fills_w = abs(frame["width"] - avail_w) <= 3
    fills_h = abs(frame["height"] - avail_h) <= 3
    assert fills_w or fills_h, (
        f"bingkai {frame['width']:.0f}x{frame['height']:.0f} tidak memaksimalkan "
        f"ruang stage {stage['width']:.0f}x{stage['height']:.0f} "
        f"(tersedia {avail_w:.0f}x{avail_h:.0f})"
    )
    print(
        f"    stage {stage['width']:.0f}x{stage['height']:.0f} -> "
        f"bingkai {frame['width']:.0f}x{frame['height']:.0f} "
        f"({'lebar penuh' if fills_w else 'tinggi penuh'})",
        flush=True,
    )


def wait_until_settled(page: Page, timeout: int = 25000) -> None:
    """Tunggu sampai tidak ada veil loading dan baris status kosong."""
    page.wait_for_function(
        """() => {
            const veil = document.querySelector('#tlPreviewVeil');
            const status = document.querySelector('#tlPreviewStatus');
            if (!veil || !status) return false;
            return !veil.classList.contains('show') && status.textContent.trim() === '';
        }""",
        timeout=timeout,
    )


def check_frame_ratio(page: Page, canvas: str) -> None:
    set_canvas(page, canvas)
    measured = assert_ratio(frame_box(page), CANVAS_RATIO[canvas], f"bingkai kanvas {canvas}")
    assert_frame_uses_stage(page)
    print(f"  kanvas {canvas:<9} rasio {measured:.4f} (target {CANVAS_RATIO[canvas]:.4f})", flush=True)


def check_loading_state(page: Page, shot: Path) -> None:
    """Saat render draf berjalan: veil + spinner tampil dan teks status = loading."""
    expect(page.locator("#tlPreviewVeil")).to_have_class(re.compile(r"\bshow\b"), timeout=12000)
    expect(page.locator("#tlPreviewStatus")).to_have_class(re.compile(r"\bis-loading\b"), timeout=4000)
    expect(page.locator("#tlPreviewStatus")).to_have_text(LOADING_TEXT, timeout=4000)
    page.screenshot(path=str(shot))
    wait_until_settled(page)
    expect(page.locator("#tlPreviewVeil")).not_to_have_class(re.compile(r"\bshow\b"))
    expect(page.locator("#tlPreviewStatus")).to_have_text("")


def check_error_state(page: Page, canvas: str, shot: Path) -> None:
    """Kegagalan harus tampil merah + teks berbeda, bukan status loading."""
    set_canvas(page, canvas)
    expect(page.locator("#tlPreviewStatus")).to_have_class(re.compile(r"\bis-error\b"), timeout=15000)
    expect(page.locator("#tlPreviewStatus")).to_contain_text(ERROR_PREFIX, timeout=4000)
    # Veil loading tidak boleh ikut tampil saat gagal.
    expect(page.locator("#tlPreviewVeil")).not_to_have_class(re.compile(r"\bshow\b"), timeout=500)
    page.screenshot(path=str(shot))
    print(f"  status gagal: {(page.locator('#tlPreviewStatus').text_content() or '').strip()}", flush=True)


def check_embed(page: Page, canvas: str) -> None:
    """Embed YouTube: bingkai mengikuti kanvas, embed tetap 16:9 dan muat penuh."""
    set_canvas(page, canvas)
    frame = frame_box(page)
    assert_ratio(frame, CANVAS_RATIO[canvas], f"bingkai embed kanvas {canvas}")

    embed = page.locator("#tlStage .yt-embed").bounding_box()
    assert embed, "elemen .yt-embed tidak ada — cabang pratinjau YouTube belum dipakai"
    assert_ratio(embed, 16 / 9, "embed YouTube", tolerance=0.04)

    # Regresi: tanpa CSS untuk `.output-frame iframe`, embed tinggal 300x150
    # tersangkut di pojok bingkai yang jauh lebih besar.
    iframe = page.locator("#tlStage .yt-embed iframe").bounding_box()
    assert iframe, "iframe YouTube tidak punya kotak tata letak"
    assert abs(iframe["width"] - embed["width"]) <= 1 and abs(iframe["height"] - embed["height"]) <= 1, (
        f"iframe {iframe['width']:.0f}x{iframe['height']:.0f} tidak mengisi embed "
        f"{embed['width']:.0f}x{embed['height']:.0f} (CSS `.output-frame iframe` hilang?)"
    )
    assert embed["width"] >= frame["width"] - 1, (
        f"embed hanya selebar {embed['width']:.0f}px dari bingkai {frame['width']:.0f}px — "
        "embed YouTube tidak membentang mengikuti kanvas"
    )
    assert_frame_uses_stage(page)

    # Embed tidak boleh keluar dari bingkai kanvas.
    overflow = (embed["x"] - frame["x"] < -1 or embed["y"] - frame["y"] < -1
                or (embed["x"] + embed["width"]) - (frame["x"] + frame["width"]) > 1
                or (embed["y"] + embed["height"]) - (frame["y"] + frame["height"]) > 1)
    assert not overflow, f"embed {embed} tumpah keluar bingkai {frame}"
    print(
        f"  embed kanvas {canvas:<9} bingkai {frame['width']:.0f}x{frame['height']:.0f} | "
        f"embed {embed['width']:.0f}x{embed['height']:.0f}",
        flush=True,
    )


def main() -> None:
    OUT.mkdir(parents=True)
    config._base_dir = lambda: OUT
    # Katalog penyedia hanya sebagai fixture: tanpa kunci atau inferensi awan.
    server.ai.request = lambda *args, **kwargs: {"data": [{"id": "fixture-flash-2"}]}
    config.save_settings({"setup_version": 2, "setup_done": True, "lang": "id"})

    # --- proyek lokal: sumber video nyata, pratinjau render berjalan sungguhan.
    local = projects.Project.create("Preview panel - sumber lokal")
    local.source_dir.mkdir()
    source = local.source_dir / "source.mp4"
    result = ffmpeg.run_ffmpeg([
        "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=15:duration=4",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(source),
    ])
    assert result.ok, result.stderr
    local.source, local.width, local.height, local.duration = str(source), 1280, 720, 4
    local_clip = projects.Clip(0, 0, 3, title="Klip lokal", canvas="original", score=0.8)
    local_clip.captions = [{"start": 0, "end": 1, "text": "Subtitle uji"}]
    local_clip.timeline = timeline.default_timeline(0, 3, str(source), canvas="original")
    local.clips = [local_clip]
    local.save()

    # --- proyek online: hanya URL YouTube, belum ada berkas sama sekali.
    online = projects.Project.create("Preview panel - online")
    online.online = True
    online.source_url = "https://youtu.be/abcdefghijk"
    online.width, online.height, online.duration = 1280, 720, 60
    online_clip = projects.Clip(0, 0, 12, title="Klip online", canvas="portrait", score=0.7)
    online_clip.captions = [{"start": 0, "end": 1, "text": "Subtitle uji"}]
    online.clips = [online_clip]
    online.save()

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    app_server = uvicorn.Server(uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=app_server.run, daemon=True).start()
    deadline = time.monotonic() + 15
    while not app_server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    assert app_server.started

    global BASE_URL
    BASE_URL = f"http://127.0.0.1:{port}"
    base = BASE_URL
    page_errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 980})
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            # Jangan pernah menyentuh jaringan: embed YouTube diblokir agar smoke
            # selalu offline dan deterministik.
            page.route(re.compile(r"https?://[^/]*\.(?:youtube|googlevideo|ytimg|ggpht)\..*"),
                       lambda route: route.abort())
            # Endpoint pratinjau proyek online diblokir agar tidak mengunduh media.
            page.route(
                re.compile(rf"{re.escape(base)}/api/projects/{re.escape(online.id)}/clips/\d+/preview$"),
                lambda route: route.fulfill(
                    status=409, content_type="application/json",
                    body=json.dumps({"detail": "media belum tersedia"}),
                ),
            )

            goto_home(page)

            print("Proyek lokal: status loading vs siap", flush=True)
            open_editor(page, local.id)
            check_loading_state(page, OUT / "preview-loading.png")
            wait_until_settled(page)
            print("  loading dicek: veil + spinner + teks memuat, lalu bersih kembali", flush=True)

            print("Proyek lokal: rasio bingkai per pilihan kanvas", flush=True)
            for canvas in CANVAS_RATIO:
                check_frame_ratio(page, canvas)
            page.screenshot(path=str(OUT / "preview-ratio.png"))

            print("Proyek lokal: status gagal render", flush=True)
            # Endpoint preview dibuat gagal supaya cabang error deterministik.
            page.route(
                re.compile(rf"{re.escape(base)}/api/projects/{re.escape(local.id)}/clips/\d+/preview$"),
                lambda route: route.fulfill(
                    status=500, content_type="application/json",
                    body=json.dumps({"detail": "uji kegagalan pratinjau"}),
                ),
            )
            check_error_state(page, "portrait", OUT / "preview-error.png")
            page.unroute(re.compile(rf"{re.escape(base)}/api/projects/{re.escape(local.id)}/clips/\d+/preview$"))

            print("Proyek online: embed YouTube di dalam bingkai kanvas", flush=True)
            page.locator(".editor-overlay [data-tl='close']").click()
            expect(page.locator(".editor-overlay")).to_be_hidden()
            # `state.project` masih terisi, jadi daftar proyek tidak akan muncul
            # kembali tanpa memuat ulang halaman.
            goto_home(page)
            open_editor(page, online.id)
            expect(page.locator("#tlStage .yt-embed iframe")).to_be_visible(timeout=15000)
            for canvas in ("portrait", "square", "landscape"):
                check_embed(page, canvas)
            page.screenshot(path=str(OUT / "preview-embed.png"))

            assert not page_errors, f"error JavaScript di halaman: {page_errors}"
            browser.close()
    finally:
        app_server.should_exit = True

    print(f"\nPreview panel smoke passed. Artefact di {OUT}", flush=True)


if __name__ == "__main__":
    main()
