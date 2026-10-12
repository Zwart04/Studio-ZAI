import 'dart:async';
import 'dart:io';
import 'dart:math' as math;
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

  /// Judul aman untuk nama berkas. `VideoId.fromString` melempar
  /// [ArgumentError] untuk tautan tak dikenal — jangan biarkan itu
  /// menggagalkan unduhan; metadata judul diambil terpisah di bawah.
  static String _safeVideoId(String url) {
    try {
      return VideoId.fromString(url).value;
    } catch (_) {
      final last = Uri.tryParse(url)?.pathSegments.lastOrNull;
      if (last != null && last.isNotEmpty) return last;
      return 'video';
    }
  }

  static bool isYoutube(String url) {
    final host = Uri.tryParse(url)?.host.toLowerCase() ?? '';
    return host == 'youtu.be' ||
        host == 'youtube.com' ||
        host.endsWith('.youtube.com');
  }

  static bool _isSocialHost(String url) {
    final host = Uri.tryParse(url)?.host.toLowerCase() ?? '';
    return host == 'tiktok.com' ||
        host.endsWith('.tiktok.com') ||
        host == 'instagram.com' ||
        host.endsWith('.instagram.com');
  }

  static bool looksLikeMediaFile(String url) {
    final path = Uri.tryParse(url)?.path.toLowerCase() ?? '';
    for (final extension in const [
      '.mp4',
      '.mov',
      '.mkv',
      '.webm',
      '.m4v',
      '.mp3',
      '.m4a',
      '.wav'
    ]) {
      if (path.endsWith(extension)) return true;
    }
    return false;
  }

  static Future<File> download(
      String url, Directory outDir, void Function(double, String) onProgress,
      {String? audioLanguage, void Function(String)? onTitle}) async {
    outDir.createSync(recursive: true);
    if (looksLikeMediaFile(url)) {
      return _downloadDirect(url, outDir, onProgress);
    }
    if (isYoutube(url)) {
      return _downloadYoutube(url, outDir, onProgress,
          audioLanguage: audioLanguage, onTitle: onTitle);
    }
    if (_isSocialHost(url)) {
      throw UnsupportedError(
        'Link TikTok/Instagram belum bisa diunduh langsung di APK. '
        'Simpan videonya ke perangkat lalu pilih “Pilih video” untuk membuat '
        'klip secara lokal. Di desktop, Studio ZAI dapat mencoba link publiknya.',
      );
    }
    throw Exception(
      'Link ini bukan YouTube atau berkas video langsung. '
      'Pilih video yang sudah tersimpan di perangkat, atau tempel link berkas .mp4.',
    );
  }

  // ------------------------------------------------------------------ direct

  static Future<File> _downloadDirect(
    String url,
    Directory outDir,
    void Function(double, String) onProgress,
  ) async {
    final segments = Uri.parse(url).pathSegments;
    final name = segments.isEmpty
        ? 'video-${DateTime.now().millisecondsSinceEpoch}.mp4'
        : segments.last;
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
    if (target.lengthSync() == 0) {
      throw Exception('Berkas hasil unduhan kosong.');
    }
    onProgress(100, 'selesai');
    return target;
  }

  // ----------------------------------------------------------------- youtube

  /// YouTube track IDs may include a regional tag and a track suffix (id.4).
  static bool matchesLanguage(String trackId, String language) =>
      trackId.toLowerCase().split(RegExp(r'[-_.]')).first ==
      language.toLowerCase();

  static Future<File> _downloadYoutube(
    String url,
    Directory outDir,
    void Function(double, String) onProgress, {
    String? audioLanguage,
    void Function(String)? onTitle,
  }) async {
    final youtube = YoutubeExplode();
    final scratch = Directory(
        '${outDir.path}/.download-${DateTime.now().microsecondsSinceEpoch}');
    try {
      scratch.createSync(recursive: true);
      onProgress(3, 'membaca info video');
      final manifest = await YoutubeSource.manifest(url,
          onStatus: (message) => onProgress(3, message));
      // Metadata is optional; stream extraction must not depend on a watch page.
      var title = _safeVideoId(url);
      try {
        final video =
            await youtube.videos.get(url).timeout(const Duration(seconds: 12));
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
      await _saveStream(
          youtube,
          selectedAudio,
          a,
          (p, detail) => onProgress(
              70 + p * 0.23, 'Audio ${audioLanguage ?? "bawaan"} · $detail'));
      onProgress(94, 'Menggabungkan video dan audio');
      // AAC audio in a YouTube M4A is already MP4-compatible. Copy it bit for
      // bit so the 78-minute source is not needlessly compressed again before
      // clip rendering. Opus/WebM needs a single high-quality AAC conversion.
      final codec = selectedAudio.audioCodec.toLowerCase();
      final audioArgs = codec.contains('mp4a') || codec.contains('aac')
          ? '-c:a copy'
          : '-c:a aac -b:a 256k -ar 48000';
      final session = await FFmpegKit.execute(
          '-y -i "${v.path}" -i "${a.path}" -map 0:v:0 -map 1:a:0 -c:v copy $audioArgs -movflags +faststart "${target.path}"');
      if (!ReturnCode.isSuccess(await session.getReturnCode())) {
        if (target.existsSync()) target.deleteSync();
        throw Exception('Gagal menggabungkan track video dan audio.');
      }
      onProgress(100, 'selesai');
      return target;
    } on YoutubeExplodeException catch (error) {
      throw Exception(
          'YouTube menolak permintaan (${error.message}). Coba lagi nanti.');
    } finally {
      youtube.close();
      if (scratch.existsSync()) scratch.deleteSync(recursive: true);
    }
  }

  // ------------------------------------------------------------- online: audio
  /// Online-first import: unduh **audio saja** untuk transkrip dan pemilihan
  /// momen, jauh sebelum pun mengunduh sejumlah pun video.
  static Future<File> downloadAudio(
    String url,
    Directory outDir,
    void Function(double, String) onProgress, {
    String? audioLanguage,
    void Function(String)? onTitle,
  }) async {
    if (!isYoutube(url)) {
      throw UnsupportedError('downloadAudio hanya mendukung tautan YouTube.');
    }
    outDir.createSync(recursive: true);
    final youtube = YoutubeExplode();
    try {
      onProgress(3, 'membaca info video');
      final manifest = await YoutubeSource.manifest(url,
          onStatus: (message) => onProgress(3, message));
      final selectedAudio = YoutubeSource.audio(manifest, audioLanguage);
      onProgress(6, 'Audio ${audioLanguage ?? "bawaan"}');
      var title = _safeVideoId(url);
      try {
        final video =
            await youtube.videos.get(url).timeout(const Duration(seconds: 12));
        title = video.title;
      } catch (_) {}
      onTitle?.call(title);
      final ext = selectedAudio.container.name;
      final target = File('${outDir.path}/${_safeName(title)}-audio.$ext');
      await _saveStream(youtube, selectedAudio, target,
          (p, detail) => onProgress(6 + p * 0.86, 'Audio · $detail'));
      onProgress(100, 'selesai');
      return target;
    } on YoutubeExplodeException catch (error) {
      throw Exception(
          'YouTube menolak permintaan (${error.message}). Coba lagi nanti.');
    } finally {
      youtube.close();
    }
  }

  // ----------------------------------------------------- online: section clip
  /// Online render: unduh **hanya segmen HLS** yang menutupi [start, end].
  /// Mengembalikan berkas + [RemoteSegment.start] (timeline berkas dimulai di
  /// situ). Jika manifest tidak menyediakan HLS, fallback ke unduh video penuh
  /// (hasil tetap benar, hanya tidak section-only).
  static Future<RemoteSegment> downloadSection(
    String url,
    double start,
    double end,
    Directory outDir,
    void Function(double, String) onProgress, {
    int maxHeight = 720,
    // Berkas audio lengkap yang sudah ada (mode online selalu mengunduhnya
    // untuk transkrip): dipotong lokal agar segmen video HLS yang selalu
    // video-only ikut bersuara. Tanpa ini, preview/render online bisu.
    String? audioPath,
    String? audioLanguage,
  }) async {
    outDir.createSync(recursive: true);
    final youtube = YoutubeExplode();
    try {
      onProgress(3, 'membaca info video');
      final manifest = await YoutubeSource.manifest(url,
          onStatus: (message) => onProgress(3, message));
      final playlistUrl = YoutubeSource.hlsPlaylistUrl(manifest);
      if (playlistUrl == null) {
        final full = await download(
            url, outDir, (p, m) => onProgress(40 + p * 0.5, m),
            audioLanguage: audioLanguage);
        return RemoteSegment(full, 0.0);
      }
      final pad = 2.0;
      final double reqStart = start - pad < 0 ? 0.0 : start - pad;
      final reqEnd = end + pad;
      onProgress(10, 'memilih segmen HLS');
      final playlist = await _readPlaylist(playlistUrl);
      final parsed = _parseHls(playlist, playlistUrl);
      final chosen = _selectHlsSegment(parsed, reqStart, reqEnd);
      if (chosen.isEmpty) {
        throw StateError('Rentang yang diminta di luar durasi video.');
      }
      final segStart = chosen.first.start;
      final segEnd = chosen.last.end;
      final out = File(
          '${outDir.path}/section-${start.toStringAsFixed(0)}-${end.toStringAsFixed(0)}.mp4');
      final raw = File('${out.path}.raw.mp4');
      final sink = raw.openWrite();
      final client = http.Client();
      try {
        await _downloadHlsSegments(
            parsed, chosen, sink, client, (p, m) => onProgress(10 + p * 78, m));
      } finally {
        await sink.close();
        client.close();
      }
      onProgress(92, 'meremux segmen');
      if (await _muxSectionAudio(raw, out, audioPath, segStart, segEnd)) {
        if (await raw.exists()) await raw.delete();
        onProgress(100, 'selesai');
        return RemoteSegment(out, segStart);
      }
      await _remuxCopy(raw, out);
      if (await raw.exists()) await raw.delete();
      onProgress(100, 'selesai');
      return RemoteSegment(out, segStart);
    } on YoutubeExplodeException catch (error) {
      throw Exception(
          'YouTube menolak permintaan (${error.message}). Coba lagi nanti.');
    } finally {
      youtube.close();
    }
  }

  static Future<void> _saveStream(YoutubeExplode youtube, StreamInfo stream,
      File target, void Function(double, String) progress) async {
    if (stream.size.totalBytes <= 0) {
      throw UnsupportedError(
          'Live atau stream tanpa ukuran pasti tidak didukung. Pilih rekaman yang sudah selesai.');
    }
    final sink = target.openWrite();
    var received = 0;
    var buffered = 0;
    final clock = Stopwatch()..start();
    var lastEmit = 0;
    try {
      await for (final chunk
          in YoutubeSource.bytes(stream).timeout(const Duration(seconds: 90))) {
        sink.add(chunk);
        received += chunk.length;
        buffered += chunk.length;
        if (buffered >= 1024 * 1024) {
          await sink.flush();
          buffered = 0;
        }
        if (clock.elapsedMilliseconds - lastEmit >= 300 &&
            stream.size.totalBytes > 0) {
          final speed = received / (clock.elapsedMilliseconds / 1000);
          final remaining =
              ((stream.size.totalBytes - received) / speed).ceil();
          progress(
              received / stream.size.totalBytes * 100,
              '${(received / 1048576).toStringAsFixed(1)}/${(stream.size.totalBytes / 1048576).toStringAsFixed(1)} MB · '
              '${(speed / 1048576).toStringAsFixed(1)} MB/s · sisa ${remaining ~/ 60}:${(remaining % 60).toString().padLeft(2, "0")}');
          lastEmit = clock.elapsedMilliseconds;
        }
      }
      await sink.flush();
    } finally {
      await sink.close();
    }
    if (received == 0 ||
        (stream.size.totalBytes > 0 && received != stream.size.totalBytes)) {
      throw Exception('Unduhan terputus. Periksa koneksi dan coba lagi.');
    }
  }

  static String _safeName(String input) {
    final cleaned =
        input.replaceAll(RegExp(r'[<>:"/\\|?*\x00-\x1f]'), '_').trim();
    return cleaned.length > 70 ? cleaned.substring(0, 70) : cleaned;
  }
}

