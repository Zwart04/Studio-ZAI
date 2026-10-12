"""Studio ZAI desktop shell: a native window around the local server.

The frozen EXE always opens its own window (pywebview EdgeChromium).
A real browser is only used when the user explicitly runs `serve`.
All startup diagnostics go to <data dir>/launcher.log.

Exit behaviour matters for users: closing the window must end the process,
must not leave ffmpeg children behind (they lock clip files and used to make
the install folder impossible to delete), and launching the app twice must
reuse the running instance instead of spawning a second server.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path

try:  # paket engine bisa belum terpasang saat launcher dijalankan dari sumber
    from studiozai.utils import proc
except ImportError:  # pragma: no cover
    proc = None


def data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    directory = base / "StudioZAI"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


LOG_FILE = data_dir() / "launcher.log"
INSTANCE_FILE = data_dir() / "instance.json"


def log(message: str) -> None:
    try:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"[{stamp}] {message}\n")
    except OSError:
        pass


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


def port_open(port: int, timeout: float = 0.4) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_ready(port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_open(port):
            return True
        time.sleep(0.15)
    return False


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            handle = kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
            if not handle:
                return False
            try:
                code = ctypes.c_ulong()
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                    return False
                return code.value == 259  # STILL_ACTIVE
            finally:
                kernel32.CloseHandle(handle)
        except Exception:  # noqa: BLE001 - anggap mati bila tidak bisa dipastikan
            return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def live_instance() -> str | None:
    """URL instance Studio ZAI yang masih berjalan, kalau ada."""
    try:
        data = json.loads(INSTANCE_FILE.read_text(encoding="utf-8"))
        pid = int(data.get("pid", 0))
        port = int(data.get("port", 0))
    except (OSError, ValueError, TypeError):
        return None
    if pid and port and process_alive(pid) and port_open(port):
        return f"http://127.0.0.1:{port}"
    return None


def remember_instance(port: int) -> None:
    try:
        INSTANCE_FILE.write_text(
            json.dumps({"pid": os.getpid(), "port": port, "started": time.time()}),
            encoding="utf-8",
        )
    except OSError:
        pass


def forget_instance() -> None:
    try:
        INSTANCE_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def open_folder(path: str) -> None:
    if not path or not os.path.isdir(path):
        return
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def serve(port: int) -> None:
    """Run the FastAPI server, logging any startup failure."""
    try:
        log(f"server: importing (frozen={getattr(sys, 'frozen', False)})")
        from studiozai.server import run as run_server

        log(f"server: starting uvicorn on 127.0.0.1:{port}")
        run_server(host="127.0.0.1", port=port)
        log("server: uvicorn returned")
    except Exception:  # noqa: BLE001 - diagnostics are the whole point here
        log("server: FAILED\n" + traceback.format_exc())


def find_chrome_exe() -> str | None:
    """Chrome/Edge executable for --app fallback mode."""
    candidates = [
        shutil.which("chrome"),
        shutil.which("chrome.exe"),
        shutil.which("msedge"),
        shutil.which("msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def open_app_window(url: str, profile_dir: Path) -> int:
    """Buka URL sebagai jendela aplikasi Chrome/Edge (--app, tanpa tab browser).

    Dipakai HANYA jika pywebview gagal total. Fungsi ini menunggu jendela
    ditutup lalu keluar — versi sebelumnya loop selamanya sehingga proses EXE
    tetap hidup (dan mengunci folder) walau jendela sudah ditutup.
    """
    chrome = find_chrome_exe()
    if not chrome:
        log("app-window: tidak ada Chrome/Edge, membuka browser biasa")
        webbrowser.open(url)
        return 0
    profile_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        chrome,
        f"--app={url}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--disable-features=Translate",
    ]
    log(f"app-window: {chrome} --app {url}")
    try:
        child = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        log("app-window: gagal start, membuka browser biasa")
        webbrowser.open(url)
        return 0
    try:
        child.wait()
    except KeyboardInterrupt:
        child.terminate()
    log("app-window: jendela ditutup")
    return 0


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
        except (ImportError, IndexError, AttributeError) as exc:
            log(f"bridge.pick_file gagal: {exc!r}")
            return ""
        if not result:
            return ""
        return result[0] if isinstance(result, (list, tuple)) else str(result)

    def open_folder(self, path: str) -> bool:
        open_folder(path)
        return True

    def open_external(self, url: str) -> bool:
        """Buka tautan di browser luar (di jendela EdgeChromium, href biasa
        justru membuat jendela sistem baru)."""
        try:
            import webbrowser

            webbrowser.open(url)
            return True
        except Exception as exc:  # noqa: BLE001
            log(f"bridge.open_external gagal: {exc!r}")
            return False

    def open_path(self, path: str) -> bool:
        open_folder(os.path.dirname(path))
        return True

    def app_log(self, message: str) -> bool:
        log(f"ui: {message}")
        return True


def open_window(url: str) -> int:
    """Tampilkan UI: pywebview dulu, lalu jendela aplikasi Chrome/Edge."""
    try:
        import webview

        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.create_window(
            "Studio ZAI",
            url,
            js_api=Bridge(),
            width=1280,
            height=880,
            min_size=(900, 620),
        )
        log("launcher: membuka jendela (pywebview)")
        if sys.platform == "win32":
            # Backend winforms butuh .NET; edgechromium hanya butuh WebView2.
            # Catatan: 'gui' adalah argumen webview.start(), bukan create_window()
            # - kesalahan ini dulu membuat jendela native selalu gagal dan
            # aplikasi jatuh ke jendela Chrome.
            try:
                webview.start(gui="edgechromium")
            except TypeError:
                webview.start(gui="cef")
        else:
            webview.start()
        log("launcher: jendela ditutup")
        return 0
    except ImportError:
        log("launcher: pywebview tidak ada, memakai jendela aplikasi Chrome/Edge")
        return open_app_window(url, data_dir() / "webprofile")
    except Exception:  # noqa: BLE001 - fallback apa pun lebih baik daripada gagal
        log("launcher: webview gagal\n" + traceback.format_exc())
        return open_app_window(url, data_dir() / "webprofile")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    # Mode CLI: teruskan perintah ke engine studiozai (doctor, serve, download, ...).
    # Berguna untuk debugging EXE tanpa GUI: `StudioZAI.exe doctor`.
    if args and args[0] in {
        "doctor",
        "serve",
        "download",
        "probe",
        "transcribe",
        "clip",
        "tts",
        "clone",
        "models",
        "projects",
        "--help",
        "-h",
        "--version",
    }:
        from studiozai.cli import main as cli_main

        return int(cli_main(args) or 0)

    log("=== Studio ZAI launcher start ===")

    existing = live_instance()
    if existing:
        log(f"launcher: instance sudah berjalan di {existing}, memakai yang itu")
        return open_window(existing)

    port = free_port()
    remember_instance(port)
    log(f"launcher: port {port}")
    threading.Thread(target=serve, args=(port,), daemon=True).start()
    url = f"http://127.0.0.1:{port}"

    try:
        if not wait_ready(port):
            log("launcher: server tidak siap dalam 60 detik")
            return open_app_window(url, data_dir() / "webprofile")
        log("launcher: server siap")
        return open_window(url)
    finally:
        killed = proc.terminate_all() if proc is not None else 0
        if killed:
            log(f"launcher: menghentikan {killed} proses anak (ffmpeg)")
        forget_instance()
        log("launcher: keluar")


if __name__ == "__main__":
    raise SystemExit(main())
