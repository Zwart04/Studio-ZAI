"""Normalized crop centers and linear keyframes, evaluated by FFmpeg."""
from __future__ import annotations

from itertools import pairwise

from .caption_style import number


def clean(data: dict | None) -> dict:
    data = data or {}
    frames = {}
    for row in (data.get("keyframes") or [])[:600]:
        if isinstance(row, dict):
            t = number(row.get("time"), 0, 0, 86400)
            frames[t] = {"time": t, "x": number(row.get("x"), .5, 0, 1), "y": number(row.get("y"), .5, 0, 1)}
    return {"x": number(data.get("x"), .5, 0, 1), "y": number(data.get("y"), .5, 0, 1),
            "zoom": number(data.get("zoom"), 1, 1, 4), "keyframes": [frames[t] for t in sorted(frames)]}


def chain(data: dict, sw: int, sh: int, ow: int, oh: int) -> str:
    f = clean(data)
    ratio = ow / oh
    cw, ch = min(sw, sh * ratio) / f["zoom"], min(sh, sw / ratio) / f["zoom"]
    cw, ch = max(2, int(cw) // 2 * 2), max(2, int(ch) // 2 * 2)
    frames = f["keyframes"]
    if not frames or frames[0]["time"] > 0:
        frames = [{"time": 0, "x": f["x"], "y": f["y"]}, *frames]

    def expression(axis: str, source: int, size: int) -> str:
        expression = f"{frames[-1][axis]:.6f}"
        for a, b in reversed(list(pairwise(frames))):
            span = max(.001, b["time"] - a["time"])
            value = f"({a[axis]:.6f}+({b[axis] - a[axis]:.6f})*(t-{a['time']:.3f})/{span:.3f})"
            expression = f"if(lt(t,{b['time']:.3f}),{value},{expression})"
        return f"max(0,min({source - size},({expression})*{source}-{size / 2}))"
    return f"crop={cw}:{ch}:'{expression('x', sw, cw)}':'{expression('y', sh, ch)}',scale={ow}:{oh}:flags=lanczos,setsar=1"


def split_graph(data: dict, sw: int, sh: int, ow: int, oh: int) -> str:
    top_height = max(2, min(oh - 2, int(oh * number(data.get("fraction"), .35, .2, .8)) // 2 * 2))
    top = chain(data.get("top") or {"x": .15, "y": .2, "zoom": 2}, sw, sh, ow, top_height)
    bottom = chain(data.get("bottom") or {"x": .5, "y": .5}, sw, sh, ow, oh - top_height)
    return f"split=2[face][game];[face]{top}[faceout];[game]{bottom}[gameout];[faceout][gameout]vstack=inputs=2,setsar=1[vout]"


def slice_framing(data: dict, offset: float, duration: float) -> dict:
    if "top" in data or "bottom" in data:
        return {**data, **{k: slice_framing(data[k], offset, duration) for k in ("top", "bottom") if k in data}}
    f = clean(data)
    frames = f["keyframes"]
    if not frames:
        return f
    if frames[0]["time"] > 0:
        frames = [{"time": 0, "x": f["x"], "y": f["y"]}, *frames]
    def at(time):
        before = frames[0]
        for after in frames[1:]:
            if time <= after["time"]:
                ratio = max(0, min(1, (time - before["time"]) / max(.001, after["time"] - before["time"])))
                return {axis: before[axis] + (after[axis] - before[axis]) * ratio for axis in ("x", "y")}
            before = after
        return {axis: before[axis] for axis in ("x", "y")}
    first, last = at(offset), at(offset + duration)
    return {**f, **first, "keyframes": [{"time": 0, **first},
        *[{**row, "time": row["time"] - offset} for row in frames if offset < row["time"] < offset + duration],
        {"time": duration, **last}]}


def follow_face(path: str, start: float, end: float, x: float = .5, progress=None) -> dict:
    """Track the face nearest the previous center. No speaker identity inference."""
    import cv2
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    capture = cv2.VideoCapture(path)
    frames = []
    previous = (x, .4)
    duration = max(.1, end - start)
    interval = max(.75, duration / 180)
    try:
        if not capture.isOpened():
            raise ValueError("Video tidak dapat dibaca untuk pelacakan wajah")
        t = 0.0
        while t < duration:
            capture.set(cv2.CAP_PROP_POS_MSEC, (start + t) * 1000)
            ok, frame = capture.read()
            if ok:
                scale = min(1, 640 / frame.shape[1])
                small = cv2.resize(frame, None, fx=scale, fy=scale)
                faces = detector.detectMultiScale(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), 1.1, 5, minSize=(24, 24))
                centers = [((a + w / 2) / small.shape[1], (b + h / 2) / small.shape[0]) for a, b, w, h in faces]
                if centers:
                    center = min(centers, key=lambda p: (p[0] - previous[0]) ** 2 + (p[1] - previous[1]) ** 2)
                    previous = center if not frames else tuple(.65 * old + .35 * new for old, new in zip(previous, center))
                    frames.append({"time": round(t, 3), "x": round(previous[0], 4), "y": round(previous[1], 4)})
            if progress:
                progress(100 * t / duration, "mengikuti wajah")
            t += interval
    finally:
        capture.release()
    if not frames:
        raise ValueError("Wajah tidak terdeteksi. Gunakan crop manual atau keyframe.")
    return {"x": frames[0]["x"], "y": frames[0]["y"], "zoom": 1, "keyframes": frames}
