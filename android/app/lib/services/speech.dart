import 'dart:async';
import 'dart:io';
import 'dart:isolate';
import 'dart:typed_data';

import 'package:sherpa_onnx/sherpa_onnx.dart' as sherpa;

import 'media_tools.dart';
import 'wav_chunks.dart';
import 'model_manager.dart';

// Native handles stay in the worker isolate; UI callbacks receive messages.
Future<void> _speechWorkerEntry(List<Object?> request) async {
  final reply = request.last as SendPort;
  final worker =
      SpeechService(ModelManager.forDirectory(Directory(request[1] as String)));
  try {
    switch (request[0] as String) {
      case 'transcribe':
        final modelId = request[3] as String;
        final language = request[4] as String;
        await worker.loadAsr(modelId, language: language);
        final segments = await worker.transcribeWav(request[2] as String,
            language: language,
            onProgress: (seconds) =>
                reply.send(<Object?>['progress', seconds]));
        reply.send(<Object?>[
          'done',
          segments.map((segment) => segment.toJson()).toList()
        ]);
      case 'synthesize':
        final file = await worker._synthesize(
          text: request[2] as String,
          modelId: request[3] as String,
          outputPath: request[4] as String,
          speed: request[5] as double,
          language: request[6] as String,
          speakerId: request[7] as int,
        );
        reply.send(<Object?>['done', file.path]);
      case 'clone':
        final file = await worker._cloneWithZipVoice(
          text: request[2] as String,
          referenceWav: request[3] as String,
          referenceText: request[4] as String,
          outputPath: request[5] as String,
        );
        reply.send(<Object?>['done', file.path]);
      default:
        throw StateError('Pekerjaan suara tidak dikenal.');
    }
  } catch (error) {
    reply.send(<Object?>['error', error.toString()]);
  } finally {
    worker.reset();
  }
}

Future<Object?> _runSpeechWorker(List<Object?> request,
    {void Function(double)? onProgress}) async {
  final reply = ReceivePort();
  final errors = ReceivePort();
  final result = Completer<Object?>();
  final subscription = reply.listen((message) {
    if (message is! List || message.isEmpty) return;
    switch (message[0]) {
      case 'progress':
        if (message.length > 1 && message[1] is num) {
          onProgress?.call((message[1] as num).toDouble());
        }
      case 'done':
        if (!result.isCompleted) result.complete(message[1]);
      case 'error':
        if (!result.isCompleted) result.completeError(Exception(message[1]));
    }
  });
  final errorSubscription = errors.listen((error) {
    if (!result.isCompleted) {
      result.completeError(Exception('Pekerjaan model suara berhenti: $error'));
    }
  });
  Isolate? isolate;
  try {
    isolate = await Isolate.spawn<List<Object?>>(
      _speechWorkerEntry,
      <Object?>[...request, reply.sendPort],
      onError: errors.sendPort,
      errorsAreFatal: true,
    );
    return await result.future;
  } finally {
    isolate?.kill(priority: Isolate.immediate);
    await subscription.cancel();
    await errorSubscription.cancel();
    reply.close();
    errors.close();
  }
}

class TranscriptSegment {
  TranscriptSegment(this.start, this.end, this.text,
      [this.words = const [], this.language = '']);

  final double start;
  final double end;
  final String text;
  final List<Map<String, dynamic>> words;
  final String language;

  Map<String, dynamic> toJson() => {
        'start': double.parse(start.toStringAsFixed(3)),
        'end': double.parse(end.toStringAsFixed(3)),
        'text': text,
        'words': words,
        'language': language,
      };

  static TranscriptSegment fromJson(Map<String, dynamic> json) =>
      TranscriptSegment(
        (json['start'] as num).toDouble(),
        (json['end'] as num).toDouble(),
        json['text'] as String? ?? '',
        (json['words'] as List? ?? [])
            .map((w) => Map<String, dynamic>.from(w))
            .toList(),
        json['language'] as String? ?? '',
      );
}

Future<void> _asrServer(List<Object?> init) async {
  final worker =
      SpeechService(ModelManager.forDirectory(Directory(init[0] as String)));
  final inbox = ReceivePort();
  (init[1] as SendPort).send(inbox.sendPort);
  Timer? idle;
  try {
    await for (final message in inbox) {
      final request = message as List;
      idle?.cancel();
      final reply = request.last as SendPort;
      if (request[0] == 'shutdown') {
        worker.reset();
        reply.send(['done', null]);
        break;
      }
      try {
        await worker.loadAsr(request[2] as String,
            language: request[3] as String);
        final segments = await worker.transcribeWav(request[1] as String,
            language: request[3] as String,
            onProgress: (seconds) => reply.send(['progress', seconds]));
        reply.send(['done', segments.map((row) => row.toJson()).toList()]);
      } catch (error) {
        worker.reset();
        reply.send(['error', error.toString()]);
      }
      idle = Timer(const Duration(seconds: 30), worker.reset);
    }
  } finally {
    idle?.cancel();
    worker.reset();
    inbox.close();
  }
}