// Top-level HLS/section helpers, used only by [Downloader.downloadSection].

class _HlsEntry {
  final double start;
  final double duration;
  final String url;
  _HlsEntry(this.start, this.duration, this.url);
  double get end => start + duration;
}

class _HlsPlaylist {
  final String? initUrl;
  final List<_HlsEntry> segments;
  _HlsPlaylist(this.initUrl, this.segments);
}

/// Result of an online section download: the [file] plus the absolute time
/// its timeline starts at ([start]). Renderers shift source timestamps by
/// [start] so `-ss` lands on the right frame inside the segment.
class RemoteSegment {
  final File file;
  final double start;
  RemoteSegment(this.file, this.start);
}

/// Download a single range-able URL (HLS segment or init) fully, using fresh
/// 1 MB range requests so the per-connection YouTube throttle never kicks in.
Future<void> _writeUrlChunked(
    String url, IOSink sink, http.Client client) async {
  final uri = Uri.parse(url);
  final ua = YoutubeSource.rangeUserAgent(uri);
  // Probe the object size. Fall back gracefully when HEAD is unsupported.
  int? total;
  try {
    final probe = await client
        .send(http.Request('HEAD', uri)
          ..headers['User-Agent'] = ua
          ..headers['Accept'] = '*/*')
        .timeout(const Duration(seconds: 15));
    total = int.tryParse(probe.headers['content-length'] ?? '');
    await probe.stream.drain<void>();
  } catch (_) {
    total = 0;
  }
  if (total == null || total <= 0) {
    // Ukuran tidak diketahui: satu GET satu-satunya pilihan.
    final resp = await client
        .send(http.Request('GET', uri)
          ..headers['User-Agent'] = ua
          ..headers['Accept'] = '*/*')
        .timeout(const Duration(seconds: 120));
    if (resp.statusCode != 200) {
      throw StateError('HTTP ${resp.statusCode} saat unduh segmen.');
    }
    await for (final chunk in resp.stream) {
      sink.add(chunk);
    }
    return;
  }
  var pos = 0;
  while (pos < total) {
    final end = math.min(pos + 1024 * 1024, total) - 1;
    final resp = await client
        .send(http.Request('GET', uri)
          ..headers['User-Agent'] = ua
          ..headers['Accept'] = '*/*'
          ..headers['Range'] = 'bytes=$pos-$end')
        .timeout(const Duration(seconds: 30));
    if (resp.statusCode == 200 && pos == 0) {
      // Server mengabaikan Range: ambil seluruh isi dalam satu koneksi.
      await for (final chunk in resp.stream) {
        sink.add(chunk);
        pos += chunk.length;
      }
      break;
    }
    if (resp.statusCode != 206) {
      throw StateError(
          'YouTube menolak range request (HTTP ${resp.statusCode}).');
    }
    var got = 0;
    await for (final chunk in resp.stream) {
      sink.add(chunk);
      pos += chunk.length;
      got += chunk.length;
    }
    if (got == 0) throw StateError('Respons kosong dari CDN.');
  }
}

