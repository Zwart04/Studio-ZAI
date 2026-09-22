// Subtitle builders: SRT and ASS (burned-in), ported from
// core/studiozai/pipeline/subtitle.py.
//
// ASS dipakai untuk semua teks di video: caption otomatis maupun item track
// teks pada editor timeline. Satu berkas memuat banyak style (template
// tipografi) dan penempatan bebas lewat \pos, jadi hasilnya sama dengan versi
// desktop tanpa perlu filter drawtext.

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
  /// Caption dibuat lebih pendek + margin lebih lega daripada versi lama
  /// (42 karakter / margin 60): pada kanvas 1080x1920 teks sepanjang itu
  /// melewati area aman dan terlihat terpotong di tepi.
  static const defaultMaxWords = 5;
  static const defaultMaxChars = 28;
  static const marginH = 90.0;

  /// Template tipografi. Ukuran ditulis untuk tinggi kanvas 1920 lalu
  /// diskalakan (lihat [toAss]) sehingga proporsional di kanvas lain.
  static const presets = <String, Map<String, Object>>{
    'clean': {
      'label': 'Clean',
      'size': 56,
      'primary': '&H00FFFFFF',
      'secondary': '&H00FFFFFF',
      'outlineColour': '&H00101010',
      'bold': 0,
      'outline': 3,
      'shadow': 1,
      'border': 1,
      'marginV': 220,
      'karaoke': false,
      'anim': r'{\fad(120,120)}',
    },
    'bold_highlight': {
      'label': 'Bold highlight',
      'size': 68,
      'primary': '&H00FFFFFF',
      'secondary': '&H0000E1FF',
      'outlineColour': '&H00101010',
      'bold': -1,
      'outline': 4,
      'shadow': 1,
      'border': 1,
      'marginV': 250,
      'karaoke': true,
      'anim': '',
    },
    'tiktok_pop': {
      'label': 'TikTok pop',
      'size': 76,
      'primary': '&H00FFFFFF',
      'secondary': '&H0000E1FF',
      'outlineColour': '&H00000000',
      'bold': -1,
      'outline': 5,
      'shadow': 2,
      'border': 1,
      'marginV': 300,
      'karaoke': true,
      'anim': r'{\fad(80,80)\fscx94\fscy94\t(0,150,\fscx100\fscy100)}',
    },
    'karaoke_fill': {
      'label': 'Karaoke fill',
      'size': 66,
      'primary': '&H00FFFFFF',
      'secondary': '&H0000D158',
      'outlineColour': '&H00101010',
      'bold': -1,
      'outline': 3,
      'shadow': 1,
      'border': 1,
      'marginV': 250,
      'karaoke': true,
      'anim': '',
    },
    'title_card': {
      'label': 'Title card',
      'size': 96,
      'primary': '&H00FFFFFF',
      'secondary': '&H00FFFFFF',
      'outlineColour': '&H00101010',
      'bold': -1,
      'outline': 4,
      'shadow': 2,
      'border': 1,
      'marginV': 0,
      'karaoke': false,
      'anim': r'{\fad(160,160)}',
    },
    'minimal_lower': {
      'label': 'Minimal lower',
      'size': 44,
      'primary': '&H00F2F2F7',
      'secondary': '&H00F2F2F7',
      'outlineColour': '&H00101010',
      'bold': 0,
      'outline': 2,
      'shadow': 0,
      'border': 1,
      'marginV': 140,
      'karaoke': false,
      'anim': r'{\fad(100,100)}',
    },
    'neon': {
      'label': 'Neon',
      'size': 70,
      'primary': '&H00FFFFFF',
      'secondary': '&H00FF453A',
      'outlineColour': '&H00FF453A',
      'bold': -1,
      'outline': 5,
      'shadow': 4,
      'border': 1,
      'marginV': 260,
      'karaoke': false,
      'anim': r'{\fad(120,120)}',
    },
    'subtitle_box': {
      'label': 'Subtitle box',
      'size': 54,
      'primary': '&H00FFFFFF',
      'secondary': '&H00FFFFFF',
      'outlineColour': '&H99000000',
      'bold': 0,
      'outline': 12,
      'shadow': 0,
      'border': 3,
      'marginV': 220,
      'karaoke': false,
      'anim': r'{\fad(120,120)}',
    },
  };

  static const defaultPreset = 'clean';

  static List<Map<String, String>> presetList() => presets.entries
      .map((entry) => {'id': entry.key, 'label': entry.value['label'] as String})
      .toList();

  /// Nama template yang aman dipakai sebagai nama style ASS.
  ///
  /// Dipakai saat membuat style DAN saat menulis event Dialogue, supaya
  /// keduanya selalu menunjuk style yang sama.
  static String templateId(Object? name) {
    final text = name?.toString() ?? defaultPreset;
    return presets.containsKey(text) ? text : defaultPreset;
  }

  /// Group word-level entries into readable captions.
  static List<Caption> groupWords(
    List<Map<String, dynamic>> words, {
    int maxWords = defaultMaxWords,
    int maxChars = defaultMaxChars,
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
    int maxWords = defaultMaxWords,
    int maxChars = defaultMaxChars,
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

  static String _styleLine(String name, Map<String, Object> style, double scale, int alignment, int marginV) {
    final marginH = (SubtitleBuilder.marginH * scale).round();
    return 'Style: $name,Roboto,${style['size']},${style['primary']},${style['secondary']},'
        '${style['outlineColour']},&H80000000,${style['bold']},0,0,0,100,100,0,0,'
        '${style['border']},${style['outline']},${style['shadow']},$alignment,'
        '$marginH,$marginH,$marginV,1';
  }

  static String _karaoke(Caption caption, Map<String, Object> style) {
    if (style['karaoke'] != true || caption.words.isEmpty) return _escape(caption.text);
    return caption.words.map((w) {
      final duration = ((w['end'] as num).toDouble() - (w['start'] as num).toDouble()) * 100;
      return '{\\k${duration.round().clamp(1, 100000)}}${_escape(w['word'] as String)}';
    }).join(' ');
  }

  /// Berkas ASS lengkap: caption + item track teks (template).
  static String toAss(
    List<Caption> captions, {
    String preset = defaultPreset,
    int width = 1080,
    int height = 1920,
    List<Map<String, dynamic>> textItems = const [],
  }) {
    final style = presets[preset] ?? presets[defaultPreset]!;
    final scale = height / 1920.0;
    final marginV = ((style['marginV'] as int? ?? 220) * scale).round();

    final styles = <String>[_styleLine('Default', style, scale, 2, marginV)];
    final usedTemplates = <String>{
      for (final item in textItems) templateId(item['template']),
    }.toList()
      ..sort();
    for (final template in usedTemplates) {
      styles.add(_styleLine('Tpl_$template', presets[template]!, scale, 5, 0));
    }

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
${styles.join('\n')}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text''';

    final events = <String>[];
    for (final caption in captions) {
      final anim = style['anim'] as String? ?? '';
      events.add('Dialogue: 0,${_assTime(caption.start)},'
          '${_assTime(caption.end > caption.start ? caption.end : caption.start + 0.2)},'
          'Default,,0,0,0,,$anim${_karaoke(caption, style)}');
    }
    for (final item in textItems) {
      final text = (item['text'] as String? ?? '').trim();
      if (text.isEmpty) continue;
      final template = templateId(item['template']);
      final start = (item['start'] as num?)?.toDouble() ?? 0;
      final end = (item['end'] as num?)?.toDouble() ?? (start + 2);
      final x = ((item['x'] as num?)?.toDouble() ?? 0.5).clamp(0.0, 1.0) * width;
      final y = ((item['y'] as num?)?.toDouble() ?? 0.5).clamp(0.0, 1.0) * height;
      final anim = presets[template]?['anim'] as String? ?? '';
      events.add('Dialogue: 0,${_assTime(start)},${_assTime(end < start + 0.2 ? start + 0.2 : end)},'
          'Tpl_$template,,0,0,0,,{\\an5\\pos(${x.round()},${y.round()})}$anim${_escape(text)}');
    }
    return '$header\n${events.join('\n')}\n';
  }
}
