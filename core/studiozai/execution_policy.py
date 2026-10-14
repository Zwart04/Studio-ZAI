"""Processing policy is independent from media acquisition and saved cloud keys."""
from contextlib import contextmanager
from contextvars import ContextVar
from urllib.parse import urlparse

MODE = ContextVar("processing_mode", default="legacy")


@contextmanager
def processing(mode: str):
    if mode not in {"local", "hybrid", "offline", "online_ai", "legacy"}:
        raise ValueError("Mode pemrosesan tidak dikenal")
    token = MODE.set(mode)
    try:
        yield
    finally:
        MODE.reset(token)


def check_network(url: str, *, inference: bool = False):
    host = urlparse(url).hostname
    local = host in {"127.0.0.1", "localhost", "::1"}
    mode = MODE.get()
    if mode == "offline" and not (inference and local):
        raise ValueError("Full Offline tidak mengizinkan akses jaringan")
    if inference and mode in {"local", "hybrid"} and not local:
        raise ValueError("Model offline memakai runtime lokal. Pilih model online untuk cloud/LAN.")
