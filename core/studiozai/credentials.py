"""Keep API keys out of settings responses and project exports."""
from __future__ import annotations

import base64
import ctypes
import json
import os
import sys
from ctypes import wintypes

from . import config


def _protect(value: bytes, decrypt: bool = False) -> bytes:
    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(value)
    source = Blob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    function = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise OSError("Penyimpanan kunci Windows tidak dapat diakses")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        ctypes.windll.kernel32.LocalFree(target.data)


def read() -> dict[str, str]:
    path = config.data_dir() / "credentials.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = base64.b64decode(payload["data"])
    if payload["storage"] == "windows-dpapi":
        raw = _protect(raw, decrypt=True)
    return json.loads(raw)


def update(values: dict[str, str]) -> None:
    data = read()
    data.update({k: v for k, v in values.items() if v != "***"})
    raw = json.dumps(data).encode()
    windows = sys.platform == "win32"
    if windows:
        raw = _protect(raw)
    path = config.data_dir() / "credentials.json"
    path.write_text(json.dumps({"storage": "windows-dpapi" if windows else "private-file",
        "data": base64.b64encode(raw).decode()}), encoding="utf-8")
    os.chmod(path, 0o600)
