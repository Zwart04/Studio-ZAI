import 'package:flutter/material.dart';

import '../services/cloud_ai.dart';
import '../theme/tokens.dart';

class CloudSettingsScreen extends StatelessWidget {
  const CloudSettingsScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('AI lokal & online')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: const [
            Text(
              'Opsional. Mode online mengirim teks atau prompt ke penyedia pilihanmu dan dapat memakai kuota berbayar. API key disimpan di perangkat.',
            ),
            SizedBox(height: 16),
            _ProviderForm(
              kind: 'ai',
              title: 'AI teks · pemilih momen',
              providers: [
                'groq',
                'gemini',
                'openai',
                'anthropic',
                'deepseek',
                'compatible',
              ],
            ),
            _ProviderForm(
              kind: 'image',
              title: 'Gambar',
              providers: ['openai', 'sd_local'],
            ),
            _ProviderForm(
              kind: 'speech',
              title: 'Suara online · 13 pilihan',
              providers: ['openai'],
            ),
          ],
        ),
      );
}

class _ProviderForm extends StatefulWidget {
  const _ProviderForm({
    required this.kind,
    required this.title,
    required this.providers,
  });
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
  bool _detecting = false;
  int _revision = 0;
  String _selection = 'auto', _notice = '';
  List<Map<String, dynamic>> _models = [];
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final settings = await CloudAI.settings(widget.kind);
    final stored = await CloudAI.storage.containsKey(
      key: '${widget.kind}_api_key',
    );
    if (!mounted) return;
    setState(() {
      _provider = settings['provider']!;
      _url.text = settings['base_url']!;
      _model.text = settings['model']!;
      _selection =
          _model.text.isEmpty || _model.text == 'auto' ? 'auto' : _model.text;
      _models = _selection == 'auto'
          ? []
          : [
              {'id': _selection, 'label': '$_selection · tersimpan'}
            ];
      _savedKey = stored;
      _loaded = true;
    });
  }

  Future<void> _detect() async {
    if (_detecting || _provider.isEmpty) return;
    final revision = _revision;
    setState(() {
      _detecting = true;
      _notice = 'Memeriksa model pada akunmu…';
    });
    try {
      final catalog = await CloudAI.discoverModels(
        _provider,
        _url.text.trim(),
        _key.text.trim(),
        widget.kind,
        useSavedKey: _savedKey && _key.text.isEmpty,
      );
      if (!mounted || revision != _revision) return;
      setState(() {
        _models = (catalog['models'] as List).cast<Map<String, dynamic>>();
        _selection = catalog['recommended'] as String;
        _model.text = _selection;
        _notice =
            'Saran: $_selection. Berdasarkan jenis/nama model; biaya dan kuota mengikuti akunmu.';
      });
    } catch (error) {
      if (mounted && revision == _revision) setState(() => _notice = '$error');
    } finally {
      if (mounted) setState(() => _detecting = false);
    }
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
            'model': _selection == 'auto' ? 'auto' : _model.text.trim(),
          },
          clear ? '' : (_key.text.trim().isEmpty ? null : _key.text.trim()));
      _key.clear();
      await _load();
      if (mounted) {
        setState(() {
          _notice = '';
        });
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(clear ? 'API key dihapus' : 'Pengaturan tersimpan'),
          ),
        );
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
          initiallyExpanded: widget.kind == 'ai',
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
                      const DropdownMenuItem(
                          value: '', child: Text('Nonaktif')),
                      ...widget.providers.map(
                        (p) => DropdownMenuItem(
                          value: p,
                          child: Text(
                            p == 'sd_local' ? 'Stable Diffusion lokal' : p,
                          ),
                        ),
                      ),
                    ],
                    onChanged: (p) => setState(() {
                      _revision++;
                      _provider = p ?? '';
                      _url.text = CloudAI.providers[_provider] ?? '';
                      _model.clear();
                      _key.clear();
                      _selection = 'auto';
                      _models = [];
                      _savedKey = false;
                      _notice = '';
                    }),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    key: ValueKey('$_provider/$_selection/${_models.length}'),
                    initialValue: _selection,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Model'),
                    items: [
                      const DropdownMenuItem(
                        value: 'auto',
                        child: Text('Otomatis · pilih saran saat digunakan'),
                      ),
                      for (final model in _models)
                        DropdownMenuItem(
                          value: model['id'] as String,
                          child: Text(
                            model['label'] as String,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      const DropdownMenuItem(
                        value: 'manual',
                        child: Text('Isi nama model manual'),
                      ),
                    ],
                    onChanged: (value) => setState(() {
                      _selection = value ?? 'auto';
                      if (_selection != 'manual') _model.text = _selection;
                    }),
                  ),
                  if (_selection == 'manual')
                    TextField(
                      controller: _model,
                      decoration: InputDecoration(
                        labelText: 'Nama model',
                        hintText: widget.kind == 'speech'
                            ? 'gpt-4o-mini-tts'
                            : widget.kind == 'image'
                                ? 'gpt-image-1-mini / sd-cpp-local'
                                : 'Nama model dari penyedia',
                      ),
                    ),
                  const SizedBox(height: 12),
                  if (['compatible', 'sd_local'].contains(_provider))
                    TextField(
                      controller: _url,
                      onChanged: (_) {
                        _revision++;
                      },
                      keyboardType: TextInputType.url,
                      decoration:
                          const InputDecoration(labelText: 'Alamat API'),
                    ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _key,
                    obscureText: true,
                    enableSuggestions: false,
                    autocorrect: false,
                    onChanged: (_) {
                      _revision++;
                    },
                    onSubmitted: (_) => _detect(),
                    decoration: InputDecoration(
                      labelText: 'API key',
                      hintText: _savedKey
                          ? 'Tersimpan · kosongkan untuk tetap memakai'
                          : 'Masukkan kunci dari penyedia',
                    ),
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: _detecting || _provider.isEmpty ? null : _detect,
                    icon: const Icon(Icons.auto_awesome),
                    label: Text(
                      _detecting ? 'Mendeteksi…' : 'Deteksi & sarankan model',
                    ),
                  ),
                  if (_notice.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(_notice),
                    ),
                  if (_provider == 'sd_local')
                    const Padding(
                      padding: EdgeInsets.only(top: 12),
                      child: Text(
                        'Jalankan server stable-diffusion.cpp + SD-Turbo di komputer, lalu isi alamat HTTPS server tersebut. Model tidak dibundel di APK. Lihat panduan Model di README.',
                        style: TextStyle(color: Tokens.textDim, fontSize: 12),
                      ),
                    ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    children: [
                      FilledButton(
                        onPressed: _saving ? null : () => _save(),
                        child: const Text('Simpan'),
                      ),
                      if (_savedKey)
                        TextButton(
                          onPressed: _saving ? null : () => _save(clear: true),
                          child: const Text('Hapus API key'),
                        ),
                    ],
                  ),
                ],
        ),
      );
}
