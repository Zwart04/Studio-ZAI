import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Optional providers; keys stay in Android Keystore, outside project files.
class CloudAI {
  static final _catalogCache = <String, (DateTime, Map<String, dynamic>)>{};
  static const storage = FlutterSecureStorage();
  static const providers = {
    'openai': 'https://api.openai.com/v1',
    'anthropic': 'https://api.anthropic.com/v1',
    'groq': 'https://api.groq.com/openai/v1',
    'gemini': 'https://generativelanguage.googleapis.com/v1beta/openai',
    'deepseek': 'https://api.deepseek.com',
    'compatible': 'http://127.0.0.1:11434/v1',
    'sd_local': 'http://127.0.0.1:1234/v1',
  };
  static const voices = [
    'marin',
    'cedar',
    'alloy',
    'ash',
    'ballad',
    'coral',
    'echo',
    'fable',
    'nova',
    'onyx',
    'sage',
    'shimmer',
    'verse',
  ];

  static Future<Map<String, String>> settings(String kind) async {
    final prefs = await SharedPreferences.getInstance();
    return {
      for (final field in ['provider', 'base_url', 'model'])
        field: prefs.getString('${kind}_$field') ?? '',
    };
  }

  static Future<void> save(
    String kind,
    Map<String, String> values,
    String? key,
  ) async {
    final prefs = await SharedPreferences.getInstance();
    if ((prefs.getString('${kind}_provider') != values['provider'] ||
            (prefs.getString('${kind}_base_url') ?? '') !=
                (values['base_url'] ?? '')) &&
        key == null) {
      key = '';
    }
    for (final entry in values.entries) {
      await prefs.setString('${kind}_${entry.key}', entry.value);
    }
    if (key != null) {
      if (key.isEmpty) {
        await storage.delete(key: '${kind}_api_key');
      } else {
        await storage.write(key: '${kind}_api_key', value: key);
      }
    }
  }

  static String validateBase(String provider, String base) {
    if (!providers.containsKey(provider)) {
      throw Exception('Penyedia tidak dikenal.');
    }
    base = (base.isEmpty ? providers[provider]! : base).replaceFirst(
      RegExp(r'/+$'),
      '',
    );
    final uri = Uri.tryParse(base);
    if (uri == null ||
        !['http', 'https'].contains(uri.scheme) ||
        uri.host.isEmpty ||
        uri.userInfo.isNotEmpty ||
        uri.hasQuery ||
        uri.hasFragment) {
      throw Exception('Alamat API tidak valid.');
    }
    if (!['compatible', 'sd_local'].contains(provider) &&
        (uri.scheme != 'https' ||
            uri.host != Uri.parse(providers[provider]!).host ||
            uri.port != 443)) {
      throw Exception('Gunakan alamat resmi atau pilih API kompatibel.');
    }
    return base;
  }

  static bool supportsModel(String id, String kind) {
    final name = id.toLowerCase();
    if (kind == 'image') {
      return name.contains('image') ||
          name.startsWith('dall-e') ||
          name.startsWith('sd-');
    }
    if (kind == 'speech') return name.contains('tts');
    return ![
      'embed',
      'whisper',
      'audio',
      'speech',
      'tts',
      'realtime',
      'image',
      'dall-e',
      'moderation',
      'guard',
      'compound',
      'codex',
      'robotics',
    ].any(name.contains);
  }

  static int compareModels(String a, String b) {
    bool stable(String id) => ![
          'preview',
          'experimental',
          'exp-',
          'deprecated',
        ].any(id.toLowerCase().contains);
    bool preferred(String id) => [
          'mini',
          'luna',
          'flash',
          'haiku',
          'instant',
          'lite',
          '20b',
        ].any(id.toLowerCase().contains);
    for (final score in [stable, preferred]) {
      if (score(a) != score(b)) return score(a) ? -1 : 1;
    }
    final av = RegExp(r'\d+')
        .allMatches(a)
        .take(3)
        .map((m) => int.parse(m[0]!))
        .toList();
    final bv = RegExp(r'\d+')
        .allMatches(b)
        .take(3)
        .map((m) => int.parse(m[0]!))
        .toList();
    for (var i = 0; i < 3; i++) {
      final diff = (i < bv.length ? bv[i] : 0) - (i < av.length ? av[i] : 0);
      if (diff != 0) return diff;
    }
    return b.compareTo(a);
  }

