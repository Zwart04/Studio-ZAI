import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:studiozai/services/cloud_ai.dart';

void main() {
  test(
      'Catalog uses real provider response, filters tasks and recommends a returned model',
      () async {
    final client = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.host, 'api.groq.com');
      expect(request.followRedirects, false);
      expect(request.headers['Authorization'], 'Bearer fixture-only');
      return http.Response(
          jsonEncode({
            'data': [
              {'id': 'text-embedding'},
              {'id': 'llama-70b'},
              {'id': 'llama-20b-instant'},
              {'id': 'inactive', 'active': false}
            ]
          }),
          200);
    });
    final catalog = await CloudAI.discoverModels(
        'groq', '', 'fixture-only', 'ai',
        client: client);
    expect(catalog['recommended'], 'llama-20b-instant');
    expect((catalog['models'] as List).length, 2);
    expect(jsonEncode(catalog), isNot(contains('fixture-only')));
    client.close();
  });
  test('Unavailable models are never replaced with a fake catalog', () async {
    final client = MockClient((_) async => http.Response('{"data":[]}', 200));
    await expectLater(
        CloudAI.discoverModels('openai', '', 'fixture', 'ai', client: client),
        throwsException);
    client.close();
  });
  test(
      'Official provider rejects changed host or insecure URL before network access',
      () async {
    for (final base in [
      'http://api.openai.com/v1',
      'https://example.com/v1',
      'https://api.openai.com:8443/v1',
      'https://api.openai.com/v1?key=private'
    ]) {
      expect(() => CloudAI.validateBase('openai', base), throwsException);
    }
    expect(CloudAI.validateBase('compatible', 'http://127.0.0.1:11434/v1'),
        'http://127.0.0.1:11434/v1');
  });
  test('Filter separates transcription, image, speech and text models', () {
    expect(CloudAI.supportsModel('whisper-large', 'ai'), false);
    expect(CloudAI.supportsModel('gpt-image-1', 'image'), true);
    expect(CloudAI.supportsModel('gpt-4o-mini-tts', 'speech'), true);
    expect(CloudAI.supportsModel('claude-haiku', 'ai'), true);
  });
}
