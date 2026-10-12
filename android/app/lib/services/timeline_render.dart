// Renderer timeline multi-track — cermin core/studiozai/pipeline/timeline.py.
//
// Hanya membangun graf FFmpeg. Teks (caption + item track teks) sudah
// dirangkum jadi satu berkas ASS oleh pemanggil, jadi di sini cukup satu filter
// `subtitles` — sama seperti versi desktop.

import 'dart:io';

import 'package:ffmpeg_kit_flutter_new/ffmpeg_kit.dart';
import 'package:ffmpeg_kit_flutter_new/return_code.dart';

import 'media_tools.dart';
import 'timeline.dart';

class TimelineRender {
  static String _quote(String path) => "'${path.replaceAll("'", r"'\''")}'";

  /// Bangun perintah ffmpeg lengkap untuk sebuah timeline.
  static Future<String> buildCommand({
    required String source,
    required Timeline timeline,
    required String output,
    required int sourceWidth,
    required int sourceHeight,
    String? subtitlesPath,
    String? voicePath,
    double originalVolume = 1.0,
    double voiceVolume = 1.0,
    double sourceOffset = 0.0,
  }) async {
    final videoItems =
        timeline.trackOf('video')?.items ?? const <TimelineItem>[];
    final base = videoItems.isEmpty ? null : videoItems.first;
    // Saat render dari segmen yang diunduh (mode online), file dimulai pada
    // [sourceOffset] sebelum timeline-nya; geser srcStart agar -ss akurat.
    final offset = (base?.srcStart ?? 0) - sourceOffset;
    var duration = (base?.end ?? 0) - (base?.start ?? 0);
    if (duration <= 0.2) duration = timeline.duration;
    if (duration <= 0.2) duration = 0.2;

    await MediaTools.prepareFonts();
    final crop = base?.crop ?? 'center';
    final canvas = base?.canvas ?? 'portrait';
    final size = MediaTools.canvasSize(canvas, sourceWidth, sourceHeight);
    final filter = MediaTools.cropFilter(
      crop,
      sourceWidth,
      sourceHeight,
      canvas: canvas,
      framing: base?.framing ?? {},
    );
    final complex = filter.contains(';');

    final buffer = StringBuffer()
      ..write(
        '-y -ss ${offset.toStringAsFixed(3)} -t ${duration.toStringAsFixed(3)} -i ${_quote(source)}',
      );

    final filters = <String>[];
    if (complex) {
      filters.add('[0:v]${filter.replaceAll("[vout]", "[vbase]")}');
    } else {
      filters.add('[0:v]$filter[vbase]');
    }
    var label = '[vbase]';
    var index = 1;

    // -------------------------------------------------------- media overlays
    for (final item
        in timeline.trackOf('media')?.items ?? const <TimelineItem>[]) {
      if (item.src.isEmpty ||
          item.end <= item.start ||
          !File(item.src).existsSync()) {
        continue;
      }
      if (item.type == 'video') {
        buffer.write(
          ' -ss ${item.srcStart.toStringAsFixed(3)} '
          '-t ${(item.end - item.start).toStringAsFixed(3)} -i ${_quote(item.src)}',
        );
      } else {
        buffer.write(
          ' -loop 1 -t ${duration.toStringAsFixed(3)} -i ${_quote(item.src)}',
        );
      }
      final width = (size[0] * item.scale.clamp(0.05, 1.0)).round();
      filters.add(
        '[$index:v]scale=${width < 2 ? 2 : width}:-2,format=rgba,colorchannelmixer=aa=${item.opacity.clamp(0, 1)}[s$index]',
      );
      filters.add(
        '$label[s$index]overlay='
        'x=(W-w)*${item.x.clamp(0.0, 1.0).toStringAsFixed(4)}:'
        'y=(H-h)*${item.y.clamp(0.0, 1.0).toStringAsFixed(4)}:'
        "enable='between(t,${item.start.toStringAsFixed(3)},${item.end.toStringAsFixed(3)})'"
        '[v$index]',
      );
      label = '[v$index]';
      index++;
    }

    // ---------------------------------------------------------------- audio
    final audioLabels = <String>[];
    if (await MediaTools.hasAudio(source)) {
      filters.add(
        '[0:a]volume=${originalVolume.clamp(0.0, 4.0).toStringAsFixed(3)}[abase]',
      );
      audioLabels.add('[abase]');
    }
    for (final item
        in timeline.trackOf('audio')?.items ?? const <TimelineItem>[]) {
      if (item.src.isEmpty || !File(item.src).existsSync()) continue;
      final start = item.start < 0 ? 0.0 : item.start;
      final length = item.end > item.start ? item.end - item.start : duration;
      buffer.write(' -i ${_quote(item.src)}');
      filters.add(
        '[$index:a]atrim=0:${length.toStringAsFixed(3)},asetpts=PTS-STARTPTS,'
        'volume=${item.gain.clamp(0.0, 4.0).toStringAsFixed(3)},'
        'adelay=${(start * 1000).round()}:all=1[a$index]',
      );
      audioLabels.add('[a$index]');
      index++;
    }
    if (voicePath != null && File(voicePath).existsSync()) {
      buffer.write(' -i ${_quote(voicePath)}');
      filters.add(
        '[$index:a]volume=${voiceVolume.clamp(0.0, 4.0).toStringAsFixed(3)}[a$index]',
      );
      audioLabels.add('[a$index]');
      index++;
    }

    final String audioMap;
    if (audioLabels.isEmpty) {
      audioMap = '0:a?';
    } else if (audioLabels.length == 1) {
      audioMap = audioLabels.first;
    } else {
      filters.add(
        '${audioLabels.join()}amix=inputs=${audioLabels.length}:duration=first:normalize=0[aaudio]',
      );
      audioMap = '[aaudio]';
    }

    // ----------------------------------------------------------------- teks
    if (subtitlesPath != null) {
      filters.add(
        '$label'
        '${MediaTools.subtitleFilter(subtitlesPath)}[vfinal]',
      );
      label = '[vfinal]';
    }

    buffer
      ..write(
        ' -filter_complex "${filters.join(';')}" -map "$label" -map "$audioMap"',
      )
      ..write(
        ' -c:a aac -b:a 256k -ar 48000 -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p',
      )
      ..write(
        ' -t ${duration.toStringAsFixed(3)} -movflags +faststart ${_quote(output)}',
      );
    return buffer.toString();
  }

