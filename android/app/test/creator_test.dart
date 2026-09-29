import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/services/creator_tools.dart';
import 'package:studiozai/services/subtitle_builder.dart';
import 'package:studiozai/services/timeline.dart';
import 'package:studiozai/models.dart';
import 'package:studiozai/services/clip_edits.dart';

void main() {
  test('Split preserves language variants and interpolates crop at new start',
      () {
    final row = <String, dynamic>{
      'start': 1.0,
      'end': 3.0,
      'text': 'Halo',
      'words': [
        {'start': 1.0, 'end': 3.0, 'word': 'Halo'}
      ]
    };
    final clip = Clip(
        index: 0,
        start: 10,
        end: 14,
        captions: [row],
        captionVariants: {
          'id': [row]
        },
        captionLanguage: 'id');
    final timeline = Timeline.fromClip(clip: clip, sourcePath: 'source.mp4');
    timeline.trackOf('video')!.items.first.framing = {
      'keyframes': [
        {'time': 0.0, 'x': 0.0, 'y': .5},
        {'time': 4.0, 'x': 1.0, 'y': .5}
      ]
    };
    clip.timeline = timeline.toJson();
    final part = sliceClip(Clip.fromJson(clip.toJson()), 12, 14, 1);
    expect(part.captionLanguage, 'id');
    expect(part.captionVariants['id']!.single['end'], 1);
    expect(part.captions.single['words'][0]['start'], 0);
    expect(
        Timeline.fromJson(part.timeline!)
            .trackOf('video')!
            .items
            .first
            .framing['keyframes'][0]['x'],
        .5);
  });
  test('Podcast ranks a complete answer above an advertisement', () {
    final result = CreatorTools.podcast([
      {
        'start': 0.0,
        'end': 15.0,
        'text': 'Sponsor kami. Kode promo dan diskon di link di bio.'
      },
      {
        'start': 15.0,
        'end': 45.0,
        'text': 'Subscribe sekarang untuk promo code.'
      },
      {
        'start': 50.0,
        'end': 60.0,
        'text': 'Kenapa kamu akhirnya belajar dari kesalahan?'
      },
      {
        'start': 60.0,
        'end': 85.0,
        'text':
            'Dulu saya pernah gagal. Ternyata rahasia itu adalah pengalaman.'
      },
      {
        'start': 85.0,
        'end': 100.0,
        'text': 'Intinya, pelajaran ini memberi solusi.'
      },
    ], 100, 1);
    expect(result.single['start'], 50);
    expect(result.single['end'], 100);
    expect(result.single['reason'], contains('tanya-jawab'));
  });
  test('Per-word style and keyframes survive serialization and reach renderer',
      () {
    final c = Caption(0, 2, 'Halo dunia', [
      {
        'word': 'Halo',
        'start': 0.0,
        'end': .7,
        'style': {'font': 'Anton', 'color': '#12ab34', 'bold': true}
      },
      {
        'word': 'dunia',
        'start': 1.0,
        'end': 2.0,
        'style': {'animation': 'type'}
      },
    ], {
      'x': .5,
      'y': .7,
      'size': 72
    });
    final ass = SubtitleBuilder.toAss([Caption.fromJson(c.toJson())]);
    expect(ass, contains(r'\fnAnton'));
    expect(ass, contains(r'\c&H34ab12&'));
    expect(ass, contains(r'\t(1000,1001,\alpha&H00&)'));
    final item =
        TimelineItem(id: 'v', start: 0, end: 2, crop: 'manual', framing: {
      'zoom': 1,
      'keyframes': [
        {'time': 0, 'x': .2, 'y': .5},
        {'time': 2, 'x': .8, 'y': .5}
      ]
    });
    final f = CreatorTools.cropFilter(
        TimelineItem.fromJson(item.toJson()).framing, 1920, 1080, 1080, 1920);
    expect(f, contains('crop=606:1080'));
    expect(f, contains('if(lt(t,2.0)'));
    expect(f, contains('max(0,min(1314'));
  });
  test('True word timestamps are kept inside grouped captions', () {
    final rows = SubtitleBuilder.captionsFromSegments([
      {
        'start': 0.0,
        'end': 4.0,
        'text': 'Halo dunia',
        'words': [
          {'word': 'Halo', 'start': .2, 'end': .8},
          {'word': 'dunia', 'start': 1.4, 'end': 2.0}
        ]
      }
    ]);
    expect(rows.first.words.first['start'], .2);
    expect(rows.last.words.last['end'], 2.0);
  });
}
