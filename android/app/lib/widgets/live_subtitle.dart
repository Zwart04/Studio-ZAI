import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../services/creator_tools.dart';

class LiveSubtitle extends StatelessWidget {
  const LiveSubtitle(
      {super.key,
      required this.captions,
      required this.seconds,
      this.position = 'bottom'});
  final List<Map<String, dynamic>> captions;
  final double seconds;
  final String position;

  @override
  Widget build(BuildContext context) {
    if (position == 'off') return const SizedBox.shrink();
    Map<String, dynamic>? cue;
    for (final row in captions) {
      if ((row['start'] as num).toDouble() <= seconds &&
          seconds < (row['end'] as num).toDouble()) {
        cue = row;
        break;
      }
    }
    if (cue == null) return const SizedBox.shrink();
    final row = cue, words = CreatorTools.previewWords(row, seconds);
    final base = Map<String, dynamic>.from(row['style'] as Map? ?? {});
    Color color(dynamic value, Color fallback) {
      final text = '$value';
      if (!RegExp(r'^#[\da-fA-F]{6}$').hasMatch(text)) return fallback;
      return Color(0xff000000 | int.parse(text.substring(1), radix: 16));
    }

    return LayoutBuilder(builder: (context, bounds) {
      final y = CreatorTools.value(
          base['y'],
          (position == 'top'
              ? .15
              : position == 'middle'
                  ? .5
                  : .82),
          .05,
          .95);
      final x = CreatorTools.value(base['x'], .5, .05, .95);
      return Stack(children: [
        if (row['timing_quality'] == 'estimated' ||
            (row['words'] as List? ?? []).isEmpty)
          const Positioned(
              top: 4,
              left: 4,
              child: ColoredBox(
                  color: Colors.black,
                  child: Padding(
                      padding: EdgeInsets.all(2),
                      child: Text('Timing kata diperkirakan',
                          style:
                              TextStyle(color: Colors.white, fontSize: 10))))),
        Align(
          alignment: Alignment(x * 2 - 1, y * 2 - 1),
          child: IgnorePointer(
              child: Container(
            constraints: BoxConstraints(maxWidth: bounds.maxWidth * .9),
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
            color: const Color(0xDD000000),
            child: Semantics(
                label: '${row['text']}',
                child: Wrap(
                  alignment: WrapAlignment.center,
                  children: words.map((word) {
                    final start = (word['start'] as num).toDouble(),
                        end = (word['end'] as num).toDouble();
                    final active = start <= seconds && seconds < end;
                    final style = {
                      ...base,
                      ...Map<String, dynamic>.from(word['style'] as Map? ?? {})
                    };
                    final mode = '${base['mode'] ?? 'line'}',
                        animation = '${style['animation'] ?? 'none'}';
                    final p = ((seconds - start) / .22).clamp(0.0, 1.0);
                    final age = math.max(0.0, seconds - start);
                    var scale = 1.0, scaleY = 1.0, dy = 0.0, opacity = 1.0;
                    if (active && animation == 'pop') {
                      scale = age < .13
                          ? .75 + (age / .13).clamp(0.0, 1.0) * .33
                          : 1.08 - ((age - .13) / .09).clamp(0.0, 1.0) * .08;
                    }
                    if (active && animation == 'bounce') {
                      scaleY = age < .1
                          ? .7 + age * 5
                          : 1.2 - ((age - .1) / .12).clamp(0.0, 1.0) * .2;
                    }
                    if (active && animation == 'rise') dy = (1 - p) * 8;
                    if (active && animation == 'zoom') scale = .85 + p * .15;
                    if (active && animation == 'fade') opacity = p;
                    if ((mode == 'word' && !active) ||
                        (['type', 'typewriter'].contains(animation) &&
                            seconds < start)) {
                      opacity = 0;
                    }
                    Widget fill(Widget text) {
                      if (mode != 'karaoke') return text;
                      final fraction =
                          ((seconds - start) / (end - start)).clamp(0.0, 1.0);
                      return ShaderMask(
                          blendMode: BlendMode.srcIn,
                          shaderCallback: (rect) => LinearGradient(
                                colors: [
                                  color(base['highlight'],
                                      const Color(0xFFABFF66)),
                                  color(style['color'], Colors.white)
                                ],
                                stops: [fraction, fraction],
                              ).createShader(rect),
                          child: text);
                    }

                    return Transform.translate(
                        offset: Offset(0, dy),
                        child: Transform.scale(
                            scaleX: scale,
                            scaleY: scale * scaleY,
                            child: Opacity(
                                opacity: opacity,
                                child: ColoredBox(
                                  color: active && mode == 'box'
                                      ? color(base['boxColor'], Colors.black)
                                      : Colors.transparent,
                                  child: fill(Text('${word['word']} ',
                                      style: TextStyle(
                                        color: active &&
                                                ['highlight', 'box', 'karaoke']
                                                    .contains(mode)
                                            ? color(base['highlight'],
                                                const Color(0xFFABFF66))
                                            : color(
                                                style['color'], Colors.white),
                                        fontFamily: CreatorTools.fonts
                                                .contains(style['font'])
                                            ? style['font'] as String
                                            : 'Inter',
                                        fontWeight: style['bold'] == true
                                            ? FontWeight.w700
                                            : FontWeight.w600,
                                        fontSize: math.max(
                                            12,
                                            CreatorTools.value(style['size'],
                                                    56, 14, 160) *
                                                bounds.maxHeight /
                                                1920),
                                      ))),
                                ))));
                  }).toList(),
                )),
          )),
        )
      ]);
    });
  }
}
