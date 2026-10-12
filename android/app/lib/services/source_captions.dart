import 'dart:io';

class SourceCaptions {
  static List<Map<String, dynamic>> parse(String text, {double duration = 0}) {
    final normalized = text.replaceAll('\r\n', '\n');
    final pattern = RegExp(
        r'(\d{1,2}:\d{2}(?::\d{2})?[.,]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}(?::\d{2})?[.,]\d{1,3})[^\n]*\n([\s\S]*?)(?=\n\s*\n|$)');
    double seconds(String clock) => clock
        .replaceAll(',', '.')
        .split(':')
        .fold<double>(0, (n, part) => n * 60 + double.parse(part));
    final rows = <Map<String, dynamic>>[];
    for (final match in pattern.allMatches(normalized)) {
      final start = seconds(match[1]!), end = seconds(match[2]!);
      final content = match[3]!
          .replaceAll(RegExp(r'<[^>]+>'), '')
          .replaceAll('\n', ' ')
          .trim();
      if (!start.isFinite ||
          !end.isFinite ||
          start < 0 ||
          end <= start ||
          (duration > 0 && end > duration + 2)) {
        continue;
      }
      if (content.isNotEmpty) {
        rows.add({
          'start': start,
          'end': end,
          'text': content,
          'words': <Map<String, dynamic>>[]
        });
      }
    }
    return rows;
  }

  static Future<List<Map<String, dynamic>>> sidecar(
      String source, double duration) async {
    final stem = source.replaceFirst(RegExp(r'\.[^./\\]+$'), '');
    for (final ext in ['srt', 'vtt']) {
      final file = File('$stem.$ext');
      if (await file.exists()) {
        final rows = parse(await file.readAsString(), duration: duration);
        if (rows.isNotEmpty) return rows;
      }
    }
    return [];
  }
}
