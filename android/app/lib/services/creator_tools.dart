import 'dart:math' as math;
import 'dart:convert';

import 'package:flutter/services.dart';

import 'cloud_ai.dart';

/// Local editorial cues. Scores help review; they do not predict virality.
class CreatorTools {
  static List<Map<String, dynamic>> trimRows(
    List<Map<String, dynamic>> rows,
    double offset,
    double duration,
  ) =>
      rows
          .where(
            (r) =>
                (r['end'] as num) > offset &&
                (r['start'] as num) < offset + duration,
          )
          .map(
            (r) => {
              ...r,
              'start': ((r['start'] as num) - offset).clamp(0, duration),
              'end': ((r['end'] as num) - offset).clamp(0, duration),
              if (r['words'] is List)
                'words': trimRows(
                  List<Map<String, dynamic>>.from(r['words']),
                  offset,
                  duration,
                ),
            },
          )
          .toList();
  static Map<String, dynamic> trimFraming(
    Map<String, dynamic> f,
    double offset,
    double duration,
  ) {
    if (f.containsKey('top') || f.containsKey('bottom')) {
      return {
        ...f,
        for (final k in ['top', 'bottom'])
          if (f[k] is Map)
            k: trimFraming(Map<String, dynamic>.from(f[k]), offset, duration),
      };
    }
    final frames = (f['keyframes'] as List? ?? [])
        .map((k) => Map<String, dynamic>.from(k))
        .toList();
    if (frames.isEmpty) return Map.from(f);
    frames.sort((a, b) => (a['time'] as num).compareTo(b['time'] as num));
    if (frames.first['time'] > 0) {
      frames.insert(0, {'time': 0, 'x': f['x'] ?? .5, 'y': f['y'] ?? .5});
    }
    Map<String, dynamic> at(double time) {
      var a = frames.first;
      for (final b in frames.skip(1)) {
        if (time <= b['time']) {
          final r = ((time - (a['time'] as num)) /
                  math.max(.001, (b['time'] as num) - (a['time'] as num)))
              .clamp(0, 1);
          return {
            'x': a['x'] + (b['x'] - a['x']) * r,
            'y': a['y'] + (b['y'] - a['y']) * r,
          };
        }
        a = b;
      }
      return {'x': a['x'], 'y': a['y']};
    }

    final first = at(offset), last = at(offset + duration);
    return {
      ...f,
      ...first,
      'keyframes': [
        {'time': 0.0, ...first},
        ...frames
            .where((k) => k['time'] > offset && k['time'] < offset + duration)
            .map((k) => {...k, 'time': k['time'] - offset}),
        {'time': duration, ...last},
      ],
    };
  }

