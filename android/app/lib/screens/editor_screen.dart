import 'package:flutter/material.dart';

import '../models.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class EditorScreen extends StatefulWidget {
  const EditorScreen({super.key, required this.state, required this.clip});

  final AppState state;
  final Clip clip;

  @override
  State<EditorScreen> createState() => _EditorScreenState();
}

class _EditorScreenState extends State<EditorScreen> {
  late TextEditingController _start;
  late TextEditingController _end;
  late TextEditingController _captions;
  late TextEditingController _narration;
  late String _crop;
  late String _style;
  late String _audioMode;

  @override
  void initState() {
    super.initState();
    final clip = widget.clip;
    _start = TextEditingController(text: clip.start.toStringAsFixed(2));
    _end = TextEditingController(text: clip.end.toStringAsFixed(2));
    _captions = TextEditingController(text: _captionsToText(clip));
    _narration = TextEditingController(text: clip.narration);
    _crop = clip.crop;
    _style = clip.subtitlePreset;
    _audioMode = clip.audioMode;
  }

  String _captionsToText(Clip clip) => clip.captions
      .map((c) => '${(c['start'] as num).toStringAsFixed(2)}|${(c['end'] as num).toStringAsFixed(2)}|${c['text']}')
      .join('\n');

  List<Map<String, dynamic>> _textToCaptions(String value) {
    final rows = <Map<String, dynamic>>[];
    for (final line in value.split('\n')) {
      final parts = line.trim().split('|');
      if (parts.length < 3) continue;
      final start = double.tryParse(parts[0]);
      final end = double.tryParse(parts[1]);
      final text = parts.sublist(2).join('|').trim();
      if (start == null || end == null || text.isEmpty) continue;
      rows.add({'start': start, 'end': end, 'text': text});
    }
    return rows;
  }

  @override
  void dispose() {
    _start.dispose();
    _end.dispose();
    _captions.dispose();
    _narration.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final clip = widget.clip;
    clip.start = double.tryParse(_start.text) ?? clip.start;
    clip.end = double.tryParse(_end.text) ?? clip.end;
    if (clip.end <= clip.start) clip.end = clip.start + 1;
    clip.crop = _crop;
    clip.subtitlePreset = _style;
    clip.audioMode = _audioMode;
    clip.captions = _textToCaptions(_captions.text);
    clip.narration = _narration.text;
    final project = widget.state.currentProject;
    if (project != null) await widget.state.saveProject(project);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(widget.state.translate('common.done'))),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final ttsModels = state.catalog.where((m) => m.kind == 'tts' && m.installed).toList();
    return Scaffold(
      appBar: AppBar(title: Text(state.translate('editor.title'))),
      body: ListView(
        padding: const EdgeInsets.all(Tokens.space4),
        children: [
          SectionCard(
            title: state.translate('editor.trim'),
            child: Row(children: [
              Expanded(child: TextField(controller: _start, decoration: const InputDecoration(labelText: 'Mulai (s)'), keyboardType: TextInputType.number)),
              const SizedBox(width: Tokens.space3),
              Expanded(child: TextField(controller: _end, decoration: const InputDecoration(labelText: 'Selesai (s)'), keyboardType: TextInputType.number)),
            ]),
          ),
          const SizedBox(height: Tokens.space3),
          SectionCard(
            child: Column(children: [
              DropdownButtonFormField<String>(
                initialValue: _crop,
                decoration: InputDecoration(labelText: state.translate('editor.crop')),
                items: const [
                  DropdownMenuItem(value: 'center', child: Text('Center 9:16')),
                  DropdownMenuItem(value: 'blur', child: Text('Blur background')),
                  DropdownMenuItem(value: 'none', child: Text('Tanpa crop')),
                ],
                onChanged: (value) => setState(() => _crop = value ?? 'center'),
              ),
              const SizedBox(height: Tokens.space3),
              DropdownButtonFormField<String>(
                initialValue: _style,
                decoration: InputDecoration(labelText: state.translate('editor.style')),
                items: const [
                  DropdownMenuItem(value: 'clean', child: Text('Clean')),
                  DropdownMenuItem(value: 'bold_highlight', child: Text('Bold highlight')),
                ],
                onChanged: (value) => setState(() => _style = value ?? 'clean'),
              ),
              const SizedBox(height: Tokens.space3),
              DropdownButtonFormField<String>(
                initialValue: _audioMode,
                decoration: InputDecoration(labelText: state.translate('editor.audio')),
                items: [
                  DropdownMenuItem(value: 'original', child: Text(state.translate('audio.original'))),
                  DropdownMenuItem(value: 'voice', child: Text(state.translate('audio.voice'))),
                  DropdownMenuItem(value: 'mix', child: Text(state.translate('audio.mix'))),
                ],
                onChanged: (value) => setState(() => _audioMode = value ?? 'original'),
              ),
            ]),
          ),
          const SizedBox(height: Tokens.space3),
          SectionCard(
            title: state.translate('editor.captions'),
            child: TextField(controller: _captions, maxLines: 8, style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
          ),
          const SizedBox(height: Tokens.space3),
          SectionCard(
            title: state.translate('editor.narration'),
            child: Column(children: [
              TextField(controller: _narration, maxLines: 4),
              const SizedBox(height: Tokens.space3),
              if (ttsModels.isEmpty)
                const Text('Unduh model suara dulu di halaman Model.',
                    style: TextStyle(color: Tokens.textDim, fontSize: 12))
              else
                Align(
                  alignment: Alignment.centerLeft,
                  child: OutlinedButton(
                    onPressed: () async {
                      final modelId = state.ttsModelId.isNotEmpty && ttsModels.any((m) => m.id == state.ttsModelId)
                          ? state.ttsModelId
                          : ttsModels.first.id;
                      try {
                        await state.narrateClip(widget.clip, _narration.text, modelId);
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(state.translate('common.done'))),
                          );
                        }
                      } catch (error) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
                        }
                      }
                    },
                    child: Text(state.translate('editor.tts')),
                  ),
                ),
              if (state.jobState == JobState.running) ...[
                const SizedBox(height: Tokens.space3),
                ProgressStrip(progress: state.jobProgress, label: state.jobStage),
              ],
            ]),
          ),
          const SizedBox(height: Tokens.space4),
          Row(children: [
            Expanded(child: FilledButton(onPressed: _save, child: Text(state.translate('editor.save')))),
            const SizedBox(width: Tokens.space3),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  await _save();
                  try {
                    await state.renderClip(widget.clip);
                    if (mounted) Navigator.of(context).pop();
                  } catch (error) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
                    }
                  }
                },
                child: Text(state.translate('clips.render')),
              ),
            ),
          ]),
        ],
      ),
    );
  }
}
