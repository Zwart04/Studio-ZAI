import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/models.dart';
import 'package:studiozai/services/clip_edits.dart';
import 'package:studiozai/services/timeline.dart';
import 'package:studiozai/services/subtitle_builder.dart';

void main() {
  test(
      'Splitting after hour one preserves source time, captions, styles and overlays',
      () {
    final clip = Clip(
        index: 3,
        start: 3650,
        end: 3680,
        canvas: 'original',
        subtitlePreset: 'viral_yellow',
        captions: [
          {'start': 18.0, 'end': 22.0, 'text': 'Indonesia'}
        ]);
    final timeline = Timeline.fromClip(clip: clip, sourcePath: 'saved.mp4');
    timeline
        .trackOf('audio')!
        .items
        .add(TimelineItem(id: 'music', start: 0, end: 30, srcStart: 5));
    clip.timeline = timeline.toJson();
    final right = sliceClip(clip, 3665, 3680, 4);
    expect(right.captions.single['start'], 3);
    expect(right.captions.single['end'], 7);
    expect(right.canvas, 'original');
    expect(right.subtitlePreset, 'viral_yellow');
    expect(
        Timeline.fromJson(right.timeline!)
            .trackOf('video')!
            .items
            .single
            .srcStart,
        3665);
    expect(
        Timeline.fromJson(right.timeline!)
            .trackOf('audio')!
            .items
            .single
            .srcStart,
        20);
    expect(clip.start, 3650);
    expect(timeline.trackOf('audio')!.items.single.srcStart, 5);
    expect(() => sliceClip(clip, 3649, 3660, 5), throwsArgumentError);
  });
  test(
      'Disabling subtitles removes only generated captions, preserving typed overlays',
      () {
    final result = SubtitleBuilder.toAss([Caption(0, 2, 'generated')],
        position: 'off',
        textItems: [
          {
            'id': 'text',
            'start': 0.0,
            'end': 2.0,
            'text': 'overlay',
            'template': 'clean',
            'x': .5,
            'y': .5
          }
        ]);
    expect(result, isNot(contains('generated')));
    expect(result, contains('overlay'));
  });
}
