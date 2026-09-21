"""Studio ZAI desktop shell: a pywebview window around the local server.

Falls back to the default browser when pywebview is unavailable.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser


def free_port(preferred: int = 8737) -> int:
    for candidate in range(preferred, preferred + 40):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", candidate))
            except OSError:
                continue
        return candidate
    raise RuntimeError("tidak ada port kosong yang tersedia")


def wait_ready(port: int, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.4)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.15)
    return False


def open_folder(path: str) -> None:
    if not path or not os.path.isdir(path):
        return
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class Bridge:
    """JS API exposed to the web UI (file picker, open folder)."""

    def pick_file(self) -> str:
        try:
            import webview

            window = webview.windows[0]
            result = window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=(
                    "Video/audio (*.mp4;*.mkv;*.mov;*.webm;*.avi;*.mp3;*.wav;*.m4a)",
                    "Semua berkas (*.*)",
                ),
            )
        except (ImportError, IndexError, AttributeError):
            return ""
        if not result:
            return ""
        return result[0] if isinstance(result, (list, tuple)) else str(result)

    def open_folder(self, path: str) -> bool:
        open_folder(path)
        return True

    def open_path(self, path: str) -> bool:
        open_folder(os.path.dirname(path))
        return True


def main() -> int:
    port = free_port()
    from studiozai.server import run as run_server

    threading.Thread(target=run_server, args=("127.0.0.1", port), daemon=True).start()
    url = f"http://127.0.0.1:{port}"
    if not wait_ready(port):
        print("Server gagal start.", file=sys.stderr)
        return 1

    try:
        import webview

        window = webview.create_window(
            "Studio ZAI",
            url,
            js_api=Bridge(),
            width=1280,
            height=880,
            min_size=(900, 620),
        )
        webview.start()
        return 0
    except ImportError:
        print(f"pywebview tidak terpasang - membuka {url} di browser.")
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
