import 'dart:io';
import 'dart:isolate';
import 'dart:math' as math;
import 'dart:typed_data';

import '../models.dart';
import 'creator_tools.dart';
import 'media_tools.dart';
import 'wav_chunks.dart';
import 'model_manager.dart';
import 'speech.dart';
import 'subtitle_builder.dart';
import 'timeline.dart';
import 'timeline_render.dart';

class ClipCandidate {
  ClipCandidate(this.start, this.end, this.score, this.reason,
      [this.title = '']);

  final double start;
  final double end;
  final double score;
  final String reason;
  final String title;

  double get duration => end - start;
}

/// Auto-clip pipeline for Android: audio → transcript → scoring → render.
class Pipeline {
  Pipeline(
      {required this.models, required this.speech, required this.projectDir});

  final ModelManager models;
  final SpeechService speech;
  final Directory projectDir;

  static const hopSeconds = 0.5;
  static const weightLoudness = 0.55;
  static const weightDensity = 0.35;
  static const weightSilence = 0.10;
  static const _ordinal =
      r'(?:pertama|kedua|ketiga|keempat|kelima|keenam|ketujuh|kedelapan|kesembilan|kesepuluh|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|berikutnya|selanjutnya|terakhir|ke[\s-]?\d+|[1-9]\d?)';

  /// Cues at the start of an utterance indicate a new product or review topic.
  /// Keeping the whole topic avoids starting a clip halfway through a demo.
  static bool _topicStarts(String text) {
    final opening =
        text.trim().toLowerCase().split(RegExp(r'\s+')).take(12).join(' ');
    return RegExp(
      r'^(?:(?:nah|oke|jadi|lalu|dan)\s+){0,2}(?:'
      r'(?:yang|speaker|produk|barang|nomor|number|urutan)\s+'
      '$_ordinal'
      r'|(?:sekarang|selanjutnya|berikutnya)\s+(?:(?:yang\s+)?'
      '$_ordinal'
      r'|kita\s+(?:bahas|review|ke))'
      r'|(?:first|second|third|next)\s+(?:speaker|product|one))',
    ).hasMatch(opening);
  }

  static List<List<double>> _speechWindows(
      List<TranscriptSegment> segments, double duration, double maxLength) {
    final ordered = [...segments]..sort((a, b) => a.start.compareTo(b.start));
    final windows = <List<double>>[];
    if (ordered.isEmpty) return windows;
    final hasTopics = ordered.any((segment) => _topicStarts(segment.text));
    var first = 0;
    for (var i = 1; i < ordered.length; i++) {
      final length = ordered[i].end - ordered[first].start;
      final gap = ordered[i].start - ordered[i - 1].end;
      final newTopic = _topicStarts(ordered[i].text);
      final naturalPause = !hasTopics &&
          gap >= 4.0 &&
          ordered[i - 1].end - ordered[first].start >= 45;
      if (newTopic || naturalPause || length > maxLength) {
        final start = ordered[first].start.clamp(0.0, duration);
        final end = ordered[i - 1].end.clamp(0.0, duration);
        final isIntro =
            newTopic && first == 0 && !_topicStarts(ordered[first].text);
        if (!isIntro && end - start >= 3) windows.add([start, end]);
        first = i;
      }
    }
    final start = ordered[first].start.clamp(0.0, duration);
    final end = ordered.last.end.clamp(0.0, duration);
    if (end - start >= 3) windows.add([start, end]);
    return windows;
  }

  static List<List<double>> _acousticWindows(
      double duration, List<List<double>> silences, double maxLength) {
    if (duration <= 0) return const [];
    final breaks = <double>[0];
    for (final silence in silences) {
      if (silence[1] - silence[0] >= 0.5 && silence[1] < duration - 3) {
        breaks.add(silence[1]);
      }
    }
    breaks.add(duration);
    final windows = <List<double>>[];
    var start = 0.0;
    for (final point in breaks.skip(1)) {
      if (point - start < 50 && point < duration) continue;
      if (point - start > maxLength) {
        while (point - start > maxLength) {
          final end = start + maxLength;
          windows.add([start, end]);
          start = end;
        }
      }
      if (point - start >= 3) {
        windows.add([start, point]);
        start = point;
      }
    }
    if (windows.isEmpty) windows.add([0, duration]);
    return windows;
  }

