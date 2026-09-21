"""Thin wrappers around the system FFmpeg/FFprobe binaries."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

TIME_RE = re.compile(r"time=(\d+):(\d{2}):(\d{2})(?:\.(\d+))?")

ProgressCb = Callable[[float], None]


class FFmpegNotFound(RuntimeError):
    pass


def ffmpeg_path() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise FFmpegNotFound(
            "ffmpeg tidak ditemukan di PATH. Instal ffmpeg lalu jalankan 'studiozai doctor'."
        )
    return path


def ffprobe_path() -> str:
    path = shutil.which("ffprobe")
    if not path:
        raise FFmpegNotFound("ffprobe tidak ditemukan di PATH (biasanya satu paket dengan ffmpeg).")
    return path


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def detect_h264_encoder() -> str:
    """Prefer NVENC only when an NVIDIA GPU is actually present, otherwise x264."""
    if not shutil.which("nvidia-smi"):
        return "libx264"
    try:
        probe_result = subprocess.run(
            ["nvidia-smi", "-L"], capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return "libx264"
    if probe_result.returncode != 0 or "GPU" not in probe_result.stdout:
        return "libx264"
    try:
        out = subprocess.run(
            [ffmpeg_path(), "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return "libx264"
    return "h264_nvenc" if "h264_nvenc" in out else "libx264"


@dataclass
class RunResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    command: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_ffmpeg(
    args: Sequence[str],
    total_duration: float | None = None,
    progress_cb: ProgressCb | None = None,
    timeout: int | None = None,
) -> RunResult:
    """Run ffmpeg with array args (never shell) and optional progress parsing."""
    cmd = [ffmpeg_path(), "-hide_banner", "-nostdin", "-y", *args]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stderr_lines: list[str] = []
    assert proc.stderr is not None
    for line in proc.stderr:
        stderr_lines.append(line)
        if progress_cb and total_duration:
            match = TIME_RE.search(line)
            if match:
                h, m, s, frac = match.groups()
                seconds = int(h) * 3600 + int(m) * 60 + int(s) + float(f"0.{frac or 0}")
                progress_cb(min(99.0, max(0.0, seconds / total_duration * 100)))
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
    if progress_cb and proc.returncode == 0:
        progress_cb(100.0)
    return RunResult(proc.returncode, "", "".join(stderr_lines[-200:]), cmd)


def run_command(args: Sequence[str], timeout: int | None = None) -> RunResult:
    proc = subprocess.run(
        list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return RunResult(proc.returncode, proc.stdout, proc.stderr, list(args))


def ffprobe_json(path: str | Path) -> dict:
    res = run_command(
        [
            ffprobe_path(),
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        timeout=60,
    )
    if not res.ok:
        raise RuntimeError(f"ffprobe gagal untuk {path}: {res.stderr[:300]}")
    return json.loads(res.stdout or "{}")
