import 'dart:io';
import 'package:archive/archive.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/services/clip_archive.dart';

void main() {
  test(
      'Streaming ZIP contains selected videos and excludes neighboring private files',
      () async {
    final dir = await Directory.systemTemp.createTemp('studio-archive-');
    try {
      final video = File('${dir.path}/video.mp4')..writeAsBytesSync([1, 2, 3]);
      File('${dir.path}/credentials.json').writeAsStringSync('fixture-private');
      final output = '${dir.path}/clips.zip';
      await ClipArchive.create({video.path: '001-portrait.mp4'}, output);
      final archive = ZipDecoder()
          .decodeBytes(File(output).readAsBytesSync(), verify: true);
      expect(archive.files.map((f) => f.name).toList(), ['001-portrait.mp4']);
      expect(archive.files.first.content, [1, 2, 3]);
      expect(File('$output.partial').existsSync(), false);
    } finally {
      cleanup(dir);
    }
  });
  test(
      'Failed archive removes partial output and does not publish an incomplete ZIP',
      () async {
    final dir = await Directory.systemTemp.createTemp('studio-archive-');
    try {
      final output = '${dir.path}/clips.zip';
      await expectLater(
          ClipArchive.create({'${dir.path}/missing.mp4': '001.mp4'}, output),
          throwsA(anything));
      expect(File(output).existsSync(), false);
      expect(File('$output.partial').existsSync(), false);
      await expectLater(
          ClipArchive.create({'missing': '../private.json'}, output),
          throwsArgumentError);
    } finally {
      cleanup(dir);
    }
  });
}

void cleanup(Directory directory) {
  final root = Directory.systemTemp.resolveSymbolicLinksSync();
  final target = directory.resolveSymbolicLinksSync();
  if (!target.startsWith('$root${Platform.pathSeparator}studio-archive-')) {
    throw StateError('Test cleanup escaped its temporary directory');
  }
  directory.deleteSync(recursive: true);
}
