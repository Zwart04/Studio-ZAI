"""High-level orchestration shared by the CLI, the web server and the tests."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import cache, config, credentials, models, projects
from .jobs import Job
from .pipeline import crop as crop_mod
from .pipeline import download, highlight, probe, render, subtitle, transcribe, voice
from .pipeline import timeline as timeline_mod
from .utils import ffmpeg
from .utils.text import clock, human_size, sanitize_filename

Report = Callable[[float, str, str], None]


def clip_poster(project: projects.Project, clip: projects.Clip) -> Path:
    """Read the first frame at the clip boundary, without encoding a preview."""
    import hashlib
    import tempfile

    media = project.media_path()
    offset = 0.0
    identity = cache.file_identity(media) if media else project.source_url
    key = hashlib.sha256(repr((clip.start, identity)).encode()).hexdigest()[:20]
    target = project.clip_dir(clip.index) / f"poster-{key}.jpg"
    with projects.project_lock(f"poster:{project.id}:{clip.storage_id}"):
        if target.is_file():
            return target
        if media is None:
            segment = project.segment_path(clip.storage_id)
            start, end = project.segment_bounds(clip.storage_id)
            if segment and start <= clip.start < end:
                media, offset = segment, start
        if media:
            return render.thumbnail(media, target, at=max(0, clip.start - offset))
        if project.processing_mode == "offline" or not project.online or not project.source_url:
            raise FileNotFoundError("Frame klip belum tersedia; buka atau hubungkan video sumber.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="poster-", dir=target.parent) as temp:
            result = download.download_range(project.source_url, clip.start,
                min(clip.end, clip.start + 1), temp, max_height=360,
                cookies=config.load_settings().get("cookies_path") or None)
            return render.thumbnail(result["path"], target,
                at=max(0, clip.start - float(result["start"])))


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
        "youtube_transcript_api": _module_ok("youtube_transcript_api"),
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
    if not optional["youtube_transcript_api"]:
        # Bukan penghalang: jalur yt-dlp tetap bekerja; ini lapis cadangan
        # yang bertahan bila jalur player YouTube diblokir.
        problems.append(
            "youtube-transcript-api belum terpasang (cadangan caption YouTube mati): "
            "pip install -e \"core[media]\"")
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
    online: bool = False,
    captions_first: bool = False,
) -> Path | None:
    """Bring the source video into the project (download for URLs, copy for local files).

    Dengan ``online=True`` dan sumber URL, hanya track audio yang
    diunduh: transkripsi dan pemilihan klip jalan tanpa video.
    Video diunduh per-rentang klip saat render.
    """
    project.source_dir.mkdir(parents=True, exist_ok=True)
    project.execution["audio_language"] = audio_lang or ""
    if project.language == "auto" and audio_lang:
        project.language = audio_lang
    if download.is_url(source):
        if online and captions_first:
            project.execution["caption_attempted"] = True
            from .pipeline.captions import fetch_captions
            project.source_kind, project.source_url, project.online = "url", source, True
            metadata_key = cache.key("metadata", source)
            info = cache.read(metadata_key, max_age=1800)
            if not info:
                info = download.fetch_info(source, cookies=cookies)
                cache.write(metadata_key, info)
            project.title = info["title"]
            project.duration = info.get("duration") or 0.0
            project.heatmap = list(info.get("heatmap") or [])
            caption_key = cache.key("platform-caption-v2", source, project.language)
            try:
                transcript = cache.read(caption_key, max_age=86400)
                if not transcript:
                    transcript = fetch_captions(source, project.source_dir, lang=project.language, cookies=cookies)
                transcript = validate_transcript(transcript, project.duration, project.language)
                cache.write(caption_key, transcript)
                project.transcript = transcript
                project.execution["transcript"] = "platform captions"
                project.save()
                _report(job, 40, "caption siap", "tanpa unduh audio/video atau ASR")
                return None
            except (RuntimeError, ValueError) as exc:
                _report(job, 10, "caption tidak tersedia", str(exc)[:180])
        if online:
            _report(job, 2, "mengunduh", "track audio saja (mode online)")
            info = download.download_audio(
                source,
                project.source_dir,
                cookies=cookies or None,
                progress_cb=lambda p, m: _report(job, 3 + p * 0.32, "mengunduh audio", m),
                audio_lang=audio_lang,
            )
            project.source = ""
            project.source_kind = "url"
            project.source_url = source
            project.audio_path = info["path"]
            project.online = True
            project.title = info["title"]
            project.duration = info.get("duration") or 0.0
            project.heatmap = list(info.get("heatmap") or [])
            project.save()
            _report(job, 40, "siap", "audio tersimpan; video diunduh saat render klip")
            return Path(info["path"])
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
        project.heatmap = list(info.get("heatmap") or [])
    else:
        src_path = Path(source)
        if not src_path.exists():
            raise FileNotFoundError(f"berkas tidak ditemukan: {source}")
        _report(job, 5, "membuka", "memakai berkas lokal asli")
        project.source = str(src_path.resolve())
        project.source_kind = "local"
        if not project.title:
            project.title = src_path.stem

    _report(job, 38, "memeriksa", "membaca metadata media")
    info = probe.probe(project.source)
    project.duration = info.duration
    project.width = info.width
    project.height = info.height
    project.execution["has_audio"] = info.has_audio
    project.execution["source_identity"] = cache.file_identity(project.source)
    if project.source_kind == "local":
        project.transcript = _local_captions(project)
        if project.transcript:
            project.execution["transcript"] = "local captions"
    project.save()
    _report(job, 40, "siap", f"durasi {clock(info.duration)}")
    return Path(project.source)


def validate_transcript(transcript, duration: float = 0, language: str = "auto"):
    import math
    actual = str(transcript.get("language") or "auto").split("-")[0]
    if language not in {"auto", "unknown", ""} and actual not in {language.split("-")[0], "auto"}:
        raise ValueError("Bahasa caption tidak sesuai pilihan")
    rows = []
    for row in transcript.get("segments", []):
        start, end = float(row["start"]), float(row["end"])
        if not math.isfinite(start + end) or start < 0 or end <= start:
            raise ValueError("Timestamp caption tidak valid")
        if duration > 0 and end > duration + 2:
            raise ValueError("Caption melewati durasi sumber")
        if str(row.get("text", "")).strip():
            valid_words = []
            for word in row.get("words") or []:
                try:
                    ws, we = float(word["start"]), float(word["end"])
                    if math.isfinite(ws + we) and start <= ws < we <= end:
                        valid_words.append(word)
                except (KeyError, ValueError, TypeError):
                    continue
            row = {**row, "words": valid_words}
            rows.append(row)
    if not rows:
        raise ValueError("Caption kosong")
    rows.sort(key=lambda row: row["start"])
    return {**transcript, "segments": rows}


def _local_captions(project):
    from .pipeline.captions import parse_subtitle_file
    source = Path(project.source)
    options = [source.with_suffix(".vtt"), source.with_suffix(".srt")]
    try:
        data = ffmpeg.ffprobe_json(source)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "subtitle" and stream.get("codec_name") in {"subrip", "ass", "webvtt", "mov_text", "ssa"}:
                target = project.source_dir / "embedded.srt"
                result = ffmpeg.run_ffmpeg(["-i", str(source), "-map", f"0:{stream['index']}", str(target)], timeout=60)
                if result.ok:
                    options.append(target)
                break
        for path in options:
            if path.is_file():
                rows = parse_subtitle_file(path)
                return validate_transcript({"source": "local-caption", "language": project.language, "segments": rows}, project.duration, project.language)
    except (OSError, RuntimeError, ValueError):
        pass
    return {}


def ensure_transcript(
    project: projects.Project,
    model_id: str | None = None,
    lang: str | None = None,
    job: Job | None = None,
) -> dict[str, Any]:
    _refresh_source_identity(project)
    if project.transcript.get("segments"):
        return project.transcript
    media = project.audio_media_path()
    if media is None:
        raise FileNotFoundError("media sumber tidak ditemukan")
    settings = config.load_settings()
    model_id = model_id or settings.get("asr_model", "whisper-small-int8")
    _report(job, 45, "menranskripsi", f"model {model_id}")
    identifier = cache.key("asr-v3", cache.file_identity(media), model_id, transcribe.model_revision(model_id), lang or project.language)
    transcript = cache.read(identifier)
    if not transcript:
        transcript = transcribe.transcribe(
        media,
        model_id=model_id,
        lang=lang or project.language,
        progress_cb=lambda p, m: _report(job, 45 + p * 0.3, "menranskripsi", m),
        )
        cache.write(identifier, transcript)
    project.transcript = transcript
    project.execution["transcript"] = f"local ASR · {model_id}"
    project.execution["asr_device"] = transcript.get("device", "unknown")
    if transcript.get("language"):
        project.language = str(transcript["language"])[:5]
    project.save()
    return transcript


def _refresh_source_identity(project):
    media = project.audio_media_path()
    identity = project.execution.get("source_identity")
    if project.source_kind == "local" and media is not None and identity and cache.file_identity(media) != identity:
        project.transcript = {}
        project.execution["source_identity"] = cache.file_identity(media)
        project.notes = "Sumber berubah; transkrip dan kandidat dibuat ulang."


def relink_source(project, source):
    """Relink the same local video while preserving the user's clip edits and exports."""
    if project.online or download.is_url(source):
        raise ValueError("Penautan ulang ini hanya untuk video lokal yang sama")
    path = Path(source).resolve()
    if not path.is_file():
        raise ValueError("Video lokal tidak ditemukan")
    info = probe.probe(path)
    import math
    if not info.width or not info.height or not math.isfinite(info.duration) or info.duration <= 0 or info.duration < max((clip.end for clip in project.clips), default=0):
        raise ValueError("Video tidak valid atau lebih pendek dari klip tersimpan")
    if project.duration and abs(info.duration-project.duration) > max(.5, project.duration*.01):
        raise ValueError("Durasi berbeda. Pilih video yang sama; buat proyek baru untuk video lain.")
    if project.width and (info.width,info.height)!=(project.width,project.height):
        raise ValueError("Ukuran berbeda. Pilih video yang sama agar framing tetap sesuai.")
    old = project.source
    project.source = str(path)
    project.source_kind = "local"
    project.audio_path = ""
    project.preview_path = ""
    project.execution["source_identity"] = cache.file_identity(path)
    for clip in project.clips:
        for item in timeline_mod.track(clip.timeline, "video"):
            if not item.get("src") or item.get("src") == old:
                item["src"] = str(path)
    project.notes = "Video ditautkan ulang. Trim, subtitle, dan ekspor dipertahankan. Pastikan berkas ini video yang sama."
    project.save()
    return project