  Directory get workDir {
    final dir = Directory('${projectDir.path}/work');
    if (!dir.existsSync()) dir.createSync(recursive: true);
    return dir;
  }

  Directory clipDir(int index) {
    final dir = Directory('${projectDir.path}/clips/$index');
    if (!dir.existsSync()) dir.createSync(recursive: true);
    return dir;
  }

  // ------------------------------------------------------------------ audio analysis

  static List<double> rmsEnvelope(Float32List samples, int sampleRate) {
    final hop = (sampleRate * hopSeconds).round();
    if (samples.isEmpty || hop <= 0) return const [];
    final frames = samples.length ~/ hop;
    final rms = List<double>.filled(frames, 0);
    for (var frame = 0; frame < frames; frame++) {
      var sum = 0.0;
      final offset = frame * hop;
      for (var i = 0; i < hop; i++) {
        final value = samples[offset + i];
        sum += value * value;
      }
      rms[frame] = math.sqrt(sum / hop + 1e-12);
    }
    return rms;
  }

  /// [start, end] pairs of silence longer than [minSilence] seconds.
  static List<List<double>> silenceIntervals(
    Float32List samples,
    int sampleRate, {
    double thresholdDb = -38,
    double minSilence = 0.4,
    List<double>? envelope,
  }) {
    final rms = envelope ?? rmsEnvelope(samples, sampleRate);
    if (rms.isEmpty) return const [];
    final peak = rms.reduce(math.max);
    final intervals = <List<double>>[];
    double? start;
    for (var i = 0; i < rms.length; i++) {
      final db = 20 * (math.log(math.max(rms[i], 1e-9)) / math.ln10) -
          20 * (math.log(math.max(peak, 1e-9)) / math.ln10);
      final silent = db < thresholdDb;
      if (silent && start == null) {
        start = i * hopSeconds;
      } else if (!silent && start != null) {
        if (i * hopSeconds - start >= minSilence) {
          intervals.add([start, i * hopSeconds]);
        }
        start = null;
      }
    }
    if (start != null && rms.length * hopSeconds - start >= minSilence) {
      intervals.add([start, rms.length * hopSeconds]);
    }
    return intervals;
  }

  static double _overlap(
      List<List<double>> intervals, double start, double end) {
    var total = 0.0;
    for (final interval in intervals) {
      total += math.max(
          0.0, math.min(interval[1], end) - math.max(interval[0], start));
    }
    return total;
  }

