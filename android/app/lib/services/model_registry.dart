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

  static final whisperSmall = ModelInfo(
    id: 'whisper-small',
    kind: 'asr',
    langs: ['id', 'en'],
    sizeMb: 480,
    license: 'MIT',
    note: 'Akurasi lebih baik untuk Bahasa Indonesia (butuh RAM lega).',
    url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2',
    tier: 2,
  );

  static final whisperMedium = ModelInfo(
    id: 'whisper-medium',
    kind: 'asr',
    langs: ['id', 'en'],
    sizeMb: 1500,
    license: 'MIT',
    note: 'Paling akurat, paling berat. Untuk HP dengan RAM besar saja.',
    url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-medium.tar.bz2',
    tier: 3,
  );

  static final piperEnGb = ModelInfo(
    id: 'piper-en_GB-alba-medium',
    kind: 'tts',
    langs: ['en'],
    sizeMb: 63,
    license: 'MIT',
    note: 'Suara Inggris (British) alternatif',
    url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_GB-alba-medium.tar.bz2',
    tier: 0,
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
    whisperSmall,
    whisperMedium,
    piperId,
    piperEn,
    piperEnGb,
    ...['amy', 'ryan', 'joe', 'ljspeech'].map((name) => ModelInfo(
      id: 'piper-en_US-$name-medium', kind: 'tts', langs: ['en'], sizeMb: 63,
      license: 'Lihat model card', note: 'English US · $name · opsional',
      url: 'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-$name-medium.tar.bz2',
    )),
    zipVoice,
    vad,
  ];
}
