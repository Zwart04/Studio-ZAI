"""Local web server: REST API + SSE progress + the static Studio ZAI UI."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__, config, jobs, models, projects, service
from .pipeline import download as download_pipeline
from .pipeline import subtitle, voice
from .utils.text import clock

app = FastAPI(title="Studio ZAI", version=__version__)


class NewProject(BaseModel):
    title: str = ""
    source: str = ""
    lang: str = "id"


class ProcessRequest(BaseModel):
    source: str
    count: int = 5
    min_len: float = 15.0
    max_len: float = 60.0
    use_transcript: bool = True
    use_llm: bool = False
    model: str | None = None
    quality: str = "720p"
    format_id: str | None = None
    subtitle_position: str = "bottom"  # bottom | middle | top | off
    canvas: str = "portrait"  # portrait | original | square | landscape
    audio_lang: str | None = None  # pilih track audio multi-bahasa (mis. "id")
    audio_mode: str = "original"  # original | voice (ganti) | mix (campur)
    voice_id: str | None = None  # model suara untuk sulih suara TTS


class LinkInfoRequest(BaseModel):
    url: str


class ClipUpdate(BaseModel):
    start: float | None = None
    end: float | None = None
    title: str | None = None
    crop: str | None = None
    canvas: str | None = None
    subtitle_preset: str | None = None
    subtitle_position: str | None = None
    audio_mode: str | None = None
    original_volume: float | None = None
    voice_volume: float | None = None
    captions: list[dict[str, Any]] | None = None
    # Editor timeline multi-track (video/media/teks/audio).
    timeline: dict[str, Any] | None = None


class AssetRequest(BaseModel):
    path: str


class TtsRequest(BaseModel):
    text: str
    lang: str = "id"
    voice_id: str | None = None
    clip: int | None = None


class CloneRequest(BaseModel):
    text: str
    sample: str
    lang: str = "id"
    clip: int | None = None


class SettingsUpdate(BaseModel):
    values: dict[str, Any]


def _project(project_id: str) -> projects.Project:
    try:
        return projects.load_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --------------------------------------------------------------------------- meta


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "version": __version__, "app": "Studio ZAI"}


@app.on_event("startup")
def _startup_cleanup() -> None:
    try:
        removed = config.cleanup_stale_transcript_chunks()
        if removed:
            print(f"[studiozai] membersihkan {removed} file chunk yatim")
    except Exception:  # noqa: BLE001, S110 - pembersihan opsional saat start
        pass


@app.get("/api/doctor")
def doctor() -> dict[str, Any]:
    return service.doctor()


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    settings = dict(config.load_settings())
    if settings.get("llm_api_key"):
        settings["llm_api_key"] = "***"
    return settings


@app.post("/api/settings")
def post_settings(payload: SettingsUpdate) -> dict[str, Any]:
    return service.update_settings(payload.values)


# --------------------------------------------------------------------------- models


@app.get("/api/models")
def list_models() -> dict[str, Any]:
    return {
        "hardware": models.manager.detect_hardware(),
        "tier": models.manager.resolve_tier(models.manager.detect_hardware(), config.load_settings().get("lang", "id")),
        "models": models.manager.status(),
    }


@app.post("/api/models/{model_id}/download")
def download_model(model_id: str) -> dict[str, Any]:
    try:
        models.manager.get_model(model_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    job = jobs.MANAGER.submit("model", f"Unduh {model_id}", _download_task(model_id))
    return job.as_dict()


def _download_task(model_id: str):
    def run(job: jobs.Job) -> dict[str, Any]:
        path = models.manager.download(
            model_id, lambda p, m: job.report(p, "unduh", m)
        )
        return {"path": str(path)}

    return run


@app.delete("/api/models/{model_id}")
def remove_model(model_id: str) -> dict[str, Any]:
    models.manager.remove(model_id)
    return {"removed": model_id}


@app.post("/api/models/benchmark/{model_id}")
def benchmark_model(model_id: str, sample: str = "") -> dict[str, Any]:
    job = jobs.MANAGER.submit(
        "benchmark", f"Benchmark {model_id}", lambda j: service.benchmark_clone(model_id, sample or None)
    )
    return job.as_dict()


# --------------------------------------------------------------------------- projects


@app.get("/api/projects")
def list_projects() -> list[dict[str, Any]]:
    return [
        {
            "id": p.id,
            "title": p.title,
            "clips": len(p.clips),
            "duration": p.duration,
            "duration_label": clock(p.duration),
            "language": p.language,
            "updated": p.updated,
            "thumb": next((c.files.get("thumb") for c in p.clips if c.files.get("thumb")), None),
        }
        for p in projects.list_projects()
    ]


@app.post("/api/projects")
def create_project(payload: NewProject) -> dict[str, Any]:
    project = projects.Project.create(payload.title, payload.source, language=payload.lang)
    if payload.source:
        jobs.MANAGER.submit("ingest", f"Siapkan {project.title}", _ingest_task(project.id, payload.source))
    return project.as_dict()


@app.post("/api/link-info")
def link_info(payload: LinkInfoRequest) -> dict[str, Any]:
    """Baca metadata link (judul, durasi, daftar kualitas) tanpa mengunduh."""
    try:
        info = download_pipeline.fetch_info(
            payload.url,
            cookies=config.load_settings().get("cookies_path") or None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return info


def _ingest_task(project_id: str, source: str):
    def run(job: jobs.Job) -> dict[str, Any]:
        project = projects.load_project(project_id)
        path = service.ingest(project, source, cookies=config.load_settings().get("cookies_path") or None, job=job)
        return {"media": str(path), "duration": project.duration}

    return run


@app.get("/api/projects/{project_id}")
def get_project(project_id: str) -> dict[str, Any]:
    return _project(project_id).as_dict()


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str) -> dict[str, Any]:
    try:
        projects.delete_project(project_id)
    except KeyError as exc:
        # id tidak valid/berbahaya -> 404, bukan 500 (dan tidak menghapus apa pun)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": project_id}


@app.post("/api/projects/{project_id}/duplicate")
def duplicate_project(project_id: str) -> dict[str, Any]:
    try:
        return projects.duplicate_project(project_id).as_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/process")
def process_project(project_id: str, payload: ProcessRequest) -> dict[str, Any]:
    project = _project(project_id)
    job = jobs.MANAGER.submit("process", f"Proses {project.title}", _process_task(project_id, payload))
    return job.as_dict()


def _narration_text(project: Any, clip: Any) -> str:
    """Gabungkan transkrip yang jatuh di rentang klip -> teks narasi sulih suara."""
    parts: list[str] = []
    for segment in (project.transcript or {}).get("segments", []):
        try:
            start = float(segment.get("start", 0.0))
            end = float(segment.get("end", 0.0))
        except (AttributeError, TypeError, ValueError):
            continue
        if end > clip.start and start < clip.end:
            text = str(segment.get("text", "")).strip()
            if text:
                parts.append(text)
    return " ".join(parts).strip()


def _process_task(project_id: str, payload: ProcessRequest):
    def run(job: jobs.Job) -> dict[str, Any]:
        project = projects.load_project(project_id)
        if not project.source:
            fmt = payload.format_id or download_pipeline.pick_format_id([], payload.quality)
            service.ingest(
                project,
                payload.source,
                cookies=config.load_settings().get("cookies_path") or None,
                job=job,
                format_id=fmt,
                audio_lang=payload.audio_lang,
            )
        service.generate_clips(
            project,
            count=payload.count,
            min_len=payload.min_len,
            max_len=payload.max_len,
            use_llm=payload.use_llm,
            use_transcript=payload.use_transcript,
            job=job,
        )
        for clip in list(project.clips):
            clip.subtitle_position = payload.subtitle_position
            clip.canvas = payload.canvas
            if payload.audio_mode != "original":
                # Sulih suara: buat narasi TTS dari transkrip klip lalu ganti/campur audio.
                text = _narration_text(project, clip)
                if text:
                    out_path = project.clip_dir(clip.index) / "voice.wav"
                    try:
                        voice.synthesize(text, out_path, voice_id=payload.voice_id or None)
                        clip.files["voice"] = str(out_path)
                        clip.audio_mode = payload.audio_mode
                        if payload.voice_id:
                            clip.voice_id = payload.voice_id
                    except Exception as exc:  # noqa: BLE001 - narasi opsional, tetap render klipnya
                        job.report(60.0, "sulih suara gagal", str(exc)[:140])
            project.save()
            service.render_clip(project, clip, job=job)
        return {"clips": len(project.clips), "project": projects.load_project(project_id).as_dict()}

    return run


@app.patch("/api/projects/{project_id}/clips/{index}")
def update_clip(project_id: str, index: int, payload: ClipUpdate) -> dict[str, Any]:
    project = _project(project_id)
    values = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        clip = project.update_clip(index, values)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    project.save()
    return clip.as_dict()


@app.delete("/api/projects/{project_id}/clips/{index}")
def delete_clip(project_id: str, index: int) -> dict[str, Any]:
    project = _project(project_id)
    project.remove_clip(index)
    project.save()
    return {"clips": [c.as_dict() for c in project.clips]}


@app.post("/api/projects/{project_id}/clips/{index}/split")
def split_clip(project_id: str, index: int, at: float) -> dict[str, Any]:
    project = _project(project_id)
    try:
        project.split_clip(index, at)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    project.save()
    return {"clips": [c.as_dict() for c in project.clips]}


@app.post("/api/projects/{project_id}/clips/{index}/move")
def move_clip(project_id: str, index: int, delta: int) -> dict[str, Any]:
    project = _project(project_id)
    project.move_clip(index, delta)
    project.save()
    return {"clips": [c.as_dict() for c in project.clips]}


@app.post("/api/projects/{project_id}/clips/{index}/render")
def render_clip(project_id: str, index: int) -> dict[str, Any]:
    project = _project(project_id)
    try:
        project.clip(index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    job = jobs.MANAGER.submit("render", f"Render klip {index + 1}", _render_task(project_id, index))
    return job.as_dict()


def _render_task(project_id: str, index: int):
    def run(job: jobs.Job) -> dict[str, Any]:
        project = projects.load_project(project_id)
        files = service.render_clip(project, project.clip(index), job=job)
        return {"files": files}

    return run


@app.post("/api/projects/{project_id}/clips/{index}/preview")
def preview_clip(project_id: str, index: int) -> dict[str, Any]:
    """Render draf cepat klip (540x960) untuk pratinjau di editor."""
    project = _project(project_id)
    try:
        project.clip(index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    job = jobs.MANAGER.submit("preview", f"Pratinjau klip {index + 1}", _preview_task(project_id, index))
    return job.as_dict()


@app.post("/api/projects/{project_id}/clips/{index}/captions")
def generate_clip_captions(project_id: str, index: int) -> dict[str, Any]:
    project = _project(project_id)
    try:
        project.clip(index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    def run(job: jobs.Job) -> dict[str, Any]:
        current = projects.load_project(project_id)
        service.ensure_transcript(current, job=job)
        clip = current.clip(index)
        service.refresh_captions(current, clip)
        current.save()
        return {"captions": clip.captions}

    return jobs.MANAGER.submit("captions", "Subtitle otomatis", run).as_dict()


def _preview_task(project_id: str, index: int):
    def run(job: jobs.Job) -> dict[str, Any]:
        project = projects.load_project(project_id)
        return service.render_preview(project, project.clip(index), job=job)

    return run


@app.get("/api/subtitle-presets")
def subtitle_presets() -> list[dict[str, str]]:
    """Daftar template tipografi untuk galeri di editor."""
    return subtitle.preset_list()


@app.post("/api/projects/{project_id}/assets")
def add_project_asset(project_id: str, payload: AssetRequest) -> dict[str, Any]:
    """Salin berkas media pengguna ke folder proyek (dipakai timeline)."""
    project = _project(project_id)
    try:
        path = service.add_asset(project, payload.path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"path": path}


@app.post("/api/projects/{project_id}/export")
def export_project(project_id: str) -> dict[str, Any]:
    _project(project_id)
    job = jobs.MANAGER.submit("export", "Export gabungan", _export_task(project_id))
    return job.as_dict()


def _export_task(project_id: str):
    def run(job: jobs.Job) -> dict[str, Any]:
        project = projects.load_project(project_id)
        path = service.export_all(project, job=job)
        return {"path": str(path)}

    return run


@app.post("/api/projects/{project_id}/tts")
def project_tts(project_id: str, payload: TtsRequest) -> dict[str, Any]:
    project = _project(project_id)
    job = jobs.MANAGER.submit(
        "tts", "Buat suara", lambda j: {"path": str(service.make_voice(project, payload.text, payload.lang, payload.voice_id, payload.clip, j))}
    )
    return job.as_dict()


@app.post("/api/projects/{project_id}/clone")
def project_clone(project_id: str, payload: CloneRequest) -> dict[str, Any]:
    project = _project(project_id)
    job = jobs.MANAGER.submit(
        "clone",
        "Kloning suara",
        lambda j: {"path": str(service.make_clone(project, payload.text, payload.sample, payload.lang, for_clip=payload.clip, job=j))},
    )
    return job.as_dict()


@app.get("/api/voices")
def list_voices() -> dict[str, Any]:
    return {
        "piper": [m["id"] for m in voice.tts_models() if models.manager.is_installed(m["id"])],
        "clone": [m["id"] for m in voice.clone_models() if models.manager.is_installed(m["id"])],
        "available": {"piper": voice.piper_available(), "chatterbox": voice.chatterbox_available()},
        "default": {"id": voice.default_voice("id"), "en": voice.default_voice("en")},
    }


@app.post("/api/tts")
def quick_tts(payload: TtsRequest) -> dict[str, Any]:
    job = jobs.MANAGER.submit("tts", "Buat suara", _quick_tts_task(payload))
    return job.as_dict()


def _quick_tts_task(payload: TtsRequest):
    def run(job: jobs.Job) -> dict[str, Any]:
        out_dir = config.data_dir() / "voices"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"tts-{int(time.time())}.wav"
        voice.synthesize(
            payload.text,
            target,
            voice_id=payload.voice_id,
            lang=payload.lang,
            progress_cb=lambda p, m: job.report(p, "membuat suara", m),
        )
        return {"path": str(target)}

    return run


@app.post("/api/clone")
def quick_clone(payload: CloneRequest) -> dict[str, Any]:
    job = jobs.MANAGER.submit("clone", "Kloning suara", _quick_clone_task(payload))
    return job.as_dict()


def _quick_clone_task(payload: CloneRequest):
    def run(job: jobs.Job) -> dict[str, Any]:
        settings = config.load_settings()
        out_dir = config.data_dir() / "voices"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"clone-{int(time.time())}.wav"
        voice.clone_speak(
            payload.text,
            target,
            sample=payload.sample,
            language=payload.lang,
            model_id=settings.get("clone_model", "chatterbox-base"),
            progress_cb=lambda p, m: job.report(p, "mengkloning", m),
        )
        return {"path": str(target)}

    return run


@app.get("/api/benchmarks")
def benchmarks() -> dict[str, Any]:
    return config.load_settings().get("benchmarks", {})


# --------------------------------------------------------------------------- jobs


@app.get("/api/jobs")
def list_jobs() -> list[dict[str, Any]]:
    return [job.as_dict() for job in jobs.MANAGER.list()]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    try:
        return jobs.MANAGER.get(job_id).as_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict[str, Any]:
    try:
        return jobs.MANAGER.cancel(job_id).as_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}/events")
def job_events(job_id: str) -> StreamingResponse:
    try:
        jobs.MANAGER.get(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    def stream():
        cursor = 0
        while True:
            job = jobs.MANAGER.get(job_id)
            while cursor < len(job.events):
                payload = job.events[cursor].as_dict()
                cursor += 1
                yield f"data: {json.dumps({'type': 'progress', **payload})}\n\n"
            if job.status in {"done", "error", "cancelled"}:
                yield f"data: {json.dumps({'type': 'end', **job.as_dict()})}\n\n"
                break
            time.sleep(0.25)

    return StreamingResponse(stream(), media_type="text/event-stream")


# --------------------------------------------------------------------------- media


@app.get("/api/media")
def media(path: str) -> FileResponse:
    target = Path(path)
    try:
        resolved = target.resolve()
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="berkas tidak ditemukan")
    roots = [config.data_dir().resolve()]
    if not any(root in resolved.parents or resolved == root for root in roots):
        raise HTTPException(status_code=403, detail="akses di luar folder data")
    return FileResponse(resolved)


def mount_ui() -> None:
    ui = config.ui_dir()
    if ui.is_dir():
        app.mount("/", StaticFiles(directory=str(ui), html=True), name="ui")


mount_ui()


def run(host: str = "127.0.0.1", port: int = 8737) -> None:
    import uvicorn

    # In a windowed build (PyInstaller console=False) sys.stdout/sys.stderr are
    # None, which makes uvicorn's default logging config crash on isatty().
    # Skipping it keeps the server usable from a GUI-only executable.
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_config=None,
        log_level=None,
        access_log=False,
    )