  /// Pick top-N non-overlapping clips using loudness, speech density and silence.
  static List<ClipCandidate> pickClips({
    required Float32List samples,
    required int sampleRate,
    required double duration,
    List<double>? envelope,
    List<TranscriptSegment> segments = const [],
    int count = 5,
    double minLength = 8,
    double maxLength = 330,
  }) {
    count = CreatorTools.autoCount(duration, count);
    final rms = envelope ?? rmsEnvelope(samples, sampleRate);
    final silences = silenceIntervals(samples, sampleRate, envelope: rms);
    final windows = _speechWindows(segments, duration, maxLength);
    if (windows.isEmpty) {
      windows.addAll(
          _acousticWindows(duration, silences, math.min(maxLength, 120)));
    }
    windows.removeWhere((w) => w[1] - w[0] < math.min(minLength, duration));
    if (windows.isEmpty && duration >= 1) {
      windows.add([0, math.min(duration, maxLength)]);
    }
    final peak = rms.isEmpty ? 1.0 : rms.reduce(math.max);
    final densities = windows.map((w) {
      final words = segments
          .where((s) => s.end > w[0] && s.start < w[1])
          .fold<int>(0, (sum, s) => sum + s.text.split(' ').length);
      return words / math.max(1.0, w[1] - w[0]);
    }).toList();
    final peakDensity = densities.isEmpty ? 0.0 : densities.reduce(math.max);

    final scored = <List<double>>[];
    final reasons = <String>[];
    for (var i = 0; i < windows.length; i++) {
      final window = windows[i];
      var loudness = 0.0;
      if (rms.isNotEmpty) {
        final first = (window[0] / hopSeconds).floor().clamp(0, rms.length - 1);
        final last = (window[1] / hopSeconds).ceil().clamp(0, rms.length);
        var sum = 0.0;
        var n = 0;
        for (var f = first; f < last; f++) {
          sum += rms[f];
          n++;
        }
        loudness = n == 0 ? 0 : (sum / n) / math.max(peak, 1e-9);
      }
      final density = peakDensity == 0 ? 0.0 : densities[i] / peakDensity;
      final silenceRatio = (_overlap(silences, window[0], window[1]) /
              math.max(1.0, window[1] - window[0]))
          .clamp(0.0, 1.0);
      final score = weightLoudness * loudness +
          weightDensity * density +
          weightSilence * (1 - silenceRatio);
      scored.add([window[0], window[1], score]);
      reasons.add('loudness ${loudness.toStringAsFixed(2)}'
          '${density > 0 ? ', kepadatan ${density.toStringAsFixed(2)}' : ''}'
          '${silenceRatio > 0 ? ', sunyi ${(silenceRatio * 100).round()}%' : ''}');
    }

    final order = List.generate(scored.length, (i) => i)
      ..sort((a, b) => scored[b][2] == scored[a][2]
          ? scored[a][0].compareTo(scored[b][0])
          : scored[b][2].compareTo(scored[a][2]));

    final chosen = <List<double>>[];
    final chosenReasons = <String>[];
    for (final index in order) {
      if (chosen.length >= count) break;
      final candidate = scored[index];
      final overlaps =
          chosen.any((c) => _overlap([c], candidate[0], candidate[1]) > 1.0);
      if (overlaps) continue;
      chosen.add(candidate);
      chosenReasons.add(reasons[index]);
    }

    final result = <ClipCandidate>[];
    final pairs = List.generate(chosen.length, (i) => i)
      ..sort((a, b) => chosen[a][0].compareTo(chosen[b][0]));
    for (final index in pairs) {
      final window = chosen[index];
      result.add(
          ClipCandidate(window[0], window[1], window[2], chosenReasons[index]));
    }
    return result;
  }

  static Future<List<ClipCandidate>> pickClipsFromWav(String path,
          double duration, List<TranscriptSegment> segments, int count) =>
      Isolate.run(() {
        final envelope = <double>[];
        for (final samples in readWavChunks(path, sampleCount: 8000)) {
          envelope.addAll(rmsEnvelope(samples, 16000));
        }
        return pickClips(
            samples: Float32List(0),
            sampleRate: 16000,
            duration: duration,
            segments: segments,
            count: count,
            envelope: envelope);
      });

  /// Last-resort selection when FFmpeg cannot extract audio from a source.
  /// This still creates editable clips from the video already on the device.
  static List<ClipCandidate> pickClipsWithoutAudio(
          double duration, int count) =>
      pickClips(
          samples: Float32List(0),
          sampleRate: 16000,
          duration: duration,
          count: count);

  /// Captions for a clip window, with clip-relative timings.
  static List<Caption> captionsForRange(
      List<TranscriptSegment> segments, double start, double end) {
    final rows = <Map<String, dynamic>>[];
    for (final segment in segments) {
      if (segment.end <= start || segment.start >= end) continue;
      rows.add({
        'start': math.max(0.0, segment.start - start),
        'end': math.min(end - start, segment.end - start),
        'text': segment.text,
        'words': segment.words
            .where(
                (w) => (w['end'] as num) > start && (w['start'] as num) < end)
            .map((w) => {
                  ...w,
                  'start': ((w['start'] as num) - start).clamp(0, end - start),
                  'end': ((w['end'] as num) - start).clamp(0, end - start)
                })
            .toList(),
      });
    }
    return SubtitleBuilder.captionsFromSegments(rows);
  }