  static Future<List<Map<String, dynamic>>> rankAi(
    List<Map<String, dynamic>> transcript,
    double duration,
    int count,
  ) async {
    final chunks = <List<Map<String, dynamic>>>[],
        current = <Map<String, dynamic>>[];
    var length = 0;
    for (final row in transcript) {
      final size = '${row['text']}'.length + 40;
      if (current.isNotEmpty && length + size > 18000) {
        chunks.add(List.from(current));
        final last = current.last;
        current
          ..clear()
          ..add(last);
        length = '${last['text']}'.length + 40;
      }
      current.add(row);
      length += size;
    }
    if (current.isNotEmpty) chunks.add(current);
    final pool = <Map<String, dynamic>>[];
    for (final chunk in chunks) {
      final compact =
          chunk.map((s) => '${s['start']}-${s['end']} ${s['text']}').join('\n');
      final result = await CloudAI.text(
        'Select up to ${autoCount(duration, count)} complete standalone moments. Include questions with answers, stories, hooks and takeaways. Avoid ads and repetition. Use transcript timestamps and duration 3–180 seconds. Return only JSON array with numeric start, end, score from 0 to 1, short title and reason.\n$compact',
      );
      final first = result.indexOf('['), last = result.lastIndexOf(']');
      if (first < 0 || last < first) {
        throw const FormatException('Respons AI tidak berisi JSON klip.');
      }
      final decoded = jsonDecode(result.substring(first, last + 1));
      if (decoded is! List) {
        throw const FormatException('Respons AI tidak valid.');
      }
      for (final r in decoded.whereType<Map>()) {
        if (r['start'] is! num || r['end'] is! num) continue;
        final start = (r['start'] as num).toDouble(),
            end = (r['end'] as num).toDouble();
        if (!start.isFinite ||
            !end.isFinite ||
            start < (chunk.first['start'] as num) ||
            end > math.min(duration, (chunk.last['end'] as num).toDouble()) ||
            end - start < 3 ||
            end - start > 180) {
          continue;
        }
        pool.add({
          'start': start,
          'end': end,
          'score': value(r['score'], .8, 0, 1),
          'title': '${r['title'] ?? ''}',
          'reason': '${r['reason'] ?? 'AI'}',
        });
      }
    }
    pool.sort((a, b) => (b['score'] as num).compareTo(a['score'] as num));
    final chosen = <Map<String, dynamic>>[];
    for (final r in pool) {
      if (chosen.any(
        (c) =>
            math.min(r['end'] as num, c['end'] as num) -
                math.max(r['start'] as num, c['start'] as num) >
            .5,
      )) {
        continue;
      }
      chosen.add(r);
      if (chosen.length >= autoCount(duration, count)) break;
    }
    if (chosen.isEmpty) {
      throw const FormatException('AI tidak memilih klip yang valid.');
    }
    return chosen
      ..sort((a, b) => (a['start'] as num).compareTo(b['start'] as num));
  }

  static const channel = MethodChannel('studiozai/creator');
  static const fonts = [
    'Inter',
    'Anton',
    'Barlow Condensed',
    'DM Serif Display',
    'Kalam',
  ];
  static const languages = {
    'id': 'Indonesia',
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'pt': 'Português',
    'ar': 'العربية',
    'ja': '日本語',
    'ko': '한국어',
    'zh': '中文',
    'ru': 'Русский',
  };
  static final cues = <(RegExp, double, String)>[
    (
      RegExp(
        r'\?|\b(kenapa|mengapa|bagaimana|gimana|apa yang|what|why|how)\b',
        caseSensitive: false,
      ),
      .18,
      'tanya-jawab',
    ),
    (
      RegExp(
        r'\b(ternyata|rahasia|kesalahan|jangan|bayangkan|fakta|terpenting|secret|mistake|never|imagine|surprising|truth)\b',
        caseSensitive: false,
      ),
      .20,
      'hook',
    ),
    (
      RegExp(
        r'\b(dulu|pernah|waktu itu|pengalaman|akhirnya|belajar|kisah|once|remember|learned|story|realized)\b',
        caseSensitive: false,
      ),
      .14,
      'cerita',
    ),
    (
      RegExp(
        r'\b(intinya|jadi|kesimpulan|caranya|pelajaran|solusi|tips|because|lesson|therefore|solution|advice)\b',
        caseSensitive: false,
      ),
      .17,
      'poin utama',
    ),
  ];
  static final ads = RegExp(
    r'\b(sponsor|kode promo|link di bio|subscribe|diskon|promo code|discount|commercial break)\b',
    caseSensitive: false,
  );
  static int autoCount(double duration, int count) =>
      count > 0 ? count : (duration / 300).ceil().clamp(3, 10);
  static List<Map<String, dynamic>> podcast(
    List<Map<String, dynamic>> transcript,
    double duration,
    int count,
  ) {
    final segments = transcript
        .where(
          (s) =>
              s['start'] is num &&
              s['end'] is num &&
              (s['start'] as num).isFinite &&
              (s['end'] as num).isFinite &&
              s['start'] >= 0 &&
              s['end'] > s['start'] &&
              s['start'] < duration,
        )
        .toList()
      ..sort((a, b) => (a['start'] as num).compareTo(b['start'] as num));
    final pool = <Map<String, dynamic>>[];
    for (var i = 0; i < segments.length; i++) {
      final rows = <Map<String, dynamic>>[];
      for (final row in segments.skip(i)) {
        final start = (segments[i]['start'] as num).toDouble(),
            end = math.min(duration, (row['end'] as num).toDouble()),
            span = end - start;
        if (span > 90) break;
        rows.add(row);
        final text = rows.map((r) => r['text'] ?? '').join(' ').trim();
        if (span < 20 ||
            text.isEmpty ||
            (rows.length == 1 && text.endsWith('?'))) {
          continue;
        }
        var score = .25;
        final reasons = <String>[];
        for (final cue in cues) {
          if (cue.$1.hasMatch(text)) {
            score += cue.$2;
            reasons.add(cue.$3);
          }
        }
        if (ads.hasMatch(text)) {
          score -= .4;
          reasons.add('mengandung promosi');
        }
        if (RegExp(r'[.!?…]$').hasMatch(text)) score += .06;
        score -= math.min(.12, (span - 50).abs() / 500);
        pool.add({
          'start': start,
          'end': end,
          'score': score.clamp(0, 1),
          'reason':
              'Podcast lokal · ${reasons.isEmpty ? 'ucapan utuh' : reasons.join(', ')}',
          'title':
              '${segments[i]['text']}'.split(RegExp(r'\s+')).take(12).join(' '),
        });
        if (span >= 45 && RegExp(r'[.!?…]$').hasMatch(text)) break;
      }
    }
    pool.sort((a, b) => (b['score'] as num).compareTo(a['score'] as num));
    final chosen = <Map<String, dynamic>>[];
    for (final c in pool) {
      if (chosen.any(
        (s) =>
            math.min(c['end'] as num, s['end'] as num) -
                math.max(c['start'] as num, s['start'] as num) >
            .5,
      )) {
        continue;
      }
      chosen.add(c);
      if (chosen.length >= autoCount(duration, count)) break;
    }
    return chosen
      ..sort((a, b) => (a['start'] as num).compareTo(b['start'] as num));
  }