class _AsrSession {
  static Isolate? isolate;
  static SendPort? server;
  static String directory = '';
  static Future<void> tail = Future.value();

  static Future<Object?> run(String modelDirectory, String path, String model,
      String language, void Function(double)? progress) async {
    final previous = tail, gate = Completer<void>();
    tail = gate.future;
    await previous;
    final reply = ReceivePort(), errors = ReceivePort();
    final result = Completer<Object?>();
    StreamSubscription? subscription, errorSubscription;
    var settling = false, sent = false;
    Future<void> finish() async {
      isolate?.removeErrorListener(errors.sendPort);
      isolate?.removeOnExitListener(errors.sendPort);
      await subscription?.cancel();
      await errorSubscription?.cancel();
      reply.close();
      errors.close();
      gate.complete();
    }

    try {
      if (server == null || directory != modelDirectory) {
        if (server != null) {
          final closing = ReceivePort();
          server!.send(['shutdown', closing.sendPort]);
          await closing.first.timeout(const Duration(seconds: 5));
          closing.close();
        }
        isolate?.kill(priority: Isolate.immediate);
        server = null;
        final ready = ReceivePort();
        try {
          isolate = await Isolate.spawn(
              _asrServer, <Object?>[modelDirectory, ready.sendPort]);
          server = await ready.first.timeout(const Duration(seconds: 10))
              as SendPort;
          directory = modelDirectory;
        } finally {
          ready.close();
        }
      }
      errorSubscription = errors.listen((error) {
        server = null;
        if (!result.isCompleted) {
          result.completeError(StateError('ASR worker berhenti: $error'));
        }
      });
      isolate!.addErrorListener(errors.sendPort);
      isolate!.addOnExitListener(errors.sendPort);
      subscription = reply.listen((message) {
        final row = message as List;
        if (row[0] == 'progress') progress?.call((row[1] as num).toDouble());
        if (row[0] == 'done' && !result.isCompleted) result.complete(row[1]);
        if (row[0] == 'error' && !result.isCompleted) {
          result.completeError(StateError('${row[1]}'));
        }
      });
      server!.send(['transcribe', path, model, language, reply.sendPort]);
      sent = true;
      return await result.future.timeout(const Duration(minutes: 15));
    } on TimeoutException {
      // Native inference cannot be safely killed mid-call. Keep the serial gate
      // until it returns, so a retry cannot allocate a second recognizer.
      if (sent) {
        settling = true;
        unawaited(result.future
            .then<void>((_) => finish(), onError: (_) => finish()));
      }
      rethrow;
    } finally {
      if (!settling) await finish();
    }
  }
}

/// On-device speech: Whisper (ASR), Piper/VITS (TTS) and ZipVoice (cloning)
/// through sherpa-onnx. Everything runs offline on the phone.
class SpeechService {
  SpeechService(this.models);

  final ModelManager models;

  sherpa.OfflineRecognizer? _recognizer;
  String? _loadedAsr;
  String? _loadedLanguage;
  sherpa.OfflineTts? _tts;
  String? _loadedTts;

  bool get asrReady => _recognizer != null;
  bool get ttsReady => _tts != null;

  Future<List<TranscriptSegment>> transcribeFile(
      String path, String modelId, String language,
      {void Function(double)? onProgress}) async {
    final value = await _AsrSession.run(
        models.modelsDir.path, path, modelId, language, onProgress);
    return (value as List)
        .map((row) =>
            TranscriptSegment.fromJson(Map<String, dynamic>.from(row as Map)))
        .toList();
  }

  void reset() {
    // Urutan bebas yang aman: stream dulu (tidak ada di sini), lalu
    // recognizer/tts. Bungkus try/catch per objek: free() native bisa
    // throw bila objek setengah jadi -> itu yang bikin "ke close sendiri".
    try {
      _recognizer?.free();
    } catch (_) {}
    _recognizer = null;
    _loadedAsr = null;
    try {
      _tts?.free();
    } catch (_) {}
    _tts = null;
    _loadedTts = null;
  }

  // ------------------------------------------------------------------- asr

