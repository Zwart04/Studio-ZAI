"""Project storage: source media, transcript, clips and edits (JSON on disk)."""

from __future__ import annotations

import copy
import json
import re
import shutil
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import config
from .utils.text import sanitize_filename

# Id proyek dipakai langsung sebagai nama folder -> batasi ke karakter aman.
PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

DEFAULT_CROP = "center"
DEFAULT_SUBTITLE_PRESET = "clean"
_MISSING = object()
_LOCKS: dict[str, threading.RLock] = {}
_LOCK_GUARD = threading.Lock()


def project_lock(project_id: str):
    with _LOCK_GUARD:
        return _LOCKS.setdefault(project_id, threading.RLock())


class ProjectConflict(RuntimeError):
    pass


def _merge(base, local, current, path="project"):
    if local == base:
        return current
    if current == base or current == local:
        return local
    if all(isinstance(value, dict) for value in (base, local, current)):
        merged = {}
        for name in base.keys() | local.keys() | current.keys():
            value = _merge(base.get(name, _MISSING), local.get(name, _MISSING), current.get(name, _MISSING), f"{path}.{name}")
            if value is not _MISSING:
                merged[name] = value
        return merged
    if path == "project.clips" and all(isinstance(value, list) for value in (base, local, current)):
        def keyed(rows):
            return {row.get("storage_id", f"{row['index']:03d}"): {k: v for k, v in row.items() if k != "index"} for row in rows}
        before, changed, latest = keyed(base), keyed(local), keyed(current)
        if list(changed) == list(before):
            order = list(latest)
        elif list(latest) == list(before) or list(latest) == list(changed):
            order = list(changed)
        else:
            raise ProjectConflict("Urutan klip berubah pada pekerjaan lain. Muat ulang proyek.")
        rows = []
        for key in dict.fromkeys([*order, *changed, *latest]):
            value = _merge(before.get(key, _MISSING), changed.get(key, _MISSING), latest.get(key, _MISSING), f"clip.{key}")
            if value is not _MISSING:
                rows.append({**value, "index": len(rows)})
        return rows
    raise ProjectConflict(f"Perubahan bersamaan pada {path}. Data lama tetap aman; muat ulang proyek.")


@dataclass
class Clip:
    index: int
    start: float
    end: float
    title: str = ""
    score: float = 0.0
    reason: str = ""
    analysis_metadata: dict[str, Any] = field(default_factory=dict)
    crop: str = DEFAULT_CROP
    subtitle_preset: str = DEFAULT_SUBTITLE_PRESET
    subtitle_position: str = "bottom"  # bottom | middle | top | off
    canvas: str = "portrait"  # portrait | original | square | landscape
    audio_mode: str = "original"
    original_volume: float = 0.25
    voice_volume: float = 1.0
    voice_id: str = ""
    voice_clone_sample: str = ""
    captions: list[dict[str, Any]] = field(default_factory=list)
    caption_variants: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    caption_language: str = ""
    files: dict[str, str] = field(default_factory=dict)
    status: str = "draft"
    # Editor timeline multi-track (video/media/teks/audio). None = proyek lama,
    # dirender lewat jalur tunggal seperti sebelumnya.
    timeline: dict[str, Any] | None = None
    storage_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    @property
    def duration(self) -> float:
        return round(max(0.0, self.end - self.start), 3)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["duration"] = self.duration
        return data

    def invalidate_renders(self) -> None:
        for key in ("mp4", "thumb", "mp4_portrait", "mp4_square", "mp4_landscape",
                    "thumb_portrait", "thumb_square", "thumb_landscape"):
            self.files.pop(key, None)
        self.status = "draft"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Clip:
        allowed = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        allowed.pop("duration", None)
        allowed.setdefault("storage_id", f"{int(data['index']):03d}")
        return cls(**allowed)


