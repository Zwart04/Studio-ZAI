import '../models.dart';

/// Android model catalog (mirrors docs/MODELS.md).
///
/// All entries are downloaded on demand from official release assets
/// (k2-fsa/sherpa-onnx for speech models, HuggingFace for Piper voices).
class ModelRegistry {
  static final whisperTiny = ModelInfo(
    id: 'whisper-tiny',
    kind: 'asr',
    langs: ['id', 'en'],
    sizeMb: 110,
    license: 'MIT',
    note: 'Paling cepat, akurasi dasar',
    url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-tiny.tar.bz2',
    tier: 0,
  );

  static final whisperBase = ModelInfo(
    id: 'whisper-base',
    kind: 'asr',
    langs: ['id', 'en'],
    sizeMb: 190,
    license: 'MIT',
    note: 'Seimbang untuk subtitle ID/EN',
    url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-base.tar.bz2',
    tier: 1,
  );

  static final piperId = ModelInfo(
    id: 'piper-id_ID-news_tts-medium',
    kind: 'tts',
    langs: ['id'],
    sizeMb: 63,
    license: 'MIT',
    note: 'Suara Indonesia (Piper) — realtime di HP',
    url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-id_ID-news_tts-medium.tar.bz2',
    tier: 0,
  );

  static final piperEn = ModelInfo(
    id: 'piper-en_US-lessac-medium',
    kind: 'tts',
    langs: ['en'],
    sizeMb: 63,
    license: 'MIT',
    note: 'Suara Inggris (Piper)',
    url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-medium.tar.bz2',
    tier: 0,
  );

  static final zipVoice = ModelInfo(
    id: 'zipvoice-zh-en',
    kind: 'clone',
    langs: ['en'],
    sizeMb: 350,
    license: 'Apache-2.0',
    note: 'Kloning EN ringan (butuh rekaman contoh)',
    url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia.tar.bz2',
    tier: 1,
  );

  static final chatterboxQ4 = ModelInfo(
    id: 'chatterbox-gguf-q4',
    kind: 'clone',
    langs: ['id', 'en'],
    sizeMb: 550,
    license: 'MIT',
    note: 'EKSPERIMENTAL: kloning ID/EN (uji kecepatan dulu). Di CPU HP bisa sangat lambat.',
    url: 'https://huggingface.co/calcuis/chatterbox-gguf/resolve/main/chatterbox-q4.gguf',
    archive: false,
    tier: 3,
    experimental: true,
  );

  static final vad = ModelInfo(
    id: 'silero-vad',
    kind: 'asr',
    langs: ['multi'],
    sizeMb: 2,
    license: 'MIT',
    note: 'Deteksi suara/bicara (dipakai untuk membagi segmen)',
    url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx',
    archive: false,
    tier: 0,
  );

  static final all = <ModelInfo>[
    whisperTiny,
    whisperBase,
    piperId,
    piperEn,
    zipVoice,
    vad,
    chatterboxQ4,
  ];
}
