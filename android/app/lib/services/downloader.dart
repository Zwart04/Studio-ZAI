import 'dart:io';

import 'package:http/http.dart' as http;
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
  ) async {
    outDir.createSync(recursive: true);
    if (looksLikeMediaFile(url)) {
      return _downloadDirect(url, outDir, onProgress);
    }
    if (isYoutube(url)) {
      return _downloadYoutube(url, outDir, onProgress);
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

  static Future<File> _downloadYoutube(
    String url,
    Directory outDir,
    void Function(double, String) onProgress,
  ) async {
    final youtube = YoutubeExplode();
    try {
      onProgress(3, 'membaca info video');
      final video = await youtube.videos.get(url);
      final manifest = await youtube.videos.streamsClient.getManifest(video.id);
      if (manifest.muxed.isEmpty) {
        throw Exception('Tidak ada stream video+audio untuk video ini.');
      }
      // Muxed streams already carry audio, so no remux step is needed.
      final stream = manifest.muxed.withHighestBitrate();
      final target = File('${outDir.path}/${_safeName(video.title)}.mp4');
      final sink = target.openWrite();
      var received = 0;
      final total = stream.size.totalBytes;
      await for (final chunk in youtube.videos.streamsClient.get(stream)) {
        sink.add(chunk);
        received += chunk.length;
        if (total > 0) onProgress(5 + received / total * 93, 'mengunduh video');
      }
      await sink.flush();
      await sink.close();
      onProgress(100, 'selesai');
      return target;
    } on YoutubeExplodeException catch (error) {
      throw Exception('YouTube menolak permintaan (${error.message}). Coba lagi nanti.');
    } finally {
      youtube.close();
    }
  }

  static String _safeName(String input) {
    final cleaned = input.replaceAll(RegExp(r'[<>:"/\\|?*\x00-\x1f]'), '_').trim();
    return cleaned.length > 70 ? cleaned.substring(0, 70) : cleaned;
  }
}
