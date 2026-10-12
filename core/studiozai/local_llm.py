"""Semantic ranking of bounded candidates using the selected inference runtime."""
import json
import math
import time
from urllib.parse import urlparse

from . import ai, cache

SCHEMA = {"type": "array", "maxItems": 24, "items": {"type": "object", "properties": {
    "candidate_id": {"type": "integer"}, "start": {"type": "number"}, "end": {"type": "number"},
    "title": {"type": "string"}, "reason": {"type": "string"}, "score": {"type": "number", "minimum": 0, "maximum": 1},
    "hook_assessment": {"type": "string"}, "context_completeness": {"type": "number", "minimum": 0, "maximum": 1}},
    "required": ["candidate_id", "start", "end", "title", "reason", "score", "hook_assessment", "context_completeness"],
    "additionalProperties": False}}
_NATIVE_CAPABILITIES = {}


def ollama_origin(base, model, key=""):
    parsed = urlparse(base)
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.port != 11434 or parsed.path.rstrip("/") != "/v1":
        return None
    origin = base[:-3].rstrip("/")
    identifier = (origin, model)
    cached = _NATIVE_CAPABILITIES.get(identifier)
    if not cached or time.monotonic() - cached[0] > 60:
        try:
            version = ai.request(origin, "/api/version", key, timeout=3)
            if not isinstance(version.get("version"), str):
                return None
            show = ai.request(origin, "/api/show", key, {"model": model}, timeout=8)
            _NATIVE_CAPABILITIES[identifier] = (time.monotonic(), (origin, show.get("capabilities", [])))
        except (RuntimeError, ValueError, OSError, AttributeError):
            _NATIVE_CAPABILITIES[identifier] = (time.monotonic(), None)
    return _NATIVE_CAPABILITIES[identifier][1]


def rank_shortlist(*args, **kwargs):
    from .jobs import inference_slot
    with inference_slot(kwargs.get("check_cancel")):
        return _rank_shortlist(*args, **kwargs)


def _rank_shortlist(transcript, candidates, count=5, base_url="http://127.0.0.1:11434/v1", model="",
                   api_key=None, provider=None, min_len=0, max_len=0, **kwargs):
    if provider:
        provider, base_url, saved_model, api_key = kwargs.get("connection_override") or ai.connection("ai")
        model = model or saved_model
        if model in {"auto", ""}:
            model = ai.discover_models(provider, base_url, api_key or "", "ai")["recommended"]
    if not model or model == "auto":
        raise ValueError("Pilih model LLM terpasang di Pengaturan; tidak ada unduhan otomatis.")
    base_url = ai.validate_provider_base(provider or "compatible", base_url)
    options = []
    for i, candidate in enumerate(sorted(candidates, key=lambda c: -c.score)[:24]):
        text = " ".join(str(s.get("text", "")) for s in transcript.get("segments", [])
                        if s["end"] > candidate.start and s["start"] < candidate.end)
        excerpt = text if len(text) <= 900 else text[:450] + " [middle omitted] " + text[-450:]
        options.append({"candidate_id": i, "start": candidate.start, "end": candidate.end, "text": excerpt,
                        "truncated": len(text) > 900})
    if not options:
        return []
    from . import local_runtime
    revision = cache.file_identity(local_runtime._MODEL) if base_url == local_runtime.BASE and local_runtime._MODEL else None
    identifier = cache.key("semantic-v3", transcript, options, base_url, provider, model, revision, min_len, max_len, count)
    previous = cache.read(identifier, max_age=86400)
    if previous is not None:
        return previous
    rows = []
    native = ollama_origin(base_url, model, api_key or "") if provider in {None, "compatible"} else None
    for first in range(0, len(options), 8):
        batch = options[first:first + 8]
        prompt = ("/no_think\nRank only these clip candidates by meaning, hook and narrative completeness. "
                  "Omit advertisements, repetition and incomplete questions or answers. Return only worthwhile standalone clips. "
                  "Do not invent transcript content. Penalize truncated context. Keep timestamps inside each candidate. "
                  f"Duration limits: {min_len or 3} to {max_len or 180} seconds. "
                  "Return JSON matching this schema: " + json.dumps(SCHEMA) + "\n" + json.dumps(batch, ensure_ascii=False))
        if native:
            response = ai.request(native[0], "/api/chat", api_key or "", {
                "model": model, "messages": [{"role": "user", "content": prompt}], "format": SCHEMA,
                "stream": False, "keep_alive": "60s", "options": {"num_ctx": 4096, "num_thread": 4, "num_predict": 1000, "temperature": 0},
                **({"think": False} if "thinking" in native[1] else {})}, check_cancel=kwargs.get("check_cancel"))
            content = response["message"]["content"]
        elif provider:
            content = ai.text(prompt, model_override=model, connection_override=(provider, base_url, model, api_key), check_cancel=kwargs.get("check_cancel"))
        else:
            response = ai.request(base_url, "/chat/completions", api_key or "", {
                "model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0,
                "max_tokens": 1000,
                "response_format": {"type": "json_schema", "json_schema": {"name": "highlights", "schema": SCHEMA}}}, check_cancel=kwargs.get("check_cancel"))
            content = response["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content[content.index("["):content.rindex("]") + 1])
        except (ValueError, TypeError, AttributeError):
            continue
        allowed = {option["candidate_id"]: option for option in batch}
        if not isinstance(parsed, list):
            continue
        for item in parsed[:24]:
            if not isinstance(item, dict):
                continue
            try:
                if type(item.get("candidate_id")) is not int:
                    continue
                if any(type(item.get(field)) not in {int, float} for field in ("start", "end", "score", "context_completeness")):
                    continue
                option = allowed[item["candidate_id"]]
                start, end = float(item["start"]), float(item["end"])
                score, context = float(item["score"]), float(item["context_completeness"])
                if not all(math.isfinite(v) for v in (start, end, score, context)):
                    continue
                if start < option["start"] or end > option["end"] or not (min_len or 3) <= end - start <= (max_len or 180):
                    continue
                if not 0 <= score <= 1 or not 0 <= context <= 1:
                    continue
                if not all(isinstance(item[key], str) and item[key].strip() for key in ("title", "reason", "hook_assessment")):
                    continue
                host = urlparse(base_url).hostname
                engine = "local LLM" if host in {"localhost", "127.0.0.1", "::1"} else "LAN LLM" if provider in {None, "compatible"} else "online AI"
                rows.append({"engine": engine, "start": start, "end": end, "score": score, "title": item["title"][:160],
                             "reason": item["reason"][:300], "hook_assessment": item["hook_assessment"][:300],
                             "context_completeness": context, "model": model})
            except (KeyError, TypeError, ValueError):
                continue
    chosen = []
    for row in sorted(rows, key=lambda r: (-r["score"], r["start"])):
        if any(min(row["end"], other["end"]) - max(row["start"], other["start"]) > .5 for other in chosen):
            continue
        chosen.append(row)
        if len(chosen) >= count:
            break
    if chosen:
        cache.write(identifier, chosen)
    return sorted(chosen, key=lambda r: r["start"])
