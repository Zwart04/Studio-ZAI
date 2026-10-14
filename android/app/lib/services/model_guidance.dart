import 'dart:convert';
import 'package:flutter/services.dart';

class ModelGuidance {
  static Future<Map<String, dynamic>> help() async => Map<String, dynamic>.from(
      jsonDecode(await rootBundle.loadString('assets/providers/help.json')));

  static Future<Map<String, String>> choices(
      String provider, List<Map<String, dynamic>> models, String recommended,
      {DateTime? now}) async {
    final data =
        jsonDecode(await rootBundle.loadString('assets/providers/prices.json'))
            as Map;
    final result = {'recommended': recommended};
    final age = (now ?? DateTime.now())
        .difference(DateTime.parse(data['checked']))
        .inDays;
    for (final row in models) {
      row.remove('priceLabel');
    }
    double? cheapest;
    if (age >= 0 && age <= 30) {
      for (final row in models) {
        final price = data['prices'][provider]?[row['id']] as List?;
        if (price == null) continue;
        final cost =
            (price[0] as num).toDouble() * 5 + (price[1] as num).toDouble();
        row['priceLabel'] =
            'USD ${price[0]} input / ${price[1]} output per 1 juta token. Tarif standar konteks pendek, diperiksa ${data['checked']}.';
        if (cheapest == null || cost < cheapest) {
          cheapest = cost;
          result['cheapest'] = row['id'] as String;
        }
      }
    }
    final families = {
          'openai': ['astra', 'sol', 'luna'],
          'anthropic': ['fable', 'mythos', 'opus', 'sonnet', 'haiku'],
          'gemini': ['pro', 'flash'],
          'deepseek': ['pro', 'reasoner', 'flash', 'chat'],
          'groq': ['120b', '70b', '27b', '20b', '8b'],
        }[provider] ??
        <String>[];
    for (final family in families) {
      final matching =
          models.where((m) => '${m['id']}'.contains(family)).toList()
            ..sort((a, b) {
              final av = RegExp(r'\d+')
                  .allMatches('${a['id']}')
                  .take(3)
                  .map((m) => int.parse(m[0]!))
                  .toList();
              final bv = RegExp(r'\d+')
                  .allMatches('${b['id']}')
                  .take(3)
                  .map((m) => int.parse(m[0]!))
                  .toList();
              for (var i = 0; i < av.length && i < bv.length; i++) {
                final cmp = bv[i].compareTo(av[i]);
                if (cmp != 0) return cmp;
              }
              return bv.length.compareTo(av.length);
            });
      if (matching.isNotEmpty) {
        result['smartest'] = matching.first['id'] as String;
        break;
      }
    }
    return result;
  }
}
