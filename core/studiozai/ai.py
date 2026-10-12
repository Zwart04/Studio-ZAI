"""Optional HTTP AI providers. Local editing never requires a cloud account."""
from __future__ import annotations

import base64
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from . import config, credentials
from .jobs import bounded_inference

PROVIDERS = {
    "sdxs_local": {"label": "Di perangkat · SDXS-512", "url": "", "image": True},
    "openai": {"label": "OpenAI", "url": "https://api.openai.com/v1", "text": True, "image": True, "speech": True},
    "anthropic": {"label": "Anthropic", "url": "https://api.anthropic.com/v1", "text": True},
    "groq": {"label": "Groq", "url": "https://api.groq.com/openai/v1", "text": True},
    "gemini": {"label": "Google Gemini", "url": "https://generativelanguage.googleapis.com/v1beta/openai", "text": True},
    "deepseek": {"label": "DeepSeek", "url": "https://api.deepseek.com", "text": True},
    "compatible": {"label": "API kompatibel / Ollama", "url": "http://127.0.0.1:11434/v1", "text": True},
    "sd_local": {"label": "Stable Diffusion lokal", "url": "http://127.0.0.1:1234/v1", "image": True},
}
VOICES = ["marin", "cedar", "alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse"]
_MODEL_CACHE: dict[tuple, tuple[float, dict]] = {}


def model_rank(identifier: str, kind: str = "ai") -> tuple:
    name = identifier.lower()
    preferred = any(word in name for word in ("mini", "luna", "flash", "haiku", "instant", "lite", "20b"))
    stable = not any(word in name for word in ("preview", "experimental", "exp-", "deprecated"))
    version = tuple(int(part) for part in re.findall(r"\d+", name)[:3])
    return (stable, preferred, version, name)


def supports_model(identifier: str, kind: str) -> bool:
    name = identifier.lower()
    if kind == "image":
        return "image" in name or name.startswith(("dall-e", "sd-"))
    if kind == "speech":
        return "tts" in name
    return not any(word in name for word in ("embed", "whisper", "audio", "speech", "tts", "realtime", "image", "dall-e", "moderation", "guard", "compound", "codex", "robotics"))


def validate_provider_base(provider: str, base: str) -> str:
    from urllib.parse import urlparse
    if provider not in PROVIDERS:
        raise ValueError("Penyedia tidak dikenal")
    base = (base or PROVIDERS[provider]["url"]).rstrip("/")
    parsed = urlparse(base)
    if provider not in {"compatible", "sd_local"}:
        official = urlparse(PROVIDERS[provider]["url"])
        if parsed.scheme != "https" or parsed.hostname != official.hostname or parsed.port not in {None, 443}:
            raise ValueError("Penyedia ini memakai alamat resmi. Untuk endpoint lain pilih API kompatibel.")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Alamat API tidak boleh memuat kredensial atau parameter")
    return base


