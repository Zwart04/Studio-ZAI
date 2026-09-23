import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:youtube_explode_dart/youtube_explode_dart.dart';
import 'package:studiozai/services/youtube_source.dart';

AudioOnlyStreamInfo audio(String track,
        {int size = 5, String url = 'https://example.test/expired'}) =>
    AudioOnlyStreamInfo.fromJson({
      'videoId': {'value': 'kIB-ypmiIzo'},
      'tag': 251,
      'url': url,
      'container': {'name': 'webm'},
      'size': {'totalBytes': size},
      'bitrate': {'bitsPerSecond': 128000},
      'audioCodec': 'opus',
      'qualityLabel': 'medium',
      'fragments': [],
      'codec': 'audio/webm',
      'audioTrack': {
        'id': track,
        'displayName': track,
        'audioIsDefault': track.startsWith('en')
      },
    });

void main() {
  test('Expired URL refresh preserves the exact Indonesian track', () async {
    final urls = <String>[];
    var refreshes = 0;
    final client = MockClient((request) async {
      urls.add(request.url.path);
      expect(request.headers['Range'], 'bytes=0-4');
      return request.url.path == '/expired'
          ? http.Response('', 403)
          : http.Response.bytes([1, 2, 3, 4, 5], 206,
              headers: {'content-range': 'bytes 0-4/5'});
    });
    final result = await YoutubeSource.bytes(audio('id.3'), transport: client,
        refresh: (_) async {
      refreshes++;
      return StreamManifest([
        audio('en.0', url: 'https://example.test/english'),
        audio('id.3', url: 'https://example.test/indonesia')
      ]);
    }).expand((b) => b).toList();
    expect(result, [1, 2, 3, 4, 5]);
    expect(urls, ['/expired', '/indonesia']);
    expect(refreshes, 1);
  });
  test('Repeated 403 errors terminate after bounded retries', () async {
    var calls = 0;
    final client = MockClient((_) async {
      calls++;
      return http.Response('', 403);
    });
    await expectLater(
        YoutubeSource.bytes(audio('id.3'),
                transport: client,
                refresh: (_) async => StreamManifest([audio('id.3')]))
            .drain<void>(),
        throwsStateError);
    expect(calls, 3);
  });
  test('Requested language never silently falls back to English', () {
    final manifest = StreamManifest([audio('en.0'), audio('id-ID.3')]);
    expect(YoutubeSource.audio(manifest, 'id').audioTrack!.id, 'id-ID.3');
    expect(() => YoutubeSource.audio(manifest, 'fr'), throwsStateError);
  });
}
