import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/models.dart';
import 'package:studiozai/services/source_captions.dart';
import 'package:studiozai/widgets/live_subtitle.dart';
import 'package:studiozai/services/stage_cache.dart';
import 'package:studiozai/services/creator_tools.dart';
import 'package:studiozai/widgets/live_video_subtitle.dart';
import 'package:video_player/video_player.dart';
import 'package:studiozai/services/media_tools.dart';

void main() {
  test('Phone display matrix uses portrait dimensions before crop', () {
    expect(
        MediaTools.displayResolution({
          'width': 640,
          'height': 360,
          'side_data_list': [
            {'rotation': -90}
          ]
        }),
        {'width': 360, 'height': 640});
    expect(
        MediaTools.displayResolution({
          'width': 640,
          'height': 360,
          'tags': {'rotate': '180'}
        }),
        {'width': 640, 'height': 360});
  });
  testWidgets(
      'Playback clock animates between sparse native position reports and stops on pause',
      (tester) async {
    final player = ValueNotifier(const VideoPlayerValue(
        duration: Duration(seconds: 3),
        position: Duration(milliseconds: 400),
        isPlaying: true));
    final rows = <Map<String, dynamic>>[
      {
        'start': .4,
        'end': 2.4,
        'text': 'Halo',
        'style': {'animation': 'fade'},
        'words': [
          {'word': 'Halo', 'start': .4, 'end': 2.4}
        ]
      }
    ];
    await tester.pumpWidget(MaterialApp(
        home: SizedBox(
            width: 240,
            height: 400,
            child: LiveVideoSubtitle(player: player, captions: rows))));
    await tester.pump();
    final opacity = find
        .ancestor(of: find.text('Halo '), matching: find.byType(Opacity))
        .first;
    expect(tester.widget<Opacity>(opacity).opacity, 0);
    await tester.pump(const Duration(milliseconds: 100));
    expect(tester.widget<Opacity>(opacity).opacity, greaterThan(.3));
    player.value = player.value.copyWith(
        isPlaying: false, position: const Duration(milliseconds: 500));
    await tester.pump();
    final paused = tester.widget<Opacity>(opacity).opacity;
    await tester.pump(const Duration(milliseconds: 400));
    expect(tester.widget<Opacity>(opacity).opacity, paused);
    await tester.pumpWidget(const SizedBox());
    player.dispose();
    expect(tester.takeException(), isNull);
  });
  test('Stage cache rejects corruption and stale versions', () async {
    final root = await Directory.systemTemp.createTemp('studio-cache-');
    try {
      final cache = StageCache(root);
      await cache.write('fixture', {'segments': []});
      expect(cache.read('fixture'), {'segments': []});
      cache.file('fixture').writeAsStringSync(
          '{"version":2,"complete":true,"digest":"wrong","value":{}}');
      expect(cache.read('fixture'), isNull);
    } finally {
      await root.delete(recursive: true);
    }
  });
  test('Highlight live preview uses the exported chunk boundaries', () {
    final row = <String, dynamic>{
      'start': 0.0,
      'end': 4.0,
      'style': {'mode': 'highlight'},
      'text': 'satu dua tiga empat',
      'words': List.generate(
          4,
          (i) => {
                'word': ['satu', 'dua', 'tiga', 'empat'][i],
                'start': i.toDouble(),
                'end': i + 1.0
              })
    };
    expect(CreatorTools.previewWords(row, .5).length, 3);
    expect(CreatorTools.previewWords(row, 3.5).single['word'], 'empat');
  });
  test('Sidecar timestamps reject invalid and out-of-source cues', () {
    final rows = SourceCaptions.parse(
        '1\n00:00:01,000 --> 00:00:03,000\nHalo dunia\n\n2\n00:00:09,000 --> 00:00:11,000\nBeyond source\n',
        duration: 5);
    expect(rows.length, 1);
    expect(rows.first['start'], 1);
    expect(rows.first['text'], 'Halo dunia');
  });
  test('Local sidecar leaves original media untouched', () async {
    final root =
        await Directory.systemTemp.createTemp('studio-hybrid-caption-');
    try {
      final video = File('${root.path}/sample.mp4')
        ..writeAsBytesSync([1, 2, 3]);
      File('${root.path}/sample.vtt').writeAsStringSync(
          'WEBVTT\n\n00:01.000 --> 00:03.000\nCaption fixture\n');
      expect(await SourceCaptions.sidecar(video.path, 5), isNotEmpty);
      expect(video.readAsBytesSync(), [1, 2, 3]);
    } finally {
      await root.delete(recursive: true);
    }
  });
  test('Legacy projects preserve online fields and processing metadata', () {
    final project = Project.fromJson({
      'id': 'fixture',
      'title': 'Fixture',
      'source': '',
      'online': true,
      'sourceUrl': 'https://youtu.be/abcdefghijk'
    });
    expect(project.processingMode, 'legacy');
    project.processingMode = 'hybrid';
    project.execution = {'ranking': 'heuristic-only'};
    final restored = Project.fromJson(project.toJson());
    expect(restored.sourceUrl, project.sourceUrl);
    expect(restored.execution['ranking'], 'heuristic-only');
  });
  testWidgets('Live subtitle follows seeking without moving the text layout',
      (tester) async {
    final rows = <Map<String, dynamic>>[
      {
        'start': 0.0,
        'end': 2.0,
        'text': 'Halo dunia',
        'style': {'mode': 'highlight'},
        'words': [
          {'word': 'Halo', 'start': 0.0, 'end': 1.0},
          {'word': 'dunia', 'start': 1.0, 'end': 2.0}
        ]
      }
    ];
    Future<void> show(double seconds) => tester.pumpWidget(MaterialApp(
        home: SizedBox(
            width: 240,
            height: 400,
            child: LiveSubtitle(captions: rows, seconds: seconds))));
    await show(.5);
    final before = tester.getRect(find.text('Halo '));
    expect(tester.widget<Text>(find.text('Halo ')).style!.color,
        const Color(0xFFABFF66));
    await show(1.5);
    expect(tester.getRect(find.text('Halo ')), before);
    expect(tester.widget<Text>(find.text('dunia ')).style!.color,
        const Color(0xFFABFF66));
    await show(3);
    expect(find.text('Halo '), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