@dataclass
class Project:
    id: str
    title: str
    source: str = ""
    source_kind: str = "local"
    language: str = "id"
    duration: float = 0.0
    width: int = 0
    height: int = 0
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    transcript: dict[str, Any] = field(default_factory=dict)
    clips: list[Clip] = field(default_factory=list)
    notes: str = ""
    processing_mode: str = "legacy"
    execution: dict[str, Any] = field(default_factory=dict)
    # Mode online: transkrip dari audio tanpa mengunduh video penuh.
    # Video diunduh per-rentang klip saat render (lihat download.download_range).
    online: bool = False
    source_url: str = ""
    audio_path: str = ""
    preview_path: str = ""
    heatmap: list[dict[str, float]] = field(default_factory=list)
    segments: dict[str, dict[str, Any]] = field(default_factory=dict)
    _history: list[dict[str, Any]] = field(default_factory=list, repr=False)
    _baseline_json: str | None = field(default=None, repr=False)

    # ------------------------------------------------------------------ paths
    @property
    def root(self) -> Path:
        return config.projects_dir() / self.id

    @property
    def source_dir(self) -> Path:
        return self.root / "source"

    @property
    def clips_dir(self) -> Path:
        return self.root / "clips"

    @property
    def voices_dir(self) -> Path:
        return self.root / "voice"

    @property
    def project_file(self) -> Path:
        return self.root / "project.json"

    def clip_dir(self, index: int) -> Path:
        clip = next((c for c in self.clips if c.index == index), None)
        storage = clip.storage_id if clip else f"{index:03d}"
        if not PROJECT_ID_RE.fullmatch(storage):
            raise ValueError("Folder klip tidak valid")
        path = self.clips_dir / storage
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ------------------------------------------------------------------ crud
    def save(self) -> Path:
        with project_lock(self.id):
            payload = self.as_dict()
            if self._baseline_json is not None and self.project_file.is_file():
                current = Project.from_dict(json.loads(self.project_file.read_text(encoding="utf-8")), capture_baseline=False).as_dict()
                base = json.loads(self._baseline_json)
                for value in (payload, current, base):
                    value.pop("updated", None)
                payload = _merge(base, payload, current)
            self.updated = time.time()
            payload["updated"] = self.updated
            self.root.mkdir(parents=True, exist_ok=True)
            temporary = self.root / f".project-{uuid.uuid4().hex}.tmp"
            try:
                temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
                temporary.replace(self.project_file)
            finally:
                temporary.unlink(missing_ok=True)
            restored = Project.from_dict(payload, capture_baseline=False)
            by_id = {clip.storage_id: clip for clip in self.clips}
            for clip in restored.clips:
                if clip.storage_id in by_id:
                    by_id[clip.storage_id].__dict__.update(clip.__dict__)
            restored.clips = [by_id.get(clip.storage_id, clip) for clip in restored.clips]
            for name in payload:
                if name in self.__dataclass_fields__:
                    setattr(self, name, getattr(restored, name))
            self._baseline_json = json.dumps(self.as_dict(), ensure_ascii=False)
        return self.project_file

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "source_kind": self.source_kind,
            "language": self.language,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "created": self.created,
            "updated": self.updated,
            "transcript": self.transcript,
            "notes": self.notes,
            "processing_mode": self.processing_mode,
            "execution": self.execution,
            "online": self.online,
            "source_url": self.source_url,
            "audio_path": self.audio_path,
            "preview_path": self.preview_path,
            "heatmap": self.heatmap,
            "segments": self.segments,
            "clips": [c.as_dict() for c in self.clips],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], capture_baseline: bool = True) -> Project:
        project = cls(
            id=data["id"],
            title=data.get("title") or "Tanpa judul",
            source=data.get("source", ""),
            source_kind=data.get("source_kind", "local"),
            language=data.get("language", "id"),
            duration=float(data.get("duration") or 0.0),
            width=int(data.get("width") or 0),
            height=int(data.get("height") or 0),
            created=float(data.get("created") or time.time()),
            updated=float(data.get("updated") or time.time()),
            transcript=data.get("transcript") or {},
            notes=data.get("notes", ""),
            processing_mode=data.get("processing_mode", "legacy"),
            execution=dict(data.get("execution") or {}),
            online=bool(data.get("online", False)),
            source_url=data.get("source_url", ""),
            audio_path=data.get("audio_path", ""),
            preview_path=data.get("preview_path", ""),
            heatmap=list(data.get("heatmap") or []),
            segments=dict(data.get("segments") or {}),
        )
        project.clips = [Clip.from_dict(c) for c in data.get("clips", [])]
        if capture_baseline:
            project._baseline_json = json.dumps(project.as_dict(), ensure_ascii=False)
        return project

    # ------------------------------------------------------------------ history
    def snapshot(self) -> None:
        self._history.append({"clips": [c.as_dict() for c in self.clips]})
        del self._history[:-20]

    def undo(self) -> bool:
        if not self._history:
            return False
        previous = self._history.pop()
        self.clips = [Clip.from_dict(c) for c in previous["clips"]]
        return True

    # ------------------------------------------------------------------ clips
    def renumber(self) -> None:
        for position, clip in enumerate(self.clips):
            clip.index = position

    def add_clip(self, clip: Clip) -> Clip:
        self.snapshot()
        clip.index = len(self.clips)
        self.clips.append(clip)
        return clip

    def set_clips(self, clips: list[Clip]) -> None:
        self.snapshot()
        self.clips = clips
        self.renumber()

    def clip(self, index: int) -> Clip:
        for clip in self.clips:
            if clip.index == index:
                return clip
        raise KeyError(f"clip {index} tidak ditemukan")

    def update_clip(self, index: int, values: dict[str, Any]) -> Clip:
        self.snapshot()
        clip = self.clip(index)
        import copy
        values = copy.deepcopy(values)
        timeline = copy.deepcopy(values.get("timeline", clip.timeline))
        if timeline:
            base = next((t.get("items", []) for t in timeline.get("tracks", []) if t.get("kind") == "video"), [])
            if base:
                if "canvas" in values:
                    base[0]["canvas"] = values["canvas"]
                else:
                    values["canvas"] = base[0].get("canvas", clip.canvas)
                values["timeline"] = timeline
        if any(
            key not in {"title", "index", "files", "storage_id"}
            and hasattr(clip, key) and getattr(clip, key) != value
            for key, value in values.items()
        ):
            clip.invalidate_renders()
        for key, value in values.items():
            if hasattr(clip, key) and key not in {"index", "files", "storage_id"}:
                setattr(clip, key, value)
        if clip.end <= clip.start:
            clip.end = clip.start + 1.0
        return clip

    def remove_clip(self, index: int) -> None:
        self.snapshot()
        clip = self.clip(index)
        # Only remove outputs owned by this project; imported sources are never touched.
        folders = {self.clip_dir(index)}
        base = (self.root / "clips").resolve()
        for value in clip.files.values():
            parent = Path(value).resolve().parent
            if parent.parent == base:
                folders.add(parent)
        other_files = {str(Path(v).resolve()) for c in self.clips if c is not clip for v in c.files.values()}
        for folder in folders:
            if folder.exists() and folder.resolve().parent == base and not any(Path(other).is_relative_to(folder.resolve()) for other in other_files):
                shutil.rmtree(folder)
        self.clips = [c for c in self.clips if c.index != index]
        self.renumber()

    def move_clip(self, index: int, delta: int) -> None:
        self.snapshot()
        position = next((i for i, c in enumerate(self.clips) if c.index == index), None)
        if position is None:
            raise KeyError(f"clip {index} tidak ditemukan")
        target = max(0, min(len(self.clips) - 1, position + delta))
        self.clips.insert(target, self.clips.pop(position))
        self.renumber()

    def split_clip(self, index: int, at: float) -> tuple[Clip, Clip]:
        self.snapshot()
        clip = self.clip(index)
        at = max(clip.start + 0.5, min(clip.end - 0.5, at))
        original = copy.deepcopy(clip.as_dict())
        right = Clip.from_dict(copy.deepcopy(original))
        right.storage_id = uuid.uuid4().hex[:12]
        right.start = at
        right.files = {}
        right.status = "draft"
        clip.end = at
        clip.status = "draft"
        clip.files = {}
        for part in (clip, right):
            offset = part.start - original["start"]
            part.captions = trim_captions(original["captions"], offset, offset + part.duration)
            part.caption_variants = {lang: trim_captions(rows, offset, offset + part.duration)
                                     for lang, rows in original["caption_variants"].items()}
            if original["timeline"]:
                part.timeline = copy.deepcopy(original["timeline"])
                for track in part.timeline.get("tracks", []):
                    if track.get("kind") == "video":
                        for item in track.get("items", []):
                            item.update(start=0, end=part.duration, srcStart=part.start)
                            if item.get("framing"):
                                from .pipeline.framing import slice_framing
                                item["framing"] = slice_framing(item["framing"], offset, part.duration)
                    else:
                        track["items"] = trim_captions(track.get("items", []), offset, offset + part.duration)
        position = self.clips.index(clip)
        self.clips.insert(position + 1, right)
        self.renumber()
        return clip, right

    def media_path(self) -> Path | None:
        if not self.source:
            return None
        candidate = Path(self.source)
        if candidate.exists():
            return candidate
        matches = sorted(self.source_dir.glob("*"), key=lambda p: p.stat().st_size)
        return matches[-1] if matches else None

    def audio_media_path(self) -> Path | None:
        """Media untuk transkripsi/analisis: video kalau ada, audio kalau online."""
        media = self.media_path()
        if media is not None:
            return media
        if self.online and self.audio_path:
            candidate = Path(self.audio_path)
            if candidate.exists():
                return candidate
        return None

    def segment_path(self, storage_id: str) -> Path | None:
        entry = self.segments.get(storage_id)
        if not entry:
            return None
        candidate = Path(entry.get("path", ""))
        return candidate if candidate.exists() else None

    def segment_bounds(self, storage_id: str) -> tuple[float, float]:
        entry = self.segments.get(storage_id) or {}
        return float(entry.get("start") or 0.0), float(entry.get("end") or 0.0)

    def store_segment(
        self,
        storage_id: str,
        path: str | Path,
        start: float = 0.0,
        end: float = 0.0,
    ) -> None:
        self.segments[storage_id] = {
            "path": str(path),
            "start": float(start),
            "end": float(end),
        }

    def clear_segments(self) -> None:
        self.segments = {}

    # ------------------------------------------------------------------ factory
    @classmethod
    def create(cls, title: str, source: str = "", source_kind: str = "local", language: str = "id") -> Project:
        project = cls(
            id=uuid.uuid4().hex[:12],
            title=title or sanitize_filename(source or "proyek"),
            source=source,
            source_kind=source_kind,
            language=language,
        )
        project.root.mkdir(parents=True, exist_ok=True)
        project.save()
        return project


