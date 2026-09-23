import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:archive/archive.dart';
import 'package:crypto/crypto.dart';
import 'package:studiozai/models.dart';
import 'package:studiozai/services/model_manager.dart';
import 'package:studiozai/services/model_registry.dart';
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
    expect(MediaTools.cropFilter('center', 1280, 720, canvas: 'original'),
        isNot(contains('crop=')));
  });

  for (final fixture in ['model', 'unsafe', 'broken']) {
    test('Model download and isolate extraction: $fixture', () async {
      // The real UI passes a progress callback owned by a widget. It must stay
      // on the main isolate while extraction receives only serializable paths.
      final binding = TestWidgetsFlutterBinding.ensureInitialized();
      final root = await Directory.systemTemp.createTemp('studiozai-test-');
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final manager = ModelManager.forDirectory(root);
      final model = ModelInfo(
          id: 'fixture',
          kind: 'test',
          langs: ['id'],
          sizeMb: 1,
          license: 'test',
          note: '',
          url: 'http://127.0.0.1:${server.port}/model.tar.bz2');
      final bytes = fixture == 'broken'
          ? [1, 2, 3]
          : await File('test/fixtures/$fixture.tar.bz2').readAsBytes();
      server.listen((request) async {
        request.response.contentLength = bytes.length;
        request.response.add(bytes);
        await request.response.close();
      });
      var responsiveTicks = 0;
      var extracting = false;
      final timer = Timer.periodic(const Duration(milliseconds: 1), (_) {
        if (extracting) responsiveTicks++;
      });
      try {
        final operation = manager.download(model, (p, message) {
          expect(binding, same(TestWidgetsFlutterBinding.ensureInitialized()));
          if (message.startsWith('mengekstrak')) extracting = true;
        });
        if (fixture == 'model') {
          await operation;
          expect(manager.isInstalled(model), isTrue);
          expect(File('${root.path}/fixture/sample/model.onnx').lengthSync(),
              1000000);
          expect(responsiveTicks, greaterThan(0),
              reason: 'UI isolate must keep running during decompression');
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

  test('Single-file model is installed only after its SHA-256 matches',
      () async {
    final root = await Directory.systemTemp.createTemp('studiozai-hash-');
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    final bytes = 'GGUF-fixture'.codeUnits;
    server.listen((request) async {
      request.response.contentLength = bytes.length;
      request.response.add(bytes);
      await request.response.close();
    });
    final manager = ModelManager.forDirectory(root);
    ModelInfo model(String hash) => ModelInfo(
        id: 'image-fixture',
        kind: 'image',
        langs: ['multi'],
        sizeMb: 0,
        license: 'test',
        note: '',
        archive: false,
        url: 'http://127.0.0.1:${server.port}/fixture.gguf',
        sha256: hash);
    try {
      final bad = model(List.filled(64, '0').join());
      await expectLater(manager.download(bad, (_, __) {}), throwsException);
      expect(manager.isInstalled(bad), isFalse);
      expect(File('${root.path}/image-fixture/fixture.gguf').existsSync(),
          isFalse);
      final good = model(sha256.convert(bytes).toString());
      await manager.download(good, (_, __) {});
      expect(manager.isInstalled(good), isTrue);
    } finally {
      await server.close(force: true);
      await root.delete(recursive: true);
    }
  });

  test('Supertonic archive installs without Piper tokens.txt', () async {
    final archive = Archive();
    for (final name in ModelRegistry.supertonicFiles) {
      archive.addFile(ArchiveFile('supertonic/$name', 1, [1]));
    }
    final bytes = BZip2Encoder().encode(TarEncoder().encode(archive));
    final root =
        await Directory.systemTemp.createTemp('studio-supertonic-mini-');
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    server.listen((request) async {
      request.response.contentLength = bytes.length;
      request.response.add(bytes);
      await request.response.close();
    });
    final model = ModelInfo.fromJson({
      ...ModelRegistry.supertonic3.toJson(),
      'sizeMb': 0,
      'url': 'http://127.0.0.1:${server.port}/model.tar.bz2',
      'sha256': sha256.convert(bytes).toString(),
    });
    final manager = ModelManager.forDirectory(root);
    try {
      await manager.download(model, (_, __) {});
      expect(manager.isInstalled(model), isTrue);
      for (final name in ModelRegistry.supertonicFiles) {
        expect(manager.fileWith(model, [name]), isNotNull);
      }
    } finally {
      await server.close(force: true);
      await root.delete(recursive: true);
    }
  });
}
