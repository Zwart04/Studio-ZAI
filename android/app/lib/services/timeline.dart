// Model editor timeline multi-track — cermin core/studiozai/pipeline/timeline.py.
//
// Empat track: video (satu item sumber), media (overlay gambar/video),
// teks (template tipografi) dan audio (musik tambahan). Posisi x/y berupa rasio
// 0..1 terhadap kanvas supaya tetap sama di resolusi apa pun.

import '../models.dart';

class TimelineItem {
  TimelineItem({
    required this.id,
    required this.start,
    required this.end,
    this.src = '',
    this.srcStart = 0,
    this.type = 'image',
    this.text = '',
    this.template = 'clean',
    this.x = 0.5,
    this.y = 0.5,
    this.scale = 0.6,
    this.gain = 1.0,
    this.crop = 'center',
    this.canvas = 'portrait',
  });

  String id;
  double start;
  double end;
  String src;
  double srcStart;
  String type; // image | video (track media), audio (track audio)
  String text;
  String template;
  double x;
  double y;
  double scale;
  double gain;
  String crop;
  String canvas;

  double get duration => (end - start).clamp(0, double.infinity).toDouble();

  TimelineItem copy() => TimelineItem(
        id: id,
        start: start,
        end: end,
        src: src,
        srcStart: srcStart,
        type: type,
        text: text,
        template: template,
        x: x,
        y: y,
        scale: scale,
        gain: gain,
        crop: crop,
        canvas: canvas,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'start': start,
        'end': end,
        'src': src,
        'srcStart': srcStart,
        'type': type,
        'text': text,
        'template': template,
        'x': x,
        'y': y,
        'scale': scale,
        'gain': gain,
        'crop': crop,
        'canvas': canvas,
      };

  static TimelineItem fromJson(Map<String, dynamic> json) => TimelineItem(
        id: json['id'] as String? ?? 'item',
        start: (json['start'] as num?)?.toDouble() ?? 0,
        end: (json['end'] as num?)?.toDouble() ?? 0,
        src: json['src'] as String? ?? '',
        srcStart: (json['srcStart'] as num?)?.toDouble() ?? 0,
        type: json['type'] as String? ?? 'image',
        text: json['text'] as String? ?? '',
        template: json['template'] as String? ?? 'clean',
        x: (json['x'] as num?)?.toDouble() ?? 0.5,
        y: (json['y'] as num?)?.toDouble() ?? 0.5,
        scale: (json['scale'] as num?)?.toDouble() ?? 0.6,
        gain: (json['gain'] as num?)?.toDouble() ?? 1.0,
        crop: json['crop'] as String? ?? 'center',
        canvas: json['canvas'] as String? ?? 'portrait',
      );
}

class TimelineTrack {
  TimelineTrack({required this.id, required this.kind, List<TimelineItem>? items})
      : items = items ?? <TimelineItem>[];

  String id;
  String kind; // video | media | text | audio
  List<TimelineItem> items;

  Map<String, dynamic> toJson() => {
        'id': id,
        'kind': kind,
        'items': items.map((item) => item.toJson()).toList(),
      };

  static TimelineTrack fromJson(Map<String, dynamic> json) => TimelineTrack(
        id: json['id'] as String? ?? 'track',
        kind: json['kind'] as String? ?? 'media',
        items: (json['items'] as List? ?? const [])
            .map((entry) => TimelineItem.fromJson(Map<String, dynamic>.from(entry as Map)))
            .toList(),
      );
}

class Timeline {
  Timeline({List<TimelineTrack>? tracks, this.version = 1}) : tracks = tracks ?? <TimelineTrack>[];

  int version;
  List<TimelineTrack> tracks;

  TimelineTrack? trackOf(String kind) {
    for (final track in tracks) {
      if (track.kind == kind) return track;
    }
    return null;
  }

  double get duration {
    var longest = 0.0;
    for (final track in tracks) {
      for (final item in track.items) {
        if (item.end > longest) longest = item.end;
      }
    }
    return longest;
  }

  Map<String, dynamic> toJson() => {
        'version': version,
        'duration': duration,
        'tracks': tracks.map((track) => track.toJson()).toList(),
      };

  static Timeline fromJson(Map<String, dynamic> json) => Timeline(
        version: (json['version'] as num?)?.toInt() ?? 1,
        tracks: (json['tracks'] as List? ?? const [])
            .map((entry) => TimelineTrack.fromJson(Map<String, dynamic>.from(entry as Map)))
            .toList(),
      );

  /// Timeline awal untuk sebuah klip: satu item video + track kosong lainnya.
  static Timeline fromClip({required Clip clip, required String sourcePath}) {
    return Timeline(tracks: [
      TimelineTrack(id: 'v1', kind: 'video', items: [
        TimelineItem(
          id: 'v0',
          start: 0,
          end: clip.duration <= 0 ? 1 : clip.duration,
          src: sourcePath,
          srcStart: clip.start,
          type: 'video',
          crop: clip.crop,
          canvas: clip.canvas,
        ),
      ]),
      TimelineTrack(id: 'm1', kind: 'media'),
      TimelineTrack(id: 't1', kind: 'text'),
      TimelineTrack(id: 'a1', kind: 'audio'),
    ]);
  }
}
