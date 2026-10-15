"""Reusable low-resolution edit media, prepared one clip at a time."""
import hashlib
import threading

from . import cache, jobs, projects
from .pipeline import render
from .utils import ffmpeg

_LOCK = threading.Lock()
_ACTIVE = {}


def destination(project, clip):
    media = project.media_path()
    identity = cache.file_identity(media) if media else project.source_url
    key = hashlib.sha256(repr((identity, clip.start, clip.end, "edit-v1")).encode()).hexdigest()[:20]
    return project.clip_dir(clip.index) / f"edit-{key}.mp4"


def ready(project, clip):
    path = destination(project, clip)
    if path.is_file():
        return {"path": str(path), "offset": clip.start, "end": clip.end}
    return None


def prepare(project, clip, job=None):
    from . import service
    with projects.project_lock(f"edit:{project.id}:{clip.storage_id}"):
        cached = ready(project, clip)
        if cached:
            return cached
        source, offset = service._resolve_render_media(project, clip, job)
        target = destination(project, clip)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".partial.mp4")
        args = [
            "-ss", str(max(0, clip.start - offset)), "-threads", "1", "-i", str(source),
            "-t", str(clip.duration), "-map", "0:v:0", "-map", "0:a:0?",
            "-vf", "scale=640:360:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1",
            "-filter_threads", "1", "-r", "24", *render.encoder_args("preview"),
            "-threads", str(render.threads_per_ffmpeg()), "-c:a", "aac", "-b:a", "96k",
            "-movflags", "+faststart", str(temporary)]
        try:
            result = ffmpeg.run_ffmpeg(args, total_duration=clip.duration,
                progress_cb=(lambda _: job.check_cancel()) if job else None, timeout=900)
            if not result.ok:
                raise RuntimeError("Preview ringan gagal dibuat; sumber asli tetap tersedia.")
            ffmpeg.validate_video(temporary, duration=clip.duration)
            temporary.replace(target)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        return ready(project, clip)


def enqueue(project_id):
    with _LOCK:
        previous = _ACTIVE.get(project_id)
        if previous and previous.status in {"queued", "running"}:
            return previous

        def run(job):
            result = {"ready": 0, "failed": []}
            project = projects.load_project(project_id)
            identities = [c.storage_id for c in project.clips]
            for number, identity in enumerate(identities):
                job.check_cancel()
                project = projects.load_project(project_id)
                clip = next((c for c in project.clips if c.storage_id == identity), None)
                if clip is None:
                    continue
                job.report(number / max(1, len(identities)) * 100, "preview bertahap", f"Klip {number + 1}/{len(identities)}")
                try:
                    prepare(project, clip, job)
                    result["ready"] += 1
                except jobs.JobCancelled:
                    raise
                except (RuntimeError, ValueError, FileNotFoundError, OSError):
                    result["failed"].append(identity)
            return result

        job = jobs.MANAGER.submit("prepare-previews", "Siapkan preview ringan", run)
        _ACTIVE[project_id] = job
        return job
