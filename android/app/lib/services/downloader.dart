import 'dart:async';
import 'dart:io';
import 'youtube_source.dart';

import 'package:http/http.dart' as http;
import 'package:ffmpeg_kit_flutter_new/ffmpeg_kit.dart';
import 'package:ffmpeg_kit_flutter_new/return_code.dart';
import 'package:youtube_explode_dart/youtube_explode_dart.dart';

/// Resolves and downloads media from a link.
///
/// Android supports two paths, both dependency-light and fully on-device:
///  1. direct media URL (mp4/mov/mkv/webm/mp3...) -> plain HTTP download
///  2. YouTube link (including Shorts) -> youtube_explode_dart, pure Dart
///
/// TikTok / Instagram links need yt-dlp, which currently only runs in the
/// desktop Studio ZAI app (the Android yt-dlp plugins do not build against
/// AGP 9 / Gradle 9 yet). Those links raise a clear, actionable error.
class Downloader {
  static bool isUrl(String value) =>
      value.startsWith('http://') || value.startsWith('https://');

  static bool isYoutube(String url) =>
      url.contains('youtube.com') || url.contains('youtu.be');

  static bool looksLikeMediaFile(String url) {
    final path = Uri.tryParse(url)?.path.toLowerCase() ?? '';
    for (final extension in const ['.mp4', '.mov', '.mkv', '.webm', '.m4v', '.mp3', '.m4a', '.wav']) {
      if (path.endsWith(extension)) return true;
    }
    return false;
  }

  static Future<File> download(
    String url,
    Directory outDir,
    void Function(double, String) onProgress,
    {String? audioLanguage, void Function(String)? onTitle}
  ) async {
    outDir.createSync(recursive: true);
    if (looksLikeMediaFile(url)) {
      return _downloadDirect(url, outDir, onProgress);
    }
    if (isYoutube(url)) {
      return _downloadYoutube(url, outDir, onProgress, audioLanguage: audioLanguage, onTitle: onTitle);
    }
    throw Exception(
      'Link ini butuh yt-dlp, yang untuk saat ini hanya jalan di aplikasi desktop '
      'Studio ZAI (TikTok/Instagram). Di HP kamu bisa: (1) tempel link file video '
      'langsung (.mp4), (2) pakai link YouTube, atau (3) unduh di desktop lalu '
      'pindahkan videonya ke HP.',
    );
  }

  // ------------------------------------------------------------------ direct

  static Future<File> _downloadDirect(
    String url,
    Directory outDir,
    void Function(double, String) onProgress,
  ) async {
    final segments = Uri.parse(url).pathSegments;
    final name = segments.isEmpty ? 'video-${DateTime.now().millisecondsSinceEpoch}.mp4' : segments.last;
    final target = File('${outDir.path}/$name');

    final response = await http.Request('GET', Uri.parse(url)).send();
    if (response.statusCode >= 400) {
      throw Exception('Unduhan gagal (HTTP ${response.statusCode}).');
    }
    final total = response.contentLength ?? 0;
    final sink = target.openWrite();
    var received = 0;
    await for (final chunk in response.stream) {
      sink.add(chunk);
      received += chunk.length;
      if (total > 0) onProgress(received / total * 100, 'mengunduh video');
    }
    await sink.flush();
    await sink.close();
    if (target.lengthSync() == 0) throw Exception('Berkas hasil unduhan kosong.');
    onProgress(100, 'selesai');
    return target;
  }

  // ----------------------------------------------------------------- youtube

  /// YouTube track IDs may include a regional tag and a track suffix (id.4).
  static bool matchesLanguage(String trackId, String language) =>
      trackId.toLowerCase().split(RegExp(r'[-_.]')).first == language.toLowerCase();

