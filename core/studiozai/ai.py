"""Optional HTTP AI providers. Local editing never requires a cloud account."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from . import config, credentials

PROVIDERS = {
    "openai": {"label": "OpenAI", "url": "https://api.openai.com/v1", "text": True, "image": True, "speech": True},
    "anthropic": {"label": "Anthropic", "url": "https://api.anthropic.com/v1", "text": True},
    "deepseek": {"label": "DeepSeek", "url": "https://api.deepseek.com", "text": True},
    "compatible": {"label": "API kompatibel / Ollama", "url": "http://127.0.0.1:11434/v1", "text": True},
    "sd_local": {"label": "Stable Diffusion lokal", "url": "http://127.0.0.1:1234/v1", "image": True},
}
VOICES = ["marin", "cedar", "alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse"]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Alamat API dialihkan. Isi alamat resmi penyedia di Pengaturan.")


def request(base: str, route: str, key: str, payload: dict | None = None, *, anthropic: bool = False, binary: bool = False) -> Any:
    from urllib.parse import urlparse
    url = urlparse(base)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
        raise ValueError("Alamat API tidak valid")
    if key and url.scheme != "https" and url.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("API key hanya boleh dikirim melalui HTTPS atau localhost")
    headers = {"Content-Type": "application/json"}
    if key:
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"} if anthropic else {"Authorization": f"Bearer {key}"})
    req = urllib.request.Request(base.rstrip("/") + route,
        data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=180) as response:
            raw = response.read(32 * 1024 * 1024 + 1)
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError("Respons AI terlalu besar")
        return raw if binary else json.loads(raw)
    except urllib.error.HTTPError as exc:
        hints = {401: "API key tidak valid", 403: "Akses model tidak diizinkan", 429: "Kuota atau batas permintaan tercapai"}
        raise RuntimeError(hints.get(exc.code, f"Penyedia AI gagal (HTTP {exc.code})")) from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Penyedia AI tidak merespons. Periksa alamat dan koneksi.") from exc


def connection(kind: str) -> tuple[str, str, str, str]:
    settings = config.load_settings()
    provider = str(settings.get(f"{kind}_provider", ""))
    capability = {"ai": "text", "image": "image", "speech": "speech"}[kind]
    if provider not in PROVIDERS or not PROVIDERS[provider].get(capability):
        raise ValueError(f"Pilih penyedia {kind} di Pengaturan")
    base = str(settings.get(f"{kind}_base_url") or PROVIDERS[provider]["url"])
    model = str(settings.get(f"{kind}_model", "")).strip()
    key = credentials.read().get(f"{kind}_api_key", "")
    if provider not in {"compatible", "sd_local"} and not key:
        raise ValueError("Isi API key di Pengaturan")
    return provider, base, model, key


def text(prompt: str) -> str:
    provider, base, model, key = connection("ai")
    if not model:
        raise ValueError("Isi nama model teks di Pengaturan")
    messages = [{"role": "user", "content": prompt}]
    payload: dict[str, Any] = {"model": model, "messages": messages}
    if provider == "anthropic":
        payload["max_tokens"] = 2048
        response = request(base, "/messages", key, payload, anthropic=True)
        return "".join(p.get("text", "") for p in response.get("content", []) if p.get("type") == "text")
    response = request(base, "/chat/completions", key, payload)
    return str(response["choices"][0]["message"]["content"])


def image(prompt: str) -> Path:
    provider, base, model, key = connection("image")
    if not prompt.strip():
        raise ValueError("Deskripsi gambar kosong")
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
