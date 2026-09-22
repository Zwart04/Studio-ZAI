import 'dart:io';
import 'dart:typed_data';

import 'package:archive/archive_io.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

import '../models.dart';
import 'model_registry.dart';

/// Detects the device and manages on-demand model downloads (resume + verify).
class ModelManager {
  ModelManager._(this.modelsDir);

  final Directory modelsDir;
  static ModelManager? _instance;
  static const _channel = MethodChannel('studiozai/device');

  static Future<ModelManager> instance() async {
    if (_instance != null) return _instance!;
    final base = await getApplicationSupportDirectory();
    final dir = Directory('${base.path}/models');
    if (!dir.existsSync()) dir.createSync(recursive: true);
    _instance = ModelManager._(dir);
    return _instance!;
  }

  Directory dirFor(String modelId) {
    final dir = Directory('${modelsDir.path}/$modelId');
    if (!dir.existsSync()) dir.createSync(recursive: true);
    return dir;
  }

  bool isInstalled(ModelInfo model) => File('${dirFor(model.id).path}/.installed').existsSync();

  double installedSizeMb(String modelId) {
    final dir = Directory('${modelsDir.path}/$modelId');
    if (!dir.existsSync()) return 0;
    var bytes = 0;
    for (final entity in dir.listSync(recursive: true)) {
      if (entity is File) bytes += entity.lengthSync();
    }
    return bytes / (1024 * 1024);
  }

  List<ModelInfo> catalog() {
    final models = ModelRegistry.all;
    for (final model in models) {
      model.installed = isInstalled(model);
      model.installedMb = model.installed ? installedSizeMb(model.id) : 0;
    }
    return models;
  }

  List<ModelInfo> byKind(String kind) => catalog().where((m) => m.kind == kind).toList();

  Future<DeviceReport> deviceReport() async {
    final android = await DeviceInfoPlugin().androidInfo;
    var ramGb = 0.0;
    var diskFreeGb = 0.0;
    try {
      final info = await _channel.invokeMapMethod<String, dynamic>('memoryInfo');
      ramGb = (info?['totalRam'] as num?)?.toDouble() ?? 0;
      diskFreeGb = (info?['availDisk'] as num?)?.toDouble() ?? 0;
    } on PlatformException {
      ramGb = 0;
    }
    return DeviceReport(
      model: '${android.manufacturer} ${android.model}',
      androidVersion: 'Android ${android.version.release} (SDK ${android.version.sdkInt})',
      ramGb: ramGb,
      diskFreeGb: diskFreeGb,
      abis: android.supportedAbis,
    );
  }

  /// Download a model with HTTP range resume, then extract archives.
  /// Returns normally only when the model is fully verified + marked installed.
  /// Any failure removes partial files so a retry starts clean.
  Future<void> download(ModelInfo model, void Function(double, String) onProgress) async {
    final dir = dirFor(model.id);
    final rawName = model.url.split('/').last;
    final target = File('${dir.path}/$rawName');

    try {
      final existing = target.existsSync() ? target.lengthSync() : 0;
      final request = http.Request('GET', Uri.parse(model.url));
      if (existing > 0) request.headers['Range'] = 'bytes=$existing-';

      final response = await request.send().timeout(const Duration(seconds: 30));
      if (response.statusCode >= 400) {
        throw Exception('Unduhan gagal (HTTP ${response.statusCode}). Cek koneksi.');
      }
      // Server menolak resume (200 padahal kita minta lanjut) -> mulai dari nol.
      final resumed = response.statusCode == 206 && existing > 0;
      final total = (response.contentLength ?? 0) + (resumed ? existing : 0);
      final sink = target.openWrite(
        mode: resumed ? FileMode.append : FileMode.write,
      );
      var received = resumed ? existing : 0;
      try {
        await for (final chunk in response.stream.timeout(const Duration(seconds: 60))) {
          sink.add(chunk);
          received += chunk.length;
          if (total > 0) {
            onProgress(received / total * 100, 'mengunduh ${model.id}');
          }
        }
        await sink.flush();
      } finally {
        await sink.close();
      }

      if (model.archive) {
        onProgress(96, 'mengekstrak ${model.id}');
        // Ekstrak dulu ke folder sementara; kalau gagal, folder model tetap bersih.
        final tmpDir = Directory('${dir.path}/.extract_tmp');
        if (tmpDir.existsSync()) tmpDir.deleteSync(recursive: true);
        tmpDir.createSync(recursive: true);
        try {
          await _extract(target, tmpDir);
          _verifyExtracted(model, tmpDir);
          _moveExtracted(tmpDir, dir);
        } finally {
          if (tmpDir.existsSync()) tmpDir.deleteSync(recursive: true);
        }
        target.deleteSync();
        _pruneStrayArchives(dir, keep: null);
      } else {
        _verifySingleFile(model, target);
      }
      File('${dir.path}/.installed').writeAsStringSync(model.toJson().toString());
      onProgress(100, 'terpasang');
    } catch (e) {
      // Jangan pernah menandai terpasang bila gagal; bersihkan file setengah jadi.
      try {
        if (target.existsSync()) {
          // Pertahankan resume HANYA bila file terlihat sehat (tumbuh normal);
          // untuk kasus rusak/404 simpan agar retry bisa lanjut — kecuali arsip.
          if (model.archive && target.lengthSync() < 1024) target.deleteSync();
        }
        final marker = File('${dir.path}/.installed');
        if (marker.existsSync()) marker.deleteSync();
      } catch (_) {}
      rethrow;
    }
  }