  Future<void> loadAsr(String modelId, {String language = 'id'}) async {
    language = language.toLowerCase().replaceAll('_', '-').split('-').first;
    if (language == 'und' || language == 'unknown') language = 'auto';
    if (_loadedAsr == modelId &&
        _loadedLanguage == language &&
        _recognizer != null) {
      return;
    }
    final model = models.find(modelId);
    if (model == null || !models.isInstalled(model)) {
      throw Exception('Model transkripsi belum terpasang: $modelId');
    }
    final encoder =
        models.fileWith(model, ['encoder.onnx', 'encoder.int8.onnx']);
    final decoder =
        models.fileWith(model, ['decoder.onnx', 'decoder.int8.onnx']);
    final tokens = models.fileWith(model, ['tokens.txt']);
    if (encoder == null || decoder == null || tokens == null) {
      throw Exception(
          'Berkas model $modelId tidak lengkap (encoder/decoder/tokens).');
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
            language: language == 'auto' ? '' : language,
            task: 'transcribe',
            enableTokenTimestamps: true,
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
    _loadedLanguage = language;
  }

  /// Transcribe a 16 kHz mono WAV; silero VAD splits it into speech segments.
  Future<List<TranscriptSegment>> transcribeWav(String wavPath,
      {String? language, void Function(double)? onProgress}) async {
    if (language != null && language != _loadedLanguage && _loadedAsr != null) {
      await loadAsr(_loadedAsr!, language: language);
    }
    final recognizer = _recognizer;
    if (recognizer == null) throw Exception('Model transkripsi belum dimuat.');

    final vadModel = models.find('silero-vad');
    final vadFile = vadModel == null
        ? null
        : models.fileWith(vadModel, ['silero_vad.onnx']);
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
      void drain() {
        while (!vad.isEmpty()) {
          final speech = vad.front();
          late sherpa.OfflineRecognizerResult decoded;
          try {
            decoded = _decode(recognizer, speech.samples);
          } finally {
            try {
              vad.pop();
            } catch (_) {}
          }
          final text = decoded.text;
          if (text.trim().isNotEmpty) {
            segments.add(TranscriptSegment(
              speech.start / 16000.0,
              (speech.start + speech.samples.length) / 16000.0,
              text.trim(),
              _timedWords(decoded, speech.start / 16000.0,
                  speech.samples.length / 16000.0),
              decoded.lang,
            ));
          }
        }
      }

      var processed = 0.0;
      try {
        for (final samples in readWavChunks(wavPath)) {
          vad.acceptWaveform(samples);
          drain();
          processed += samples.length / 16000.0;
          onProgress?.call(processed);
        }
        vad.flush();
        drain();
      } finally {
        try {
          vad.free();
        } catch (_) {}
      }
    } else {
      var offset = 0.0;
      for (final samples in readWavChunks(wavPath, sampleCount: 20 * 16000)) {
        final decoded = _decode(recognizer, samples);
        final text = decoded.text;
        final end = offset + samples.length / 16000.0;
        if (text.trim().isNotEmpty) {
          segments.add(TranscriptSegment(offset, end, text.trim(),
              _timedWords(decoded, offset, end - offset), decoded.lang));
        }
        offset = end;
        onProgress?.call(end);
      }
    }
    return segments;
  }

  static List<Map<String, dynamic>> _timedWords(
      sherpa.OfflineRecognizerResult result, double offset, double duration) {
    if (result.tokens.length != result.timestamps.length ||
        result.tokens.isEmpty) {
      return [];
    }
    final words = <Map<String, dynamic>>[];
    for (var i = 0; i < result.tokens.length; i++) {
      final token = result.tokens[i].replaceAll('▁', ' ');
      if (token.trim().isEmpty || token.startsWith('<|')) continue;
      final start = offset + result.timestamps[i].clamp(0, duration);
      final end = offset +
          (i + 1 < result.timestamps.length
                  ? result.timestamps[i + 1]
                  : duration)
              .clamp(0, duration);
      if (words.isEmpty || token.startsWith(' ')) {
        words.add({'word': token.trim(), 'start': start, 'end': end});
      } else {
        words.last['word'] = '${words.last['word']}$token';
        words.last['end'] = end;
      }
    }
    String compact(String s) => s.replaceAll(RegExp(r'\s+'), '');
    if (compact(words.map((w) => w['word']).join()) != compact(result.text)) {
      return [];
    }
    return words.where((w) => w['end'] > w['start']).toList();
  }

  sherpa.OfflineRecognizerResult _decode(
      sherpa.OfflineRecognizer recognizer, Float32List samples) {
    final stream = recognizer.createStream();
    try {
      stream.acceptWaveform(samples: samples, sampleRate: 16000);
      recognizer.decode(stream);
      final result = recognizer.getResult(stream);
      return result;
    } finally {
      try {
        stream.free();
      } catch (_) {}
    }
  }

  // ------------------------------------------------------------------- tts

