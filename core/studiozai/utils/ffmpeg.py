"""Thin wrappers around the system FFmpeg/FFprobe binaries."""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from ..jobs import HEAVY_SLOT
from . import proc

TIME_RE = re.compile(r"time=(\d+):(\d{2}):(\d{2})(?:\.(\d+))?")

ProgressCb = Callable[[float], None]
_ENCODER_SLOT = HEAVY_SLOT


class FFmpegNotFound(RuntimeError):
    pass


def bundled_bin_dir() -> Path | None:
    """Directory holding the ffmpeg/ffprobe shipped with the packaged app."""
    env = os.environ.get("STUDIOZAI_BIN")
    if env and Path(env).is_dir():
        return Path(env)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        for candidate in (Path(meipass) / "bin", Path(meipass)):
            if (candidate / "ffmpeg.exe").exists() or (candidate / "ffmpeg").exists():
                return candidate
    exe_dir = Path(sys.executable).resolve().parent
    for candidate in (exe_dir / "bin", exe_dir):
        if (candidate / "ffmpeg.exe").exists() or (candidate / "ffmpeg").exists():
            return candidate
    return None


def _find_tool(name: str) -> str | None:
    bundled = bundled_bin_dir()
    if bundled:
        for candidate in (bundled / f"{name}.exe", bundled / name):
            if candidate.exists():
                return str(candidate)
    return shutil.which(name)


def ffmpeg_path() -> str:
    path = _find_tool("ffmpeg")
    if not path:
        raise FFmpegNotFound(
            "ffmpeg tidak ditemukan (versi bundel maupun di PATH). "
            "Instal ffmpeg lalu jalankan 'studiozai doctor'."
        )
    return path


def ffprobe_path() -> str:
    path = _find_tool("ffprobe")
    if not path:
        raise FFmpegNotFound("ffprobe tidak ditemukan (biasanya satu paket dengan ffmpeg).")
    return path


def ffmpeg_available() -> bool:
    return _find_tool("ffmpeg") is not None and _find_tool("ffprobe") is not None


def detect_h264_encoder() -> str:
    """Prefer NVENC only when an NVIDIA GPU is actually present, otherwise x264."""
    if not shutil.which("nvidia-smi"):
        return "libx264"
    try:
        code, out, _ = proc.run(["nvidia-smi", "-L"], timeout=15)
    except (OSError, subprocess.SubprocessError):
        return "libx264"
    if code != 0 or "GPU" not in out:
        return "libx264"
    try:
        _, encoders, _ = proc.run([ffmpeg_path(), "-hide_banner", "-encoders"], timeout=20)
    except (OSError, subprocess.SubprocessError):
        return "libx264"
    if "h264_nvenc" in encoders:
        try:
            test = run_ffmpeg(["-f", "lavfi", "-i", "color=s=128x128:d=0.1", "-c:v", "h264_nvenc", "-f", "null", "-"], timeout=15)
            if test.ok:
                return "h264_nvenc"
        except (OSError, subprocess.SubprocessError):
            pass
    return "libx264"


@dataclass
class RunResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    command: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _creation_flags() -> int:
    """On Windows, prevent child process consoles from flashing on screen."""
    if sys.platform == "win32":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return 0


def run_ffmpeg(
    args: Sequence[str],
    total_duration: float | None = None,
    progress_cb: ProgressCb | None = None,
    timeout: int | None = None,
) -> RunResult:
    while not _ENCODER_SLOT.acquire(timeout=0.1):
        if progress_cb:
            progress_cb(0.0)
    try:
        return _run_ffmpeg(args, total_duration, progress_cb, timeout)
    finally:
        _ENCODER_SLOT.release()


def _run_ffmpeg(args, total_duration=None, progress_cb=None, timeout=None) -> RunResult:
    """Run ffmpeg with array args (never shell) and optional progress parsing."""
    cmd = [ffmpeg_path(), "-hide_banner", "-nostdin", "-y", *args]
    proc_handle = proc.spawn(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    stderr_lines: list[str] = []
    assert proc_handle.stderr is not None
    lines: queue.Queue[str | None] = queue.Queue(maxsize=200)

    def read_stderr():
        for line in proc_handle.stderr:
            lines.put(line)
        lines.put(None)

    reader = threading.Thread(target=read_stderr, daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout if timeout is not None else None
    progress = 0.0
    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(cmd, timeout)
            try:
                line = lines.get(timeout=0.1)
            except queue.Empty:
                if progress_cb:
                    progress_cb(progress)
                continue
            if line is None:
                break
            stderr_lines.append(line)
            del stderr_lines[:-200]
            if progress_cb and total_duration:
                match = TIME_RE.search(line)
                if match:
                    h, m, s, frac = match.groups()
                    seconds = int(h) * 3600 + int(m) * 60 + int(s) + float(f"0.{frac or 0}")
                    progress = min(99.0, max(0.0, seconds / total_duration * 100))
                    progress_cb(progress)
        proc_handle.wait(timeout=max(0.001, deadline - time.monotonic()) if deadline is not None else None)
    except BaseException:
        # Cancellation raised by a progress callback must also stop the encoder.
        proc_handle.kill()
        proc_handle.wait()
        raise
    finally:
        # Drain queued lines so the bounded reader can finish after cancellation.
        while reader.is_alive():
            try:
                lines.get(timeout=0.1)
            except queue.Empty:
                pass
            reader.join(timeout=0.01)
        proc.forget(proc_handle)
        proc_handle.stderr.close()
        if proc_handle.stdout:
            proc_handle.stdout.close()
    if progress_cb and proc_handle.returncode == 0:
        progress_cb(100.0)
    return RunResult(proc_handle.returncode, "", "".join(stderr_lines[-200:]), cmd)


def run_command(args: Sequence[str], timeout: int | None = None) -> RunResult:
    code, out, err = proc.run(list(args), timeout=timeout)
    return RunResult(code, out, err, list(args))


def validate_video(path, duration=None, size=None, require_audio=False):
    data = ffprobe_json(path)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video or int(video.get("width", 0)) < 1 or int(video.get("height", 0)) < 1:
        raise RuntimeError("Output tidak memiliki stream video yang valid")
    if size and (int(video["width"]), int(video["height"])) != tuple(size):
        raise RuntimeError("Ukuran output tidak sesuai kanvas")
    length = float(data.get("format", {}).get("duration") or video.get("duration") or 0)
    if length <= 0 or duration and abs(length - duration) > max(1, duration * .05):
        raise RuntimeError("Durasi output tidak sesuai klip")
    if require_audio and not any(s.get("codec_type") == "audio" for s in streams):
        raise RuntimeError("Output kehilangan audio")


def finalize_video(args, out, duration, progress_cb=None, size=None, require_audio=False):
    """Publish only a probed complete file; failed exports preserve the previous file."""
    out = Path(out)
    temporary = out.with_name(f".{out.stem}-{uuid.uuid4().hex}.partial{out.suffix}")
    command = [*args[:-1], str(temporary)]
    try:
        result = run_ffmpeg(command, duration, progress_cb, timeout=7200)
        if not result.ok and "h264_nvenc" in command:
            # A driver can fail after the startup probe. Retry the same snapshot on CPU.
            first = command.index("-c:v")
            last = command.index("-threads", first)
            command[first:last] = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
            result = run_ffmpeg(command, duration, progress_cb, timeout=7200)
        if not result.ok:
            raise RuntimeError(f"render gagal: {result.stderr[-400:]}")
        validate_video(temporary, duration, size, require_audio)
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)


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