def ensure_transcript_from_captions(
    project: projects.Project,
    lang: str | None = None,
    job: Job | None = None,
) -> dict[str, Any]:
    """Transkrip instan dari caption YouTube (tanpa unduh/transkripsi).

    Pola cheat-clip-pro: teks ber-timing diambil langsung (detik, KB),
    Whisper lokal hanya cadangan bila caption tidak ada. Hasil dicatat
    dengan source="youtube" agar UI tahu asalnya.
    """
    from .pipeline import captions as captions_mod

    if not project.online or not project.source_url:
        raise RuntimeError("caption hanya untuk proyek online dari tautan")
    _report(job, 42, "caption", "mengambil subtitle YouTube")
    transcript = captions_mod.fetch_captions(
        project.source_url,
        project.source_dir,
        lang=lang or project.language,
        cookies=config.load_settings().get("cookies_path") or None,
        progress_cb=lambda p, m: _report(job, 42 + p * 0.03, "caption", m),
    )
    project.transcript = transcript
    if transcript.get("language"):
        project.language = str(transcript["language"])[:5]
    project.save()
    _report(job, 45, "caption", f"{len(transcript.get('segments', []))} baris caption siap")
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
    measured = any(s.get("words") for s in transcript.get("segments", []) if s.get("end", 0) > start and s.get("start", 0) < end)
    return [{**c.as_dict(), "timing_quality": "measured" if measured else "estimated"} for c in subtitle.group_words(words)]


