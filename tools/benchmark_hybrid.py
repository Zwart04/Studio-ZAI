"""Opt-in measurements using installed models and controlled synthetic speech."""
import gc
import json
import threading
import time
from pathlib import Path

import psutil

from studiozai import cache, config
from studiozai.models import manager
from studiozai.pipeline import highlight, probe, transcribe, voice
from studiozai.execution_policy import processing

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/hybrid-asr-benchmark'
TEXTS = {
    'id': 'Bagaimana membuat klip podcast tanpa mengunduh video penuh? Gunakan caption untuk memilih bagian yang menarik. Setelah itu ambil hanya video klip yang dibutuhkan. Simpan video dengan kanvas portrait agar siap diputar di telepon.',
    'en': 'How do we create podcast clips without downloading the full video? Use captions to choose a complete question and answer. Then fetch only the selected video segment. Keep the portrait canvas when exporting for a phone.',
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    models = {name: manager.model_dir(name) for name in ('whisper-tiny-int8', 'whisper-base-int8', 'whisper-small-int8')}
    available = {name: manager.is_installed(name) for name in models}
    speech = {}
    for language, text in TEXTS.items():
        voice_id = 'piper-id_ID-news_tts-medium' if language == 'id' else 'supertonic-3-int8'
        if not manager.is_installed(voice_id):
            continue
        path = OUT / f'{language}.wav'
        with processing('offline'):
            voice.synthesize(text, path, voice_id=voice_id, lang=language)
        speech[language] = path
        voice._SUPERTONIC_ENGINE = None
        gc.collect()
    config._base_dir = lambda: OUT / 'isolated-data'
    report = {'fixture': 'Synthetic local TTS with known reference text; not a real-podcast quality benchmark',
              'cloud_requests': 0, 'model_downloads': 0, 'models_available': available, 'runs': []}
    stop = threading.Event()
    samples = []
    def sample():
        while not stop.wait(.05):
            samples.append(psutil.Process().memory_info().rss)
    worker = threading.Thread(target=sample, daemon=True)
    worker.start()
    try:
        for model, directory in models.items():
            if not available[model]:
                continue
            for language, path in speech.items():
                transcribe.ModelCache.clear(); gc.collect(); samples.clear()
                started = time.perf_counter()
                with processing('offline'):
                    result = transcribe.transcribe(path, model_id=str(directory), lang=language)
                elapsed = time.perf_counter() - started
                cold_peak = max(samples, default=0)/1048576
                started = time.perf_counter()
                with processing('offline'):
                    warm = transcribe.transcribe(path, model_id=str(directory), lang=language)
                warm_seconds = time.perf_counter()-started
                started = time.perf_counter()
                clips = highlight.pick_clips(probe.probe(path).duration, transcript=result, count=2, min_len=3, max_len=30)
                candidate_seconds = time.perf_counter()-started
                identifier = cache.key('benchmark', cache.file_identity(path), model, language)
                cache.write(identifier, result)
                cache_started = time.perf_counter(); restored = cache.read(identifier)
                assert restored == result
                row = {'model':model, 'language':language, 'audio_seconds':probe.probe(path).duration,
                    'cold_seconds':round(elapsed,3), 'warm_seconds':round(warm_seconds,3),
                    'process_peak_rss_mib':round(cold_peak,1), 'device':result.get('device'),
                    'recognized_text':result['text'], 'reference_text':TEXTS[language],
                    'measured_words':sum(len(s['words']) for s in result['segments']), 'candidates':len(clips),
                    'candidate_seconds':round(candidate_seconds,4), 'cache_read_seconds':round(time.perf_counter()-cache_started,4),
                    'warm_text_equal':warm['text']==result['text']}
                report['runs'].append(row)
                print(model,language,round(elapsed,2),round(warm_seconds,2),flush=True)
        report['success'] = bool(report['runs'])
    finally:
        stop.set(); worker.join(timeout=1); transcribe.ModelCache.clear()
        (OUT/'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
