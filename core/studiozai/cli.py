"""Studio ZAI command line interface."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path
from typing import Any

from . import __version__, models, projects, service
from .config import data_dir, load_settings
from .pipeline import voice
from .utils.text import clock


class ConsoleJob:
    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet
        self.last = ""

    def report(self, progress: float, stage: str = "", message: str = "") -> None:
        if self.quiet:
            return
        line = f"[{progress:5.1f}%] {stage} {message}".rstrip()
        if line != self.last:
            print(line, flush=True)
            self.last = line

    def check_cancel(self) -> None:  # pragma: no cover - CLI has no cancel
        return None


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_doctor(args: argparse.Namespace) -> int:
    report = service.doctor()
    hw = report["hardware"]
    print(f"Studio ZAI {report['version']}")
    print(f"  Sistem      : {hw['os']} / {hw['arch']} / Python {hw['python']}")
    print(f"  RAM         : {hw.get('ram_gb')} GB   CPU: {hw['cpu_count']} core")
    gpu = hw.get("gpu") or {}
    print(f"  GPU         : {gpu.get('name', 'tidak ada')} {gpu.get('vram_gb', '')}")
    print(f"  Disk bebas  : {report['disk_free']}   Encoder: {report['encoder']}")
    print(f"  Data        : {report['data_dir']}")
    print("  Opsional    : " + ", ".join(f"{k}={'ok' if v else 'tidak'}" for k, v in report["optional"].items()))
    print("  Rekomendasi : " + ", ".join(str(v) for v in report["tier"].values() if v))
    for reason in report["tier"]["reasons"]:
        print(f"    - {reason}")
    if report["problems"]:
        print("  Masalah     :")
        for problem in report["problems"]:
            print(f"    ! {problem}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import run

    url = f"http://{args.host}:{args.port}"
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except webbrowser.Error:
            pass
    print(f"Studio ZAI berjalan di {url}")
    run(host=args.host, port=args.port)
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    from .pipeline import download

    info = download.download(
        args.url,
        args.out,
        cookies=args.cookies or None,
        progress_cb=lambda p, m: print(f"[{p:5.1f}%] {m}", flush=True),
    )
    _print_json(info)
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    from .pipeline import probe

    _print_json(probe.probe(args.file).as_dict())
    return 0


def cmd_transcribe(args: argparse.Namespace) -> int:
    from .pipeline import transcribe

    job = ConsoleJob(args.quiet)
    transcript = transcribe.transcribe(
        args.file,
        model_id=args.model,
        lang=args.lang,
        progress_cb=job.report,
        chunk_minutes=args.chunk_minutes,
    )
    out = Path(args.out) if args.out else Path(args.file).with_suffix(".transcript.json")
    transcribe.write_transcript(out, transcript)
    print(f"Transkrip: {out}")
    print(f"Bahasa   : {transcript['language']}  Segmen: {len(transcript['segments'])}")
    return 0


def cmd_clip(args: argparse.Namespace) -> int:
    settings = load_settings()
    job = ConsoleJob(args.quiet)
    project = projects.Project.create(args.title or "", source=args.source, language=args.lang)
    print(f"Proyek: {project.id} ({project.title})")
    service.ingest(project, args.source, cookies=settings.get("cookies_path") or None, job=job)
    service.generate_clips(
        project,
        count=args.count,
        min_len=args.min,
        max_len=args.max,
        use_llm=args.llm,
        use_transcript=not args.no_transcribe,
        job=job,
    )
    for clip in list(project.clips):
        print(f"-> klip {clip.index + 1}: {clock(clip.start)} - {clock(clip.end)}  skor {clip.score:.3f}  ({clip.reason})")
        service.render_clip(project, clip, job=job)
    final = None
    if args.join and project.clips:
        final = service.export_all(project, job=job)
    print(f"Selesai. Folder proyek: {project.root}")
    if final:
        print(f"Gabungan: {final}")
    return 0


def cmd_tts(args: argparse.Namespace) -> int:
    job = ConsoleJob(args.quiet)
    voice_id = args.voice or voice.default_voice(args.lang)
    out = Path(args.out)
    voice.synthesize(args.text, out, voice_id=voice_id, lang=args.lang, progress_cb=job.report)
    print(f"Suara: {out}")
    return 0


def cmd_clone(args: argparse.Namespace) -> int:
    job = ConsoleJob(args.quiet)
    settings = load_settings()
    voice.clone_speak(
        args.text,
        args.out,
        sample=args.sample,
        language=args.lang,
        model_id=args.model or settings.get("clone_model", "chatterbox-base"),
        progress_cb=job.report,
    )
    print(f"Suara hasil kloning: {args.out}")
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    if args.action == "list":
        for row in models.manager.status():
            flag = "terpasang" if row["installed"] else ("pip" if row["requires_pip"] else "-")
            print(f"{row['id']:<32} {row['kind']:<6} {row['size_mb'] or '?':>6} MB  {flag:<9} {row['note'] or ''}")
        return 0
    if args.action == "tier":
        hw = models.manager.detect_hardware()
        _print_json(models.manager.resolve_tier(hw, load_settings().get("lang", "id")))
        return 0
    if args.action == "download":
        job = ConsoleJob(False)
        for model_id in args.ids:
            print(f"Mengunduh {model_id} ...")
            models.manager.download(model_id, lambda p, m: job.report(p, "unduh", m))
        return 0
    if args.action == "remove":
        for model_id in args.ids:
            models.manager.remove(model_id)
            print(f"Dihapus: {model_id}")
        return 0
    return 1


def cmd_projects(args: argparse.Namespace) -> int:
    if args.action == "list":
        for project in projects.list_projects():
            print(f"{project.id}  {project.title[:40]:<40} {len(project.clips):>3} klip  {clock(project.duration)}")
        return 0
    if args.action == "show":
        _print_json(projects.load_project(args.id).as_dict())
        return 0
    if args.action == "delete":
        projects.delete_project(args.id)
        print(f"Dihapus: {args.id}")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="studiozai", description="Studio ZAI - auto clip, subtitle & voiceover studio")
    parser.add_argument("--version", action="version", version=f"Studio ZAI {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="cek lingkungan, hardware, dan model yang cocok")
    doctor.set_defaults(func=cmd_doctor)

    serve = sub.add_parser("serve", help="jalankan aplikasi desktop (web UI)")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8737)
    serve.add_argument("--no-browser", action="store_true")
    serve.set_defaults(func=cmd_serve)

    download_cmd = sub.add_parser("download", help="unduh video dari URL")
    download_cmd.add_argument("url")
    download_cmd.add_argument("-o", "--out", default=str(data_dir() / "downloads"))
    download_cmd.add_argument("--cookies", default="")
    download_cmd.set_defaults(func=cmd_download)

    probe_cmd = sub.add_parser("probe", help="lihat metadata media")
    probe_cmd.add_argument("file")
    probe_cmd.set_defaults(func=cmd_probe)

    transcribe_cmd = sub.add_parser("transcribe", help="transkripsi audio/video")
    transcribe_cmd.add_argument("file")
    transcribe_cmd.add_argument("--model", default="whisper-small-int8")
    transcribe_cmd.add_argument("--lang", default="auto")
    transcribe_cmd.add_argument("--out", default="")
    transcribe_cmd.add_argument("--chunk-minutes", type=float, default=10.0)
    transcribe_cmd.add_argument("--quiet", action="store_true")
    transcribe_cmd.set_defaults(func=cmd_transcribe)

    clip_cmd = sub.add_parser("clip", help="buat klip otomatis dari URL atau berkas lokal")
    clip_cmd.add_argument("source")
    clip_cmd.add_argument("--count", type=int, default=5)
    clip_cmd.add_argument("--min", type=float, default=15.0)
    clip_cmd.add_argument("--max", type=float, default=60.0)
    clip_cmd.add_argument("--lang", default="id")
    clip_cmd.add_argument("--title", default="")
    clip_cmd.add_argument("--no-transcribe", action="store_true", help="mode murni ffmpeg tanpa model AI")
    clip_cmd.add_argument("--llm", action="store_true", help="pakai LLM lokal untuk memilih momen")
    clip_cmd.add_argument("--join", action="store_true", help="gabung semua klip jadi satu berkas")
    clip_cmd.add_argument("--quiet", action="store_true")
    clip_cmd.set_defaults(func=cmd_clip)

    tts_cmd = sub.add_parser("tts", help="buat suara dari teks")
    tts_cmd.add_argument("text")
    tts_cmd.add_argument("--lang", default="id", choices=["id", "en"])
    tts_cmd.add_argument("--voice", default="")
    tts_cmd.add_argument("-o", "--out", default="narasi.wav")
    tts_cmd.add_argument("--quiet", action="store_true")
    tts_cmd.set_defaults(func=cmd_tts)

    clone_cmd = sub.add_parser("clone", help="kloning suara dari contoh rekaman")
    clone_cmd.add_argument("--sample", required=True)
    clone_cmd.add_argument("--text", required=True)
    clone_cmd.add_argument("--lang", default="id", choices=["id", "en"])
    clone_cmd.add_argument("--model", default="")
    clone_cmd.add_argument("-o", "--out", default="kloning.wav")
    clone_cmd.add_argument("--quiet", action="store_true")
    clone_cmd.set_defaults(func=cmd_clone)

    models_cmd = sub.add_parser("models", help="kelola model (list/download/remove/tier)")
    models_cmd.add_argument("action", choices=["list", "download", "remove", "tier"])
    models_cmd.add_argument("ids", nargs="*")
    models_cmd.set_defaults(func=cmd_models)

    projects_cmd = sub.add_parser("projects", help="kelola proyek")
    projects_cmd.add_argument("action", choices=["list", "show", "delete"])
    projects_cmd.add_argument("id", nargs="?", default="")
    projects_cmd.set_defaults(func=cmd_projects)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        print("\nDibatalkan.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001 - CLI should print friendly errors
        print(f"Error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