def generate_clips(
    project: projects.Project,
    count: int = 5,
    min_len: float = 0.0,
    max_len: float = 0.0,
    use_llm: bool = False,
    use_transcript: bool = True,
    job: Job | None = None,
    analysis_mode: str = "auto",
    asr_model: str | None = None,
    model: str | None = None,
    processing_mode: str = "legacy",
    settings_override=None,
    connection_override=None,
) -> list[projects.Clip]:
    _refresh_source_identity(project)
    media = project.audio_media_path()
    if media is None and not project.transcript.get("segments"):
        raise FileNotFoundError("media sumber tidak ditemukan")
    if count <= 0:
        import math
        count = max(3, min(10, math.ceil(project.duration / 300)))
    _floor, _ceiling = highlight.clip_count_targets(project.duration or 0, count)

    transcript = project.transcript if use_transcript and project.transcript.get("segments") else None
    if use_transcript and transcript is None and not project.execution.get("caption_attempted") and project.online and project.source_url:
        try:
            transcript = ensure_transcript_from_captions(project, lang=project.language, job=job)
        except RuntimeError as exc:
            _report(job, 45, "caption kosong", f"lanjut Whisper lokal: {exc}")
    if use_transcript and transcript is None and project.execution.get("has_audio") is not False and transcribe.asr_available():
        try:
            transcript = ensure_transcript(project, model_id=asr_model, job=job)
        except RuntimeError as exc:
            _report(job, 75, "transkripsi gagal", f"memakai analisis audio saja: {exc}")
    if use_transcript and transcript is None and not transcribe.asr_available():
        _report(job, 75, "model transkrip belum siap", "memakai analisis audio saja")

    _report(job, 78, "menganalisis", "mencari momen terbaik")
    if transcript and not transcript.get("segments"):
        transcript = None
        project.notes = "Tidak ada ucapan yang terbaca. Kandidat dari aktivitas audio perlu ditinjau manual."
    if transcript:
        candidates = highlight.pick_clips(project.duration or max(s["end"] for s in transcript["segments"]),
            transcript=transcript, count=max(count * 3, count) if use_llm else count,
            min_len=min_len, max_len=max_len, heatmap=project.heatmap)
    else:
        try:
            candidates = highlight.analyze_media(
        media,
        transcript=transcript if use_transcript else None,
        count=count,
        min_len=min_len,
        max_len=max_len,
        video_duration=project.duration or 0,
        heatmap=project.heatmap,
        progress_cb=lambda p, m: _report(job, 78 + p * 0.12, "menganalisis", m),
            )
        except (RuntimeError, ValueError, OSError) as exc:
            project.notes = f"Audio tidak tersedia; rentang ini perlu dipilih manual: {str(exc)[:100]}"
            candidates = highlight.pick_clips(project.duration, count=count, min_len=min_len, max_len=max_len)

    if transcript and analysis_mode == "podcast":
        from .pipeline.podcast import moments
        rows = moments(transcript, project.duration, count, min_len, max_len)
        if rows:
            candidates = highlight.to_candidates(rows)

    heuristic_candidates = candidates
    project.execution.pop("ranking_model", None)
    settings = settings_override or config.load_settings()
    llm_rows = []
    if use_llm and transcript:
        try:
            llm_rows = highlight.rank_with_llm(
                transcript,
                count=count,
                base_url=settings.get("llm_base_url") or "http://127.0.0.1:11434/v1",
                model=model or (settings.get("ai_model") if processing_mode in {"legacy", "online_ai"} else None) or settings.get("llm_model") or "",
                api_key=settings.get("llm_api_key") if settings_override is not None else credentials.read().get("llm_api_key") or settings.get("llm_api_key") or None,
                provider=(settings.get("ai_provider") or None) if processing_mode in {"legacy", "online_ai"} else None,
                candidates=candidates,
                min_len=min_len, max_len=max_len,
                connection_override=connection_override,
                check_cancel=getattr(job, "check_cancel", None),
            )
        except (RuntimeError, ValueError, OSError) as exc:
            llm_rows = []
            project.notes = f"AI tidak tersedia; memakai deteksi lokal: {str(exc)[:200]}"
            _report(job, 89, "pilihan lokal", project.notes)
        if llm_rows:
            project.execution["ranking"] = llm_rows[0].get("engine", "online AI" if processing_mode == "online_ai" else "local LLM")
            project.execution["ranking_model"] = llm_rows[0].get("model", model or settings.get("llm_model"))
            words = [w for s in transcript.get("segments", []) for w in s.get("words") or []]
            candidates = highlight.to_candidates(llm_rows, words)
            candidates = [c for c in candidates if (min_len or 3) <= c.end - c.start <= (max_len or 180)
                          and c.start >= 0 and c.end <= (project.duration or c.end)]
            if not candidates:
                llm_rows = []
                candidates = heuristic_candidates
                project.execution["ranking"] = "heuristic-only"
                project.notes = "Batas hasil LLM tidak sesuai durasi pilihan; memakai kandidat heuristik."
        else:
            project.execution["ranking"] = "heuristic-only"
            setup = "Periksa provider, model dan API key yang dipilih." if project.processing_mode == "online_ai" else "Atur model lokal untuk analisis LLM."
            project.notes = f"LLM belum siap atau hasilnya tidak valid; kandidat ini memakai heuristik. {setup}"
    else:
        project.execution["ranking"] = "heuristic-only"
    candidates = candidates[:count]

    clips: list[projects.Clip] = []
    for position, candidate in enumerate(candidates):
        clip = projects.Clip(
            index=position,
            start=candidate.start,
            end=min(candidate.end, project.duration or candidate.end),
            title=f"{project.title} · {candidate.title or f'Klip {position + 1}'}",
            score=candidate.score,
            reason=("tanpa transkrip; " if use_transcript and transcript is None else "") + candidate.reason,
            analysis_metadata=next(({k: row[k] for k in ("hook_assessment", "context_completeness", "model") if k in row}
                                    for row in llm_rows if row.get("title") == candidate.title), {}),
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
    captions = captions_for_range(project.transcript, clip.start, clip.end)
    if captions != clip.captions:
        clip.invalidate_renders()
    clip.captions = captions
    clip.caption_language = project.transcript.get("language", project.language)
    clip.caption_variants[clip.caption_language] = captions
    return clip.captions


def generate_captions_for_clip(
    project: projects.Project,
    clip: projects.Clip,
    job: Job | None = None,
) -> list[dict[str, Any]]:
    """Create captions from local speech recognition for one editor clip.

    A project made without automatic subtitles has no transcript. Running ASR on
    its entire source here would make a short edit of an hour-long video appear
    stuck. Extract only the selected range in that case. Existing project
    transcripts are already local ASR results and can be reused directly.
    """
    if project.transcript.get("segments") and (project.transcript.get("source") not in {"youtube", "local-caption"}
            or all(row.get("words") for row in project.transcript["segments"] if row["end"] > clip.start and row["start"] < clip.end)):
        _report(job, 90, "subtitle", "memakai transkrip AI proyek")
        return refresh_captions(project, clip)

    media = project.media_path() or project.audio_media_path()
    if media is None and project.online and project.transcript.get("segments"):
        data = download.download_audio(project.source_url, project.source_dir,
            audio_lang=project.execution.get("audio_language") or None,
            cookies=config.load_settings().get("cookies_path") or None)
        project.audio_path = data["path"]
        media = Path(data["path"])
    if media is None:
        raise FileNotFoundError("media sumber tidak ditemukan")
    if clip.duration <= 0:
        raise ValueError("durasi klip harus lebih besar dari nol")

    import tempfile

    project.root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="caption-", dir=project.root) as temp_dir:
        audio = Path(temp_dir) / "clip.wav"
        _report(job, 5, "subtitle", "menyiapkan audio klip")
        result = ffmpeg.run_ffmpeg(
            [
                "-ss", f"{clip.start:.3f}",
                "-i", str(media),
                "-t", f"{clip.duration:.3f}",
                "-vn", "-ac", "1", "-ar", "16000",
                "-c:a", "pcm_s16le", str(audio),
            ],
            timeout=max(120, int(clip.duration * 3)),
        )
        if not result.ok or not audio.exists():
            raise RuntimeError("Audio klip tidak dapat dibaca untuk subtitle otomatis")

        settings = config.load_settings()
        transcript = transcribe.transcribe(
            audio,
            model_id=settings.get("asr_model", "whisper-small-int8"),
            lang=project.language,
            progress_cb=lambda p, m: _report(job, 15 + p * 0.75, "subtitle", m),
        )
    captions = captions_for_range(transcript, 0.0, clip.duration)
    if captions != clip.captions:
        clip.invalidate_renders()
    clip.captions = captions
    clip.caption_language = transcript.get("language", project.language)
    clip.caption_variants[clip.caption_language] = captions
    _report(job, 95, "subtitle", f"{len(clip.captions)} baris subtitle dibuat")
    return clip.captions