  static List<Map<String, dynamic>> words(Map<String, dynamic> row) {
    final existing = row['words'] as List?;
    if (existing != null && existing.isNotEmpty) {
      return List<Map<String, dynamic>>.from(existing);
    }
    final tokens = '${row['text'] ?? ''}'
        .split(RegExp(r'\s+'))
        .where((w) => w.isNotEmpty)
        .toList();
    final start = (row['start'] as num).toDouble(),
        span = ((row['end'] as num) - start) / math.max(1, tokens.length);
    final result = List.generate(
      tokens.length,
      (i) => <String, dynamic>{
        'word': tokens[i],
        'start': start + i * span,
        'end': start + (i + 1) * span,
      },
    );
    row['words'] = result;
    return result;
  }

  static double value(dynamic n, double fallback, double low, double high) =>
      n is num && n.isFinite ? n.toDouble().clamp(low, high) : fallback;
  static String styleTags(
    Map style,
    double scale,
    int width,
    int height, {
    bool position = true,
  }) {
    var result = '';
    if (fonts.contains(style['font'])) result += '\\fn${style['font']}';
    if (style.containsKey('size')) {
      result +=
          '\\fs${(value(style['size'], 56, 14, 160) * scale).toStringAsFixed(1)}';
    }
    final color = '${style['color']}';
    if (RegExp(r'^#[0-9a-fA-F]{6}$').hasMatch(color)) {
      result +=
          '\\c&H${color.substring(5, 7)}${color.substring(3, 5)}${color.substring(1, 3)}&';
    }
    if (style.containsKey('bold')) {
      result += '\\b${style['bold'] == true ? 1 : 0}';
    }
    if (position && (style.containsKey('x') || style.containsKey('y'))) {
      final x = (value(style['x'], .5, .05, .95) * width).round(),
          y = (value(style['y'], .82, .05, .95) * height).round();
      result += style['animation'] == 'rise'
          ? '\\an5\\move($x,${y + (height * .04).round()},$x,$y,0,220)'
          : '\\an5\\pos($x,$y)';
    }
    result += <String, String>{
          'pop':
              r'\fscx75\fscy75\t(0,130,\fscx108\fscy108)\t(130,220,\fscx100\fscy100)',
          'fade': r'\fad(150,120)',
          'rise': r'\fad(100,80)',
          'zoom': r'\fscx85\fscy85\t(0,300,\fscx100\fscy100)',
        }[style['animation']] ??
        '';
    return result;
  }