/// Fetch a full HLS playlist as text.
Future<String> _readPlaylist(String url) async {
  final uri = Uri.parse(url);
  final client = http.Client();
  try {
    final resp = await client
        .send(http.Request('GET', uri)
          ..headers['User-Agent'] = YoutubeSource.rangeUserAgent(uri)
          ..headers['Accept'] = '*/*')
        .timeout(const Duration(seconds: 30));
    if (resp.statusCode != 200) {
      throw StateError('Playlist HLS gagal (HTTP ${resp.statusCode}).');
    }
    final chunks = await resp.stream.toList();
    final buffer = <int>[];
    for (final chunk in chunks) {
      buffer.addAll(chunk);
    }
    return String.fromCharCodes(buffer);
  } finally {
    client.close();
  }
}

/// Parse an HLS (m3u8) playlist into a playlist plus a playlist into [init] and
/// ordered segments. Segment [start] is the cumulative presentation time.
_HlsPlaylist _parseHls(String text, String baseUrl) {
  final lines = text.split('\n');
  String? initUrl;
  final segments = <_HlsEntry>[];
  var cursor = 0.0;
  for (var i = 0; i < lines.length; i++) {
    final line = lines[i].trim();
    if (line.startsWith('#EXT-X-MAP:')) {
      final match = RegExp(r'URI="([^"]*)"').firstMatch(line);
      if (match != null) {
        initUrl = _resolveHlsUrl(baseUrl, match.group(1)!);
      }
    } else if (line.startsWith('#EXTINF:')) {
      final duration =
          double.tryParse(line.substring(7).split(',').first.trim()) ?? 0.0;
      if (i + 1 < lines.length) {
        final ref = lines[i + 1].trim();
        if (ref.isNotEmpty && !ref.startsWith('#')) {
          segments
              .add(_HlsEntry(cursor, duration, _resolveHlsUrl(baseUrl, ref)));
          cursor += duration;
        }
      }
    }
  }
  return _HlsPlaylist(initUrl, segments);
}

