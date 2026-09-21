import 'dart:io';
import 'dart:typed_data';

import 'package:sherpa_onnx/sherpa_onnx.dart' as sherpa;

import '../models.dart';
import 'media_tools.dart';
import 'model_manager.dart';

class TranscriptSegment {
  TranscriptSegment(this.start, this.end, this.text);

  final double start;
  final double end;
  final String text;

  Map<String, dynamic> toJson() => {
        'start': double.parse(start.toStringAsFixed(3)),
        'end': double.parse(end.toStringAsFixed(3)),
        'text': text,
      };

  static TranscriptSegment fromJson(Map<String, dynamic> json) => TranscriptSegment(
        (json['start'] as num).toDouble(),
        (json['end'] as num).toDouble(),
        json['text'] as String? ?? '',
      );
}

/// On-device speech: Whisper (ASR) and Piper/VITS (TTS) through sherpa-onnx.
///
/// Note: exact sherpa-onnx Dart symbol names can shift between releases —
/// if `flutter analyze` reports a mismatch, check the sherpa_onnx package
/// version in pubspec.yaml and adjust the constructor names here.
class SpeechService {
  SpeechService(this.models);

  final ModelManager models;

  sherpa.OfflineRecognizer? _recognizer;
  String? _loadedAsr;
  sherpa.OfflineTts? _tts;
  String? _loadedTts;

  bool get asrReady => _recognizer != null;
  bool get ttsReady => _tts != null;

  void reset() {
    _recognizer = null;
    _loadedAsr = null;
    _tts = null;
    _loadedTts = null;
  }

  Future<void> loadAsr(String modelId) async {
    if (_loadedAsr == modelId && _recognizer != null) return;
    final model = models.find(modelId);
    if (model == null || !models.isInstalled(model)) {
      throw Exception('Model transkripsi belum terpasang: $modelId');
    }
    sherpa.initBindings();
    final encoder = models.fileWith(model, ['encoder.onnx', 'encoder.int8.onnx']);
    final decoder = models.fileWith(model, ['decoder.onnx', 'decoder.int8.onnx']);
    final tokens = models.fileWith(model, ['tokens.txt']);
    if (encoder == null || decoder == null || tokens == null) {
      throw Exception('Berkas model $modelId tidak lengkap (encoder/decoder/tokens).');
    }
    final config = sherpa.OfflineRecognizerConfig(
      model: sherpa.OfflineModelConfig(
        whisper: sherpa.OfflineWhisperModelConfig(
          encoder: encoder.path,
          decoder: decoder.path,
        ),
        tokens: tokens.path,
        numThreads: 2,
        provider: 'cpu',
        debug: false,
      ),
      featConfig: const sherpa.FeatureConfig(sampleRate: 16000, featureDim: 80),
    );
    _recognizer = sherpa.OfflineRecognizer(config);
    _loadedAsr = modelId;
  }

  /// Transcribe a 16 kHz mono WAV; silero VAD splits it into speech segments.
  Future<List<TranscriptSegment>> transcribeWav(String wavPath, {String? language}) async {
    final recognizer = _recognizer;
    if (recognizer == null) throw Exception('Model transkripsi belum dimuat.');

    final samples = MediaTools.readWavSamples(wavPath);
    if (samples.isEmpty) return const [];

    final vadModel = models.find('silero-vad');
    final vadFile = vadModel == null ? null : models.fileWith(vadModel, ['silero_vad.onnx']);
    final segments = <TranscriptSegment>[];

    if (vadFile != null) {
      final vadConfig = sherpa.VadModelConfig(
        sileroVad: sherpa.SileroVadModelConfig(
          model: vadFile.path,
          threshold: 0.5,
          minSilenceDuration: 0.35,
          minSpeechDuration: 0.25,
          maxSpeechDuration: 20.0,
          windowSize: 512,
        ),
        sampleRate: 16000,
        numThreads: 1,
        provider: 'cpu',
        debug: false,
      );
      final vad = sherpa.VoiceActivityDetector(config: vadConfig, bufferSizeInSeconds: 60);
      vad.acceptWaveform(samples);
      vad.flush();
      while (!vad.isEmpty()) {
        final speech = vad.front();
        final text = _decode(recognizer, speech.samples);
        if (text.trim().isNotEmpty) {
          segments.add(TranscriptSegment(
            speech.start / 16000.0,
            (speech.start + speech.samples.length) / 16000.0,
            text.trim(),
          ));
        }
        vad.pop();
      }
      vad.free();
    } else {
      final text = _decode(recognizer, samples);
      if (text.trim().isNotEmpty) {
        segments.add(TranscriptSegment(0, samples.length / 16000.0, text.trim()));
      }
    }
    return segments;
  }

  String _decode(sherpa.OfflineRecognizer recognizer, Float32List samples) {
    final stream = recognizer.createStream();
    stream.acceptWaveform(samples: samples, sampleRate: 16000);
    recognizer.decode(stream);
    final result = recognizer.getResult(stream);
    stream.free();
    return result.text;
  }

  Future<void> loadTts(String modelId) async {
    if (_loadedTts == modelId && _tts != null) return;
    final model = models.find(modelId);
    if (model == null || !models.isInstalled(model)) {
      throw Exception('Model suara belum terpasang: $modelId');
    }
    sherpa.initBindings();
    final onnx = models.fileWith(model, ['.onnx']);
    final tokens = models.fileWith(model, ['tokens.txt']);
    final dataDir = models.directoryWith(model, 'espeak-ng-data');
    if (onnx == null || tokens == null) {
      throw Exception('Berkas model suara $modelId tidak lengkap.');
    }
    final config = sherpa.OfflineTtsConfig(
      model: sherpa.OfflineTtsModelConfig(
        vits: sherpa.OfflineTtsVitsModelConfig(
          model: onnx.path,
          tokens: tokens.path,
          dataDir: dataDir?.path ?? '',
        ),
        numThreads: 2,
        provider: 'cpu',
        debug: false,
      ),
    );
    _tts = sherpa.OfflineTts(config);
    _loadedTts = modelId;
  }

  /// Generate narration with a Piper voice (fast, no cloning).
  Future<File> synthesize({
    required String text,
    required String modelId,
    required String outputPath,
    double speed = 1.0,
  }) async {
    await loadTts(modelId);
    final tts = _tts!;
    final audio = tts.generate(text: text, sid: 0, speed: speed);
    await MediaTools.writeWav(outputPath, audio.samples, audio.sampleRate);
    return File(outputPath);
  }

  /// Experimental: ZipVoice zero-shot cloning (English) via sherpa-onnx.
  ///
  /// ZipVoice needs both the reference clip and its transcript, and is wired
  /// through a dedicated sherpa-onnx TTS configuration. Until that wiring is
  /// verified on a physical device, this method fails loudly instead of
  /// producing broken audio. Tracked in docs/FEATURES.md (F-24) and
  /// docs/PLAN.md (M4 gate).
  Future<File> cloneWithZipVoice({
    required String text,
    required String referenceWav,
    required String referenceText,
    required String outputPath,
  }) async {
    throw UnsupportedError(
      'Kloning di Android masih tahap eksperimental: konfigurasi ZipVoice sherpa-onnx '
      'belum diverifikasi di perangkat. Pakai desktop Studio ZAI untuk kloning '
      '(Chatterbox, ID + EN). Lihat docs/MODELS.md.',
    );
  }
}
