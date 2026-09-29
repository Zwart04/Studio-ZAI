"""On-device translation using downloadable Argos CTranslate2 packages."""
from __future__ import annotations

import copy
import json
import re
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from .. import config

INDEX = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
LANGUAGES = {"id": "Indonesia", "en": "English", "es": "Español", "fr": "Français", "de": "Deutsch",
             "pt": "Português", "ar": "العربية", "ja": "日本語", "ko": "한국어", "zh": "中文", "ru": "Русский"}


def root() -> Path:
    path = config.data_dir() / "translation"
    path.mkdir(parents=True, exist_ok=True)
    return path


def packages() -> list[dict]:
    cache = root() / "index.json"
    if not cache.exists():
        with urllib.request.urlopen(INDEX, timeout=30) as response:
            raw = response.read(4 * 1024 * 1024)
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("Indeks model terjemahan tidak valid")
        cache.write_bytes(raw)
    return json.loads(cache.read_text(encoding="utf-8"))


def ensure_model(source: str, target: str, progress=None) -> Path:
    destination = root() / f"{source}-{target}"
    if (destination / "model" / "model.bin").exists():
        return destination
    matches = [p for p in packages() if p.get("from_code") == source and p.get("to_code") == target]
    if not matches:
        raise ValueError(f"Model lokal {source} → {target} belum tersedia")
    package = matches[-1]
    url = next((u for u in package.get("links", []) if u.startswith("https://")), None)
    if not url:
        raise ValueError("Unduhan model HTTPS tidak tersedia")
    with tempfile.TemporaryDirectory(prefix="download-", dir=root()) as work:
        archive = Path(work) / "model.zip"
        request = urllib.request.Request(url, headers={"User-Agent": "StudioZAI/1.9 ArgosTranslate"})
        with urllib.request.urlopen(request, timeout=90) as response, archive.open("wb") as output:
            size = int(response.headers.get("Content-Length", 0))
            done = 0
            while chunk := response.read(1024 * 1024):
                done += len(chunk)
                if done > 1024**3:
                    raise ValueError("Model terlalu besar")
                output.write(chunk)
                if progress:
                    progress(min(75, 75 * done / size) if size else 10, f"unduh {source} → {target}: {done // 1048576} MB")
        extracted = Path(work) / "files"
        with zipfile.ZipFile(archive) as bundle:
            if sum(i.file_size for i in bundle.infolist()) > 2 * 1024**3:
                raise ValueError("Arsip model terlalu besar")
            for item in bundle.infolist():
                resolved = (extracted / item.filename).resolve()
                if not resolved.is_relative_to(extracted.resolve()):
                    raise ValueError("Path arsip model tidak aman")
            bundle.extractall(extracted)
        metadata = next(extracted.rglob("metadata.json"), None)
        if metadata is None or not (metadata.parent / "model" / "model.bin").exists():
            raise ValueError("Isi model terjemahan tidak lengkap")
        if destination.exists():
            # Only an incomplete model directory owned by this module.
            shutil.rmtree(destination)
        shutil.move(str(metadata.parent), destination)
    return destination


def translate_texts(texts: list[str], source: str, target: str, progress=None) -> list[str]:
    if source not in LANGUAGES or target not in LANGUAGES:
        raise ValueError("Bahasa terjemahan tidak didukung")
    if source == target:
        return list(texts)
    import ctranslate2
    import sentencepiece
    pairs = [(source, target)] if source == "en" or target == "en" else [(source, "en"), ("en", target)]
    values = texts
    for src, dst in pairs:
        path = ensure_model(src, dst, progress)
        metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        tokenizer_path = path / "sentencepiece.model"
        if tokenizer_path.exists():
            tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(tokenizer_path))
            encode = lambda text, tokenizer=tokenizer: tokenizer.encode(text, out_type=str)
            decode = tokenizer.decode
        elif (path / "bpe.model").exists():
            from sacremoses import MosesDetokenizer, MosesPunctNormalizer, MosesTokenizer
            from subword_nmt.apply_bpe import BPE
            normalizer, tokenizer, detokenizer = MosesPunctNormalizer(src), MosesTokenizer(src), MosesDetokenizer(dst)
            with (path / "bpe.model").open(encoding="utf-8") as codes:
                bpe = BPE(codes)
            encode = lambda text, bpe=bpe, tokenizer=tokenizer, normalizer=normalizer: bpe.process_line(" ".join(tokenizer.tokenize(normalizer.normalize(text)))).split()
            decode = lambda pieces, detokenizer=detokenizer: detokenizer.detokenize(" ".join(pieces).replace("@@ ", "").split())
        else:
            raise ValueError("Tokenizer model ini belum didukung")
        translator = ctranslate2.Translator(str(path / "model"), device="cpu", compute_type="int8", inter_threads=1, intra_threads=4)
        result = []
        try:
            for i in range(0, len(values), 16):
                batch = values[i:i + 16]
                tokens = [encode(text) for text in batch]
                prefix = metadata.get("target_prefix", "")
                translated = translator.translate_batch(tokens, beam_size=2, max_decoding_length=512,
                    target_prefix=[[prefix]] * len(tokens) if prefix else None, replace_unknowns=True)
                result.extend(decode(row.hypotheses[0]).removeprefix(prefix).strip() for row in translated)
                if progress:
                    progress(80 + 19 * (i + len(batch)) / max(1, len(values)), f"terjemahan {src} → {dst}")
        finally:
            translator.unload_model()
        values = result
    return values


def translate_captions(rows: list[dict], source: str, target: str, progress=None) -> list[dict]:
    texts = translate_texts([str(r.get("text", "")) for r in rows], source, target, progress)
    result = copy.deepcopy(rows)
    for row, text in zip(result, texts):
        row["text"] = text
        tokens = re.findall(r"\S+", text)
        span = (row["end"] - row["start"]) / max(1, len(tokens))
        # Translation changes word order. Cue timing/style stay exact; word
        # times are evenly estimated and individually editable in the UI.
        row["words"] = [{"word": word, "start": row["start"] + i * span,
                         "end": row["start"] + (i + 1) * span} for i, word in enumerate(tokens)]
    return result