/// Resolve a possibly-relative HLS segment URL against the playlist URL.
String _resolveHlsUrl(String baseUrl, String ref) {
  final parsed = Uri.parse(ref);
  if (parsed.isAbsolute) return ref;
  final base = Uri.parse(baseUrl);
  final dir = base.path.substring(0, base.path.lastIndexOf('/') + 1);
  return base
      .replace(path: '$dir${parsed.path}', query: null, fragment: null)
      .toString();
}

/// Pick the segments whose time window overlaps [start, end], padded with one
/// neighbour on each side for decode safety.
List<_HlsEntry> _selectHlsSegment(
    _HlsPlaylist parsed, double start, double end) {
  final entries = parsed.segments;
  _HlsEntry? first;
  final seen = <String>{};
  final chosen = <_HlsEntry>[];
  for (final entry in entries) {
    if (entry.start < end && entry.end > start) {
      first ??= entry;
      if (seen.add(entry.url)) chosen.add(entry);
    }
  }
  if (chosen.isEmpty) return const [];
  final fi = entries.indexOf(first!);
  if (fi > 0 && seen.add(entries[fi - 1].url)) {
    chosen.insert(0, entries[fi - 1]);
  }
  chosen.sort((a, b) => a.start.compareTo(b.start));
  return chosen;
}

