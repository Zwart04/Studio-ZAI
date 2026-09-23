import 'dart:async';
import 'dart:math' as math;
import 'package:http/http.dart' as http;
import 'package:youtube_explode_dart/youtube_explode_dart.dart';

/// Public YouTube extraction. Each attempt has its own client so a timeout
/// closes its outstanding requests instead of leaving them running in the app.
class YoutubeSource {
  // Current public client profile also used by yt-dlp. Older Android profiles
  // can advertise URLs that stop transferring after the first few megabytes.
  static const vision = YoutubeApiClient({
    'context': {
      'client': {
        'clientName': 'VISIONOS',
        'clientVersion': '1.02',
        'deviceMake': 'Apple',
        'deviceModel': 'RealityDevice17,1',
        'userAgent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_7_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15',
        'osName': 'visionOS',
        'osVersion': '26.5.23O471',
        'hl': 'en',
        'gl': 'US',
      }
    }
  }, 'https://www.youtube.com/youtubei/v1/player?prettyPrint=false');

  /// Bounded HTTP ranges avoid the library's unbounded 403-refresh loop.
  /// Never replace a requested audio track with a different language.
  static Stream<List<int>> bytes(StreamInfo info,
      {http.Client? transport,
      Future<StreamManifest> Function(String)? refresh}) async* {
    final client = transport ?? http.Client();
    var offset = 0;
    var failures = 0;
    var current = info;
    try {
      while (offset < info.size.totalBytes) {
        final end = math.min(offset + 1024 * 1024, info.size.totalBytes) - 1;
        try {
          final request = http.Request('GET', current.url);
          request.headers['Range'] = 'bytes=$offset-$end';
          request.headers['User-Agent'] = current.url.queryParameters['c'] ==
                  'VISIONOS'
              ? vision.payload['context']['client']['userAgent'] as String
              : 'com.google.android.youtube/20.10.38 (Linux; U; Android 11) gzip';
          final response =
              await client.send(request).timeout(const Duration(seconds: 20));
          if (response.statusCode != 206 ||
              !('${response.headers['content-range']}')
                  .startsWith('bytes $offset-')) {
            await response.stream
                .timeout(const Duration(seconds: 20))
                .drain<void>();
            throw StateError(
                'YouTube menolak bagian unduhan (HTTP ${response.statusCode}).');
          }
          final before = offset;
          await for (final chunk
              in response.stream.timeout(const Duration(seconds: 20))) {
            offset += chunk.length;
            if (offset > end + 1) {
              throw StateError('Ukuran stream tidak sesuai.');
            }
            yield chunk;
          }
          if (offset == before) {
            throw StateError('YouTube mengirim bagian kosong.');
          }
          failures = 0;
        } catch (_) {
          if (++failures > 2) rethrow;
          final fresh = await (refresh ?? manifest)(info.videoId.value);
          current = fresh.streams.firstWhere((s) =>
              s.tag == info.tag &&
              (info is! AudioOnlyStreamInfo ||
                  (s is AudioOnlyStreamInfo &&
                      s.audioTrack?.id == info.audioTrack?.id)));
        }
      }
    } finally {
      client.close();
    }
  }

  static Future<StreamManifest> manifest(String url,
      {void Function(String)? onStatus}) async {
    Object? lastError;
    final clients = [vision, YoutubeApiClient.androidSdkless];
    for (var i = 0; i < clients.length; i++) {
      final youtube = YoutubeExplode();
      try {
        onStatus
            ?.call('Membaca stream YouTube · cara ${i + 1}/${clients.length}');
        return await youtube.videos.streamsClient
            .getManifest(
              url,
              ytClients: [clients[i]],
              requireWatchPage: clients[i] == vision,
            )
            .timeout(const Duration(seconds: 25));
      } catch (error) {
        lastError = error;
      } finally {
        youtube.close();
      }
    }
    throw StateError('YouTube belum menyediakan stream yang dapat diunduh. '
        'Coba jaringan lain atau pilih berkas video dari perangkat. '
        'Video privat, dibatasi usia, atau dibatasi wilayah tidak didukung. '
        'Detail: $lastError');
  }

  static VideoOnlyStreamInfo video(StreamManifest manifest,
      {int maxHeight = 720}) {
    final choices = manifest.videoOnly
        .where((s) =>
            s.videoResolution.height <= maxHeight &&
            s.videoCodec.startsWith('avc1'))
        .toList()
      ..sort((a, b) {
        final resolution =
            b.videoResolution.height.compareTo(a.videoResolution.height);
        return resolution != 0
            ? resolution
            : a.bitrate.bitsPerSecond.compareTo(b.bitrate.bitsPerSecond);
      });
    if (choices.isEmpty) {
      throw StateError(
          'Video H.264 hingga ${maxHeight}p tidak tersedia. Pilih berkas video dari perangkat.');
    }
    return choices.first;
  }

  static AudioOnlyStreamInfo audio(StreamManifest manifest, String? language) {
    final choices = manifest.audioOnly
        .where((s) => language == null
            ? (s.audioTrack == null || s.audioTrack!.audioIsDefault)
            : (s.audioTrack?.id ?? '')
                    .toLowerCase()
                    .split(RegExp(r'[-_.]'))
                    .first ==
                language.toLowerCase())
        .toList()
      ..sort(
          (a, b) => b.bitrate.bitsPerSecond.compareTo(a.bitrate.bitsPerSecond));
    if (choices.isEmpty) {
      throw StateError(
          'Track audio ${language ?? "bawaan"} tidak tersedia. Pilih track lain.');
    }
    return choices.first;
  }
}
