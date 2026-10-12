"""Jaringan anti-error YouTube: auto-pindah keluarga alamat IP (IPv4/IPv6).

YouTube memberi "tantangan bot" (`Sign in to confirm you're not a bot`,
`RequestBlocked`) berdasarkan keluarga alamat IP yang dipakai: alamat keluar
IPv6 di banyak ISP diblokir sementara IPv4 dari mesin yang sama lolos
bersih — dan kadang kebalikannya. Karena itu SEMUA jalur YouTube Studio ZAI
tidak mengunci satu keluarga, melainkan:

- mencoba keluarga terakhir yang berhasil dulu (in-memory, thread-safe),
- otomatis pindah ke keluarga lain bila error terlihat seperti tantangan
  bot / gagal jaringan,
- mencatat keluarga yang berhasil supaya panggilan berikutnya langsung
  memakai jalur terbukti tanpa membayar biaya gagal lagi.

Pola ini sama dengan fallback cheat-clip-pro (FORCE_IPV4 + auto-failover)
tetapi tanpa proxy berbayar. Terbukti pada pengujian mesin ini: keluarga
sistem diblokir, IPv4 lolos (metadata 1,5 dtk, caption 2,8 dtk).
"""
from __future__ import annotations

import http.client
import os
import re
import threading
import urllib.request
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

FAMILY_IPV4 = "ipv4"
FAMILY_SYSTEM = "system"

T = TypeVar("T")

# Kata kunci error yang bergantung pada IP/keluarga alamat -> layak dicoba
# di keluarga lain. Selain itu (mis. "video unavailable") langsung berhenti
# supaya tidak membuang waktu mencoba keluarga yang pasti sama-sama gagal.
RETRYABLE_HINTS = (
    "not a bot",
    "sign in to confirm",
    "requestblocked",
    "ipblocked",
    "bot check",
    "could not retrieve",
    "timed out",
    "timeout",
    "connection",
    "koneksi",
    "network is unreachable",
    "temporary failure",
    "name resolution",
    "remote disconnected",
    "reset by peer",
    "unable to download",
    "http error 403",
    "http error 404",
    "http error 429",
    "http error 500",
    "http error 502",
    "http error 503",
    "http error 504",
)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/133.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
}

_family_lock = threading.Lock()
_preferred_first: str = (
    FAMILY_IPV4
    if os.environ.get("STUDIOZAI_FORCE_IPV4", "1").strip().lower() not in ("0", "false", "no", "off")
    else FAMILY_SYSTEM
)


def is_family_retryable(error: object) -> bool:
    """True bila error kemungkinan bergantung pada IP/keluarga alamat."""
    try:
        message = str(error).lower()
    except Exception:  # noqa: BLE001 - str() aneh pada objek asing
        return False
    return any(hint in message for hint in RETRYABLE_HINTS)


def get_family_order() -> list[str]:
    """Urutan keluarga alamat: [keluarga-terakhir-baik, alternatif]."""
    with _family_lock:
        first = _preferred_first
    return [first, FAMILY_SYSTEM if first == FAMILY_IPV4 else FAMILY_IPV4]


def mark_family_working(family: str) -> None:
    """Catat keluarga yang baru saja berhasil agar dicoba lebih dulu."""
    if family not in (FAMILY_IPV4, FAMILY_SYSTEM):
        return
    global _preferred_first
    with _family_lock:
        _preferred_first = family


def family_options(family: str) -> dict[str, Any]:
    """Opsi YoutubeDL yang menambatkan egress ke keluarga alamat tertentu.

    `source_address` adalah cara yt-dlp yang efektif memilih keluarga; opsi
    `force_ipv4` pada API tidak dihormati versi yang beredar.
    """
    if family == FAMILY_IPV4:
        return {"source_address": "0.0.0.0"}
    return {}


def js_runtime_options():
    import shutil
    import sys
    from pathlib import Path
    bundled = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3])) / ("bin" if getattr(sys,"frozen",False) else "vendor") / "qjs.exe"
    if bundled.is_file():
        return {"js_runtimes": {"quickjs": {"path": str(bundled)}}}
    for name in ("deno", "node", "qjs"):
        path = shutil.which(name)
        if not path and getattr(sys, "frozen", False):
            candidate = Path(sys._MEIPASS) / "bin" / f"{name}.exe"
            if candidate.is_file():
                path = str(candidate)
        if path:
            return {"js_runtimes": {"quickjs" if name == "qjs" else name: {"path": path}}}
    return {}


def family_session(family: str, timeout: float = 20.0) -> Any | None:
    """requests.Session ber-header browser (untuk youtube-transcript-api).

    Mengembalikan None bila `requests` tidak terpasang — pemanggil lalu
    memakai klien bawaan pustaka.
    """
    try:
        import requests
        from requests.adapters import HTTPAdapter
    except ImportError:  # pragma: no cover - optional dependency
        return None

    class IPv4HTTPAdapter(HTTPAdapter):
        def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
            kwargs["source_address"] = ("0.0.0.0", 0)
            return super().init_poolmanager(*args, **kwargs)

    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    if family == FAMILY_IPV4:
        session.mount("http://", IPv4HTTPAdapter())
        session.mount("https://", IPv4HTTPAdapter())
    try:  # timeout bawaan agar panggilan tidak menggantung
        session.request  # noqa: B018 - memastikan atribut ada
        original = session.request

        def request_with_timeout(*args: Any, **kwargs: Any) -> Any:
            kwargs.setdefault("timeout", timeout)
            return original(*args, **kwargs)

        session.request = request_with_timeout  # type: ignore[method-assign]
    except Exception:  # noqa: BLE001, S110 - optional wrapper for clients with different session APIs
        pass
    return session


