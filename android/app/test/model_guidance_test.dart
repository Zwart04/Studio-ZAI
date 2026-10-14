import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/services/model_guidance.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('Price priorities use published data; expire after thirty days',
      () async {
    final rows = <Map<String, dynamic>>[
      {'id': 'gpt-6-astra'},
      {'id': 'gpt-6-luna'},
      {'id': 'gpt-99-free-mini'},
    ];
    final choices = await ModelGuidance.choices('openai', rows, 'gpt-6-luna',
        now: DateTime(2026, 10, 14));
    expect(choices['cheapest'], 'gpt-6-luna');
    expect(choices['smartest'], 'gpt-6-astra');
    expect(rows.last.containsKey('priceLabel'), false);
    final later = await ModelGuidance.choices('openai', rows, 'gpt-6-luna',
        now: DateTime(2027, 1, 1));
    expect(later.containsKey('cheapest'), false);
    expect(rows.every((m) => !m.containsKey('priceLabel')), true);
  });
  test('Provider help includes official key links and free-tier conditions',
      () async {
    final help = await ModelGuidance.help();
    expect(help['gemini']['key'], 'https://aistudio.google.com/apikey');
    expect(help['groq']['badge'], contains('gratis'));
    expect(help['openai']['badge'], contains('berbayar'));
  });
}
