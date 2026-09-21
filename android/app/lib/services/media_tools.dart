import 'dart:io';
import 'dart:typed_data';

import 'package:ffmpeg_kit_flutter_new/ffmpeg_kit.dart';
import 'package:ffmpeg_kit_flutter_new/ffprobe_kit.dart';
import 'package:ffmpeg_kit_flutter_new/return_code.dart';

/// FFmpeg/FFprobe helpers running fully on-device (ffmpeg-kit maintained fork).
class MediaTools {
  static Future<bool> _run(String command) async {
    final session = await FFmpegKit.execute(command);
    final code = await session.getReturnCode();
    return ReturnCode.isSuccess(code);
  }

  static String _quote(String path) => "'${path.replaceAll("'", r"'\''")}'";

  /// Duration in seconds of any media file.
  static Future<double> duration(String path) async {
    final session = await FFprobeKit.getMediaInformation(path);
    final information = session.getMediaInformation();
    final raw = information?.getDuration();
    return double.tryParse(raw ?? '0') ?? 0;
  }

  static Future<Map<String, int>> resolution(String path) async {
    final session = await FFprobeKit.getMediaInformation(path);
    final streams = session.getMediaInformation()?.getStreams() ?? [];
    for (final stream in streams) {
      if (stream.getType() == 'video') {
        return {
          'width': int.tryParse(stream.getWidth()?.toString() ?? '0') ?? 0,
          'height': int.tryParse(stream.getHeight()?.toString() ?? '0') ?? 0,
        };
      }
    }
    return {'width': 0, 'height': 0};
  }

  /// Extract 16 kHz mono PCM used by ASR and the loudness heuristic.
  static Future<File> extractAudio(String input, String outputWav) async {
    final ok = await _run(
      '-y -i ${_quote(input)} -vn -ac 1 -ar 16000 -acodec pcm_s16le ${_quote(outputWav)}',
    );
    if (!ok) throw Exception('Gagal mengekstrak audio.');
    return File(outputWav);
  }

  static String cropFilter(String mode, int width, int height) {
    const target = 9 / 16;
    if (mode == 'none') return 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2';
    final cropWidth = (height * target).round() & ~1;
    final cropHeight = height & ~1;
    final x = ((width - cropWidth) / 2).round().clamp(0, width);
    final y = ((height - cropHeight) / 2).round().clamp(0, height);
    if (mode == 'blur') {
      return 'split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,'
          'crop=1080:1920,gblur=sigma=24[bgb];[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fgs];'
          '[bgb][fgs]overlay=(W-w)/2:(H-h)/2';
    }
    if (cropWidth >= width) {
      return 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2';
    }
    return 'crop=$cropWidth:$cropHeight:$x:$y,scale=1080:1920,setsar=1';
  }

  static Future<String> renderClip({
    required String input,
    required String output,
    required double start,
    required double end,
    required String crop,
    required int width,
    required int height,
    String? subtitlesPath,
    String audioMode = 'original',
    String? voicePath,
    double originalVolume = 0.25,
  }) async {
    final filter = cropFilter(crop, width, height);
    final complex = filter.contains(';');
    final duration = (end - start).clamp(0.5, 3600.0);

    final buffer = StringBuffer('-y -ss ${start.toStringAsFixed(3)} -t ${duration.toStringAsFixed(3)} -i ${_quote(input)}');
    if (voicePath != null && audioMode != 'original') {
      buffer.write(' -i ${_quote(voicePath)}');
    }

    final videoChain = StringBuffer();
    if (complex) {
      videoChain.write(filter.replaceAll('[bgb][fgs]overlay=(W-w)/2:(H-h)/2', '[bgb][fgs]overlay=(W-w)/2:(H-h)/2[vsrc]'));
      videoChain.write(subtitlesPath != null
          ? ';[vsrc]subtitles=${_quote(subtitlesPath)}[v]'
          : '');
    } else {
      videoChain.write('[0:v]$filter');
      if (subtitlesPath != null) {
        videoChain.write(',subtitles=${_quote(subtitlesPath)}');
      }
      videoChain.write('[v]');
    }

    if (voicePath != null && audioMode == 'mix') {
      videoChain.write(
        ';[0:a]volume=${originalVolume.toStringAsFixed(3)}[oa];[1:a]volume=1.0[va];'
        '[oa][va]amix=inputs=2:duration=first:normalize=0[a]',
      );
      buffer.write(' -filter_complex "${videoChain.toString()}" -map "[v]" -map "[a]"');
    } else if (voicePath != null) {
      buffer.write(' -filter_complex "${videoChain.toString()}" -map "[v]" -map "1:a"');
    } else {
      buffer.write(' -filter_complex "${videoChain.toString()}" -map "[v]" -map "0:a?"');
    }

    buffer.write(' -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart ${_quote(output)}');
    final ok = await _run(buffer.toString());
    if (!ok) throw Exception('Render klip gagal.');
    return output;
  }