/// Download init + chosen segments into [sink]; concat order preserved.
Future<void> _downloadHlsSegments(
    _HlsPlaylist parsed,
    List<_HlsEntry> chosen,
    IOSink sink,
    http.Client client,
    void Function(double, String)? onProgress) async {
  if (parsed.initUrl != null) {
    await _writeUrlChunked(parsed.initUrl!, sink, client);
  }
  final clientForSegments = http.Client();
  try {
    for (var i = 0; i < chosen.length; i++) {
      await _writeUrlChunked(chosen[i].url, sink, clientForSegments);
      onProgress?.call(
          (i + 1) / chosen.length, 'segmen ${i + 1}/${chosen.length}');
    }
  } finally {
    clientForSegments.close();
  }
}

/// Remux a concatenated fragmented-MP4 into a single clean MP4 (local only).
Future<void> _remuxCopy(File input, File output) async {
  final session = await FFmpegKit.execute(
      '-y -i "${input.path}" -c copy -movflags +faststart "${output.path}"');
  if (!ReturnCode.isSuccess(await session.getReturnCode())) {
    throw Exception('Gagal meremux segmen video.');
  }
}

/// Potong audio lokal pada [segStart, segEnd] lalu gabung ke segmen video.
///
/// Mengembalikan false bila audio tidak tersedia/gagal (pemanggil lanjut
/// video-only seperti sebelumnya, tanpa regresi).
Future<bool> _muxSectionAudio(File videoRaw, File output, String? audioPath,
    double segStart, double segEnd) async {
  try {
    if (audioPath == null || audioPath.isEmpty) return false;
    final audio = File(audioPath);
    if (!audio.existsSync()) return false;
    final duration = segEnd - segStart;
    if (duration <= 0.5) return false;
    final cut = File('${output.path}.range.m4a');
    final cutSession = await FFmpegKit.execute(
        '-y -ss ${segStart.toStringAsFixed(3)} -t ${duration.toStringAsFixed(3)}'
        ' -i "${audio.path}" -vn -c:a aac -b:a 128k "${cut.path}"');
    if (!ReturnCode.isSuccess(await cutSession.getReturnCode()) ||
        !cut.existsSync() ||
        cut.lengthSync() <= 1024) {
      if (cut.existsSync()) await cut.delete();
      return false;
    }
    final mux = await FFmpegKit.execute(
        '-y -i "${videoRaw.path}" -i "${cut.path}"'
        ' -map 0:v:0 -map 1:a:0 -c copy -movflags +faststart "${output.path}"');
    if (cut.existsSync()) await cut.delete();
    if (!ReturnCode.isSuccess(await mux.getReturnCode()) ||
        !output.existsSync() ||
        output.lengthSync() <= 1024) {
      if (output.existsSync()) await output.delete();
      return false;
    }
    return true;
  } catch (_) {
    return false;
  }
}