  static String escape(String s) => s
      .replaceAll('\\', r'\\')
      .replaceAll('{', r'\{')
      .replaceAll('}', r'\}')
      .replaceAll('\n', r'\N');
  static String captionText(
    Map<String, dynamic> row,
    Map preset,
    int width,
    int height,
  ) {
    final base = Map<String, dynamic>.from(row['style'] as Map? ?? {}),
        scale = height / 1920;
    final prefix = base.isEmpty
        ? '${preset['anim'] ?? ''}'
        : '{${styleTags(base, scale, width, height)}}';
    final list = words(row);
    if (base.isEmpty &&
        !list.any((w) => (w['style'] as Map? ?? {}).isNotEmpty)) {
      if (preset['karaoke'] != true) {
        return '$prefix${escape('${row['text']}')}';
      }
      return prefix +
          list
              .map(
                (w) =>
                    '{\\k${math.max(1, (((w['end'] as num) - (w['start'] as num)) * 100).round())}}${escape('${w['word']}')}',
              )
              .join(' ');
    }
    if (list.isEmpty) return '$prefix${escape('${row['text']}')}';
    return prefix +
        list.map((w) {
          final style = {...base, ...(w['style'] as Map? ?? {})};
          var tags = r'\rDefault' +
              styleTags(style, scale, width, height, position: false);
          final start = value(w['start'], 0, 0, 86400),
              end = value(w['end'], start, start, 86400),
              cueStart = (row['start'] as num).toDouble();
          if (style['animation'] == 'type') {
            final at = ((start - cueStart) * 1000).round();
            tags += '\\alpha&HFF&\\t($at,${at + 1},\\alpha&H00&)';
          } else if (preset['karaoke'] == true) {
            tags +=
                '\\kt${((start - cueStart) * 100).round()}\\k${math.max(1, ((end - start) * 100).round())}';
          }
          return '{$tags}${escape('${w['word']}')}';
        }).join(' ');
  }

  static List<String> captionEvents(
    Map<String, dynamic> row,
    Map preset,
    int width,
    int height,
  ) {
    String timestamp(num n) {
      final cs = (n * 100).round();
      return '${cs ~/ 360000}:${(cs ~/ 6000 % 60).toString().padLeft(2, '0')}:${(cs ~/ 100 % 60).toString().padLeft(2, '0')}.${(cs % 100).toString().padLeft(2, '0')}';
    }

    String event(num start, num end, String text, [String name = 'Default']) =>
        'Dialogue: 0,${timestamp(start)},${timestamp(end)},$name,,0,0,0,,$text';
    final base = Map<String, dynamic>.from(row['style'] as Map? ?? {}),
        mode = base['mode'];
    if (!['word', 'box', 'highlight'].contains(mode)) {
      return [
        event(
          row['start'],
          row['end'],
          captionText(row, preset, width, height),
        ),
      ];
    }
    final list = words(row), output = <String>[];
    var cursor = (row['start'] as num).toDouble();
    for (var i = 0; i < list.length; i++) {
      final w = list[i],
          start = value(w['start'], cursor, row['start'], row['end']),
          end = value(w['end'], start, start, row['end']);
      if (end <= start) continue;
      if (mode == 'highlight') {
        if (start > cursor) {
          output.add(
            event(cursor, start, captionText(row, preset, width, height)),
          );
        }
        final current = Map<String, dynamic>.from(jsonDecode(jsonEncode(row)));
        final currentWords = words(current);
        currentWords[i]['style'] = {
          ...(currentWords[i]['style'] as Map? ?? {}),
          'color': base['highlight'] ?? '#abff66',
        };
        output.add(
          event(start, end, captionText(current, preset, width, height)),
        );
      } else {
        final style = {...base, ...(w['style'] as Map? ?? {})};
        final color = '${base['boxColor'] ?? '#111111'}';
        final box = mode == 'box' && RegExp(r'^#[\da-fA-F]{6}$').hasMatch(color)
            ? '\\3c&H${color.substring(5, 7)}${color.substring(3, 5)}${color.substring(1, 3)}&'
            : '';
        output.add(
          event(
            start,
            end,
            '{${styleTags(style, height / 1920, width, height)}$box}${escape('${w['word']}')}',
            mode == 'box' ? 'ActiveBox' : 'Default',
          ),
        );
      }
      cursor = end;
    }
    if (mode == 'highlight' && cursor < (row['end'] as num)) {
      output.add(
        event(cursor, row['end'], captionText(row, preset, width, height)),
      );
    }
    return output;
  }