  Future<void> loadTts(String modelId) async {
    if (_loadedTts == modelId && _tts != null) return;
    final model = models.find(modelId);
    if (model == null || !models.isInstalled(model)) {
      throw Exception('Model suara belum terpasang: $modelId');
    }
    if (modelId == 'supertonic-3-int8') {
      File requiredFile(String name) {
        final file = models.fileWith(model, [name]);
        if (file == null || file.lengthSync() == 0) {
          throw Exception(
              'Model Supertonic tidak lengkap: $name. Unduh ulang.');
        }
        return file;
      }

      sherpa.initBindings();
      _tts?.free();
      _tts = sherpa.OfflineTts(sherpa.OfflineTtsConfig(
        model: sherpa.OfflineTtsModelConfig(
          supertonic: sherpa.OfflineTtsSupertonicModelConfig(
            durationPredictor:
                requiredFile('duration_predictor.int8.onnx').path,
            textEncoder: requiredFile('text_encoder.int8.onnx').path,
            vectorEstimator: requiredFile('vector_estimator.int8.onnx').path,
            vocoder: requiredFile('vocoder.int8.onnx').path,
            ttsJson: requiredFile('tts.json').path,
            unicodeIndexer: requiredFile('unicode_indexer.bin').path,
            voiceStyle: requiredFile('voice.bin').path,
          ),
          numThreads: 2,
          provider: 'cpu',
          debug: false,
        ),
      ));
      _loadedTts = modelId;
      return;
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
    String language = 'id',
    int speakerId = 0,
  }) async {
    if (text.trim().isEmpty) throw Exception('Teks kosong.');
    final path = await _runSpeechWorker(<Object?>[
      'synthesize',
      models.modelsDir.path,
      text,
      modelId,
      outputPath,
      speed,
      language,
      speakerId,
    ]);
    return File(path as String);
  }

  Future<File> _synthesize(
      {required String text,
      required String modelId,
      required String outputPath,
      required double speed,
      required String language,
      required int speakerId}) async {
    await loadTts(modelId);
    if (modelId == 'supertonic-3-int8' &&
        (speakerId < 0 || speakerId > 9 || !['id', 'en'].contains(language))) {
      throw ArgumentError(
          'Supertonic membutuhkan bahasa ID/EN dan suara 1–10.');
    }
    final audio = modelId == 'supertonic-3-int8'
        ? _tts!.generateWithConfig(
            text: text,
            config: sherpa.OfflineTtsGenerationConfig(
              sid: speakerId,
              speed: speed,
              numSteps: 8,
              extra: {'lang': language, 'num_steps': 8},
            ),
          )
        : _tts!.generate(text: text, sid: 0, speed: speed);
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
    if (!File(referenceWav).existsSync()) {
      throw Exception('Rekaman contoh tidak ditemukan.');
    }
    if (referenceText.trim().isEmpty) {
      throw Exception('Isi teks yang diucapkan pada rekaman contoh.');
    }
    final converted = '$outputPath.reference.wav';
    File(outputPath).parent.createSync(recursive: true);
    await MediaTools.extractAudioRange(referenceWav, converted, 0, 30);
    try {
      final path = await _runSpeechWorker(<Object?>[
        'clone',
        models.modelsDir.path,
        text,
        converted,
        referenceText,
        outputPath
      ]);
      return File(path as String);
    } finally {
      final temporary = File(converted);
      if (temporary.existsSync()) temporary.deleteSync();
    }
  }

  Future<File> _cloneWithZipVoice(
      {required String text,
      required String referenceWav,
      required String referenceText,
      required String outputPath}) async {
    final model = models.find('zipvoice-zh-en');
    if (model == null || !models.isInstalled(model)) {
      throw Exception(
          'Model ZipVoice belum terpasang. Unduh dulu di halaman Model.');
    }
    final encoder =
        models.fileWith(model, ['encoder.onnx', 'encoder.int8.onnx']);
    final decoder =
        models.fileWith(model, ['decoder.onnx', 'decoder.int8.onnx']);
    final vocoder = models.fileWith(
        model, ['vocos_24khz.onnx', 'vocoder.onnx', 'vocoder.int8.onnx']);
    final tokens = models.fileWith(model, ['tokens.txt']);
    final data = models.directoryWith(model, 'espeak-ng-data');
    final lexicon = models.fileWith(model, ['lexicon.txt']);
    if (encoder == null ||
        decoder == null ||
        vocoder == null ||
        tokens == null) {
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
            dataDir: data?.path ?? '',
            lexicon: lexicon?.path ?? '',
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
          numSteps: 4,
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
    if (samples.isEmpty) {
      throw Exception(
          'Rekaman contoh tidak bisa dibaca (gunakan WAV 16 kHz mono).');
    }
    // Keep the reference short: 4-15 seconds is plenty and much faster.
    final maxSamples = 16000 * 30;
    if (samples.length > maxSamples) {
      samples = Float32List.sublistView(samples, 0, maxSamples);
    }
    return samples;
  }
}
