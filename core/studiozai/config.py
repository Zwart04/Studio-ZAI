"""Local paths, settings and small helpers shared across the engine."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

APP_SLUG = "StudioZAI"

DEFAULT_SETTINGS: dict[str, Any] = {
    "lang": "id",
    "asr_model": "whisper-small-int8",
    "tts_voice_id": "piper-id_ID-news_tts-medium",
    "tts_voice_en": "piper-en_US-lessac-medium",
    "clone_model": "chatterbox-base",
    "clone_consent": False,
    "llm_base_url": "",
    "llm_model": "",
    "llm_api_key": "",
    "cookies_path": "",
    "benchmarks": {},
}


def _base_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_SLUG


def data_dir() -> Path:
    d = _base_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def models_dir() -> Path:
    d = data_dir() / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d


def projects_dir() -> Path:
    d = data_dir() / "projects"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_dir() -> Path:
    d = data_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def transcript_cache_dir() -> Path:
    """Satu folder cache untuk SEMUA chunk transkrip (bukan per folder sumber).

    Chunk wav bisa besar (10 mnt = ~20 MB); menaruhnya di folder sumber video
    membuat 'data sisa' yang dikeluhkan pengguna. Satu folder cache global
    memudahkan pembersihan + tidak mengotori folder proyek.
    """
    d = cache_dir() / "transcript_chunks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cleanup_stale_transcript_chunks(max_age_hours: float = 24.0) -> int:
    """Hapus file chunk yatim (tidak disentuh > max_age_hours). Return jumlah file."""
    import time

    cache = transcript_cache_dir()
    removed = 0
    now = time.time()
    try:
        entries = list(cache.glob("chunk_*.wav"))
    except OSError:
        return 0
    for entry in entries:
        try:
            if now - entry.stat().st_mtime > max_age_hours * 3600:
                entry.unlink(missing_ok=True)
                removed += 1
        except OSError:
            pass
    return removed


def settings_path() -> Path:
    return data_dir() / "settings.json"


def load_settings() -> dict[str, Any]:
    path = settings_path()
    data = dict(DEFAULT_SETTINGS)
    if path.exists():
        try:
            data.update(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save_settings(values: dict[str, Any]) -> dict[str, Any]:
    data = load_settings()
    data.update(values)
    path = settings_path()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return data


def ui_dir() -> Path:
    """Locate the static web UI (repo layout or PyInstaller bundle)."""
    env = os.environ.get("STUDIOZAI_UI_DIR")
    if env and Path(env).is_dir():
        return Path(env)
    bundled = Path(getattr(sys, "_MEIPASS", "")) / "ui"
    if bundled.is_dir():
        return bundled
    return Path(__file__).resolve().parents[2] / "ui"
