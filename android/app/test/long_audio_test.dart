import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/services/media_tools.dart';
import 'package:studiozai/services/pipeline.dart';
import 'package:studiozai/services/speech.dart';
import 'package:studiozai/services/model_manager.dart';
import 'package:studiozai/services/wav_chunks.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('Streaming PCM matches the original reader and clip selection',
      () async {
    final folder = Directory.systemTemp.createTempSync('studio-wav-');
    addTearDown(() => folder.deleteSync(recursive: true));
    final path = '${folder.path}/sample.wav';
    final input = Float32List.fromList(
        List.generate(16000 * 45, (i) => (i % 101) / 101 - .5));
    await MediaTools.writeWav(path, input, 16000);
    final expected = MediaTools.readWavSamples(path);
    final actual = readWavChunks(path, sampleCount: 8000)
        .expand((chunk) => chunk)
        .toList();
    expect(actual, orderedEquals(expected));
    final whole = Pipeline.pickClips(
        samples: expected, sampleRate: 16000, duration: 45, count: 2);
    final bounded = await Pipeline.pickClipsFromWav(path, 45, [], 2);
    expect(bounded.map((c) => [c.start, c.end, c.score]).toList(),
        whole.map((c) => [c.start, c.end, c.score]).toList());
  });
  test('A 65 minute WAV stays bounded to one second per chunk', () async {
    final folder = Directory.systemTemp.createTempSync('studio-hour-');
    addTearDown(() => folder.deleteSync(recursive: true));
    final path = '${folder.path}/hour.wav';
    await MediaTools.writeWav(path, Float32List(0), 16000);
    const seconds = 65 * 60, bytes = seconds * 16000 * 2;
    final file = File(path).openSync(mode: FileMode.append);
    file.truncateSync(44 + bytes);
    final field = ByteData(4)..setUint32(0, 36 + bytes, Endian.little);
    file.setPositionSync(4);
    file.writeFromSync(field.buffer.asUint8List());
    field.setUint32(0, bytes, Endian.little);
    file.setPositionSync(40);
    file.writeFromSync(field.buffer.asUint8List());
    file.closeSync();
    var count = 0, total = 0;
    for (final chunk in readWavChunks(path)) {
      expect(chunk.length, lessThanOrEqualTo(16000));
      count++;
      total += chunk.length;
    }
    expect(count, seconds);
    expect(total, seconds * 16000);
  });
  test('Truncated WAV is rejected', () async {
    final folder = Directory.systemTemp.createTempSync('studio-truncated-');
    addTearDown(() => folder.deleteSync(recursive: true));
    final path = '${folder.path}/bad.wav';
    await MediaTools.writeWav(path, Float32List(100), 16000);
    final f = File(path).openSync(mode: FileMode.append);
    f.truncateSync(50);
    f.closeSync();
    expect(() => readWavChunks(path).toList(), throwsFormatException);
  });

  test('Product review clips begin at product introductions', () {
    final segments = <TranscriptSegment>[
      TranscriptSegment(0, 10, 'Di video ini kita akan review semuanya.'),
      TranscriptSegment(10, 35, 'Produk pertama adalah speaker murah ini.'),
      TranscriptSegment(35, 60, 'Kualitas suara dan baterainya begini.'),
      TranscriptSegment(60, 95, 'Speaker kedua menawarkan bass lebih kuat.'),
      TranscriptSegment(95, 130, 'Sekarang kita dengar hasil pengujiannya.'),
      TranscriptSegment(130, 170, 'Selanjutnya kita bahas speaker terakhir.'),
      TranscriptSegment(170, 200, 'Kesimpulannya produk ini paling bagus.'),
    ];
    final clips = Pipeline.pickClips(
        samples: Float32List(0),
        sampleRate: 16000,
        duration: 200,
        segments: segments,
        count: 4);
    expect(
        clips.map((c) => [c.start, c.end]),
        containsAll([
          [10.0, 60.0],
          [60.0, 130.0],
          [130.0, 200.0]
        ]));
    expect(clips.every((c) => c.duration >= 3), isTrue);
  });

  test('Indonesian review ordinals identify product starts in long videos', () {
    final segments = <TranscriptSegment>[
      TranscriptSegment(0, 80, 'Kita akan membandingkan berbagai speaker.'),
      TranscriptSegment(
          82, 160, 'Yang pertama ini adalah pilihan paling murah.'),
      TranscriptSegment(160, 330, 'Kita dengar kualitas suara dan baterainya.'),
      TranscriptSegment(338, 420, 'Barang kedua ini punya daya lebih besar.'),
      TranscriptSegment(420, 620, 'Bass dan harganya dibandingkan.'),
      TranscriptSegment(627, 700, 'Nomor tiga ini model yang berbeda.'),
      TranscriptSegment(700, 890, 'Hasil uji berikutnya cukup bagus.'),
      TranscriptSegment(893, 950, 'Speaker keempat ini lebih premium.'),
      TranscriptSegment(950, 1050, 'Ada kelebihan dan kekurangannya.'),
      TranscriptSegment(
          1057, 1100, 'Sekarang kelima ini hadir dengan fitur lain.'),
      TranscriptSegment(1100, 1190, 'Kita coba lagi kualitas suaranya.'),
      TranscriptSegment(1200, 1260, 'Barang ke-10 ini jadi penutup ulasan.'),
      TranscriptSegment(1260, 1300, 'Kesimpulan akhir.'),
    ];
    final clips = Pipeline.pickClips(
        samples: Float32List(0),
        sampleRate: 16000,
        duration: 1300,
        segments: segments,
        count: 10);
    expect(clips.map((clip) => clip.start),
        containsAll([82.0, 338.0, 627.0, 893.0, 1057.0, 1200.0]));
    expect(clips.any((clip) => clip.start == 0), isFalse);
  });

  test('Downloaded video can yield editable clips without ASR or audio', () {
    final clips = Pipeline.pickClipsWithoutAudio(1142.4, 5);
    expect(clips.length, 5);
    expect(clips.every((c) => c.start >= 0 && c.end <= 1142.4), isTrue);
  });

  test('Speech worker receives only sendable task data', () async {
    final root = await Directory.systemTemp.createTemp('studio-speech-');
    addTearDown(() => root.deleteSync(recursive: true));
    final binding = TestWidgetsFlutterBinding.ensureInitialized();
    final speech = SpeechService(ModelManager.forDirectory(root));
    await expectLater(
      speech.transcribeFile('missing.wav', 'whisper-base', 'id',
          onProgress: (_) => expect(binding, isNotNull)),
      throwsA(predicate((error) => '$error'.contains('belum terpasang'))),
    );
  });
}