# --------------------------------------------------------------------------- render


SEGMENT_PAD = 2.0


def _shift_source_times(timeline: dict[str, Any], delta: float) -> dict[str, Any]:
    """Geser srcStart item video agar -ss mengarah ke segmen yang diunduh."""
    import copy

    shifted = copy.deepcopy(timeline)
    for item in timeline_mod.track(shifted, "video"):
        if "srcStart" in item:
            item["srcStart"] = max(0.0, float(item["srcStart"]) - delta)
    return shifted


def _resolve_render_media(
    project: projects.Project,
    clip: projects.Clip,
    job: Job | None = None,
) -> tuple[Path, float]:
    with projects.project_lock(f"media:{project.id}:{clip.storage_id}"):
        project.segments = projects.load_project(project.id).segments
        return _resolve_render_media_unlocked(project, clip, job)


def _resolve_render_media_unlocked(project, clip, job=None):
    """Media untuk render klip.

    Mode online: unduh hanya rentang klip dari URL (dengan padding
    kecil) dan cache per-klip. Mengembalikan (path, seg_start);
    bila seg_start > 0, garis waktu berkas dimulai seg_start detik
    sebelum garis waktu sumber, jadi pemanggil harus menggeser
    stempel waktu sumber sebesar -seg_start.
    """
    media = project.media_path()
    if media is not None:
        identity = project.execution.get("source_identity")
        if identity and cache.file_identity(media) != identity:
            raise ValueError("Berkas sumber berubah. Analisis ulang sebelum merender klip lama.")
        return media, 0.0
    if not project.online or not project.source_url:
        raise FileNotFoundError("media sumber tidak ditemukan")
    # Cache per-klip (storage_id stabil walau index berubah);
    # unduh ulang bila klip diedit melampaui segmen yang ada.
    key = clip.storage_id
    seg = project.segment_path(key)
    seg_start, seg_end = project.segment_bounds(key)
    if seg is not None and seg_start <= clip.start and clip.end <= seg_end + 0.5:
        return seg, seg_start
    if project.processing_mode == "offline":
        raise ValueError("Full Offline memerlukan sumber atau segmen video yang sudah tersedia di perangkat")
    seg_start = max(0.0, clip.start - SEGMENT_PAD)
    seg_end = clip.end + SEGMENT_PAD
    if project.duration:
        seg_end = min(seg_end, project.duration)
    _report(job, 55, "mengunduh", f"rentang klip {seg_start:.0f}–{seg_end:.0f}s")
    local_audio: str | None = None
    if project.audio_path and Path(project.audio_path).exists():
        # Audio lengkap sudah ada (mode online): potong lokal agar segmen bersuara.
        local_audio = project.audio_path
    if local_audio is None:
        _report(job, 52, "audio preview", "mengambil audio saat video klip diperlukan")
        audio = download.download_audio(project.source_url, project.source_dir,
            cookies=config.load_settings().get("cookies_path") or None,
            audio_lang=project.execution.get("audio_language") or None)
        project.audio_path = local_audio = audio["path"]
    result = download.download_range(
        project.source_url,
        seg_start,
        seg_end,
        project.source_dir / clip.storage_id,
        cookies=config.load_settings().get("cookies_path") or None,
        audio_path=local_audio,
        progress_cb=lambda p, m: _report(job, 55 + p * 0.04, "mengunduh klip", m),
    )
    actual_start = float(result["start"] if result.get("start") is not None else seg_start)
    project.store_segment(key, result["path"], actual_start, float(result.get("end") or seg_end))
    # Probe sekali: kanvas render butuh dimensi video asli.
    info = probe.probe(result["path"])
    if info.width <= 0 or info.height <= 0:
        raise RuntimeError("Segmen video tidak valid; cache tidak disimpan")
    if not project.width:
        project.width = info.width
    if not project.height:
        project.height = info.height
    # Cache writes must not publish the caller's preview draft or stale render snapshot.
    with projects.project_lock(project.id):
        fresh = projects.load_project(project.id)
        fresh.segments[key] = project.segments[key]
        fresh.width = fresh.width or project.width
        fresh.height = fresh.height or project.height
        fresh.audio_path = fresh.audio_path or project.audio_path
        fresh.save()
    return Path(result["path"]), actual_start


