"""Background job queue with progress events (used by the CLI and the SSE UI)."""

from __future__ import annotations

import threading
import time
import traceback
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobEvent:
    progress: float
    stage: str
    message: str = ""
    time: float = field(default_factory=time.time)

    def as_dict(self) -> dict[str, Any]:
        return {
            "progress": round(self.progress, 2),
            "stage": self.stage,
            "message": self.message,
            "time": self.time,
        }


class JobCancelled(RuntimeError):
    pass


@dataclass
class Job:
    id: str
    kind: str
    title: str
    status: str = "queued"
    progress: float = 0.0
    stage: str = "menunggu"
    message: str = ""
    error: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    created: float = field(default_factory=time.time)
    finished: float | None = None
    events: list[JobEvent] = field(default_factory=list)
    cancel_requested: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "status": self.status,
            "progress": round(self.progress, 1),
            "stage": self.stage,
            "message": self.message,
            "error": self.error,
            "result": self.result,
            "created": self.created,
            "finished": self.finished,
        }

    def report(self, progress: float, stage: str = "", message: str = "") -> None:
        if self.cancel_requested:
            raise JobCancelled("dibatalkan pengguna")
        self.progress = max(0.0, min(100.0, float(progress)))
        if stage:
            self.stage = stage
        if message:
            self.message = message
        self.events.append(JobEvent(self.progress, self.stage, self.message))
        del self.events[:-400]

    def check_cancel(self) -> None:
        if self.cancel_requested:
            raise JobCancelled("dibatalkan pengguna")


class JobManager:
    """Runs pipeline functions on worker threads while keeping progress queryable."""

    def __init__(self, max_workers: int = 2) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._slots = threading.Semaphore(max_workers)

    def submit(self, kind: str, title: str, fn: Callable[[Job], dict[str, Any] | None]) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], kind=kind, title=title)
        with self._lock:
            self._jobs[job.id] = job
        threading.Thread(target=self._run, args=(job, fn), daemon=True).start()
        return job

    def _run(self, job: Job, fn: Callable[[Job], dict[str, Any] | None]) -> None:
        with self._slots:
            job.status = "running"
            job.report(1.0, "mulai")
            try:
                result = fn(job) or {}
                job.result = result
                job.status = "done"
                job.report(100.0, "selesai", "")
            except JobCancelled:
                job.status = "cancelled"
                job.stage = "dibatalkan"
                job.events.append(JobEvent(job.progress, "dibatalkan", ""))
            except Exception as exc:  # noqa: BLE001 - surface any pipeline failure to the UI
                job.status = "error"
                job.error = f"{type(exc).__name__}: {exc}"
                job.message = job.error
                job.events.append(JobEvent(job.progress, "error", job.error))
                job.result["traceback"] = traceback.format_exc(limit=8)
            finally:
                job.finished = time.time()

    def get(self, job_id: str) -> Job:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(f"job {job_id} tidak ditemukan")
            return self._jobs[job_id]

    def list(self, limit: int = 50) -> list[Job]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda j: j.created, reverse=True)
        return jobs[:limit]

    def cancel(self, job_id: str) -> Job:
        job = self.get(job_id)
        job.cancel_requested = True
        return job

    def prune(self, keep: int = 100) -> None:
        with self._lock:
            ordered = sorted(self._jobs.values(), key=lambda j: j.created, reverse=True)
            for job in ordered[keep:]:
                self._jobs.pop(job.id, None)


MANAGER = JobManager()
