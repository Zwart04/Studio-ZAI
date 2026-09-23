import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/services/voice_reference.dart';

final class _PickerAudio extends PlatformFile {
  _PickerAudio(this.data, {this.reportedSize});

  final Uint8List data;
  final int? reportedSize;

  @override
  String get name => 'recording.m4a';
  @override
  Uri get uri => Uri.parse('content://media/recording');
  @override
  Never get xFile => throw UnimplementedError();
  @override
  int? lengthSync() => reportedSize;
  @override
  Future<int?> length() async => reportedSize;
  @override
  Future<Uint8List> readAsBytes() async => data;
  @override
  Stream<Uint8List> readAsByteStream() async* {
    for (var offset = 0; offset < data.length; offset += 2) {
      yield Uint8List.sublistView(
          data, offset, (offset + 2).clamp(0, data.length));
    }
  }
}

void main() {
  test(
      'content URI recording is copied, normalized, and temporary copy removed',
      () async {
    final dir = await Directory.systemTemp.createTemp('studiozai-voice-');
    addTearDown(() => dir.delete(recursive: true));
    final picked = _PickerAudio(Uint8List.fromList([1, 2, 3, 4]));

    final output = await VoiceReference.importFile(picked, dir,
        convert: (input, output, start, end) async {
      expect(await File(input).readAsBytes(), [1, 2, 3, 4]);
      expect([start, end], [0, 30]);
      return File(output)..writeAsBytesSync(List.filled(48, 1));
    });

    expect(await output.exists(), isTrue);
    expect(dir.listSync().whereType<File>(), hasLength(1));
  });

  test('oversized recording is rejected before decoding', () async {
    final dir = await Directory.systemTemp.createTemp('studiozai-voice-');
    addTearDown(() => dir.delete(recursive: true));
    final picked = _PickerAudio(Uint8List.fromList([1]),
        reportedSize: VoiceReference.maxInputBytes + 1);

    await expectLater(
        VoiceReference.importFile(picked, dir,
            convert: (input, output, start, end) async =>
                throw StateError('converter must not run')),
        throwsFormatException);
    expect(dir.listSync(), isEmpty);
  });

  test('decode failure removes temporary source and partial output', () async {
    final dir = await Directory.systemTemp.createTemp('studiozai-voice-');
    addTearDown(() => dir.delete(recursive: true));
    final picked = _PickerAudio(Uint8List.fromList([1, 2, 3]));

    await expectLater(
        VoiceReference.importFile(picked, dir,
            convert: (input, output, start, end) async {
          await File(output).writeAsBytes([1, 2, 3]);
          throw StateError('bad audio');
        }),
        throwsFormatException);
    expect(dir.listSync(), isEmpty);
  });
}
