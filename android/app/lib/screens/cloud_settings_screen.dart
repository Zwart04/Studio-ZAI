import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/model_guidance.dart';

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
  Map<String, dynamic> _help = {};
  Map<String, String> _priorities = {};
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final help = await ModelGuidance.help();
    final settings = await CloudAI.settings(widget.kind);
    final stored = await CloudAI.storage.containsKey(
      key: '${widget.kind}_api_key',
    );
    if (!mounted) return;
    setState(() {
      _help = help;
      _priorities = {};
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
      final models = (catalog['models'] as List).cast<Map<String, dynamic>>();
      final priorities = widget.kind == 'ai'
          ? await ModelGuidance.choices(
              _provider, models, catalog['recommended'] as String)
          : <String, String>{};
      if (!mounted || revision != _revision) return;
      setState(() {
        _priorities = priorities;
        _models = models;
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
                    isExpanded: true,
                    initialValue:
                        widget.providers.contains(_provider) ? _provider : '',
                    decoration: const InputDecoration(labelText: 'Penyedia'),
                    items: [
                      const DropdownMenuItem(
                          value: '', child: Text('Nonaktif')),
                      ...widget.providers.map(
                        (p) => DropdownMenuItem(
                          value: p,
                          child: Row(children: [
                            if (!['sd_local', 'compatible'].contains(p)) ...[
                              Image.asset('assets/providers/$p.png',
                                  width: 24, height: 24),
                              const SizedBox(width: 8)
                            ],
                            Expanded(
                                child: Text(
                                    _help[p]?['name'] ??
                                        (p == 'sd_local'
                                            ? 'Stable Diffusion lokal'
                                            : p),
                                    overflow: TextOverflow.ellipsis)),
                          ]),
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
                      _priorities = {};
                      _savedKey = false;
                      _notice = '';
                    }),
                  ),
                  if (_help[_provider] != null) ...[
                    const SizedBox(height: 12),
                    Text(_help[_provider]['badge'],
                        style: const TextStyle(fontWeight: FontWeight.bold)),
                    Text(_help[_provider]['steps']),
                    for (final key in ['key', 'docs', 'pricing'])
                      if (_help[_provider][key] != null)
                        TextButton.icon(
                            icon: const Icon(Icons.copy_outlined),
                            label: Text({
                              'key': 'Salin link API key',
                              'docs': 'Salin panduan resmi',
                              'pricing': 'Salin harga & batas'
                            }[key]!),
                            onPressed: () async {
                              await Clipboard.setData(
                                  ClipboardData(text: _help[_provider][key]));
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                        content: Text(
                                            'Tautan disalin; buka di browser Anda.')));
                              }
                            }),
                  ],
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
                  if (widget.kind == 'ai') ...[
                    Wrap(spacing: 8, children: [
                      for (final choice in {
                        'recommended': 'Rekomendasi',
                        'cheapest': 'Termurah',
                        'smartest': 'Paling pintar'
                      }.entries)
                        OutlinedButton(
                            onPressed: _priorities[choice.key] == null
                                ? null
                                : () => setState(() {
                                      _selection = _priorities[choice.key]!;
                                      _model.text = _selection;
                                    }),
                            child: Text(choice.value)),
                    ]),
                    const Text(
                        'Termurah: estimasi 5.000 token input + 1.000 output pada model dengan harga tercatat; belum termasuk kuota gratis. DeepSeek memakai tarif peak. Paling pintar: saran keluarga model, bukan benchmark.'),
                    for (final model in _models)
                      if (model['id'] == _selection &&
                          model['priceLabel'] != null)
                        Text(model['priceLabel']),
                  ],
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
                      setState(() {
                        _revision++;
                        _priorities = {};
                      });
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
