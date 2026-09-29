import 'package:flutter/material.dart';
import '../services/cloud_ai.dart';
import '../theme/tokens.dart';

class CloudSettingsScreen extends StatelessWidget {
  const CloudSettingsScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('AI lokal & online')),
        body: ListView(padding: const EdgeInsets.all(16), children: const [
          Text(
              'Opsional. Mode online mengirim teks atau prompt ke penyedia pilihanmu dan dapat memakai kuota berbayar. API key disimpan di perangkat.'),
          SizedBox(height: 16),
          _ProviderForm(
              kind: 'ai',
              title: 'AI teks · pemilih momen',
              providers: ['groq', 'gemini', 'openai', 'anthropic', 'deepseek', 'compatible']),
          _ProviderForm(
              kind: 'image',
              title: 'Gambar',
              providers: ['openai', 'sd_local']),
          _ProviderForm(
              kind: 'speech',
              title: 'Suara online · 13 pilihan',
              providers: ['openai']),
        ]),
      );
}

class _ProviderForm extends StatefulWidget {
  const _ProviderForm(
      {required this.kind, required this.title, required this.providers});
  final String kind, title;
  final List<String> providers;
  @override
  State<_ProviderForm> createState() => _ProviderFormState();
}

class _ProviderFormState extends State<_ProviderForm> {
  final _url = TextEditingController(),
      _model = TextEditingController(),
      _key = TextEditingController();
  String _provider = '';
  bool _loaded = false, _savedKey = false, _saving = false;
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final settings = await CloudAI.settings(widget.kind);
    final stored =
        await CloudAI.storage.containsKey(key: '${widget.kind}_api_key');
    if (!mounted) return;
    setState(() {
      _provider = settings['provider']!;
      _url.text = settings['base_url']!;
      _model.text = settings['model']!;
      _savedKey = stored;
      _loaded = true;
    });
  }

  @override
  void dispose() {
    _url.dispose();
    _model.dispose();
    _key.dispose();
    super.dispose();
  }

  Future<void> _save({bool clear = false}) async {
    setState(() => _saving = true);
    try {
      await CloudAI.save(
          widget.kind,
          {
            'provider': _provider,
            'base_url': _url.text.trim(),
            'model': _model.text.trim()
          },
          clear ? '' : (_key.text.trim().isEmpty ? null : _key.text.trim()));
      _key.clear();
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(clear ? 'API key dihapus' : 'Pengaturan tersimpan')));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Card(
          child: ExpansionTile(
        title: Text(widget.title),
        subtitle: Text(_provider.isEmpty ? 'Belum diatur' : _provider),
        childrenPadding: const EdgeInsets.all(16),
        children: !_loaded
            ? [const LinearProgressIndicator()]
            : [
                DropdownButtonFormField<String>(
                  initialValue:
                      widget.providers.contains(_provider) ? _provider : '',
                  decoration: const InputDecoration(labelText: 'Penyedia'),
                  items: [
                    const DropdownMenuItem(value: '', child: Text('Nonaktif')),
                    ...widget.providers.map((p) => DropdownMenuItem(
                        value: p,
                        child: Text(
                            p == 'sd_local' ? 'Stable Diffusion lokal' : p)))
                  ],
                  onChanged: (p) => setState(() {
                    _provider = p ?? '';
                    _url.text = CloudAI.providers[_provider] ?? '';
                    _model.clear();
                    _key.clear();
                  }),
                ),
                const SizedBox(height: 12),
                TextField(
                    controller: _model,
                    decoration: InputDecoration(
                        labelText: 'Nama model',
                        hintText: widget.kind == 'speech'
                            ? 'gpt-4o-mini-tts'
                            : widget.kind == 'image'
                                ? 'gpt-image-1-mini / sd-cpp-local'
                                : 'Nama model dari penyedia')),
                const SizedBox(height: 12),
                TextField(
                    controller: _url,
                    keyboardType: TextInputType.url,
                    decoration: const InputDecoration(labelText: 'Alamat API')),
                const SizedBox(height: 12),
                TextField(
                    controller: _key,
                    obscureText: true,
                    enableSuggestions: false,
                    autocorrect: false,
                    decoration: InputDecoration(
                        labelText: 'API key',
                        hintText: _savedKey
                            ? 'Tersimpan · kosongkan untuk tetap memakai'
                            : 'Masukkan kunci dari penyedia')),
                if (_provider == 'sd_local')
                  const Padding(
                      padding: EdgeInsets.only(top: 12),
                      child: Text(
                          'Jalankan server stable-diffusion.cpp + SD-Turbo di komputer, lalu isi alamat HTTPS server tersebut. Model tidak dibundel di APK. Lihat panduan Model di README.',
                          style:
                              TextStyle(color: Tokens.textDim, fontSize: 12))),
                const SizedBox(height: 12),
                Wrap(spacing: 8, children: [
                  FilledButton(
                      onPressed: _saving ? null : () => _save(),
                      child: const Text('Simpan')),
                  if (_savedKey)
                    TextButton(
                        onPressed: _saving ? null : () => _save(clear: true),
                        child: const Text('Hapus API key'))
                ]),
              ],
      ));
}
