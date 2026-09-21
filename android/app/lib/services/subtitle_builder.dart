/// Subtitle builders: SRT and ASS (burned-in), ported from core/studiozai/pipeline/subtitle.py.

class Caption {
  Caption(this.start, this.end, this.text, [this.words = const []]);

  double start;
  double end;
  String text;
  List<Map<String, dynamic>> words;

  Map<String, dynamic> toJson() => {
        'start': double.parse(start.toStringAsFixed(3)),
        'end': double.parse(end.toStringAsFixed(3)),
        'text': text,
        'words': words,
      };

  static Caption fromJson(Map<String, dynamic> json) => Caption(
        (json['start'] as num).toDouble(),
        (json['end'] as num).toDouble(),
        json['text'] as String? ?? '',
        List<Map<String, dynamic>>.from((json['words'] as List? ?? const []).map((e) => Map<String, dynamic>.from(e as Map))),
      );
}

class SubtitleBuilder {
  static const presets = {
    'clean': {
      'size': 58,
      'bold': 0,
      'outline': 3,
      'marginV': 280,
      'karaoke': false,
    },
    'bold_highlight': {
      'size': 66,
      'bold': -1,
      'outline': 4,
      'marginV': 300,
      'karaoke': true,
    },
  };

  /// Group word-level entries into readable captions.
  static List<Caption> groupWords(
    List<Map<String, dynamic>> words, {
    int maxWords = 6,
    int maxChars = 42,
    double gap = 0.7,
  }) {
    final captions = <Caption>[];
    var buffer = <Map<String, dynamic>>[];

    void flush() {
      if (buffer.isEmpty) return;
      captions.add(Caption(
        (buffer.first['start'] as num).toDouble(),
        (buffer.last['end'] as num).toDouble(),
        buffer.map((w) => w['word'] as String).join(' ').trim(),
        List<Map<String, dynamic>>.from(buffer),
      ));
      buffer = [];
    }

    for (final word in words) {
      final text = (word['word'] as String? ?? '').trim();
      if (text.isEmpty) continue;
      if (buffer.isNotEmpty) {
        final joined = '${buffer.map((w) => w['word']).join(' ')} $text';
        final tooLong = joined.length > maxChars;
        final tooMany = buffer.length >= maxWords;
        final bigGap = (word['start'] as num).toDouble() - (buffer.last['end'] as num).toDouble() > gap;
        if (tooLong || tooMany || bigGap) flush();
      }
      buffer.add({'word': text, 'start': word['start'], 'end': word['end']});
    }
    flush();
    return captions;
  }

  /// Build captions from ASR segments (Android gives segment level timings).
  static List<Caption> captionsFromSegments(
    List<Map<String, dynamic>> segments, {
    int maxWords = 6,
    int maxChars = 42,
  }) {
    final captions = <Caption>[];
    for (final segment in segments) {
      final text = (segment['text'] as String? ?? '').trim();
      if (text.isEmpty) continue;
      final start = (segment['start'] as num).toDouble();
      final end = (segment['end'] as num).toDouble();
      final tokens = text.split(RegExp(r'\s+'));
      final chunks = <List<String>>[];
      var current = <String>[];
      for (final token in tokens) {
        final candidate = [...current, token].join(' ');
        if (current.isNotEmpty && (candidate.length > maxChars || current.length >= maxWords)) {
          chunks.add(current);
          current = [token];
        } else {
          current.add(token);
        }
      }
      if (current.isNotEmpty) chunks.add(current);
      final span = (end - start).clamp(0.4, double.infinity) / chunks.length;
      for (var i = 0; i < chunks.length; i++) {
        captions.add(Caption(
          start + i * span,
          start + (i + 1) * span,
          chunks[i].join(' '),
        ));
      }
    }
    return captions;
  }

  static String _srtTime(double seconds) {
    final ms = (seconds.clamp(0, 86400) * 1000).round();
    final h = ms ~/ 3600000;
    final m = (ms % 3600000) ~/ 60000;
    final s = (ms % 60000) ~/ 1000;
    final rest = ms % 1000;
    return '${h.toString().padLeft(2, '0')}:${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')},${rest.toString().padLeft(3, '0')}';
  }

  static String _assTime(double seconds) {
    final cs = (seconds.clamp(0, 86400) * 100).round();
    final h = cs ~/ 360000;
    final m = (cs % 360000) ~/ 6000;
    final s = (cs % 6000) ~/ 100;
    final rest = cs % 100;
    return '$h:${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}.${rest.toString().padLeft(2, '0')}';
  }

  static String toSrt(List<Caption> captions) {
    final buffer = StringBuffer();
    for (var i = 0; i < captions.length; i++) {
      final caption = captions[i];
      buffer.writeln('${i + 1}');
      buffer.writeln('${_srtTime(caption.start)} --> ${_srtTime(caption.end)}');
      buffer.writeln(caption.text);
      buffer.writeln();
    }
    return buffer.toString();
  }

  static String _escape(String text) =>
      text.replaceAll(r'\', r'\\').replaceAll('{', r'\{').replaceAll('}', r'\}').replaceAll('\n', r'\N');

  static String toAss(List<Caption> captions, {String preset = 'clean', int width = 1080, int height = 1920}) {
    final style = presets[preset] ?? presets['clean']!;
    final header = '''
[Script Info]
Title: Studio ZAI
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: $width
PlayResY: $height

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Roboto,${style['size']},&H00FFFFFF,&H0000E1FF,&H00101010,&H80000000,${style['bold']},0,0,0,100,100,0,0,1,${style['outline']},1,2,60,60,${style['marginV']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text''';

    final events = <String>[];
    for (final caption in captions) {
      final karaoke = style['karaoke'] == true && caption.words.isNotEmpty;
      final text = karaoke
          ? caption.words.map((w) {
              final duration = ((w['end'] as num).toDouble() - (w['start'] as num).toDouble()) * 100;
              return '{\\k${duration.round().clamp(1, 100000)}}${_escape(w['word'] as String)}';
            }).join(' ')
          : _escape(caption.text);
      events.add('Dialogue: 0,${_assTime(caption.start)},${_assTime(caption.end)},Default,,0,0,0,,$text');
    }
    return '$header\n${events.join('\n')}\n';
  }
}