  static Future<String> renderClip({
    required String source,
    required Timeline timeline,
    required String output,
    required int sourceWidth,
    required int sourceHeight,
    String? subtitlesPath,
    String? voicePath,
    double originalVolume = 1.0,
    double voiceVolume = 1.0,
    double sourceOffset = 0.0,
  }) async {
    final command = await buildCommand(
      source: source,
      timeline: timeline,
      output: output,
      sourceWidth: sourceWidth,
      sourceHeight: sourceHeight,
      subtitlesPath: subtitlesPath,
      voicePath: voicePath,
      originalVolume: originalVolume,
      voiceVolume: voiceVolume,
      sourceOffset: sourceOffset,
    );
    final session = await FFmpegKit.execute(command);
    final code = await session.getReturnCode();
    if (!ReturnCode.isSuccess(code)) {
      final logs = await session.getOutput();
      throw Exception(
        'Render timeline gagal. ${logs == null ? '' : logs.substring(logs.length > 300 ? logs.length - 300 : 0)}',
      );
    }
    return output;
  }

  /// Render draf cepat untuk pratinjau di editor.
  ///
  /// Sama seperti render biasa, hanya keluarannya diperkecil (`-s 540x960`) dan
  /// encoder dibuat paling cepat supaya terasa responsif di HP.
  static Future<String> renderPreview({
    required String source,
    required Timeline timeline,
    required String output,
    int sourceWidth = 1920,
    int sourceHeight = 1080,
    String? subtitlesPath,
    String? voicePath,
    double originalVolume = 1.0,
    double voiceVolume = 1.0,
    double sourceOffset = 0.0,
  }) async {
    final command = await buildCommand(
      source: source,
      timeline: timeline,
      output: output,
      sourceWidth: sourceWidth,
      sourceHeight: sourceHeight,
      subtitlesPath: subtitlesPath,
      voicePath: voicePath,
      originalVolume: originalVolume,
      voiceVolume: voiceVolume,
      sourceOffset: sourceOffset,
    );
    // `-s` adalah opsi keluaran dan tetap berlaku bersama -filter_complex,
    // jadi cukup memperkecil hasil akhir tanpa menyentuh graf filternya.
    final base = timeline.trackOf('video')?.items;
    final canvas =
        base == null || base.isEmpty ? 'portrait' : base.first.canvas;
    final size = MediaTools.canvasSize(canvas, sourceWidth, sourceHeight);
    final longest = size[0] > size[1] ? size[0] : size[1];
    final ratio = longest > 960 ? 960 / longest : 1.0;
    final w = ((size[0] * ratio) ~/ 2 * 2).clamp(2, 960);
    final h = ((size[1] * ratio) ~/ 2 * 2).clamp(2, 960);
    final preview = command.replaceFirst(
      '-c:v libx264 -preset veryfast -crf 21',
      '-s ${w}x$h -c:v libx264 -preset ultrafast -crf 30',
    );
    final session = await FFmpegKit.execute(preview);
    final code = await session.getReturnCode();
    if (!ReturnCode.isSuccess(code)) {
      throw Exception('Pratinjau gagal dirender.');
    }
    return output;
  }
}