  // ------------------------------------------------------------------ rendering

  /// Timeline klip: yang tersimpan kalau ada, kalau tidak disusun dari klip.
  Timeline timelineFor(Project project, Clip clip) {
    final saved = clip.timeline;
    if (saved != null && saved.isNotEmpty) return Timeline.fromJson(saved);
    return Timeline.fromClip(clip: clip, sourcePath: project.source);
  }

  /// Volume audio asli: penuh saat "original", dikecilkan saat dicampur,
  /// nol saat hanya narasi.
  static double _baseVolume(Clip clip) {
    if (clip.audioMode == 'original') return 1.0;
    if (clip.audioMode == 'voice') return 0.0;
    return clip.originalVolume;
  }

  /// Tulis berkas ASS (caption + item track teks) dan kembalikan path-nya.
  String? _writeAss(Clip clip, Directory directory, String stem, List<int> size,
      List<TimelineItem> textItems) {
    if (clip.captions.isEmpty && textItems.isEmpty) return null;
    final captions = clip.captions.map((c) => Caption.fromJson(c)).toList();
    final ass = File('${directory.path}/$stem.ass');
    ass.writeAsStringSync(SubtitleBuilder.toAss(
      captions,
      preset: clip.subtitlePreset,
      position: clip.subtitlePosition,
      width: size[0],
      height: size[1],
      textItems: textItems
          .map((item) => <String, dynamic>{
                'text': item.text,
                'template': item.template,
                'start': item.start,
                'end': item.end,
                'x': item.x,
                'y': item.y,
              })
          .toList(),
    ));
    File('${directory.path}/$stem.srt')
        .writeAsStringSync(SubtitleBuilder.toSrt(captions));
    return ass.path;
  }

  static List<int> _canvasOf(
      Timeline timeline, Clip clip, int width, int height) {
    final items = timeline.trackOf('video')?.items ?? const <TimelineItem>[];
    final canvas = items.isEmpty ? clip.canvas : items.first.canvas;
    return MediaTools.canvasSize(canvas, width, height);
  }

  Future<Clip> renderClip(
      Project project, Clip clip, void Function(double, String) onProgress,
      {String? canvasOverride}) async {
    if (clip.audioMode != 'original' &&
        (clip.files['voice'] == null ||
            !File(clip.files['voice']!).existsSync())) {
      throw Exception(
          'Buat narasi TTS terlebih dahulu sebelum memilih audio TTS.');
    }
    final directory = canvasOverride == null
        ? clipDir(clip.index)
        : (Directory(
            '${clipDir(clip.index).path}/exports/${DateTime.now().microsecondsSinceEpoch}_$canvasOverride')
          ..createSync(recursive: true));
    final resolution = await MediaTools.resolution(project.source);
    final sourceWidth = resolution['width'] ?? 0;
    final sourceHeight = resolution['height'] ?? 0;
    final timeline = timelineFor(project, clip);
    if (canvasOverride != null) {
      timeline.trackOf('video')!.items.first.canvas = canvasOverride;
    }
    final useTimeline = canvasOverride != null ||
        clip.timeline != null && clip.timeline!.isNotEmpty;

    final size = _canvasOf(timeline, clip, sourceWidth, sourceHeight);
    final textItems = timeline.trackOf('text')?.items ?? const <TimelineItem>[];
    final assPath = _writeAss(clip, directory, 'subs', size, textItems);

    final output =
        '${directory.path}/clip_${clip.index.toString().padLeft(3, '0')}.mp4';
    onProgress(20, 'merender klip ${clip.index + 1}');
    if (useTimeline) {
      await TimelineRender.renderClip(
        source: project.source,
        timeline: timeline,
        output: output,
        sourceWidth: sourceWidth,
        sourceHeight: sourceHeight,
        subtitlesPath: assPath,
        voicePath: clip.audioMode != 'original' ? clip.files['voice'] : null,
        originalVolume: _baseVolume(clip),
        voiceVolume: clip.voiceVolume,
      );
    } else {
      await MediaTools.renderClip(
        input: project.source,
        output: output,
        start: clip.start,
        end: clip.end,
        crop: clip.crop,
        canvas: clip.canvas,
        width: sourceWidth,
        height: sourceHeight,
        subtitlesPath: assPath,
        audioMode: clip.audioMode,
        voicePath: clip.files['voice'],
        originalVolume: clip.originalVolume,
      );
    }
    final thumb = '${directory.path}/thumb.jpg';
    await MediaTools.thumbnail(output, thumb, clip.duration / 2);
    clip.files = {
      ...clip.files,
      canvasOverride == null ? 'mp4' : 'mp4_$canvasOverride': output,
      canvasOverride == null ? 'thumb' : 'thumb_$canvasOverride': thumb,
      if (assPath != null) ...{
        canvasOverride == null ? 'ass' : 'ass_$canvasOverride': assPath,
        canvasOverride == null ? 'srt' : 'srt_$canvasOverride':
            assPath.replaceFirst(RegExp(r'\.ass$'), '.srt'),
      }
    };
    clip.status = 'rendered';
    onProgress(100, 'klip ${clip.index + 1} selesai');
    return clip;
  }

