import 'dart:io';
import 'dart:typed_data';

import 'package:sherpa_onnx/sherpa_onnx.dart' as sherpa;

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

/// On-device speech: Whisper (ASR), Piper/VITS (TTS) and ZipVoice (cloning)
/// through sherpa-onnx. Everything runs offline on the phone.
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
    _recognizer?.free();
    _recognizer = null;
    _loadedAsr = null;
    _tts?.free();
    _tts = null;
    _loadedTts = null;
  }

  // ------------------------------------------------------------------- asr

  Future<void> loadAsr(String modelId) async {
    if (_loadedAsr == modelId && _recognizer != null) return;
    final model = models.find(modelId);
    if (model == null || !models.isInstalled(model)) {
      throw Exception('Model transkripsi belum terpasang: $modelId');
    }
    final encoder = models.fileWith(model, ['encoder.onnx', 'encoder.int8.onnx']);
    final decoder = models.fileWith(model, ['decoder.onnx', 'decoder.int8.onnx']);
    final tokens = models.fileWith(model, ['tokens.txt']);
    if (encoder == null || decoder == null || tokens == null) {
      throw Exception('Berkas model $modelId tidak lengkap (encoder/decoder/tokens).');
    }
    sherpa.initBindings();
    _recognizer?.free();
    _recognizer = sherpa.OfflineRecognizer(
      sherpa.OfflineRecognizerConfig(
        feat: const sherpa.FeatureConfig(sampleRate: 16000, featureDim: 80),
        model: sherpa.OfflineModelConfig(
          whisper: sherpa.OfflineWhisperModelConfig(
            encoder: encoder.path,
            decoder: decoder.path,
          ),
          tokens: tokens.path,
          modelType: 'whisper',
          numThreads: 2,
          provider: 'cpu',
          debug: false,
        ),
      ),
    );
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
      final vad = sherpa.VoiceActivityDetector(
        config: sherpa.VadModelConfig(
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
        ),
        bufferSizeInSeconds: 60,
      );
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
    final text = result.text;
    stream.free();
    return text;
  }

  // ------------------------------------------------------------------- tts

  Future<void> loadTts(String modelId) async {
    if (_loadedTts == modelId && _tts != null) return;
    final model = models.find(modelId);
    if (model == null || !models.isInstalled(model)) {
      throw Exception('Model suara belum terpasang: $modelId');
    }
    final onnx = models.fileWith(model, ['.onnx']);
    final tokens = models.fileWith(model, ['tokens.txt']);
    final dataDir = models.directoryWith(model, 'espeak-ng-data');
    if (onnx == null || tokens == null) {
      throw Exception('Berkas model suara $modelId tidak lengkap.');
    }
    sherpa.initBindings();
    _tts?.free();
    _tts = sherpa.OfflineTts(
      sherpa.OfflineTtsConfig(
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
      ),
    );
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
    final audio = _tts!.generate(text: text, sid: 0, speed: speed);
    await MediaTools.writeWav(outputPath, audio.samples, audio.sampleRate);
    return File(outputPath);
  }

  // --------------------------------------------------------------- cloning

  /// Zero-shot cloning with ZipVoice (English) - fully on-device.
  ///
  /// Needs the reference clip *and* its transcript; sherpa-onnx matches them to
  /// transfer the speaker's timbre onto new text.
  Future<File> cloneWithZipVoice({
    required String text,
    required String referenceWav,
    required String referenceText,
    required String outputPath,
  }) async {
    if (text.trim().isEmpty) throw Exception('Teks kosong.');
    if (!File(referenceWav).existsSync()) throw Exception('Rekaman contoh tidak ditemukan.');

    final model = models.find('zipvoice-zh-en');
    if (model == null || !models.isInstalled(model)) {
      throw Exception('Model ZipVoice belum terpasang. Unduh dulu di halaman Model.');
    }
    final encoder = models.fileWith(model, ['encoder.onnx', 'encoder.int8.onnx']);
    final decoder = models.fileWith(model, ['decoder.onnx', 'decoder.int8.onnx']);
    final vocoder = models.fileWith(model, ['vocoder.onnx', 'vocoder.int8.onnx']);
    final tokens = models.fileWith(model, ['tokens.txt']);
    if (encoder == null || decoder == null || vocoder == null || tokens == null) {
      throw Exception('Berkas model ZipVoice tidak lengkap.');
    }

    sherpa.initBindings();
    final tts = sherpa.OfflineTts(
      sherpa.OfflineTtsConfig(
        model: sherpa.OfflineTtsModelConfig(
          zipvoice: sherpa.OfflineTtsZipVoiceModelConfig(
            tokens: tokens.path,
            encoder: encoder.path,
            decoder: decoder.path,
            vocoder: vocoder.path,
          ),
          numThreads: 2,
          provider: 'cpu',
          debug: false,
        ),
      ),
    );

    try {
      final reference = _readReference(referenceWav);
      final audio = tts.generateWithConfig(
        text: text,
        config: sherpa.OfflineTtsGenerationConfig(
          referenceAudio: reference,
          referenceSampleRate: 16000,
          referenceText: referenceText,
          speed: 1.0,
          numSteps: 8,
        ),
      );
      await MediaTools.writeWav(outputPath, audio.samples, audio.sampleRate);
      return File(outputPath);
    } finally {
      tts.free();
    }
  }

  /// ZipVoice expects 16 kHz mono float samples (-1..1).
  Float32List _readReference(String path) {
    var samples = MediaTools.readWavSamples(path);
    if (samples.isEmpty) throw Exception('Rekaman contoh tidak bisa dibaca (gunakan WAV 16 kHz mono).');
    // Keep the reference short: 4-15 seconds is plenty and much faster.
    final maxSamples = 16000 * 15;
    if (samples.length > maxSamples) samples = Float32List.sublistView(samples, 0, maxSamples);
    return samples;
  }
}
