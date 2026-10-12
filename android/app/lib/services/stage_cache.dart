import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';

class StageCache {
  StageCache(this.root);
  final Directory root;
  static String key(Object identity) =>
      sha256.convert(utf8.encode(jsonEncode(identity))).toString();
  File file(String id) => File('${root.path}/$id.json');
  Map<String, dynamic>? read(String id, {Duration? ttl}) {
    try {
      final row = jsonDecode(file(id).readAsStringSync()) as Map;
      if (row['version'] != 2 ||
          row['complete'] != true ||
          row['digest'] != key(row['value']) ||
          ttl != null &&
              DateTime.now().millisecondsSinceEpoch - (row['time'] as int) >
                  ttl.inMilliseconds) {
        return null;
      }
      return Map<String, dynamic>.from(row['value'] as Map);
    } catch (_) {
      return null;
    }
  }

  Future<void> write(String id, Map<String, dynamic> value) async {
    await root.create(recursive: true);
    final temporary =
        File('${file(id).path}.${DateTime.now().microsecondsSinceEpoch}.tmp');
    try {
      await temporary.writeAsString(
          jsonEncode({
            'version': 2,
            'complete': true,
            'time': DateTime.now().millisecondsSinceEpoch,
            'digest': key(value),
            'value': value
          }),
          flush: true);
      await temporary.rename(file(id).path);
    } finally {
      if (temporary.existsSync()) await temporary.delete();
    }
  }

  static List<Object> identity(File file) {
    final stat = file.statSync();
    return [
      file.absolute.path,
      stat.size,
      stat.modified.millisecondsSinceEpoch
    ];
  }
}
