import 'dart:io';

import 'package:archive/archive.dart';
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
  Future<void> download(ModelInfo model, void Function(double, String) onProgress) async {
    final dir = dirFor(model.id);
    final rawName = model.url.split('/').last;
    final target = File('${dir.path}/$rawName');

    final existing = target.existsSync() ? target.lengthSync() : 0;
    final request = http.Request('GET', Uri.parse(model.url));
    if (existing > 0) request.headers['Range'] = 'bytes=$existing-';

    final response = await request.send();
    if (response.statusCode >= 400) {
      throw Exception('Unduhan gagal (${response.statusCode}). Cek koneksi atau buka: ${model.url}');
    }
    final total = (response.contentLength ?? 0) + (response.statusCode == 206 ? existing : 0);
    final sink = target.openWrite(
      mode: response.statusCode == 206 ? FileMode.append : FileMode.write,
    );
    var received = existing;
    await for (final chunk in response.stream) {
      sink.add(chunk);
      received += chunk.length;
      if (total > 0) {
        onProgress(received / total * 100, 'mengunduh ${model.id}');
      }
    }
    await sink.flush();
    await sink.close();

    if (model.archive) {
      onProgress(96, 'mengekstrak ${model.id}');
      await _extract(target, dir);
      target.deleteSync();
    }
    File('${dir.path}/.installed').writeAsStringSync(model.toJson().toString());
    onProgress(100, 'terpasang');
  }

  Future<void> _extract(File archive, Directory dir) async {
    final bytes = archive.readAsBytesSync();
    if (bytes.length > 900 * 1024 * 1024) {
      throw Exception('Arsip terlalu besar untuk diekstrak di HP (${(bytes.length / 1048576).round()} MB).');
    }
    final Archive decoded;
    if (archive.path.endsWith('.zip')) {
      decoded = ZipDecoder().decodeBytes(bytes);
    } else {
      decoded = TarDecoder().decodeBytes(BZip2Decoder().decodeBytes(bytes));
    }
    for (final entry in decoded) {
      if (!entry.isFile) continue;
      final out = File('${dir.path}/${entry.name}');
      out.parent.createSync(recursive: true);
      out.writeAsBytesSync(entry.content as List<int>);
    }
  }

  Future<void> remove(ModelInfo model) async {
    final dir = Directory('${modelsDir.path}/${model.id}');
    if (dir.existsSync()) dir.deleteSync(recursive: true);
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

  File? directoryWith(ModelInfo model, String name) {
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
