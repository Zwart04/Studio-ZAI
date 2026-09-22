import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class VoiceScreen extends StatefulWidget {
  const VoiceScreen({super.key, required this.state});

  final AppState state;

  @override
  State<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends State<VoiceScreen> {
  final _text = TextEditingController();
  final _sample = TextEditingController();
  final _sampleText = TextEditingController();
  String _modelId = '';
  String _language = 'id';
  String? _lastFile;
  bool _cloning = false;

  @override
  void dispose() {
    _text.dispose();
    _sample.dispose();
    _sampleText.dispose();
    super.dispose();
  }

  Future<void> _pickSample() async {
    final files = await FilePicker.pickFiles(type: FileType.audio);
    if (files.isEmpty) return;
    final path = files.first.path;
    if (path != null) setState(() => _sample.text = path);
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final ttsModels = state.catalog.where((m) => m.kind == 'tts').toList();
    final installed = ttsModels.where((m) => m.installed).toList();
    _modelId = installed.any((m) => m.id == _modelId)
        ? _modelId
        : (installed.isEmpty ? '' : installed.first.id);

    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        Text(state.translate('voice.title'),
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.4)),
        const SizedBox(height: Tokens.space2),
        Text(state.translate('voice.lead'), style: const TextStyle(color: Tokens.textDim)),
        const SizedBox(height: Tokens.space4),
        SectionCard(
          title: state.translate('voice.generate'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(controller: _text, maxLines: 4, decoration: InputDecoration(labelText: state.translate('voice.text'))),
              const SizedBox(height: Tokens.space3),
              Row(children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _language,
                    decoration: InputDecoration(labelText: state.translate('voice.lang')),
                    items: const [
                      DropdownMenuItem(value: 'id', child: Text('Indonesia')),
                      DropdownMenuItem(value: 'en', child: Text('English')),
                    ],
                    onChanged: (value) => setState(() => _language = value ?? 'id'),
                  ),
                ),
                const SizedBox(width: Tokens.space3),
                Expanded(
                  child: installed.isEmpty
                      ? const Text('Belum ada model suara terpasang.',
                          style: TextStyle(color: Tokens.textDim, fontSize: 12))
                      : DropdownButtonFormField<String>(
                          initialValue: _modelId,
                          decoration: InputDecoration(labelText: state.translate('voice.model')),
                          items: installed
                              .map((m) => DropdownMenuItem(value: m.id, child: Text(m.id.split('_').first, overflow: TextOverflow.ellipsis)))
                              .toList(),
                          onChanged: (value) => setState(() => _modelId = value ?? ''),
                        ),
                ),
              ]),
              const SizedBox(height: Tokens.space3),
              FilledButton(
                onPressed: installed.isEmpty || state.jobState == JobState.running
                    ? null
                    : () async {
                        try {
                          final file = await state.quickVoice(_text.text, _modelId, _language);
                          setState(() => _lastFile = file.path);
                        } catch (error) {
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
                          }
                        }
                      },
                child: Text(state.translate('voice.generate')),
              ),
              if (state.jobState == JobState.running) ...[
                const SizedBox(height: Tokens.space3),
                ProgressStrip(progress: state.jobProgress, label: state.jobStage),
              ],
              if (_lastFile != null) ...[
                const SizedBox(height: Tokens.space3),
                Row(children: [
                  const Icon(Icons.graphic_eq, color: Tokens.success, size: 18),
                  const SizedBox(width: Tokens.space2),
                  Expanded(child: Text(File(_lastFile!).uri.pathSegments.last, style: const TextStyle(fontSize: 12))),
                  TextButton(
                    onPressed: () => SharePlus.instance.share(ShareParams(files: [XFile(_lastFile!)])),
                    child: Text(state.translate('clips.share')),
                  ),
                ]),
              ],
            ],
          ),
        ),
        const SizedBox(height: Tokens.space3),
        SectionCard(
          title: state.translate('voice.clone'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Pill('eksperimental', tone: 'warn'),
              const SizedBox(height: Tokens.space2),
              Text(
                state.translate('voice.experimentalNote'),
                style: const TextStyle(color: Tokens.textDim, fontSize: 12),
              ),
              const SizedBox(height: Tokens.space3),
              TextField(
                controller: _sample,
                decoration: InputDecoration(labelText: state.translate('voice.sample')),
              ),
              const SizedBox(height: Tokens.space2),
              OutlinedButton.icon(
                onPressed: _pickSample,
                icon: const Icon(Icons.audiotrack, size: 18),
                label: Text(state.translate('voice.pickSample')),
              ),
              const SizedBox(height: Tokens.space2),
              TextField(
                controller: _sampleText,
                decoration: InputDecoration(
                  labelText: state.translate('voice.sampleText'),
                  hintText: 'teks yang diucapkan di rekaman contoh',
                ),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: state.cloneConsent,
                onChanged: (value) => state.setConsent(value),
                title: Text(state.translate('voice.consent'), style: const TextStyle(fontSize: 13)),
              ),
              OutlinedButton(
                onPressed: !state.cloneConsent
                    ? null
                    : () async {
                        try {
                          setState(() => _cloning = true);
                          final file = await state.speech.cloneWithZipVoice(
                            text: _text.text,
                            referenceWav: _sample.text,
                            referenceText: _sampleText.text,
                            outputPath: '${state.dataDir.path}/voices/clone-'
                                '${DateTime.now().millisecondsSinceEpoch}.wav',
                          );
                          if (mounted) {
                            setState(() {
                              _cloning = false;
                              _lastFile = file.path;
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text(state.translate('common.done'))),
                            );
                          }
                        } catch (error) {
                          if (mounted) {
                            setState(() => _cloning = false);
                            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
                          }
                        }
                      },
                child: _cloning
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(state.translate('voice.clone')),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