  static Future<Map<String, dynamic>> discoverModels(
    String provider,
    String base,
    String key,
    String kind, {
    bool useSavedKey = false,
    http.Client? client,
  }) async {
    base = validateBase(provider, base);
    if (useSavedKey && key.isEmpty) {
      final saved = await settings(kind);
      if (saved['provider'] != provider ||
          validateBase(provider, saved['base_url']!) != base) {
        throw Exception('Masukkan API key untuk penyedia atau alamat baru.');
      }
      key = await storage.read(key: '${kind}_api_key') ?? '';
    }
    if (key.isEmpty && !['compatible', 'sd_local'].contains(provider)) {
      throw Exception('Masukkan API key.');
    }
    final uri = Uri.parse(
      '$base/models${provider == 'anthropic' ? '?limit=1000' : ''}',
    );
    if (key.isNotEmpty &&
        uri.scheme != 'https' &&
        !['localhost', '127.0.0.1', '::1'].contains(uri.host)) {
      throw Exception('API key memerlukan HTTPS.');
    }
    final ownClient = client == null;
    final cacheKey =
        '$provider|$base|$kind|${sha256.convert(utf8.encode(key))}';
    final cached = _catalogCache[cacheKey];
    if (ownClient &&
        cached != null &&
        DateTime.now().difference(cached.$1).inMinutes < 5) { return cached.$2; }
    client ??= http.Client();
    try {
      final req = http.Request('GET', uri)..followRedirects = false;
      if (key.isNotEmpty) {
        req.headers.addAll(
          provider == 'anthropic'
              ? {'x-api-key': key, 'anthropic-version': '2023-06-01'}
              : {'Authorization': 'Bearer $key'},
        );
      }
      final response =
          await client.send(req).timeout(const Duration(seconds: 30));
      if (response.statusCode != 200) {
        throw Exception(
          'Deteksi model gagal (HTTP ${response.statusCode}). Periksa API key dan kuota.',
        );
      }
      final bytes = <int>[];
      await for (final chunk in response.stream.timeout(
        const Duration(seconds: 30),
      )) {
        bytes.addAll(chunk);
        if (bytes.length > 2 * 1024 * 1024) {
          throw Exception('Daftar model terlalu besar.');
        }
      }
      final data = jsonDecode(utf8.decode(bytes));
      if (data is! Map || data['data'] is! List) {
        throw Exception('Daftar model tidak valid.');
      }
      final choices = <String, String>{};
      for (final row in data['data'] as List) {
        if (row is! Map || row['active'] == false || row['id'] is! String) {
          continue;
        }
        final id = row['id'] as String;
        if (id.isNotEmpty && id.length <= 200 && supportsModel(id, kind)) {
          choices[id] = '${row['display_name'] ?? id}';
        }
      }
      final ids = choices.keys.toList()..sort(compareModels);
      if (ids.isEmpty) {
        throw Exception(
          'Tidak ada model yang sesuai. Isi model manual atau pilih penyedia lain.',
        );
      }
      final catalog = <String, dynamic>{
        'models': [
          for (final id in ids) {'id': id, 'label': choices[id]!},
        ],
        'recommended': ids.first,
      };
      if (ownClient) {
        if (_catalogCache.length >= 64) _catalogCache.clear();
        _catalogCache[cacheKey] = (DateTime.now(), catalog);
      }
      return catalog;
    } finally {
      if (ownClient) client.close();
    }
  }

