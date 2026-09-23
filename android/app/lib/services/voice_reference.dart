import 'dart:io';

import 'package:file_picker/file_picker.dart';

import 'media_tools.dart';

/// Copies a picker result out of its temporary provider location and converts
/// the first 30 seconds to the 16 kHz mono PCM required by ZipVoice.
class VoiceReference {
  static const maxInputBytes = 100 * 1024 * 1024;

  static Future<File> importFile(
    PlatformFile picked,
    Directory voicesDir, {
    Future<File> Function(String, String, double, double)? convert,
  }) async {
    final reportedSize = await picked.length();
    if (reportedSize != null &&
        (reportedSize <= 0 || reportedSize > maxInputBytes)) {
      throw const FormatException('Pilih rekaman suara maksimal 100 MB.');
    }
    await voicesDir.create(recursive: true);
    final stamp = DateTime.now().microsecondsSinceEpoch;
    File? temporarySource;
    final normalized = File('${voicesDir.path}/reference-$stamp.wav');
    try {
      File source;
      final pickedPath = picked.path;
      if (pickedPath != null && await File(pickedPath).exists()) {
        source = File(pickedPath);
        if (await source.length() > maxInputBytes) {
          throw const FormatException('Pilih rekaman suara maksimal 100 MB.');
        }
      } else {
        // Android document providers often expose a content:// URI instead of
        // a usable path. Stream it into app storage with a strict size cap.
        temporarySource = File('${voicesDir.path}/reference-source-$stamp');
        final sink = temporarySource.openWrite();
        var written = 0;
        try {
          await for (final chunk in picked.readAsByteStream()) {
            written += chunk.length;
            if (written > maxInputBytes) {
              throw const FormatException(
                  'Pilih rekaman suara maksimal 100 MB.');
            }
            sink.add(chunk);
          }
          await sink.flush();
        } finally {
          await sink.close();
        }
        if (written == 0) {
          throw const FormatException(
              'Berkas tidak dapat dibaca. Simpan rekaman ke perangkat lalu pilih lagi.');
        }
        source = temporarySource;
      }
      await (convert ?? MediaTools.extractAudioRange)(
          source.path, normalized.path, 0, 30);
      if (!await normalized.exists() || await normalized.length() <= 44) {
        throw const FormatException(
            'Rekaman tidak mengandung audio yang terbaca.');
      }
      return normalized;
    } on FormatException {
      if (await normalized.exists()) await normalized.delete();
      rethrow;
    } catch (_) {
      if (await normalized.exists()) await normalized.delete();
      throw const FormatException(
          'Audio tidak dapat dibaca. Coba WAV, MP3, M4A, OGG, atau rekam dari mikrofon.');
    } finally {
      if (temporarySource != null && await temporarySource.exists()) {
        await temporarySource.delete();
      }
    }
  }
}