def project_dirs() -> list[Path]:
    return sorted(
        (p for p in config.projects_dir().iterdir() if (p / "project.json").exists()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def list_projects() -> list[Project]:
    projects: list[Project] = []
    for path in project_dirs():
        try:
            projects.append(Project.from_dict(json.loads((path / "project.json").read_text(encoding="utf-8"))))
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return projects


def _project_root(project_id: str) -> Path:
    """Folder proyek dengan validasi id.

    Id datang dari URL (`/api/projects/{id}`) dan dipakai sebagai nama folder.
    Tanpa validasi, id seperti `..` bisa membuat operasi baca/hapus keluar dari
    folder data (mis. `DELETE /api/projects/..` menghapus seluruh data aplikasi).
    """
    if not project_id or not PROJECT_ID_RE.match(project_id):
        raise KeyError(f"id proyek tidak valid: {project_id!r}")
    base = config.projects_dir().resolve()
    root = (base / project_id).resolve()
    if root.parent != base:
        raise KeyError(f"id proyek di luar folder data: {project_id!r}")
    return root


def load_project(project_id: str) -> Project:
    path = _project_root(project_id) / "project.json"
    if not path.exists():
        raise KeyError(f"proyek {project_id} tidak ditemukan")
    return Project.from_dict(json.loads(path.read_text(encoding="utf-8")))


def delete_project(project_id: str) -> None:
    directory = _project_root(project_id)
    if directory.exists():
        shutil.rmtree(directory)


def trim_captions(rows: list[dict[str, Any]], start: float, end: float) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if float(row["end"]) <= start or float(row["start"]) >= end:
            continue
        item = copy.deepcopy(row)
        item["start"] = max(0.0, float(row["start"]) - start)
        item["end"] = min(end - start, float(row["end"]) - start)
        if "srcStart" in item:
            item["srcStart"] = float(item["srcStart"]) + max(0.0, start - float(row["start"]))
        if row.get("words"):
            item["words"] = trim_captions(row["words"], start, end)
        result.append(item)
    return result


def duplicate_project(project_id: str) -> Project:
    project = load_project(project_id)
    clone_id = uuid.uuid4().hex[:12]
    target = _project_root(clone_id)
    # A duplicate owns its media, so deleting the original cannot break it.
    shutil.copytree(project.root, target)

    def relocate(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: relocate(item) for key, item in value.items()}
        if isinstance(value, list):
            return [relocate(item) for item in value]
        if isinstance(value, str):
            try:
                relative = Path(value).relative_to(project.root)
                return str(target / relative)
            except (ValueError, OSError):
                pass
        return value

    try:
        payload = relocate(project.as_dict())
        payload.update(id=clone_id, title=f"{project.title} (salinan)", created=time.time())
        clone = Project.from_dict(payload, capture_baseline=False)
        clone.save()
    except Exception:
        shutil.rmtree(target)
        raise
    return clone