  static Future<http.Response> request(
    String kind,
    String route,
    Map<String, dynamic> payload,
  ) async {
    final config = await settings(kind);
    final provider = config['provider']!;
    if (!providers.containsKey(provider)) {
      throw Exception('Pilih penyedia AI di Pengaturan.');
    }
    final base = validateBase(provider, config['base_url']!);
    final uri = Uri.tryParse('${base.replaceFirst(RegExp(r'/+$'), '')}$route');
    final key = await storage.read(key: '${kind}_api_key') ?? '';
    if (uri == null ||
        !['https', 'http'].contains(uri.scheme) ||
        uri.host.isEmpty ||
        uri.userInfo.isNotEmpty) {
      throw Exception('Alamat API tidak valid.');
    }
    if (key.isNotEmpty &&
        uri.scheme != 'https' &&
        !['localhost', '127.0.0.1', '::1'].contains(uri.host)) {
      throw Exception('API key memerlukan HTTPS.');
    }
    if (!['compatible', 'sd_local'].contains(provider) && key.isEmpty) {
      throw Exception('Isi API key di Pengaturan.');
    }
    final headers = {'Content-Type': 'application/json'};
    if (key.isNotEmpty) {
      if (provider == 'anthropic') {
        headers.addAll({'x-api-key': key, 'anthropic-version': '2023-06-01'});
      } else {
        headers['Authorization'] = 'Bearer $key';
      }
    }
    if (config['model'] == 'auto' ||
        (kind == 'ai' && config['model']!.isEmpty)) {
      payload['model'] = (await discoverModels(
        provider,
        base,
        key,
        kind,
      ))['recommended'];
    } else if (config['model']!.isNotEmpty) {
      payload['model'] = config['model'];
    }
    final client = http.Client();
    try {
      final req = http.Request('POST', uri)
        ..headers.addAll(headers)
        ..body = jsonEncode(payload)
        ..followRedirects = false;
      final response =
          await client.send(req).timeout(const Duration(seconds: 180));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw Exception(
          response.statusCode == 429
              ? 'Kuota penyedia AI habis atau permintaan terlalu sering.'
              : 'Penyedia AI gagal (HTTP ${response.statusCode}). Periksa API key dan nama model.',
        );
      }
      final bytes = <int>[];
      await for (final chunk in response.stream.timeout(
        const Duration(seconds: 180),
      )) {
        bytes.addAll(chunk);
        if (bytes.length > 32 * 1024 * 1024) {
          throw Exception('Respons AI terlalu besar.');
        }
      }
      return http.Response.bytes(bytes, response.statusCode);
    } finally {
      client.close();
    }
  }

  static Future<String> text(String prompt) async {
    final config = await settings('ai');
    final anthropic = config['provider'] == 'anthropic';
    final response = await request(
      'ai',
      anthropic ? '/messages' : '/chat/completions',
      {
        'messages': [
          {'role': 'user', 'content': prompt},
        ],
        if (anthropic) 'max_tokens': 2048,
      },
    );
    final result = jsonDecode(response.body) as Map<String, dynamic>;
    return anthropic
        ? (result['content'] as List)
            .where((p) => p['type'] == 'text')
            .map((p) => p['text'])
            .join()
        : result['choices'][0]['message']['content'] as String;
  }

  static Future<File> image(String prompt, Directory dataDir) async {
    if (prompt.trim().isEmpty) throw Exception('Isi deskripsi gambar.');
    final local = (await settings('image'))['provider'] == 'sd_local';
    final response = await request('image', '/images/generations', {
      'model': local ? 'sd-cpp-local' : 'gpt-image-1-mini',
      'prompt': prompt,
      'n': 1,
      'size': local ? '512x512' : '1024x1024',
      if (!local) 'quality': 'low',
      if (local) ...{
        'response_format': 'b64_json',
        'steps': 4,
        'cfg_scale': 1.0,
      },
    });
    final raw = base64Decode(
      jsonDecode(response.body)['data'][0]['b64_json'] as String,
    );
    if (raw.length < 8 ||
        raw[0] != 137 ||
        raw[1] != 80 ||
        raw[2] != 78 ||
        raw[3] != 71) {
      throw Exception('Respons bukan PNG.');
    }
    final directory = Directory('${dataDir.path}/images')
      ..createSync(recursive: true);
    final target = File(
      '${directory.path}/image-${DateTime.now().microsecondsSinceEpoch}.png',
    );
    await target.writeAsBytes(raw);
    await File('${target.path}.json')
        .writeAsString(jsonEncode({'prompt': prompt, 'local': local}));
    return target;
  }

  static Future<File> speech(
    String text,
    String voice,
    String language,
    Directory dataDir,
  ) async {
    if (text.trim().isEmpty || !voices.contains(voice)) {
      throw Exception('Isi teks dan pilih suara.');
    }
    final response = await request('speech', '/audio/speech', {
      'model': 'gpt-4o-mini-tts',
      'voice': voice,
      'input': text,
      'response_format': 'wav',
      'instructions':
          language == 'id' ? 'Speak in Indonesian.' : 'Speak in English.',
    });
    if (response.bodyBytes.length < 12 ||
        ascii.decode(response.bodyBytes.take(4).toList(), allowInvalid: true) !=
            'RIFF') {
      throw Exception('Respons bukan WAV.');
    }
    final directory = Directory('${dataDir.path}/voices')
      ..createSync(recursive: true);
    return File(
      '${directory.path}/cloud-${DateTime.now().microsecondsSinceEpoch}.wav',
    ).writeAsBytes(response.bodyBytes);
  }
}
