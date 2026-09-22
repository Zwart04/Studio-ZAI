import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/models.dart';
import 'package:studiozai/services/model_manager.dart';
import 'package:studiozai/services/downloader.dart';
import 'package:studiozai/services/media_tools.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  HttpOverrides.global = null;

  test('YouTube language IDs include track suffixes', () {
    expect(Downloader.matchesLanguage('id.4', 'id'), isTrue);
    expect(Downloader.matchesLanguage('id-ID.4', 'id'), isTrue);
    expect(Downloader.matchesLanguage('en.0', 'id'), isFalse);
    expect(Downloader.matchesLanguage('', 'id'), isFalse);
  });

  test('Original canvas retains geometry', () {
    expect(MediaTools.canvasSize('original', 1280, 720), [1280, 720]);
    expect(MediaTools.cropFilter('center', 1280, 720, canvas: 'original'), isNot(contains('crop=')));
  });

  for (final fixture in ['model', 'unsafe', 'broken']) {
    test('Model download and isolate extraction: $fixture', () async {
      final root = await Directory.systemTemp.createTemp('studiozai-test-');
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final manager = ModelManager.forDirectory(root);
      final model = ModelInfo(id: 'fixture', kind: 'test', langs: ['id'], sizeMb: 1,
          license: 'test', note: '', url: 'http://127.0.0.1:${server.port}/model.tar.bz2');
      final bytes = fixture == 'broken' ? [1, 2, 3] : await File('test/fixtures/$fixture.tar.bz2').readAsBytes();
      server.listen((request) async {
        request.response.contentLength = bytes.length;
        request.response.add(bytes);
        await request.response.close();
      });
      var responsiveTicks = 0;
      var extracting = false;
      final timer = Timer.periodic(const Duration(milliseconds: 1), (_) { if (extracting) responsiveTicks++; });
      try {
        final operation = manager.download(model, (p, message) { if (message.startsWith('mengekstrak')) extracting = true; });
        if (fixture == 'model') {
          await operation;
          expect(manager.isInstalled(model), isTrue);
          expect(File('${root.path}/fixture/sample/model.onnx').lengthSync(), 1000000);
          expect(responsiveTicks, greaterThan(0), reason: 'UI isolate must keep running during decompression');
        } else {
          await expectLater(operation, throwsA(isA<Exception>()));
          expect(manager.isInstalled(model), isFalse);
          expect(File('${root.path}/escape.onnx').existsSync(), isFalse);
        }
      } finally {
        timer.cancel();
        await server.close(force: true);
        await root.delete(recursive: true);
      }
    });
  }
}