  static String cropFilter(
    Map<String, dynamic> f,
    int sw,
    int sh,
    int ow,
    int oh,
  ) {
    final zoom = value(f['zoom'], 1, 1, 4), ratio = ow / oh;
    final cw = math.max(2, (math.min(sw, sh * ratio) / zoom).floor() ~/ 2 * 2),
        ch = math.max(2, (math.min(sh, sw / ratio) / zoom).floor() ~/ 2 * 2);
    final byTime = <double, Map<String, dynamic>>{};
    for (final k in (f['keyframes'] as List? ?? []).take(600)) {
      if (k is Map) {
        byTime[value(k['time'], 0, 0, 86400)] = {
          'time': value(k['time'], 0, 0, 86400),
          'x': value(k['x'], .5, 0, 1),
          'y': value(k['y'], .5, 0, 1),
        };
      }
    }
    byTime.putIfAbsent(
      0,
      () => {
        'time': 0.0,
        'x': value(f['x'], .5, 0, 1),
        'y': value(f['y'], .5, 0, 1),
      },
    );
    final frames = byTime.values.toList()
      ..sort((a, b) => (a['time'] as num).compareTo(b['time'] as num));
    String expr(String axis, int size, int crop) {
      var e = '${frames.last[axis]}';
      for (var i = frames.length - 2; i >= 0; i--) {
        final a = frames[i],
            b = frames[i + 1],
            span = math.max(.001, (b['time'] as num) - (a['time'] as num));
        e = 'if(lt(t,${b['time']}),(${a[axis]}+(${(b[axis] as num) - (a[axis] as num)})*(t-${a['time']})/$span),$e)';
      }
      return 'max(0,min(${size - crop},($e)*$size-${crop / 2}))';
    }

    return "crop=$cw:$ch:'${expr('x', sw, cw)}':'${expr('y', sh, ch)}',scale=$ow:$oh,setsar=1";
  }

  static String splitFilter(
    Map<String, dynamic> f,
    int sw,
    int sh,
    int ow,
    int oh,
  ) {
    final topHeight = (oh * value(f['fraction'], .35, .2, .8)).floor() ~/ 2 * 2;
    final top = cropFilter(
      Map<String, dynamic>.from(
        f['top'] as Map? ?? {'x': .15, 'y': .2, 'zoom': 2},
      ),
      sw,
      sh,
      ow,
      topHeight,
    );
    final bottom = cropFilter(
      Map<String, dynamic>.from(f['bottom'] as Map? ?? {'x': .5, 'y': .5}),
      sw,
      sh,
      ow,
      oh - topHeight,
    );
    return 'split=2[face][game];[face]$top[faceout];[game]$bottom[gameout];[faceout][gameout]vstack=inputs=2,setsar=1[vout]';
  }

  static Future<List<Map<String, dynamic>>> translate(
    List<Map<String, dynamic>> rows,
    String source,
    String target,
  ) async {
    final result = await channel.invokeListMethod<String>('translate', {
      'source': source,
      'target': target,
      'texts': rows.map((r) => r['text']).toList(),
    });
    if (result == null || result.length != rows.length) {
      throw Exception('Terjemahan tidak lengkap');
    }
    return List.generate(rows.length, (i) {
      final row = <String, dynamic>{
        ...rows[i],
        'text': result[i],
        'words': <Map<String, dynamic>>[],
      };
      words(row);
      return row;
    });
  }
}
