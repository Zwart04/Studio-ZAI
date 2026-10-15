"""An owned loopback inference process for explicitly selected existing GGUF files."""
import atexit
import secrets
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import ai, config, resources
from .jobs import inference_slot
from .utils import proc

_LOCK = threading.RLock()
_CHILD = None
_MODEL = None
_KEY = ""
PORT = 1235
BASE = f"http://127.0.0.1:{PORT}/v1"


def binary():
    candidates = [Path(__file__).resolve().parents[2] / "vendor" / "llama-cpu" / "llama-server.exe"]
    if getattr(sys, "frozen", False):
        candidates.insert(0, Path(sys._MEIPASS) / "bin" / "llama-server.exe")
    return next((path for path in candidates if path.is_file()), None)


def existing_models():
    roots = [config.models_dir(), Path.home() / ".lmstudio" / "models"]
    models = []
    for root in roots:
        if root.is_dir():
            for path in root.rglob("*.gguf"):
                if path.is_file() and any(family in path.name.lower() for family in ("qwen", "llama", "gemma", "phi", "mistral", "nemotron", "smollm", "deepseek")):
                    models.append({"path": str(path.resolve()), "name": path.name, "size_mb": round(path.stat().st_size / 1048576)})
    return sorted(models, key=lambda row: row["size_mb"])


def stop():
    global _CHILD, _MODEL, _KEY
    with _LOCK:
        if _CHILD is not None:
            if _CHILD.poll() is None:
                _CHILD.terminate()
                try:
                    _CHILD.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    _CHILD.kill()
                    _CHILD.wait()
            proc.forget(_CHILD)
        _CHILD, _MODEL, _KEY = None, None, ""


def start(model_path, check_cancel=None):
    global _CHILD, _MODEL, _KEY
    path = Path(model_path).resolve()
    executable = binary()
    if not executable:
        raise RuntimeError("Runtime CPU belum disertakan. Jalankan tools/fetch_llama_runtime.py atau gunakan Ollama/API lokal.")
    if path.suffix.lower() != ".gguf" or not path.is_file():
        raise ValueError("Pilih berkas GGUF yang sudah ada")
    with path.open("rb") as file:
        if file.read(4) != b"GGUF":
            raise ValueError("Berkas bukan model GGUF")
    from .models.manager import _ram_gb
    measured = _ram_gb(available=True)
    available = 4 if measured is None else measured
    total = _ram_gb() or available
    # GGUF weights stay memory mapped; do not reserve their full file size twice.
    # Keep a floor for scratch/KV allocations and bound the model against physical RAM.
    if available < 1 or path.stat().st_size / 1024**3 + 1 > total:
        raise ValueError("RAM belum cukup untuk runtime. Tutup aplikasi berat atau pilih model lebih kecil, lalu coba lagi.")
    with inference_slot(check_cancel), _LOCK:
        if _CHILD is not None and _CHILD.poll() is None and _MODEL == str(path):
            return BASE, path.stem, _KEY
        stop()
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", PORT)) == 0:
                raise RuntimeError("Port runtime dipakai proses lain. Runtime tersebut tidak dihentikan.")
        _KEY = secrets.token_urlsafe(32)
        args = [str(executable), "-m", str(path), "--alias", path.stem, "--host", "127.0.0.1", "--port", str(PORT),
                "-c", "4096", "-t", str(resources.cpu_threads()), "-np", "1", "-ngl", "0", "-b", "64", "-ub", "64", "--jinja", "--api-key", _KEY,
                "--chat-template-kwargs", '{"enable_thinking":false}', "--log-disable", "--no-webui"]
        _CHILD = proc.spawn(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _MODEL = str(path)
        deadline = time.monotonic() + 60
        try:
            while time.monotonic() < deadline:
                if check_cancel:
                    check_cancel()
                if _CHILD.poll() is not None:
                    raise RuntimeError("Runtime tidak dapat memuat model; periksa berkas dan RAM tersedia")
                try:
                    ai.request(BASE, "/models", _KEY, timeout=1)
                    return BASE, path.stem, _KEY
                except RuntimeError:
                    time.sleep(.2)
            raise RuntimeError("Pemuatan model melewati batas waktu")
        except BaseException:
            stop()
            raise


atexit.register(stop)
