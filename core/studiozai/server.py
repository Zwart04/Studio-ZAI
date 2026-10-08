"""Local web server: REST API + SSE progress + the static Studio ZAI UI."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__, ai, config, credentials, jobs, models, projects, service, typography
from .pipeline import download as download_pipeline
from .pipeline import subtitle, voice
from .utils.text import clock, sanitize_filename

app = FastAPI(title="Studio ZAI", version=__version__)


class NewProject(BaseModel):
    title: str = ""
    source: str = ""
    lang: str = "id"


class ProcessRequest(BaseModel):
    source: str
    count: int = Field(default=0, ge=0)
    analysis_mode: Literal["auto", "podcast"] = "auto"
    review_first: bool = True
    formats: list[Literal["portrait", "square", "landscape"]] = Field(default_factory=list)
    min_len: float = 0.0
    max_len: float = 0.0
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


class TranslateRequest(BaseModel):
    captions: list[dict[str, Any]]
    source: str = "id"
    target: str = "en"


class TrackFaceRequest(BaseModel):
    start: float
    end: float
    x: float = .5


@app.post("/api/source-upload")
async def upload_source(request: Request) -> dict[str, str]:
    import uuid
    from urllib.parse import unquote
    name = sanitize_filename(unquote(request.headers.get("x-filename", "video.mp4")), "video.mp4")
    directory = config.data_dir() / "imports"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid.uuid4().hex[:12]}-{name}"
    try:
        with path.open("wb") as output:
            async for chunk in request.stream():
                output.write(chunk)
        if path.stat().st_size == 0:
            raise HTTPException(400, "Berkas kosong")
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return {"path": str(path)}


@app.post("/api/projects/{project_id}/translate")
def translate_captions(project_id: str, payload: TranslateRequest) -> dict[str, Any]:
    from .pipeline import translation
    project = _project(project_id)
    if payload.source not in translation.LANGUAGES or payload.target not in translation.LANGUAGES:
        raise HTTPException(400, "Bahasa tidak didukung")
    def run(job):
        rows = translation.translate_captions(payload.captions, payload.source, payload.target,
            lambda p, m: job.report(p, "terjemahan", m))
        files = subtitle.write_subtitles([subtitle.Caption(**r) for r in rows],
            project.root / "translations" / job.id, payload.target)
        return {"captions": rows, "files": files}
    return jobs.MANAGER.submit("translation", f"Terjemahan {payload.source} → {payload.target}", run).as_dict()


@app.post("/api/projects/{project_id}/track-face")
def track_face(project_id: str, payload: TrackFaceRequest) -> dict[str, Any]:
    from .pipeline.framing import follow_face
    project = _project(project_id)
    if not 0 <= payload.start < payload.end <= project.duration or project.media_path() is None:
        raise HTTPException(400, "Rentang video tidak valid")
    return jobs.MANAGER.submit("framing", "Mengikuti wajah", lambda job: follow_face(
        str(project.media_path()), payload.start, payload.end, payload.x,
        lambda p, m: job.report(p, "crop", m))).as_dict()


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
    caption_variants: dict[str, list[dict[str, Any]]] | None = None
    caption_language: str | None = None
    # Editor timeline multi-track (video/media/teks/audio).
    timeline: dict[str, Any] | None = None


class AssetRequest(BaseModel):
    path: str


class ManualClip(BaseModel):
    start: float
    end: float
    canvas: Literal["portrait", "original", "square", "landscape"] = "portrait"


class BatchRenderRequest(BaseModel):
    clips: list[int]
    formats: list[str]


class TtsRequest(BaseModel):
    text: str
    lang: str = "id"
    voice_id: str | None = None
    clip: int | None = None


class CloneRequest(BaseModel):
    text: str
    sample: str
    lang: str = "id"
    model_id: str | None = None
    clip: int | None = None
    reference_text: str = ""


class SettingsUpdate(BaseModel):
    values: dict[str, Any]


class PromptRequest(BaseModel):
    prompt: str
    provider: str | None = None


class CloudSpeechRequest(BaseModel):
    text: str
    voice: str = "marin"
    language: str = "id"


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
    for key, value in {**settings, **credentials.read()}.items():
        if key.endswith("_api_key"):
            settings[key] = "***" if value else ""
    return settings


@app.post("/api/settings")
def post_settings(payload: SettingsUpdate) -> dict[str, Any]:
    service.update_settings(payload.values)
    return get_settings()


@app.get("/api/ai/providers")
def ai_providers() -> dict[str, Any]:
    return {"providers": ai.PROVIDERS, "voices": ai.VOICES}


@app.post("/api/ai/text")
def generate_text(payload: PromptRequest) -> dict[str, Any]:
    return jobs.MANAGER.submit("text", "Menyusun teks", lambda _: {"text": ai.text(payload.prompt)}).as_dict()


@app.post("/api/images")
def generate_image(payload: PromptRequest) -> dict[str, Any]:
    return jobs.MANAGER.submit("image", "Membuat gambar", lambda _: {"image": str(ai.image(payload.prompt, payload.provider))}).as_dict()


@app.get("/api/images")
def list_images() -> list[dict[str, str]]:
    return [{"path": str(p), "name": p.name} for p in sorted((config.data_dir() / "images").glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)]


@app.delete("/api/images/{name}")
def delete_image(name: str) -> dict[str, bool]:
    import re
    if not re.fullmatch(r"image-[a-f0-9]{12}\.png", name):
        raise HTTPException(400, "Nama gambar tidak valid")
    path = config.data_dir() / "images" / name
    path.unlink(missing_ok=True)
    path.with_suffix(".json").unlink(missing_ok=True)
    return {"ok": True}


@app.post("/api/ai/speech")
def cloud_speech(payload: CloudSpeechRequest) -> dict[str, Any]:
    return jobs.MANAGER.submit("tts", "Membuat suara online", lambda _: {"path": str(ai.speech(payload.text, payload.voice, payload.language))}).as_dict()


@app.post("/api/voice-sample")
async def upload_voice_sample(request: Request) -> dict[str, str]:
    import asyncio
    import uuid

    from .utils import ffmpeg
    directory = config.data_dir() / "voices"
    directory.mkdir(exist_ok=True)
    target = directory / f"sample-{uuid.uuid4().hex[:12]}.wav"
    temporary = target.with_suffix(".upload")
    size = 0
    try:
        with temporary.open("wb") as output:
            async for chunk in request.stream():
                size += len(chunk)
                if size > 100 * 1024 * 1024:
                    raise HTTPException(413, "Berkas contoh suara maksimal 100 MB")
                output.write(chunk)
        if not size:
            raise HTTPException(400, "Berkas contoh suara kosong")
        result = await asyncio.to_thread(
            ffmpeg.run_ffmpeg,
            ["-i", str(temporary), "-t", "30", "-vn", "-ar", "24000", "-ac", "1", str(target)],
            timeout=180,
        )
        if not result.ok:
            target.unlink(missing_ok=True)
            raise HTTPException(400, "Rekaman tidak dapat dibaca. Pilih berkas audio lain.")
    finally:
        temporary.unlink(missing_ok=True)
    return {"path": str(target)}


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


@app.get("/api/gallery")
def clip_gallery() -> list[dict[str, Any]]:
    """Browse saved clips across projects without loading their full timelines."""
    gallery: list[dict[str, Any]] = []
    for project in projects.list_projects():
        for clip in project.clips:
            available = {
                key: path for key, path in clip.files.items()
                if key in {"mp4", "mp4_portrait", "mp4_square", "mp4_landscape",
                           "thumb", "thumb_portrait", "thumb_square", "thumb_landscape"}
                and Path(path).is_file()
            }
            gallery.append({
                "project_id": project.id,
                "project_title": project.title,
                "index": clip.index,
                "storage_id": clip.storage_id,
                "title": clip.title or f"Klip {clip.index + 1}",
                "start": clip.start,
                "end": clip.end,
                "score": clip.score,
                "updated": project.updated,
                "files": available,
            })
    return sorted(gallery, key=lambda item: item["updated"], reverse=True)


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
            analysis_mode=payload.analysis_mode,
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
            if not payload.review_first:
                if payload.formats:
                    for fmt in dict.fromkeys(payload.formats):
                        service.render_clip(project, clip, job=job, canvas_override=fmt)
                else:
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


@app.post("/api/projects/{project_id}/clips")
def create_manual_clip(project_id: str, payload: ManualClip) -> dict[str, Any]:
    project = _project(project_id)
    if project.media_path() is None:
        raise HTTPException(400, "Video sumber belum tersimpan")
    if not 0 <= payload.start < payload.end <= project.duration or payload.canvas not in {"original", "portrait", "landscape", "square"}:
        raise HTTPException(400, "Rentang harus berada di dalam durasi video dan kanvas harus valid")
    clip = project.add_clip(projects.Clip(index=0, start=payload.start, end=payload.end,
        title=f"{project.title} · {clock(payload.start)}–{clock(payload.end)}", canvas=payload.canvas, crop="fit"))
    clip.captions = service.captions_for_range(project.transcript, clip.start, clip.end)
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


@app.post("/api/projects/{project_id}/batch-render")
def batch_render(project_id: str, payload: BatchRenderRequest) -> dict[str, Any]:
    project = _project(project_id)
    clip_ids = list(dict.fromkeys(payload.clips))
    formats = list(dict.fromkeys(payload.formats))
    if not clip_ids or not formats or len(formats) > 3:
        raise HTTPException(400, "Pilih minimal satu klip dan satu format")
    if any(fmt not in {"portrait", "square", "landscape"} for fmt in formats):
        raise HTTPException(400, "Format kanvas tidak valid")
    try:
        for index in clip_ids:
            project.clip(index)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    if project.media_path() is None:
        raise HTTPException(400, "Video sumber tidak ditemukan")

    # Capture storage IDs and edits now: queued work must not silently switch to
    # a different clip if another clip is removed or reordered before it starts.
    selected = [project.clip(index) for index in clip_ids]

    def render_state(clip: projects.Clip) -> dict[str, Any]:
        values = {key: value for key, value in clip.as_dict().items()
                  if key not in {"index", "files", "status", "title"}}
        values["voice_file"] = clip.files.get("voice")
        if values["voice_file"]:
            try:
                stat = Path(values["voice_file"]).stat()
                values["voice_revision"] = (stat.st_mtime_ns, stat.st_size)
            except OSError:
                values["voice_revision"] = None
        return values

    expected = {clip.storage_id: render_state(clip) for clip in selected}

    def run(job: jobs.Job) -> dict[str, Any]:
        total = len(clip_ids) * len(formats)
        exports: list[dict[str, Any]] = []

        class Progress:
            def __init__(self, position: int, index: int, fmt: str):
                self.position = position
                label = {"portrait": "9:16", "square": "1:1", "landscape": "16:9"}[fmt]
                self.label = f"{position + 1}/{total} · Klip {index + 1} · {label}"

            def report(self, progress: float, stage: str = "", message: str = "") -> None:
                fraction = max(0.0, min(1.0, (progress - 60) / 40))
                job.report(5 + 90 * (self.position + fraction) / total, "render batch", self.label)

        for position, (clip, fmt) in enumerate(
            (clip, fmt) for clip in selected for fmt in formats
        ):
            job.check_cancel()
            current = projects.load_project(project_id)
            latest = next((item for item in current.clips if item.storage_id == clip.storage_id), None)
            if latest is None or render_state(latest) != expected[clip.storage_id]:
                raise RuntimeError("Klip berubah saat menunggu. Pilih kembali klip lalu ulangi ekspor.")
            files = service.render_clip(
                project, clip, job=Progress(position, clip.index, fmt),
                canvas_override=fmt, persist=False,
            )
            job.check_cancel()
            current = projects.load_project(project_id)
            latest = next((item for item in current.clips if item.storage_id == clip.storage_id), None)
            if latest is None or render_state(latest) != expected[clip.storage_id]:
                raise RuntimeError("Klip berubah saat dirender. Ulangi ekspor untuk memakai edit terbaru.")
            latest.files[f"mp4_{fmt}"] = files[f"mp4_{fmt}"]
            if files.get(f"thumb_{fmt}"):
                latest.files[f"thumb_{fmt}"] = files[f"thumb_{fmt}"]
            current.save()
            exports.append({"index": latest.index, "format": fmt, "path": files[f"mp4_{fmt}"]})
        return {"exports": exports, "project": project_id}

    return jobs.MANAGER.submit("batch-render", "Render beberapa format", run).as_dict()


def _render_task(project_id: str, index: int):
    def run(job: jobs.Job) -> dict[str, Any]:
        project = projects.load_project(project_id)
        files = service.render_clip(project, project.clip(index), job=job)
        return {"files": files}

    return run


@app.post("/api/projects/{project_id}/clips/{index}/preview")
def preview_clip(project_id: str, index: int, payload: ClipUpdate | None = None) -> dict[str, Any]:
    """Render draf cepat klip (540x960) untuk pratinjau di editor."""
    project = _project(project_id)
    try:
        project.clip(index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    values = payload.model_dump(exclude_none=True) if payload else None
    job = jobs.MANAGER.submit("preview", f"Pratinjau klip {index + 1}", _preview_task(project_id, index, values))
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
        clip = current.clip(index)
        service.generate_captions_for_clip(current, clip, job=job)
        current.save()
        return {"captions": clip.captions}

    return jobs.MANAGER.submit("captions", "Subtitle otomatis", run).as_dict()


def _preview_task(project_id: str, index: int, values: dict | None = None):
    def run(job: jobs.Job) -> dict[str, Any]:
        project = projects.load_project(project_id)
        if values:
            project.update_clip(index, values)
        return service.render_preview(project, project.clip(index), job=job)

    return run


@app.get("/api/subtitle-presets")
def subtitle_presets() -> list[dict[str, str]]:
    """Daftar template tipografi untuk galeri di editor."""
    subtitle.PRESETS.update(typography.load())
    return subtitle.preset_list()


@app.post("/api/subtitle-presets")
def create_subtitle_preset(values: dict[str, Any]) -> dict[str, str]:
    try:
        key, style = typography.create(values)
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, str(exc)) from exc
    subtitle.PRESETS[key] = style
    return {"id": key}


@app.post("/api/projects/{project_id}/assets")
def add_project_asset(project_id: str, payload: AssetRequest) -> dict[str, Any]:
    """Salin berkas media pengguna ke folder proyek (dipakai timeline)."""
    project = _project(project_id)
    try:
        path = service.add_asset(project, payload.path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"path": path}


@app.post("/api/projects/{project_id}/assets-upload")
async def upload_project_logo(project_id: str, request: Request) -> dict[str, str]:
    import uuid
    from urllib.parse import unquote
    project = _project(project_id)
    name = sanitize_filename(Path(unquote(request.headers.get("x-filename", "logo.png"))).name, "logo.png")
    if Path(name).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(400, "Logo harus PNG, JPEG, atau WebP")
    directory = project.root / "assets"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"logo-{uuid.uuid4().hex[:12]}-{name}"
    total = 0
    try:
        with target.open("wb") as output:
            async for chunk in request.stream():
                total += len(chunk)
                if total > 30 * 1024**2:
                    raise HTTPException(413, "Logo maksimal 30 MB")
                output.write(chunk)
        if not total:
            raise HTTPException(400, "Berkas kosong")
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return {"path": str(target)}


@app.post("/api/projects/{project_id}/assets/upload")
async def upload_project_asset(project_id: str, request: Request) -> dict[str, str]:
    """Stream a dropped browser file into project storage without loading it into RAM."""
    import uuid
    from urllib.parse import unquote

    project = _project(project_id)
    raw_name = unquote(request.headers.get("x-filename", ""))
    name = sanitize_filename(raw_name, "media")
    allowed = {
        ".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi",
        ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp",
        ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".wma", ".aif", ".aiff",
    }
    if Path(name).suffix.lower() not in allowed:
        raise HTTPException(400, "Pilih berkas video, gambar, atau audio yang didukung")
    directory = project.root / "assets"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{uuid.uuid4().hex[:12]}-{name}"
    temporary = directory / f".{target.name}.upload"
    size = 0
    try:
        with temporary.open("wb") as output:
            async for chunk in request.stream():
                size += len(chunk)
                if size > 4 * 1024**3:
                    raise HTTPException(413, "Berkas maksimal 4 GB")
                output.write(chunk)
        if not size:
            raise HTTPException(400, "Berkas kosong")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return {"path": str(target)}


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
        lambda j: {"path": str(service.make_clone(project, payload.text, payload.sample, payload.lang, model_id=payload.model_id, for_clip=payload.clip, job=j, reference_text=payload.reference_text))},
    )
    return job.as_dict()


@app.get("/api/voices")
def list_voices() -> dict[str, Any]:
    tts_models = voice.tts_models()
    clone_models = voice.clone_models()
    runtime = {
        "piper": voice.piper_available(),
        "chatterbox": voice.chatterbox_available(),
        "zipvoice": voice.zipvoice_available(),
    }

    def runnable(model: dict[str, Any]) -> bool:
        if not models.manager.is_installed(model["id"]):
            return False
        if model["id"].startswith("chatterbox"):
            return runtime["chatterbox"]
        if model["id"] == "zipvoice-zh-en" or model["id"] == "supertonic-3-int8":
            return runtime["zipvoice"]
        return runtime["piper"]

    descriptors = [
        {**model, "installed": models.manager.is_installed(model["id"]), "runnable": runnable(model)}
        for model in (*tts_models, *clone_models)
    ]
    return {
        "piper": [m["id"] for m in tts_models if runnable(m) and not m.get("deprecated")],
        "clone": [m["id"] for m in clone_models if runnable(m)],
        "models": descriptors,
        "available": runtime,
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
            model_id=payload.model_id or settings.get("clone_model", "zipvoice-zh-en"),
            reference_text=payload.reference_text,
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
        previous = None
        last_emit = 0.0
        while True:
            job = jobs.MANAGER.get(job_id)
            # The event list is bounded (400 entries). An array-index cursor
            # permanently stalls after 400 reports. Follow the latest event.
            latest = job.events[-1] if job.events else None
            if latest is not None and (latest is not previous or time.time() - last_emit >= 1):
                payload = latest.as_dict()
                payload["elapsed"] = int(time.time() - job.created)
                idle = time.time() - latest.time
                if idle >= 10:
                    payload["message"] += f" · tahap ini masih berjalan ({int(idle)} dtk tanpa hasil baru)"
                previous = latest
                last_emit = time.time()
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
