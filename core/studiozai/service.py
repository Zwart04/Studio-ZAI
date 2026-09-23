"""High-level orchestration shared by the CLI, the web server and the tests."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import config, credentials, models, projects
from .jobs import Job
from .pipeline import crop as crop_mod
from .pipeline import download, highlight, probe, render, subtitle, transcribe, voice
from .pipeline import timeline as timeline_mod
from .utils import ffmpeg
from .utils.text import clock, human_size, sanitize_filename

Report = Callable[[float, str, str], None]


def _emit_progress(sse: Any, prog: float, msg: str) -> None:
    """Emit a progress SSE event without touching a job dict."""
    try:
        sse.send({"type": "progress", "progress": round(min(99.0, max(0.0, prog)), 1), "message": msg})
    except Exception:  # noqa: BLE001, S110 - progres SSE bersifat best-effort
        pass


def _report(job: Job | None, prog: float, stage: str, message: str = "") -> None:
    if job is None:
        return
    job.report(prog, stage, message)


# --------------------------------------------------------------------------- doctor


def doctor() -> dict[str, Any]:
    hw = models.manager.detect_hardware()
    tier = models.manager.resolve_tier(hw, config.load_settings().get("lang", "id"))
    optional = {
        "yt_dlp": _module_ok("yt_dlp"),
        "faster_whisper": transcribe.asr_available(),
        "piper": voice.piper_available(),
        "chatterbox": voice.chatterbox_available(),
        "cuda": _cuda_available(),
        "pywebview": _module_ok("webview"),
    }
    installed = [m["id"] for m in models.manager.status() if m["installed"]]
    problems: list[str] = []
    if not ffmpeg.ffmpeg_available():
        problems.append("FFmpeg/FFprobe tidak ditemukan di PATH (wajib untuk semua fitur media).")
    if not optional["yt_dlp"]:
        problems.append("yt-dlp belum terpasang: pip install -e \"core[media]\"")
    if not optional["faster_whisper"]:
        problems.append("faster-whisper belum terpasang (subtitle otomatis mati): pip install -e \"core[asr]\"")
    if not optional["piper"]:
        problems.append("piper-tts belum terpasang (voiceover mati): pip install -e \"core[tts]\"")
    return {
        "version": _version(),
        "hardware": hw,
        "tier": tier,
        "optional": optional,
        "installed_models": installed,
        "data_dir": str(config.data_dir()),
        "models_dir": str(config.models_dir()),
        "disk_free": human_size(hw.get("disk_free_gb", 0) * 1024**3) if hw.get("disk_free_gb") else "?",
        "encoder": ffmpeg.detect_h264_encoder() if ffmpeg.ffmpeg_available() else None,
        "problems": problems,
    }


def _module_ok(name: str) -> bool:
    try:
        __import__(name)
    except ImportError:
        return False
    return True


def _cuda_available() -> bool:
    try:
        import torch  # type: ignore

        return bool(torch.cuda.is_available())
    except ImportError:
        return False


def _version() -> str:
    from . import __version__

    return __version__


# --------------------------------------------------------------------------- ingest


def _strip_embedded_subtitles(path: Path) -> Path:
    """Buang track subtitle/data bawaan dari berkas kerja.

    Video dari YouTube/media lain kadang membawa track subtitle sendiri. Kalau
    dibiarkan, pemutar menampilkan subtitle bawaan itu DI ATAS subtitle hasil
    Studio ZAI sehingga terlihat dobel. Remux stream-copy (cepat, tanpa
    re-encode) hanya dijalankan bila memang ada track subtitle/data.
    """
    try:
        streams = ffmpeg.ffprobe_json(path).get("streams", [])
    except Exception:  # noqa: BLE001 - kalau gagal dibaca, lanjut tanpa bersih-bersih
        return path
    if not any(stream.get("codec_type") in {"subtitle", "data"} for stream in streams):
        return path

    cleaned = path.with_name(f"{path.stem}.nosub{path.suffix}")
    result = ffmpeg.run_ffmpeg(
        ["-i", str(path), "-map", "0:v?", "-map", "0:a?", "-c", "copy", "-sn", "-dn", str(cleaned)],
        timeout=900,
    )
    if result.ok and cleaned.exists() and cleaned.stat().st_size > 1024:
        path.unlink(missing_ok=True)
        cleaned.replace(path)
    else:
        cleaned.unlink(missing_ok=True)
    return path


def ingest(
    project: projects.Project,
    source: str,
    cookies: str | None = None,
    job: Job | None = None,
    format_id: str | None = None,
    audio_lang: str | None = None,
) -> Path:
    """Bring the source video into the project (download for URLs, copy for local files)."""
    project.source_dir.mkdir(parents=True, exist_ok=True)
    if download.is_url(source):
        _report(job, 2, "mengunduh", "menghubungi sumber")
        info = download.download(
            source,
            project.source_dir,
            cookies=cookies or None,
            format_id=format_id,
            audio_lang=audio_lang,
            progress_cb=lambda p, m: _report(job, 3 + p * 0.32, "mengunduh", m),
        )
        project.source = info["path"]
        project.source_kind = "url"
        project.title = info["title"]
    else:
        src_path = Path(source)
        if not src_path.exists():
            raise FileNotFoundError(f"berkas tidak ditemukan: {source}")
        _report(job, 5, "menyalin", "menyalin berkas lokal")
        target = project.source_dir / src_path.name
        if src_path.resolve() != target.resolve():
            shutil.copy2(src_path, target)
        project.source = str(target)
        project.source_kind = "local"
        if not project.title:
            project.title = src_path.stem

    _report(job, 36, "memeriksa", "membersihkan subtitle bawaan bila ada")
    project.source = str(_strip_embedded_subtitles(Path(project.source)))

    _report(job, 38, "memeriksa", "membaca metadata media")
    info = probe.probe(project.source)
    project.duration = info.duration
    project.width = info.width
    project.height = info.height
    project.save()
    _report(job, 40, "siap", f"durasi {clock(info.duration)}")
    return Path(project.source)


def ensure_transcript(
    project: projects.Project,
    model_id: str | None = None,
    lang: str | None = None,
    job: Job | None = None,
) -> dict[str, Any]:
    if project.transcript.get("segments"):
        return project.transcript
    media = project.media_path()
    if media is None:
        raise FileNotFoundError("media sumber tidak ditemukan")
    settings = config.load_settings()
    model_id = model_id or settings.get("asr_model", "whisper-small-int8")
    _report(job, 45, "menranskripsi", f"model {model_id}")
    transcript = transcribe.transcribe(
        media,
        model_id=model_id,
        lang=lang or project.language,
        progress_cb=lambda p, m: _report(job, 45 + p * 0.3, "menranskripsi", m),
    )
    project.transcript = transcript
    if transcript.get("language"):
        project.language = str(transcript["language"])[:5]
    project.save()
    return transcript


# --------------------------------------------------------------------------- clipping


def captions_for_range(
    transcript: dict[str, Any],
    start: float,
    end: float,
) -> list[dict[str, Any]]:
    """Word-accurate captions for a clip window, with clip-relative timestamps."""
    words: list[dict[str, Any]] = []
    for segment in transcript.get("segments", []):
        for word in segment.get("words") or []:
            if word.get("end", 0) > start and word.get("start", 0) < end:
                words.append(
                    {
                        "word": word.get("word", ""),
                        "start": max(0.0, float(word["start"]) - start),
                        "end": max(0.0, float(word["end"]) - start),
                    }
                )
    if not words:
        for segment in transcript.get("segments", []):
            if segment.get("end", 0) > start and segment.get("start", 0) < end:
                words.append(
                    {
                        "word": segment.get("text", "").strip(),
                        "start": max(0.0, float(segment["start"]) - start),
                        "end": max(0.0, float(segment["end"]) - start),
                    }
                )
    return [c.as_dict() for c in subtitle.group_words(words)]


def generate_clips(
    project: projects.Project,
    count: int = 5,
    min_len: float = highlight.DEFAULT_MIN_LEN,
    max_len: float = highlight.DEFAULT_MAX_LEN,
    use_llm: bool = False,
    use_transcript: bool = True,
    job: Job | None = None,
) -> list[projects.Clip]:
    media = project.media_path()
    if media is None:
        raise FileNotFoundError("media sumber tidak ditemukan")
    _floor, _ceiling = highlight.clip_count_targets(project.duration or 0, count)

    transcript = None
    if use_transcript and transcribe.asr_available():
        try:
            transcript = ensure_transcript(project, job=job)
        except RuntimeError:
            transcript = None

    _report(job, 78, "menganalisis", "mencari momen terbaik")
    candidates = highlight.analyze_media(
        media,
        transcript=transcript if use_transcript else None,
        count=count,
        min_len=min_len,
        max_len=max_len,
        video_duration=project.duration or 0,
        progress_cb=lambda p, m: _report(job, 78 + p * 0.12, "menganalisis", m),
    )

    settings = config.load_settings()
    if use_llm and transcript:
        llm_rows = highlight.rank_with_llm(
            transcript,
            count=count,
            base_url=settings.get("llm_base_url") or "http://127.0.0.1:11434/v1",
            model=settings.get("llm_model") or "qwen2.5:7b",
            api_key=credentials.read().get("llm_api_key") or settings.get("llm_api_key") or None,
            provider=settings.get("ai_provider") or None,
        )
        if llm_rows:
            words = [w for s in transcript.get("segments", []) for w in s.get("words") or []]
            candidates = highlight.to_candidates(llm_rows, words)

    clips: list[projects.Clip] = []
    for position, candidate in enumerate(candidates):
        clip = projects.Clip(
            index=position,
            start=candidate.start,
            end=min(candidate.end, project.duration or candidate.end),
            title=f"{project.title} · {candidate.title or f'Klip {position + 1}'}",
            score=candidate.score,
            reason=candidate.reason,
            crop=settings.get("crop", projects.DEFAULT_CROP),
        )
        if transcript:
            clip.captions = captions_for_range(transcript, clip.start, clip.end)
        clips.append(clip)
    project.set_clips(clips)
    project.save()
    _report(job, 92, "selesai", f"{len(clips)} klip dibuat")
    return clips


def refresh_captions(project: projects.Project, clip: projects.Clip) -> list[dict[str, Any]]:
    if not project.transcript:
        return clip.captions
    clip.captions = captions_for_range(project.transcript, clip.start, clip.end)
    return clip.captions


# --------------------------------------------------------------------------- render


def render_clip(project: projects.Project, clip: projects.Clip, job: Job | None = None) -> dict[str, str]:
    media = project.media_path()
    if media is None:
        raise FileNotFoundError("media sumber tidak ditemukan")
    directory = project.clip_dir(clip.index)

    captions = clip.captions or refresh_captions(project, clip)
    files: dict[str, str] = {}
    src_w = project.width or 1920
    src_h = project.height or 1080
    timeline = getattr(clip, "timeline", None) or None

    # Kanvas & framing diambil dari item video pada timeline (kalau ada),
    # kalau tidak dari field klip seperti biasa.
    base_item: dict[str, Any] = {}
    if timeline:
        items = timeline_mod.track(timeline, "video")
        base_item = items[0] if items else {}
    canvas = crop_mod.canvas_size(
        str(base_item.get("canvas") or getattr(clip, "canvas", "portrait")), src_w, src_h
    )
    text_items = timeline_mod.track(timeline, "text") if timeline else []

    if captions or text_items:
        captions_objs = [subtitle.Caption(**c) for c in captions]
        files.update(
            subtitle.write_subtitles(
                captions_objs,
                directory,
                "subs",
                preset=clip.subtitle_preset,
                position=getattr(clip, "subtitle_position", "bottom"),
                play_res=(canvas[0], canvas[1]),
                text_items=text_items,
            )
        )

    voice_path = clip.files.get("voice")
    if voice_path and not Path(voice_path).exists():
        voice_path = None
    if voice_path and clip.audio_mode != "original":
        target = clip.duration
        try:
            voice_path = str(
                voice.fit_duration(voice_path, target, directory / "voice_fit.wav")
            )
        except (RuntimeError, ValueError):
            pass

    out_path = directory / f"clip_{clip.index:03d}.mp4"
    _report(job, 60, "merender", f"klip {clip.index + 1}")
    if timeline:
        # Volume audio asli: penuh saat "original", dikecilkan saat dicampur,
        # nol saat hanya narasi.
        base_volume = 1.0 if clip.audio_mode == "original" else clip.original_volume
        if clip.audio_mode == "voice":
            base_volume = 0.0
        timeline_mod.render_timeline(
            media,
            out_path,
            timeline,
            src_size=(src_w, src_h),
            subtitles=files.get("ass"),
            voice_path=voice_path if clip.audio_mode != "original" else None,
            original_volume=base_volume,
            voice_volume=clip.voice_volume,
            progress_cb=lambda p, m: _report(job, 60 + p * 0.35, "merender", m),
        )
    else:
        render.render_clip(
            media,
            out_path,
            clip.start,
            clip.end,
            crop_mode=base_item.get("crop") or clip.crop,
            src_size=(src_w, src_h),
            out_size=canvas,
            subtitles=files.get("ass"),
            audio_mode=clip.audio_mode if voice_path else "original",
            voice_path=voice_path,
            original_volume=clip.original_volume,
            voice_volume=clip.voice_volume,
            progress_cb=lambda p, m: _report(job, 60 + p * 0.35, "merender", m),
        )
    thumb = render.thumbnail(out_path, directory / "thumb.jpg", at=min(1.0, clip.duration / 2))
    files["mp4"] = str(out_path)
    files["thumb"] = str(thumb)
    clip.files = {**clip.files, **files}
    clip.status = "rendered"
    project.save()
    _report(job, 100, "selesai", f"klip {clip.index + 1} selesai")
    return files


def render_preview(project: projects.Project, clip: projects.Clip, job: Job | None = None) -> dict[str, str]:
    """Render draf cepat (540x960) untuk pratinjau di editor.

    Hasilnya disimpan sebagai ``preview.mp4`` dan TIDAK menimpa klip final,
    jadi pengguna bisa mengutak-atik timeline tanpa menunggu render penuh.
    """
    media = project.media_path()
    if media is None:
        raise FileNotFoundError("media sumber tidak ditemukan")
    directory = project.clip_dir(clip.index)
    src_w = project.width or 1920
    src_h = project.height or 1080

    timeline = getattr(clip, "timeline", None) or None
    if not timeline:
        timeline = timeline_mod.default_timeline(
            clip.start,
            clip.end,
            str(media),
            crop=clip.crop,
            canvas=getattr(clip, "canvas", "portrait"),
        )
    text_items = timeline_mod.track(timeline, "text")
    base_item = (timeline_mod.track(timeline, "video") or [{}])[0]
    canvas = crop_mod.canvas_size(
        str(base_item.get("canvas") or getattr(clip, "canvas", "portrait")), src_w, src_h
    )

    captions = clip.captions or refresh_captions(project, clip)
    ass_path: str | None = None
    if captions or text_items:
        objs = [subtitle.Caption(**c) for c in captions]
        files = subtitle.write_subtitles(
            objs,
            directory,
            "preview",
            preset=clip.subtitle_preset,
            position=getattr(clip, "subtitle_position", "bottom"),
            play_res=(canvas[0], canvas[1]),
            text_items=text_items,
        )
        ass_path = files.get("ass")

    voice_path = clip.files.get("voice")
    if voice_path and not Path(voice_path).exists():
        voice_path = None

    base_volume = 1.0 if clip.audio_mode == "original" else clip.original_volume
    if clip.audio_mode == "voice":
        base_volume = 0.0

    import time
    # A playing preview must not be overwritten (Windows locks open media).
    for old in sorted(directory.glob("preview-*.mp4"), key=lambda p: p.stat().st_mtime)[:-2]:
        try:
            old.unlink()
        except OSError:
            pass
    out = directory / f"preview-{time.time_ns()}.mp4"
    _report(job, 20, "pratinjau", "merender draf cepat")
    timeline_mod.render_timeline(
        media,
        out,
        timeline,
        src_size=(src_w, src_h),
        subtitles=ass_path,
        voice_path=voice_path if clip.audio_mode != "original" else None,
        original_volume=base_volume,
        voice_volume=clip.voice_volume,
        scale_to=tuple(max(2, int(side * min(1.0, 960 / max(canvas))) // 2 * 2) for side in canvas),
        progress_cb=lambda p, m: _report(job, 20 + p * 0.75, "pratinjau", m),
    )
    _report(job, 100, "pratinjau siap")
    return {"mp4": str(out)}


def add_asset(project: projects.Project, source: str | Path) -> str:
    """Salin berkas media pengguna ke folder proyek.

    Timeline menyimpan path absolut, jadi berkas harus berada di dalam folder
    proyek — kalau tidak, memindahkan atau menghapus berkas asli akan membuat
    render gagal.
    """
    import time

    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(f"berkas tidak ditemukan: {source}")
    target_dir = project.root / "assets"
    target_dir.mkdir(parents=True, exist_ok=True)
    name = sanitize_filename(src.name, "media")
    target = target_dir / f"{int(time.time() * 1000)}-{name}"
    shutil.copy2(src, target)
    return str(target)


def export_all(project: projects.Project, job: Job | None = None) -> Path:
    rendered = [Path(c.files["mp4"]) for c in project.clips if c.files.get("mp4") and Path(c.files["mp4"]).exists()]
    if not rendered:
        raise RuntimeError("belum ada klip yang dirender")
    _report(job, 40, "menggabung", f"{len(rendered)} klip")
    out = project.root / f"{sanitize_filename(project.title, 'studio-zai')}-final.mp4"
    render.concat(rendered, out, progress_cb=lambda p, m: _report(job, 40 + p * 0.6, "menggabung", m))
    return out


# --------------------------------------------------------------------------- voice


def make_voice(
    project: projects.Project,
    text: str,
    lang: str = "id",
    voice_id: str | None = None,
    for_clip: int | None = None,
    job: Job | None = None,
) -> Path:
    project.voices_dir.mkdir(parents=True, exist_ok=True)
    stem = f"narasi-{clock(project.duration).replace(':', '-')}"
    out = project.voices_dir / f"{stem}.wav" if for_clip is None else project.voices_dir / f"clip{for_clip:03d}.wav"
    _report(job, 20, "membuat suara", "TTS")
    path = voice.synthesize(
        text,
        out,
        voice_id=voice_id,
        lang=lang,
        progress_cb=lambda p, m: _report(job, 20 + p * 0.7, "membuat suara", m),
    )
    if for_clip is not None:
        clip = project.clip(for_clip)
        clip.files["voice"] = str(path)
        clip.audio_mode = "mix"
        project.save()
    return path


def make_clone(
    project: projects.Project,
    text: str,
    sample: str | Path,
    lang: str = "id",
    model_id: str | None = None,
    for_clip: int | None = None,
    job: Job | None = None,
    reference_text: str = "",
) -> Path:
    settings = config.load_settings()
    project.voices_dir.mkdir(parents=True, exist_ok=True)
    out = project.voices_dir / f"clone-{sanitize_filename(Path(sample).stem, 'suara')}.wav"
    _report(job, 10, "mengkloning", "memuat model")
    path = voice.clone_speak(
        text,
        out,
        sample=sample,
        language=lang,
        model_id=model_id or settings.get("clone_model", "zipvoice-zh-en"),
        reference_text=reference_text,
        progress_cb=lambda p, m: _report(job, 10 + p * 0.85, "mengkloning", m),
    )
    if for_clip is not None:
        clip = project.clip(for_clip)
        clip.files["voice"] = str(path)
        clip.voice_clone_sample = str(sample)
        clip.audio_mode = "mix"
        project.save()
    return path


def benchmark_clone(model_id: str = "chatterbox-base", sample: str | Path | None = None) -> dict[str, Any]:
    """Measure real-time factor for a cloning model; used to hide slow features."""
    import time

    text = "Studio ZAI mengukur kecepatan kloning suara pada perangkat ini."
    out = config.cache_dir() / "bench-clone.wav"
    start = time.time()
    try:
        voice.clone_speak(text, out, sample=sample, model_id=model_id)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        return {"ok": False, "error": str(exc)}
    elapsed = time.time() - start
    try:
        audio_seconds = voice.duration_of(out)
    except RuntimeError:
        audio_seconds = max(1.0, len(text) / 14)
    rtf = elapsed / max(0.1, audio_seconds)
    settings = config.save_settings({"benchmarks": {**config.load_settings().get("benchmarks", {}), model_id: round(rtf, 2)}})
    return {"ok": True, "rtf": round(rtf, 2), "acceptable": rtf <= 8.0, "benchmarks": settings["benchmarks"]}


def update_settings(values: dict[str, Any]) -> dict[str, Any]:
    return config.save_settings(values)