def render_clip(
    project: projects.Project,
    clip: projects.Clip,
    job: Job | None = None,
    *,
    canvas_override: str | None = None,
    persist: bool = True,
) -> dict[str, str]:
    if canvas_override is not None and canvas_override not in {"portrait", "square", "landscape"}:
        raise ValueError("Format kanvas tidak valid")
    import copy
    import uuid
    initial = next((row for row in projects.load_project(project.id).clips if row.storage_id == clip.storage_id), clip)
    expected = copy.deepcopy({k: v for k, v in initial.as_dict().items() if k not in {"files", "status", "index", "title", "score", "reason"}})
    media, seg_start = _resolve_render_media(project, clip, job)
    directory = project.clip_dir(clip.index)
    directory = directory / "exports" / uuid.uuid4().hex[:12]
    directory.mkdir(parents=True, exist_ok=True)

    captions = clip.captions or refresh_captions(project, clip)
    files: dict[str, str] = {}
    src_w = project.width or 1920
    src_h = project.height or 1080
    timeline = getattr(clip, "timeline", None) or None
    if canvas_override and timeline:
        import copy

        timeline = copy.deepcopy(timeline)
        video_items = timeline_mod.track(timeline, "video")
        if video_items:
            video_items[0]["canvas"] = canvas_override

    # Kanvas & framing diambil dari item video pada timeline (kalau ada),
    # kalau tidak dari field klip seperti biasa.
    base_item: dict[str, Any] = {}
    if timeline:
        items = timeline_mod.track(timeline, "video")
        base_item = items[0] if items else {}
    canvas = crop_mod.canvas_size(
        canvas_override or str(base_item.get("canvas") or getattr(clip, "canvas", "portrait")),
        src_w,
        src_h,
    )
    text_items = timeline_mod.track(timeline, "text") if timeline else []

    if captions or text_items:
        captions_objs = [subtitle.Caption(**c) for c in captions]
        files.update(
            subtitle.write_subtitles(
                captions_objs,
                directory,
                f"subs_{canvas_override}" if canvas_override else "subs",
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
                voice.fit_duration(
                    voice_path,
                    target,
                    directory / (f"voice_fit_{canvas_override}.wav" if canvas_override else "voice_fit.wav"),
                )
            )
        except (RuntimeError, ValueError):
            pass

    out_path = directory / (
        f"clip_{clip.index:03d}_{canvas_override}.mp4"
        if canvas_override else f"clip_{clip.index:03d}.mp4"
    )
    _report(job, 60, "merender", f"klip {clip.index + 1}")
    if timeline:
        if seg_start:
            timeline = _shift_source_times(timeline, seg_start)
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
            clip.start - seg_start,
            clip.end - seg_start,
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
    if canvas_override:
        thumb = render.thumbnail(out_path, directory / "thumb.jpg", at=min(1.0, clip.duration / 2))
        files[f"mp4_{canvas_override}"] = str(out_path)
        files[f"thumb_{canvas_override}"] = str(thumb)
        clip.files[f"mp4_{canvas_override}"] = str(out_path)
        clip.files[f"thumb_{canvas_override}"] = str(thumb)
    else:
        thumb = render.thumbnail(out_path, directory / "thumb.jpg", at=min(1.0, clip.duration / 2))
        files["mp4"] = str(out_path)
        files["thumb"] = str(thumb)
        clip.files = {**clip.files, **files}
        clip.status = "rendered"
    if persist:
        with projects.project_lock(project.id):
            fresh = projects.load_project(project.id)
            target = next((row for row in fresh.clips if row.storage_id == clip.storage_id), None)
            actual = {k: v for k, v in target.as_dict().items() if k not in {"files", "status", "index", "title", "score", "reason"}} if target else None
            if actual != expected:
                raise RuntimeError("Klip berubah selama render. Hasil lama tidak dipasang; render ulang perubahan terbaru.")
            target.files.update(files)
            target.status = clip.status
            for field in expected:
                if field in projects.Clip.__dataclass_fields__ and field != "storage_id":
                    setattr(target, field, copy.deepcopy(getattr(clip, field)))
            fresh.save()
    _report(job, 100, "selesai", f"klip {clip.index + 1} selesai")
    return files


def render_preview(project: projects.Project, clip: projects.Clip, job: Job | None = None) -> dict[str, str]:
    """Render draf cepat (540x960) untuk pratinjau di editor.

    Hasilnya disimpan sebagai ``preview.mp4`` dan TIDAK menimpa klip final,
    jadi pengguna bisa mengutak-atik timeline tanpa menunggu render penuh.
    """
    media, seg_start = _resolve_render_media(project, clip, job)
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
    if seg_start:
        timeline = _shift_source_times(timeline, seg_start)
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
        encoder="preview",
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
        clip.invalidate_renders()
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
        clip.invalidate_renders()
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