  static Future<String> concat(List<String> inputs, String output) async {
    if (inputs.isEmpty) throw Exception('Tidak ada klip untuk digabung.');
    if (inputs.length == 1) {
      File(inputs.first).copySync(output);
      return output;
    }
    final buffer = StringBuffer();
    for (final input in inputs) {
      buffer.write('-i ${_quote(input)} ');
    }
    final streams = List.generate(inputs.length, (i) => '[$i:v][$i:a]').join();
    buffer.write('-filter_complex "${streams}concat=n=${inputs.length}:v=1:a=1[v][a]" '
        '-map "[v]" -map "[a]" -c:v libx264 -preset veryfast -crf 21 -c:a aac ${_quote(output)}');
    final ok = await _run(buffer.toString());
    if (!ok) throw Exception('Gagal menggabungkan klip.');
    return output;
  }

  static Future<String> thumbnail(String input, String output, double at) async {
    await _run('-y -ss ${at.toStringAsFixed(3)} -i ${_quote(input)} -frames:v 1 -q:v 3 ${_quote(output)}');
    return output;
  }

  /// Parse a 16-bit mono WAV (as produced by [extractAudio]) into float samples.
  static Float32List readWavSamples(String path) {
    final bytes = File(path).readAsBytesSync();
    if (bytes.length < 44) return Float32List(0);
    var offset = 12;
    while (offset + 8 < bytes.length) {
      final chunkId = String.fromCharCodes(bytes.sublist(offset, offset + 4));
      final chunkSize = ByteData.sublistView(bytes, offset + 4, offset + 8).getUint32(0, Endian.little);
      if (chunkId == 'data') {
        final start = offset + 8;
        final end = (start + chunkSize).clamp(0, bytes.length);
        final data = ByteData.sublistView(bytes, start, end);
        final count = (end - start) ~/ 2;
        final samples = Float32List(count);
        for (var i = 0; i < count; i++) {
          samples[i] = data.getInt16(i * 2, Endian.little) / 32768.0;
        }
        return samples;
      }
      offset += 8 + chunkSize + (chunkSize.isOdd ? 1 : 0);
    }
    return Float32List(0);
  }

  static Future<void> writeWav(String path, Float32List samples, int sampleRate) async {
    final data = ByteData(samples.length * 2);
    for (var i = 0; i < samples.length; i++) {
      final value = (samples[i].clamp(-1.0, 1.0) * 32767).round();
      data.setInt16(i * 2, value, Endian.little);
    }
    final header = ByteData(44);
    header.setUint32(0, 0x52494646, Endian.big); // RIFF
    header.setUint32(4, 36 + data.lengthInBytes, Endian.little);
    header.setUint32(8, 0x57415645, Endian.big); // WAVE
    header.setUint32(12, 0x666d7420, Endian.big); // fmt
    header.setUint32(16, 16, Endian.little);
    header.setUint16(20, 1, Endian.little);
    header.setUint16(22, 1, Endian.little);
    header.setUint32(24, sampleRate, Endian.little);
    header.setUint32(28, sampleRate * 2, Endian.little);
    header.setUint16(32, 2, Endian.little);
    header.setUint16(34, 16, Endian.little);
    header.setUint32(36, 0x64617461, Endian.big); // data
    header.setUint32(40, data.lengthInBytes, Endian.little);

    final file = File(path);
    file.parent.createSync(recursive: true);
    final sink = file.openSync(mode: FileMode.write);
    sink.writeFromSync(header.buffer.asUint8List());
    sink.writeFromSync(data.buffer.asUint8List());
    sink.closeSync();
  }
}