  /// Pastikan hasil ekstrak berisi file yang dibutuhkan (bukan arsip setengah unduh).
  void _verifyExtracted(ModelInfo model, Directory tmpDir) {
    final files = tmpDir.listSync(recursive: true).whereType<File>().toList();
    if (files.isEmpty) {
      throw Exception('Hasil ekstrak kosong — kemungkinan unduhan belum lengkap. Coba lagi.');
    }
    final names = files.map((f) => f.path.toLowerCase()).join('\n');
    final looksModel = names.contains('.onnx') || names.contains('.bin') || names.contains('tokens.txt') || names.contains('.gguf') || names.contains('.json');
    if (!looksModel) {
      throw Exception('Isi arsip tidak dikenali sebagai model (${files.length} file). Coba lagi.');
    }
  }

  void _moveExtracted(Directory tmpDir, Directory dir) {
    for (final entity in tmpDir.listSync(recursive: true)) {
      final rel = entity.path.substring(tmpDir.path.length + 1);
      if (entity is Directory) {
        Directory('${dir.path}/$rel').createSync(recursive: true);
      } else if (entity is File) {
        final target = File('${dir.path}/$rel');
        target.parent.createSync(recursive: true);
        entity.copySync(target.path);
      }
    }
  }

  void _pruneStrayArchives(Directory dir, {String? keep}) {
    for (final entity in dir.listSync()) {
      if (entity is! File) continue;
      final name = entity.path.toLowerCase();
      final isArchive = name.endsWith('.zip') || name.endsWith('.tar.bz2') || name.endsWith('.tar.gz') || name.endsWith('.tgz');
      if (isArchive && (keep == null || !entity.path.endsWith(keep))) {
        try {
          entity.deleteSync();
        } catch (_) {}
      }
    }
  }

  /// Pastikan file tunggal (non-arsip) valid sebelum ditandai terpasang.
  void _verifySingleFile(ModelInfo model, File target) {
    if (!target.existsSync() || target.lengthSync() == 0) {
      throw Exception('Berkas hasil unduhan kosong. Coba lagi.');
    }
    final minBytes = model.id == 'silero-vad' ? 500 * 1024 : 1024 * 1024;
    if (target.lengthSync() < minBytes && model.sizeMb * 1024 * 1024 > minBytes) {
      try {
        target.deleteSync();
      } catch (_) {}
      throw Exception('Unduhan tidak lengkap (${(target.lengthSync() / 1024).round()} KB). Coba lagi.');
    }
  }

  Future<void> _extract(File archive, Directory dir) async {
    final lower = archive.path.toLowerCase();
    if (lower.endsWith('.zip')) {
      await _extractZip(archive, dir);
      return;
    }
    if (lower.endsWith('.tar.bz2') || lower.endsWith('.tar.gz') || lower.endsWith('.tgz')) {
      await _extractTarStreaming(archive, dir);
      return;
    }
    throw Exception('Jenis arsip tidak dikenal: ${archive.path}');
  }

  /// Ekstraksi .tar.bz2 TANPA memuat arsip ke memori.
  ///
  /// Versi lama memakai `readAsBytesSync` + `decodeBytes`: untuk ZipVoice
  /// (350 MB) itu butuh ~1 GB RAM sehingga Android membunuh aplikasi
  /// (gejala: aplikasi tertutup sendiri saat unduh model). Sekarang:
  /// bz2 didekompresi streaming ke file .tar sementara, lalu .tar dibaca
  /// per blok 64 KB dan ditulis ke disk.
  Future<void> _extractTarStreaming(File archive, Directory dir) async {
    final tempTar = File('${archive.parent.path}/.tmp-${archive.uri.pathSegments.last}.tar');
    final free = await _freeDiskMb(archive.parent);
    final neededMb = (archive.lengthSync() * 3 / 1048576).round();
    if (free > 0 && free < neededMb) {
      throw Exception('Ruang penyimpanan kurang untuk mengekstrak. Butuh sekitar $neededMb MB, tersedia ${free.round()} MB.');
    }
    try {
      await _decompressTo(archive, tempTar);

      final raf = tempTar.openSync();
      var offset = 0;
      final total = tempTar.lengthSync();
      final buffer = Uint8List(65536);
      while (offset + 512 <= total) {
        raf.setPositionSync(offset);
        final header = raf.readSync(512);
        if (header.length < 512 || header.every((byte) => byte == 0)) break;
        final entryName = _tarText(header, 0, 100);
        final prefix = _tarText(header, 345, 155);
        final fullName = prefix.isEmpty ? entryName : '$prefix/$entryName';
        final size = _tarOctal(header, 124, 12);
        final type = header[156];
        offset += 512;

        if ((type == 0x30 || type == 0x00) && size > 0) {
          final target = _safeTarget(dir, fullName);
          target.parent.createSync(recursive: true);
          final sink = target.openSync(mode: FileMode.write);
          var remaining = size;
          try {
            while (remaining > 0) {
              final want = remaining < buffer.length ? remaining : buffer.length;
              final chunk = raf.readSync(want);
              if (chunk.isEmpty) break;
              sink.writeFromSync(chunk);
              remaining -= chunk.length;
            }
          } finally {
            sink.closeSync();
          }
        }
        offset += ((size + 511) ~/ 512) * 512; // data dipad ke kelipatan 512
      }
      raf.closeSync();
    } finally {
      if (tempTar.existsSync()) {
        try {
          tempTar.deleteSync();
        } catch (_) {}
      }
    }
  }