def discover_models(provider: str, base: str = "", key: str = "", kind: str = "ai") -> dict:
    if kind not in {"ai", "image", "speech"}:
        raise ValueError("Jenis model tidak dikenal")
    base = validate_provider_base(provider, base)
    if not key and provider not in {"compatible", "sd_local"}:
        raise ValueError("Masukkan API key untuk mendeteksi model di akunmu")
    cache_key = (provider, base, kind, hashlib.sha256(key.encode()).hexdigest())
    cached = _MODEL_CACHE.get(cache_key)
    if cached and time.monotonic() - cached[0] < 300:
        return cached[1]
    route = "/models?limit=1000" if provider == "anthropic" else "/models"
    result = request(base, route, key, anthropic=provider == "anthropic", timeout=8)
    rows = result.get("data", []) if isinstance(result, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Daftar model penyedia tidak valid")  # noqa: TRY004
    choices = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("active") is False:
            continue
        identifier = row.get("id")
        if isinstance(identifier, str) and 0 < len(identifier) <= 200 and supports_model(identifier, kind):
            choices[identifier] = {"id": identifier, "label": str(row.get("display_name") or identifier)[:200]}
    ordered = sorted(choices.values(), key=lambda row: model_rank(row["id"], kind), reverse=True)
    if not ordered:
        raise ValueError("Tidak ada model yang sesuai. Pilih jenis/provider lain atau isi model manual.")
    data = {"models": ordered, "recommended": ordered[0]["id"], "source": "provider", "note": "Saran berdasarkan jenis/nama model, bukan jaminan biaya atau kualitas. Akses inferensi tetap mengikuti kuota akun."}
    if len(_MODEL_CACHE) > 64:
        _MODEL_CACHE.clear()
    _MODEL_CACHE[cache_key] = (time.monotonic(), data)
    return data


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Alamat API dialihkan. Isi alamat resmi penyedia di Pengaturan.")


def request(base: str, route: str, key: str, payload: dict | None = None, *, anthropic: bool = False, binary: bool = False, timeout: float = 90, check_cancel=None) -> Any:
    from .execution_policy import check_network
    check_network(base, inference=True)
    from urllib.parse import urlparse
    url = urlparse(base)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
        raise ValueError("Alamat API tidak valid")
    if key and url.scheme != "https" and url.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("API key hanya boleh dikirim melalui HTTPS atau localhost")
    headers = {"Content-Type": "application/json"}
    if key:
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"} if anthropic else {"Authorization": f"Bearer {key}"})
    if check_cancel:
        return _cancellable_request(base, route, headers, payload, binary, timeout, check_cancel)
    req = urllib.request.Request(base.rstrip("/") + route,
        data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as response:
            raw = response.read(32 * 1024 * 1024 + 1)
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError("Respons AI terlalu besar")
        return raw if binary else json.loads(raw)
    except urllib.error.HTTPError as exc:
        hints = {401: "API key tidak valid", 403: "Akses model tidak diizinkan", 429: "Kuota atau batas permintaan tercapai"}
        raise RuntimeError(hints.get(exc.code, f"Penyedia AI gagal (HTTP {exc.code})")) from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Penyedia AI tidak merespons. Periksa alamat dan koneksi.") from exc


def _cancellable_request(base, route, headers, payload, binary, timeout, check_cancel):
    import http.client
    import queue
    import socket
    import threading
    from urllib.parse import urlparse
    parsed = urlparse(base)
    cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    connection = cls(parsed.hostname, parsed.port, timeout=timeout)
    responses = queue.Queue(maxsize=1)
    def send():
        try:
            connection.request("POST" if payload is not None else "GET", parsed.path.rstrip("/") + route,
                               body=json.dumps(payload).encode() if payload is not None else None, headers=headers)
            response = connection.getresponse()
            if response.status != 200:
                raise RuntimeError(f"Penyedia AI gagal (HTTP {response.status})")
            raw = response.read(32 * 1024 * 1024 + 1)
            if len(raw) > 32 * 1024 * 1024:
                raise ValueError("Respons AI terlalu besar")
            responses.put((True, raw if binary else json.loads(raw)))
        except Exception as exc:  # noqa: BLE001 - transport errors cross the worker boundary
            responses.put((False, exc))
    thread = threading.Thread(target=send, daemon=True)
    thread.start()
    deadline = time.monotonic() + timeout
    try:
        while True:
            check_cancel()
            if time.monotonic() >= deadline:
                raise RuntimeError("Inference melewati batas waktu")
            try:
                ok, value = responses.get(timeout=.1)
            except queue.Empty:
                continue
            if not ok:
                raise RuntimeError("Inference tidak merespons; periksa runtime atau penyedia") from value
            return value
    finally:
        if connection.sock:
            try:
                connection.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        connection.close()
        thread.join(timeout=1)


def connection(kind: str) -> tuple[str, str, str, str]:
    settings = config.load_settings()
    provider = str(settings.get(f"{kind}_provider", ""))
    capability = {"ai": "text", "image": "image", "speech": "speech"}[kind]
    if provider not in PROVIDERS or not PROVIDERS[provider].get(capability):
        raise ValueError(f"Pilih penyedia {kind} di Pengaturan")
    base = validate_provider_base(provider, str(settings.get(f"{kind}_base_url") or PROVIDERS[provider]["url"]))
    model = str(settings.get(f"{kind}_model", "")).strip()
    key = credentials.read().get(f"{kind}_api_key", "")
    if provider not in {"compatible", "sd_local", "sdxs_local"} and not key:
        raise ValueError("Isi API key di Pengaturan")
    if model == "auto" or (kind == "ai" and not model):
        model = discover_models(provider, base, key, kind)["recommended"]
    return provider, base, model, key


def text(prompt: str, model_override: str | None = None, connection_override=None, check_cancel=None) -> str:
    provider, base, model, key = connection_override or connection("ai")
    model = model_override or model
    if not model:
        raise ValueError("Isi nama model teks di Pengaturan")
    messages = [{"role": "user", "content": prompt}]
    payload: dict[str, Any] = {"model": model, "messages": messages}
    if provider == "anthropic":
        payload["max_tokens"] = 2048
        response = request(base, "/messages", key, payload, anthropic=True, check_cancel=check_cancel)
        return "".join(p.get("text", "") for p in response.get("content", []) if p.get("type") == "text")
    response = request(base, "/chat/completions", key, payload, check_cancel=check_cancel)
    return str(response["choices"][0]["message"]["content"])


@bounded_inference
def image(prompt: str, provider: str | None = None) -> Path:
    if not prompt.strip():
        raise ValueError("Deskripsi gambar kosong")
    saved = config.load_settings().get("image_provider") or "sdxs_local"
    if provider in {"configured", "cloud"} and saved == "sdxs_local":
        raise ValueError("Atur penyedia gambar online di Pengaturan terlebih dahulu.")
    selected = saved if provider in {None, "configured", "cloud"} else provider
    if selected == "sdxs_local":
        from . import local_image
        target = local_image.generate(prompt)
        target.with_suffix(".json").write_text(
            json.dumps({"prompt": prompt, "provider": "sdxs_local", "model": "sdxs-512"}, ensure_ascii=False),
            encoding="utf-8",
        )
        return target
    if selected != saved:
        raise ValueError("Atur penyedia gambar online di Pengaturan terlebih dahulu.")
    provider, base, model, key = connection("image")
    payload: dict[str, Any] = {"model": model or ("gpt-image-1-mini" if provider == "openai" else "sd-cpp-local"),
        "prompt": prompt, "n": 1, "size": "1024x1024" if provider == "openai" else "512x512"}
    if provider == "openai":
        payload["quality"] = "low"
    else:
        payload.update(response_format="b64_json", steps=4, cfg_scale=1.0)
    result = request(base, "/images/generations", key, payload)
    raw = base64.b64decode(result["data"][0]["b64_json"], validate=True)
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Penyedia tidak mengirim gambar PNG yang valid")
    directory = config.data_dir() / "images"
    directory.mkdir(exist_ok=True)
    target = directory / f"image-{uuid.uuid4().hex[:12]}.png"
    target.write_bytes(raw)
    target.with_suffix(".json").write_text(json.dumps({"prompt": prompt, "provider": provider, "model": payload["model"]}, ensure_ascii=False), encoding="utf-8")
    return target


@bounded_inference
def speech(text: str, voice: str, language: str) -> Path:
    _, base, model, key = connection("speech")
    if voice not in VOICES or not text.strip():
        raise ValueError("Pilih suara dan isi teks")
    raw = request(base, "/audio/speech", key, {"model": model or "gpt-4o-mini-tts", "voice": voice,
        "input": text, "instructions": "Speak in Indonesian." if language == "id" else "Speak in English.",
        "response_format": "wav"}, binary=True)
    if not raw.startswith(b"RIFF"):
        raise ValueError("Penyedia tidak mengirim WAV yang valid")
    directory = config.data_dir() / "voices"
    directory.mkdir(exist_ok=True)
    target = directory / f"cloud-{uuid.uuid4().hex[:12]}.wav"
    target.write_bytes(raw)
    return target
