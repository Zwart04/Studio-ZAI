import '../models.dart';
import 'timeline.dart';
import 'creator_tools.dart';

/// Slice an edited clip without changing its saved source or subtitle style.
Clip sliceClip(Clip original, double start, double end, int index) {
  if (start < original.start || end > original.end || end - start < .5) {
    throw ArgumentError('Rentang potong tidak valid');
  }
  final clip = Clip.fromJson(original.toJson());
  final offset = start - original.start, length = end - start;
  clip.index = index;
  clip.start = start;
  clip.end = end;
  clip.status = 'draft';
  clip.files = {};
  clip.captions = CreatorTools.trimRows(original.captions, offset, length);
  clip.captionVariants = original.captionVariants.map((lang, rows) =>
      MapEntry(lang, CreatorTools.trimRows(rows, offset, length)));
  if (original.timeline != null) {
    final timeline = Timeline.fromJson(original.timeline!);
    for (final track in timeline.tracks) {
      if (track.kind == 'video') {
        for (final item in track.items) {
          item.start = 0;
          item.end = length;
          item.srcStart = start;
          item.framing = CreatorTools.trimFraming(item.framing, offset, length);
        }
      } else {
        track.items = track.items
            .where((i) => i.end > offset && i.start < offset + length)
            .map((i) {
          final shift = (offset - i.start).clamp(0.0, double.infinity);
          i.srcStart += shift;
          i.start = (i.start - offset).clamp(0.0, length);
          i.end = (i.end - offset).clamp(0.0, length);
          return i;
        }).toList();
      }
    }
    clip.timeline = timeline.toJson();
  }
  return clip;
}