  Future<void> _decompressTo(File source, File target) async {
    // Factory InputFileStream/OutputFileStream langsung membuka berkasnya.
    final input = InputFileStream(source.path);
    final output = OutputFileStream(target.path);
    try {
      if (source.path.toLowerCase().endsWith('.bz2')) {
        BZip2Decoder().decodeStream(input, output);
      } else {
        GZipDecoder().decodeStream(input, output);
      }
    } finally {
      try {
        output.closeSync();
      } catch (_) {}
      try {
        input.closeSync();
      } catch (_) {}
    }
  }

  String _tarText(Uint8List header, int start, int length) {
    final end = header.indexOf(0, start);
    final stop = (end == -1 || end > start + length) ? start + length : end;
    return String.fromCharCodes(header.sublist(start, stop)).trim();
  }

  int _tarOctal(Uint8List header, int start, int length) {
    final text = _tarText(header, start, length);
    return int.tryParse(text, radix: 8) ?? 0;
  }

  File _safeTarget(Directory dir, String name) {
    final normalized = name.replaceAll('\\', '/');
    if (normalized.isEmpty || normalized.startsWith('/') || normalized.split('/').contains('..')) {
      throw Exception('Arsip berisi path tidak aman ($name). Unduhan dibatalkan.');
    }
    return File('${dir.path}/$normalized');
  }

  Future<double> _freeDiskMb(Directory dir) async {
    try {
      final stat = await FileStat.stat(dir.path);
      return stat.size / 1048576; // tidak semua platform mengisi ini
    } catch (_) {
      return 0;
    }
  }

  /// Arsip .zip (dipakai desktop; di Android jarang) dengan batas ukuran.
  Future<void> _extractZip(File archive, Directory dir) async {
    final bytes = archive.readAsBytesSync();
    if (bytes.length > 512 * 1024 * 1024) {
      throw Exception('Arsip zip terlalu besar untuk diekstrak di HP.');
    }
    if (bytes.length < 1024) {
      throw Exception('Arsip rusak (hanya ${bytes.length} byte). Coba lagi.');
    }
    final Archive decoded;
    try {
      decoded = ZipDecoder().decodeBytes(bytes);
    } catch (e) {
      throw Exception('Arsip rusak dan tidak bisa dibuka. Coba lagi. ($e)');
    }
    for (final entry in decoded) {
      if (!entry.isFile) continue;
      final out = _safeTarget(dir, entry.name);
      out.parent.createSync(recursive: true);
      final content = entry.content as List<int>;
      out.writeAsBytesSync(content);
    }
  }

  Future<void> remove(ModelInfo model) async {
    final dir = Directory('${modelsDir.path}/${model.id}');
    if (dir.existsSync()) {
      // Hapus dengan retry: di Android file .onnx bisa terkunci sesaat
      // oleh sherpa (mmap) sehingga deleteSync langsung gagal -> crash.
      var attempts = 0;
      while (dir.existsSync() && attempts < 5) {
        try {
          dir.deleteSync(recursive: true);
        } catch (_) {
          await Future<void>.delayed(const Duration(milliseconds: 300));
        }
        attempts++;
      }
    }
  }

  /// First file inside a model directory matching the given suffixes.
  File? fileWith(ModelInfo model, List<String> suffixes) {
    final dir = Directory('${modelsDir.path}/${model.id}');
    if (!dir.existsSync()) return null;
    final candidates = dir
        .listSync(recursive: true)
        .whereType<File>()
        .where((f) => suffixes.any((s) => f.path.toLowerCase().endsWith(s)))
        .toList()
      ..sort((a, b) => a.path.length.compareTo(b.path.length));
    return candidates.isEmpty ? null : candidates.first;
  }

  Directory? directoryWith(ModelInfo model, String name) {
    final dir = Directory('${modelsDir.path}/${model.id}');
    if (!dir.existsSync()) return null;
    for (final entity in dir.listSync(recursive: true)) {
      if (entity is Directory && entity.path.split('/').last == name) return entity;
    }
    return null;
  }

  ModelInfo? find(String id) {
    for (final model in ModelRegistry.all) {
      if (model.id == id) return model;
    }
    return null;
  }
}
