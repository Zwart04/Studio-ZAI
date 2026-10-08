import 'dart:io';
import 'dart:isolate';
import 'package:archive/archive_io.dart';

/// Stream only explicitly selected MP4 files. No project/config JSON is added.
class ClipArchive {
  static Future<void> create(Map<String, String> files, String output) =>
      Isolate.run(() async {
        if (files.isEmpty ||
            files.values.any(
                (name) => !RegExp(r'^[A-Za-z0-9_.-]+\.mp4$').hasMatch(name))) {
          throw ArgumentError('Pilih video MP4 dengan nama arsip yang valid.');
        }
        final partial = File('$output.partial');
        try {
          final encoder = ZipFileEncoder();
          encoder.create(partial.path, level: 0);
          try {
            for (final entry in files.entries) {
              await encoder.addFile(File(entry.key), entry.value, 0);
            }
          } finally {
            await encoder.close();
          }
          partial.renameSync(output);
        } finally {
          if (partial.existsSync()) {
            partial.deleteSync();
          }
        }
      });
}
