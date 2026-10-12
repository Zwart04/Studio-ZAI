"""Versioned, atomically finalized pipeline results; temporary entries are never read."""
import hashlib
import json
import time
import uuid
from pathlib import Path

from . import config

VERSION = 2


def key(stage: str, *parts) -> str:
    raw = json.dumps([VERSION, stage, *parts], sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def file_identity(path):
    path = Path(path)
    stat = path.stat()
    return [str(path.resolve()), stat.st_size, stat.st_mtime_ns]


def read(identifier: str, max_age: float | None = None):
    path = config.cache_dir() / "pipeline" / f"{identifier}.json"
    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(entry, dict) or not isinstance(entry.get("value"), (dict, list)):
            return None
        if entry.get("version") != VERSION or entry.get("complete") is not True:
            return None
        if max_age is not None and time.time() - entry["time"] > max_age:
            return None
        digest = hashlib.sha256(json.dumps(entry["value"], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if entry.get("digest") != digest:
            return None
        return entry["value"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def write(identifier: str, value):
    directory = config.cache_dir() / "pipeline"
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / f".{uuid.uuid4().hex}.tmp"
    try:
        digest = hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        temporary.write_text(json.dumps({"version": VERSION, "complete": True, "digest": digest,
                                        "time": time.time(), "value": value}, ensure_ascii=False), encoding="utf-8")
        temporary.replace(directory / f"{identifier}.json")
    finally:
        temporary.unlink(missing_ok=True)