  static Future<File> _downloadYoutube(
    String url,
    Directory outDir,
    void Function(double, String) onProgress, {
    String? audioLanguage,
    void Function(String)? onTitle,
  }) async {
    final youtube = YoutubeExplode();
    final scratch = Directory('${outDir.path}/.download-${DateTime.now().microsecondsSinceEpoch}');
    try {
      scratch.createSync(recursive: true);
      onProgress(3, 'membaca info video');
      final manifest = await YoutubeSource.manifest(url,
        onStatus: (message) => onProgress(3, message));
      // Metadata is optional; stream extraction must not depend on a watch page.
      var title = VideoId.fromString(url).value;
      try {
        final video = await youtube.videos.get(url).timeout(const Duration(seconds: 12));
        title = video.title;
      } catch (_) {}
      onTitle?.call(title);
      final target = File('${outDir.path}/${_safeName(title)}.mp4');
      final selectedVideo = YoutubeSource.video(manifest);
      // Validate the selected language before transferring a large video.
      YoutubeSource.audio(manifest, audioLanguage);
      final v = File('${scratch.path}/video.mp4');
      final a = File('${scratch.path}/audio.m4a');
      await _saveStream(youtube, selectedVideo, v,
        (p, detail) => onProgress(5 + p * 0.65, 'Video 720p · $detail'));
      // Android YouTube stream URLs may be single-use. Get fresh audio URLs
      // after downloading the video instead of reusing the original manifest.
      final fresh = await YoutubeSource.manifest(url,
        onStatus: (message) => onProgress(70, message));
      final selectedAudio = YoutubeSource.audio(fresh, audioLanguage);
      await _saveStream(youtube, selectedAudio, a,
        (p, detail) => onProgress(70 + p * 0.23, 'Audio ${audioLanguage ?? "bawaan"} · $detail'));
      onProgress(94, 'Menggabungkan video dan audio');
      final session = await FFmpegKit.execute('-y -i "${v.path}" -i "${a.path}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -movflags +faststart "${target.path}"');
      if (!ReturnCode.isSuccess(await session.getReturnCode())) {
        if (target.existsSync()) target.deleteSync();
        throw Exception('Gagal menggabungkan track video dan audio.');
      }
      onProgress(100, 'selesai');
      return target;
    } on YoutubeExplodeException catch (error) {
      throw Exception('YouTube menolak permintaan (${error.message}). Coba lagi nanti.');
    } finally {
      youtube.close();
      if (scratch.existsSync()) scratch.deleteSync(recursive: true);
    }
  }

  static Future<void> _saveStream(YoutubeExplode youtube, StreamInfo stream, File target, void Function(double, String) progress) async {
    final sink = target.openWrite();
    var received = 0;
    var buffered = 0;
    final clock = Stopwatch()..start();
    var lastEmit = 0;
    try {
      await for (final chunk in YoutubeSource.bytes(stream).timeout(const Duration(seconds: 90))) {
        sink.add(chunk);
        received += chunk.length;
        buffered += chunk.length;
        if (buffered >= 1024 * 1024) { await sink.flush(); buffered = 0; }
        if (clock.elapsedMilliseconds - lastEmit >= 300 && stream.size.totalBytes > 0) {
          final speed = received / (clock.elapsedMilliseconds / 1000);
          final remaining = ((stream.size.totalBytes - received) / speed).ceil();
          progress(received / stream.size.totalBytes * 100,
            '${(received / 1048576).toStringAsFixed(1)}/${(stream.size.totalBytes / 1048576).toStringAsFixed(1)} MB · '
            '${(speed / 1048576).toStringAsFixed(1)} MB/s · sisa ${remaining ~/ 60}:${(remaining % 60).toString().padLeft(2, "0")}');
          lastEmit = clock.elapsedMilliseconds;
        }
      }
      await sink.flush();
    } finally { await sink.close(); }
    if (received == 0 || (stream.size.totalBytes > 0 && received != stream.size.totalBytes)) {
      throw Exception('Unduhan terputus. Periksa koneksi dan coba lagi.');
    }
  }

  static String _safeName(String input) {
    final cleaned = input.replaceAll(RegExp(r'[<>:"/\\|?*\x00-\x1f]'), '_').trim();
    return cleaned.length > 70 ? cleaned.substring(0, 70) : cleaned;
  }
}
