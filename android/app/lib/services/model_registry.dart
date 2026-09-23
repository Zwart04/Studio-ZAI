import '../models.dart';

/// Android model catalog (mirrors docs/MODELS.md).
///
/// All entries are downloaded on demand from official release assets
/// (k2-fsa/sherpa-onnx for speech models, HuggingFace for Piper voices).
class ModelRegistry {
  static const supertonicFiles = <String>[
    'duration_predictor.int8.onnx',
    'text_encoder.int8.onnx',
    'vector_estimator.int8.onnx',
    'vocoder.int8.onnx',
    'tts.json',
    'unicode_indexer.bin',
    'voice.bin',
  ];
  static final whisperTiny = ModelInfo(
    id: 'whisper-tiny',
    kind: 'asr',
    langs: ['id', 'en'],
    sizeMb: 110,
    license: 'MIT',
    note: 'Paling cepat, akurasi dasar',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-tiny.tar.bz2',
    tier: 0,
  );

  static final whisperBase = ModelInfo(
    id: 'whisper-base',
    kind: 'asr',
    langs: ['id', 'en'],
    sizeMb: 190,
    license: 'MIT',
    note: 'Seimbang untuk subtitle ID/EN',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-base.tar.bz2',
    tier: 1,
  );

  static final piperId = ModelInfo(
    id: 'piper-id_ID-news_tts-medium',
    kind: 'tts',
    langs: ['id'],
    sizeMb: 63,
    license: 'MIT',
    note: 'Satu suara Indonesia, ringan di HP; hak data suara belum jelas.',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-id_ID-news_tts-medium.tar.bz2',
    tier: 0,
    commercialUse: 'unverified',
    licenseNote:
        'Kode/model berlabel MIT, tetapi asal dan izin rekaman suara belum terverifikasi.',
    recommended: false,
  );

  static final piperEn = ModelInfo(
    id: 'piper-en_US-ljspeech-medium',
    kind: 'tts',
    langs: ['en'],
    sizeMb: 63,
    license: 'MIT',
    note: 'Suara English ringan dari data LJSpeech domain publik.',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-ljspeech-medium.tar.bz2',
    tier: 0,
    commercialUse: 'allowed',
    licenseUrl:
        'https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ljspeech/medium/MODEL_CARD',
    licenseNote:
        'Model MIT; model card menyatakan dilatih dari awal memakai LJSpeech domain publik.',
  );

  static final piperEnLessac = ModelInfo(
    id: 'piper-en_US-lessac-medium',
    kind: 'tts',
    langs: ['en'],
    sizeMb: 63,
    license: 'Data riset saja',
    note: 'Model lama; data suara Lessac tidak ditujukan untuk komersial.',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-medium.tar.bz2',
    commercialUse: 'restricted',
    licenseNote:
        'Tidak direkomendasikan untuk publikasi atau produk komersial.',
    recommended: false,
  );

  static final zipVoice = ModelInfo(
    id: 'zipvoice-zh-en',
    kind: 'clone',
    langs: ['en', 'zh'],
    sizeMb: 350,
    license: 'Apache-2.0',
    note:
        'Kloning English/Mandarin dari rekaman contoh; bukan Bahasa Indonesia.',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia.tar.bz2',
    tier: 1,
    commercialUse: 'allowed',
    licenseUrl: 'https://github.com/k2-fsa/ZipVoice/blob/master/LICENSE',
    licenseNote:
        'Apache-2.0. Gunakan hanya rekaman suara milik sendiri atau yang diizinkan.',
  );

  static final whisperSmall = ModelInfo(
    id: 'whisper-small',
    kind: 'asr',
    langs: ['id', 'en'],
    sizeMb: 480,
    license: 'MIT',
    note: 'Akurasi lebih baik untuk Bahasa Indonesia (butuh RAM lega).',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2',
    tier: 2,
  );

  static final whisperMedium = ModelInfo(
    id: 'whisper-medium',
    kind: 'asr',
    langs: ['id', 'en'],
    sizeMb: 1500,
    license: 'MIT',
    note: 'Paling akurat, paling berat. Untuk HP dengan RAM besar saja.',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-medium.tar.bz2',
    tier: 3,
  );

  static final piperEnGb = ModelInfo(
    id: 'piper-en_GB-alba-medium',
    kind: 'tts',
    langs: ['en'],
    sizeMb: 63,
    license: 'MIT',
    note: 'Suara Inggris alternatif; hak data suara perlu diperiksa.',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_GB-alba-medium.tar.bz2',
    tier: 0,
    commercialUse: 'unverified',
    licenseNote: 'Model card belum cukup untuk memastikan izin komersial.',
    recommended: false,
  );

  static final vad = ModelInfo(
    id: 'silero-vad',
    kind: 'asr',
    langs: ['multi'],
    sizeMb: 2,
    license: 'MIT',
    note: 'Deteksi suara/bicara (dipakai untuk membagi segmen)',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx',
    archive: false,
    tier: 0,
  );

  static final sdxs = ModelInfo(
    id: 'sdxs-512',
    kind: 'image',
    langs: ['multi'],
    sizeMb: 651,
    license: 'OpenRAIL++',
    note: 'Gambar lokal 512 px · SDXS satu langkah · opsional',
    url:
        'https://huggingface.co/concedo/sdxs-512-tinySDdistilled-GGUF/resolve/3144d898d61492f8382ffcabec055733fc5b2a0e/sdxs-512-tinySDdistilled_Q8_0.gguf',
    archive: false,
    tier: 1,
    sha256: '409ab23582ee074c6b9d5395784fc0741b0599fb9d138686c69087c71678eb6a',
  );

  static final supertonic3 = ModelInfo(
    id: 'supertonic-3-int8',
    kind: 'tts',
    langs: ['id', 'en'],
    sizeMb: 123,
    license: 'OpenRAIL-M',
    note: '10 karakter suara Indonesia/English · opsional',
    url:
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11.tar.bz2',
    tier: 1,
    sha256: '82fa96f91c4ef8abaae3a14a3f4153facf88bed821d1f7331cec2700f432c427',
    commercialUse: 'allowed',
    licenseUrl:
        'https://huggingface.co/Supertone/supertonic-3/blob/main/LICENSE',
    licenseNote:
        'OpenRAIL-M mengizinkan komersial dengan syarat. Model berbobot terbuka, bukan lisensi open source OSI.',
  );

  static final all = <ModelInfo>[
    whisperTiny,
    whisperBase,
    whisperSmall,
    whisperMedium,
    piperId,
    piperEn,
    piperEnLessac,
    piperEnGb,
    ...['amy', 'ryan', 'joe'].map((name) => ModelInfo(
          id: 'piper-en_US-$name-medium',
          kind: 'tts',
          langs: ['en'],
          sizeMb: 63,
          license: name == 'ryan' ? 'CC BY-NC-SA' : 'Perlu verifikasi',
          note: 'English US · $name · model lama',
          url:
              'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-$name-medium.tar.bz2',
          commercialUse: name == 'ryan' ? 'restricted' : 'unverified',
          licenseNote: name == 'ryan'
              ? 'Data suara berlisensi nonkomersial.'
              : 'Hak data suara belum terverifikasi.',
          recommended: false,
        )),
    zipVoice,
    vad,
    supertonic3,
    sdxs,
  ];
}
