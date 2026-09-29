"""Local, explainable podcast moment selection; scores are editorial hints."""
from __future__ import annotations

import math
import re
from typing import Any

QUESTION = re.compile(r"\?|\b(kenapa|mengapa|bagaimana|gimana|apa yang|what|why|how)\b", re.IGNORECASE)
HOOK = re.compile(r"\b(ternyata|rahasia|kesalahan|jangan|bayangkan|fakta|terpenting|secret|mistake|never|imagine|surprising|truth)\b", re.IGNORECASE)
STORY = re.compile(r"\b(dulu|pernah|waktu itu|pengalaman|akhirnya|belajar|kisah|once|remember|learned|story|realized)\b", re.IGNORECASE)
TAKEAWAY = re.compile(r"\b(intinya|jadi|kesimpulan|caranya|pelajaran|solusi|tips|because|lesson|therefore|solution|advice)\b", re.IGNORECASE)
AD = re.compile(r"\b(sponsor|kode promo|link di bio|subscribe|diskon|promo code|discount|commercial break)\b", re.IGNORECASE)


def moments(transcript: dict[str, Any], duration: float, count: int = 0,
            min_len: float = 20, max_len: float = 90) -> list[dict[str, Any]]:
    """Anchor on complete utterances; retain questions with their answers.

    Never infer speaker identity from punctuation. Works without an API/model
    after transcription and reports the cues behind each score.
    """
    segments = []
    for row in transcript.get("segments", []):
        try:
            start, end = float(row["start"]), float(row["end"])
        except (KeyError, ValueError, TypeError):
            continue
        if math.isfinite(start) and math.isfinite(end) and 0 <= start < end and start < duration:
            segments.append({**row, "start": start, "end": min(end, duration)})
    segments.sort(key=lambda s: s["start"])
    minimum = max(3, min_len or 20)
    maximum = max(minimum, max_len or 90)
    target = count if count > 0 else max(3, min(10, math.ceil(duration / 300)))
    pool = []
    for i, first in enumerate(segments):
        rows = []
        for row in segments[i:]:
            if row["end"] - first["start"] > maximum:
                break
            rows.append(row)
            span = row["end"] - first["start"]
            text = " ".join(str(s.get("text", "")) for s in rows).strip()
            if span < minimum or not text:
                continue
            # A lone question is incomplete even when it exceeds the minimum.
            if len(rows) == 1 and text.endswith("?"):
                continue
            cues = []
            score = .25
            for pattern, weight, label in ((QUESTION, .18, "tanya-jawab"), (HOOK, .20, "hook"),
                                           (STORY, .14, "cerita"), (TAKEAWAY, .17, "poin utama")):
                if pattern.search(text):
                    score += weight
                    cues.append(label)
            if AD.search(text):
                score -= .4
                cues.append("mengandung promosi")
            if re.search(r"[.!?…]$", text):
                score += .06
            score -= min(.12, abs(span - 50) / 500)
            opening = str(first.get("text", "")).strip()
            title = " ".join(opening.split()[:12]).rstrip(".,;:")
            pool.append({"start": first["start"], "end": row["end"], "score": round(max(0, min(1, score)), 3),
                         "title": title, "reason": "Podcast lokal · " + (", ".join(cues) or "ucapan utuh"), "text": text})
            if span >= 45 and re.search(r"[.!?…]$", text):
                break
    chosen = []
    for candidate in sorted(pool, key=lambda s: (-s["score"], s["start"])):
        if any(min(candidate["end"], c["end"]) - max(candidate["start"], c["start"]) > .5 for c in chosen):
            continue
        chosen.append(candidate)
        if len(chosen) >= target:
            break
    return sorted(chosen, key=lambda s: s["start"])