class _BoundHTTPHandler(urllib.request.HTTPHandler):
    """Handler urllib yang mengikat alamat sumber (tambatan keluarga IP)."""

    def __init__(self, source_address: tuple[str, int]):
        super().__init__()
        self._source_address = source_address

    def http_open(self, req):  # type: ignore[override]
        return self.do_open(http.client.HTTPConnection, req, source_address=self._source_address)


class _BoundHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, source_address: tuple[str, int]):
        super().__init__()
        self._source_address = source_address

    def https_open(self, req):  # type: ignore[override]
        return self.do_open(
            http.client.HTTPSConnection, req,
            source_address=self._source_address, context=self._context,
        )


_opener_cache: dict[str, Any] = {}


def opener_for(family: str | None = None) -> Any:
    """Opener urllib yang menambatkan koneksi keluar ke keluarga alamat.

    Dipakai untuk unduh CDN (audio/video/segmen HLS) agar keluarga yang
    terbukti baik di jalur API ikut dipakai di sana — tanpa ini, yt-dlp
    bisa lolos lewat IPv4 sementara unduhan byte tetap lewat IPv6 yang
    diblokir. Tanpa keluarga (None) memakai keluarga terakhir berhasil.
    """
    resolved = family or get_family_order()[0]
    with _family_lock:
        cached = _opener_cache.get(resolved)
    if cached is not None:
        return cached
    handlers: list[Any] = []
    if resolved == FAMILY_IPV4:
        address = ("0.0.0.0", 0)
        handlers = [_BoundHTTPHandler(address), _BoundHTTPSHandler(address)]
    opener = urllib.request.build_opener(*handlers)
    with _family_lock:
        _opener_cache[resolved] = opener
    return opener


def try_families(
    attempt: Callable[[str], T],
    families: Iterable[str] | None = None,
    on_error: Callable[[str, Exception], None] | None = None,
) -> tuple[T, str]:
    """Jalankan ``attempt(family)`` per keluarga sampai berhasil.

    Mengembalikan ``(hasil, keluarga_pemenang)`` dan menandai keluarga
    tersebut sebagai yang diprioritaskan berikutnya. Error yang TIDAK
    bergantung jaringan (mis. "video unavailable") langsung dilempar agar
    hemat waktu.
    """
    errors: list[str] = []
    order = list(families) if families is not None else get_family_order()
    for family in order:
        try:
            result = attempt(family)
        except Exception as exc:
            if on_error is not None:
                try:
                    on_error(family, exc)
                except Exception:  # noqa: BLE001, S110 - error reporting cannot abort the next family attempt
                    pass
            first_line = str(exc).splitlines()[0][:180] if str(exc) else type(exc).__name__
            errors.append(f"{family}: {type(exc).__name__}: {first_line}")
            if not is_family_retryable(exc):
                raise
            continue
        mark_family_working(family)
        return result, family
    raise RuntimeError(" | ".join(errors) if errors else "tidak ada keluarga alamat yang dicoba")


BOT_HINTS = (
    "not a bot",
    "sign in to confirm",
    "requestblocked",
    "ipblocked",
    "bot check",
    "confirm you're not a bot",
    "confirm you are not a bot",
)


def friendly_error(action: str, error: object) -> str:
    """Pesan gagal yang manusiawi (tanpa dinding teks/URL yt-dlp).

    Tantangan bot menerima penjelasan + solusi nyata (cookies, tunggu,
    sumber lokal) tanpa menyisipkan instruksi CLI mentah; error jaringan
    lain tetap menampilkan detail singkat tanpa URL.
    """
    text = str(error).strip()
    lowered = text.lower()
    if any(hint in lowered for hint in BOT_HINTS):
        return (
            f"Gagal {action}: YouTube meminta verifikasi jaringan (blokir IP). "
            "Aplikasi sudah otomatis mencoba IPv4 dan IPv6, tetapi keduanya ditolak. "
            "Solusi: atur cookies akun YouTube di halaman Pengaturan, coba lagi "
            "beberapa saat, atau pakai sumber lokal."
        )
    first_line = (text.splitlines()[0] if text else "").strip()
    detail = (re.sub(r"https?://\S+", "tautan", first_line) or type(error).__name__)[:220]
    if is_family_retryable(error):
        return (
            f"Gagal {action}: koneksi/jaringan bermasalah ({detail}). "
            "Coba lagi sebentar lagi — aplikasi otomatis mencoba IPv4 dan IPv6."
        )
    return f"Gagal {action}: {detail}"
