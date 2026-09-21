"""Project storage: source media, transcript, clips and edits (JSON on disk)."""

from __future__ import annotations

import json
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import config
from .utils.text import sanitize_filename

DEFAULT_CROP = "center"
DEFAULT_SUBTITLE_PRESET = "clean"


@dataclass
class Clip:
    index: int
    start: float
    end: float
    title: str = ""
    score: float = 0.0
    reason: str = ""
    crop: str = DEFAULT_CROP
    subtitle_preset: str = DEFAULT_SUBTITLE_PRESET
    audio_mode: str = "original"
    original_volume: float = 0.25
    voice_volume: float = 1.0
    voice_id: str = ""
    voice_clone_sample: str = ""
    captions: list[dict[str, Any]] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    status: str = "draft"

    @property
    def duration(self) -> float:
        return round(max(0.0, self.end - self.start), 3)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["duration"] = self.duration
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Clip:
        allowed = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        allowed.pop("duration", None)
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
    _history: list[dict[str, Any]] = field(default_factory=list, repr=False)

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
        path = self.clips_dir / f"{index:03d}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ------------------------------------------------------------------ crud
    def save(self) -> Path:
        self.updated = time.time()
        self.root.mkdir(parents=True, exist_ok=True)
        payload = self.as_dict()
        self.project_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
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
            "clips": [c.as_dict() for c in self.clips],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
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
        )
        project.clips = [Clip.from_dict(c) for c in data.get("clips", [])]
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
        for key, value in values.items():
            if hasattr(clip, key) and key not in {"index", "files"}:
                setattr(clip, key, value)
        if clip.end <= clip.start:
            clip.end = clip.start + 1.0
        return clip

    def remove_clip(self, index: int) -> None:
        self.snapshot()
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
        right = Clip.from_dict(clip.as_dict())
        right.start = at
        right.files = {}
        right.status = "draft"
        clip.end = at
        clip.files = {**clip.files}
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


def load_project(project_id: str) -> Project:
    path = config.projects_dir() / project_id / "project.json"
    if not path.exists():
        raise KeyError(f"proyek {project_id} tidak ditemukan")
    return Project.from_dict(json.loads(path.read_text(encoding="utf-8")))


def delete_project(project_id: str) -> None:
    directory = config.projects_dir() / project_id
    if directory.exists():
        shutil.rmtree(directory, ignore_errors=True)


def duplicate_project(project_id: str) -> Project:
    project = load_project(project_id)
    clone = Project.create(f"{project.title} (salinan)", project.source, project.source_kind, project.language)
    clone.transcript = project.transcript
    clone.duration = project.duration
    clone.width = project.width
    clone.height = project.height
    clone.clips = [Clip.from_dict(c.as_dict()) for c in project.clips]
    clone.renumber()
    clone.save()
    return clone
