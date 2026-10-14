import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/services/creator_tools.dart';

void main() {
  for (final entry in CreatorTools.motionPresets.entries) {
    test('${entry.key} preserves text and word timestamps', () {
      final rows = <Map<String, dynamic>>[
        {
          'start': 0.0,
          'end': 2.0,
          'text': 'halo dunia',
          'style': {'y': .8},
          'words': [
            {
              'word': 'halo',
              'start': 0.0,
              'end': 1.0,
              'style': {'font': 'Anton', 'animation': 'fade'}
            },
            {'word': 'dunia', 'start': 1.0, 'end': 2.0},
          ],
        },
      ];
      CreatorTools.applyMotion(rows, entry.key);
      expect(rows.single['text'], 'halo dunia');
      expect(rows.single['words'][1]['start'], 1.0);
      expect(rows.single['style']['y'], .8);
      expect(rows.single['style']['animation'], entry.value['animation']);
      expect(rows.single['words'][0]['style'], {'font': 'Anton'});
      final ass =
          CreatorTools.captionEvents(rows.single, {}, 1080, 1920).join('\n');
      expect(ass, contains('halo'));
      expect(ass, contains('dunia'));
    });
  }
}