  /// Render draf cepat untuk pratinjau di editor (540x960, encoder ultrafast).
  Future<File> renderPreview(Project project, Clip clip,
      void Function(double, String) onProgress) async {
    final directory = clipDir(clip.index);
    final resolution = await MediaTools.resolution(project.source);
    final sourceWidth = resolution['width'] ?? 0;
    final sourceHeight = resolution['height'] ?? 0;
    final timeline = timelineFor(project, clip);
    final size = _canvasOf(timeline, clip, sourceWidth, sourceHeight);
    final textItems = timeline.trackOf('text')?.items ?? const <TimelineItem>[];
    final assPath = _writeAss(clip, directory, 'preview', size, textItems);

    final oldPreviews = directory
        .listSync()
        .whereType<File>()
        .where((f) =>
            f.uri.pathSegments.last.startsWith('preview-') &&
            f.path.endsWith('.mp4'))
        .toList()
      ..sort((a, b) => a.lastModifiedSync().compareTo(b.lastModifiedSync()));
    for (final old in oldPreviews.take(math.max(0, oldPreviews.length - 2))) {
      try {
        old.deleteSync();
      } on FileSystemException {/* Active player still owns it. */}
    }
    final output =
        '${directory.path}/preview-${DateTime.now().microsecondsSinceEpoch}.mp4';
    onProgress(10, 'menyiapkan pratinjau');
    await TimelineRender.renderPreview(
      source: project.source,
      timeline: timeline,
      output: output,
      sourceWidth: sourceWidth,
      sourceHeight: sourceHeight,
      subtitlesPath: assPath,
      voicePath: clip.audioMode != 'original' ? clip.files['voice'] : null,
      originalVolume: _baseVolume(clip),
    );
    onProgress(100, 'pratinjau siap');
    return File(output);
  }

  Future<File> export(
      Project project, void Function(double, String) onProgress) async {
    final inputs = project.clips
        .where((c) =>
            (c.files['mp4'] ?? '').isNotEmpty &&
            File(c.files['mp4']!).existsSync())
        .map((c) => c.files['mp4']!)
        .toList();
    if (inputs.isEmpty) throw Exception('Belum ada klip yang dirender.');
    final output = '${projectDir.path}/gabungan-${project.id}.mp4';
    onProgress(30, 'menggabungkan ${inputs.length} klip');
    await MediaTools.concat(inputs, output);
    onProgress(100, 'selesai');
    return File(output);
  }
}
