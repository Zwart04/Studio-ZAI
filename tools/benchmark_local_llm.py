"""Real inference with an existing GGUF; controlled ID/EN fixtures, no model download."""
import argparse
import json
import threading
import time
from pathlib import Path

import psutil

from studiozai import config, local_llm, local_runtime
from studiozai.pipeline.highlight import ClipCandidate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "hybrid-local-llm-benchmark"
CORPUS = {
    "id": [
        "Kenapa aplikasi mengunduh video penuh padahal ada caption? Kita cukup mengambil metadata dan caption untuk analisis awal. Audio baru dibutuhkan bila caption tidak layak. Ini mengurangi transfer dan waktu tunggu.",
        "Bagaimana menjaga hasil video portrait? Simpan pilihan kanvas sembilan banding enam belas di timeline, lalu validasi dimensi file hasil render. Jangan mengganti rasio saat membuat preview.",
        "Beli produk sponsor sekarang. Gunakan kode promo sponsor. Jangan lupa menekan tombol beli. Ini pesan iklan sponsor, bukan pembahasan utama."],
    "en": [
        "Why did the batch lose a completed export? Each worker saved an old copy of the project. We now merge cache fields into the latest state and validate the clip again after encoding, so new edits remain intact.",
        "How can subtitles update without another video render? Play the original source and draw a timed overlay. Only encode a short draft when the user requests export verification. This keeps ordinary edits responsive.",
        "Buy the sponsor product now and use our promotion code. This advertisement repeats the same offer without an independent story or answer."],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="existing GGUF file")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    config._base_dir = lambda: OUT / "isolated-data"
    report = {"fixture_kind": "controlled synthetic transcripts, not a real podcast quality benchmark",
              "model_file": Path(args.model).name, "model_downloaded": False, "runs": []}
    memory, done = [], threading.Event()
    def sample():
        while not done.wait(.05):
            child = local_runtime._CHILD
            if child:
                try:
                    memory.append(psutil.Process(child.pid).memory_info().rss)
                except psutil.Error:
                    pass
    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    try:
        started = time.perf_counter()
        base, model, key = local_runtime.start(args.model)
        report["model_load_seconds"] = round(time.perf_counter() - started, 3)
        for language, texts in CORPUS.items():
            transcript = {"segments": [{"start": i * 25, "end": i * 25 + 20, "text": text} for i, text in enumerate(texts)]}
            candidates = [ClipCandidate(i * 25, i * 25 + 20, .8, "fixture") for i in range(3)]
            started = time.perf_counter()
            rows = local_llm.rank_shortlist(transcript, candidates, count=2, base_url=base, model=model, api_key=key, min_len=10, max_len=25)
            if not rows:
                raise RuntimeError(f"Real local model did not return valid {language} results")
            report["runs"].append({"language": language, "inference_seconds": round(time.perf_counter() - started, 3),
                "validated_rows": len(rows), "selected_ad": any(row["start"] >= 50 for row in rows), "results": rows})
            print(language, "valid rows:", len(rows), flush=True)
        report["runtime_peak_rss_mib"] = round(max(memory, default=0) / 1048576, 1)
        report["success"] = True
    except Exception as exc:
        report["success"] = False
        report["error"] = str(exc)
        raise
    finally:
        done.set(); sampler.join(timeout=1); local_runtime.stop()
        (OUT / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "runs"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
