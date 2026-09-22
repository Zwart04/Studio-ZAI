import 'dart:math' as math;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../models.dart';
import '../services/subtitle_builder.dart';
import '../services/timeline.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import '../widgets/preview_player.dart';
import '../widgets/timeline_view.dart';

/// Editor klip: pratinjau + timeline multi-track (video/media/teks/audio).
class EditorScreen extends StatefulWidget {
  const EditorScreen({super.key, required this.state, required this.clip});

  final AppState state;
  final Clip clip;

  @override
  State<EditorScreen> createState() => _EditorScreenState();
}

class _EditorScreenState extends State<EditorScreen> {
  late Timeline _timeline;
  late TextEditingController _captions;
  late TextEditingController _itemText;

  String? _selectedKind;
  String? _selectedId;
  String? _previewPath;
  int _tab = 0;

  @override
  void initState() {
    super.initState();
    final clip = widget.clip;
    _timeline = widget.state.timelineForClip(clip);
    _captions = TextEditingController(text: _captionsToText(clip));
    _itemText = TextEditingController();
  }

  @override
  void dispose() {
    _captions.dispose();
    _itemText.dispose();
    super.dispose();
  }

  // ------------------------------------------------------------------ helpers

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

  TimelineItem? get _selected {
    final kind = _selectedKind;
    final id = _selectedId;
    if (kind == null || id == null) return null;
    final items = _timeline.trackOf(kind)?.items ?? const <TimelineItem>[];
    for (final item in items) {
      if (item.id == id) return item;
    }
    return null;
  }

  void _select(String kind, TimelineItem item) {
    setState(() {
      _selectedKind = kind;
      _selectedId = item.id;
    });
  }

  void _replace(String kind, TimelineItem item) {
    final track = _timeline.trackOf(kind);
    if (track == null) return;
    final index = track.items.indexWhere((entry) => entry.id == item.id);
    if (index < 0) return;
    setState(() {
      track.items[index] = item;
      // Jangan sentuh controller kalau isinya sama — menulis ulang teks yang
      // sama akan memindahkan kursor ke akhir saat mengetik di tengah.
      if (_selectedId == item.id && _itemText.text != item.text) {
        _itemText.text = item.text;
      }
    });
  }

  void _remove(String kind, TimelineItem item) {
    if (kind == 'video') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Item video tidak bisa dihapus.')),
      );
      return;
    }
    setState(() {
      _timeline.trackOf(kind)?.items.removeWhere((entry) => entry.id == item.id);
      if (_selectedId == item.id) {
        _selectedId = null;
        _selectedKind = null;
      }
    });
  }

  void _addText() {
    final track = _timeline.trackOf('text');
    if (track == null) return;
    final end = math.min(3.0, math.max(1.0, _timeline.duration));
    final item = TimelineItem(
      id: 't${DateTime.now().millisecondsSinceEpoch}',
      start: 0,
      end: end,
      text: 'Teks baru',
      template: 'tiktok_pop',
      x: 0.5,
      y: 0.8,
    );
    setState(() {
      track.items.add(item);
      _selectedKind = 'text';
      _selectedId = item.id;
      _itemText.text = item.text;
      _tab = 1;
    });
  }

  Future<void> _addMediaOrMusic({required bool music}) async {
    final files = await FilePicker.pickFiles(
      type: music ? FileType.audio : FileType.media,
      allowMultiple: !music,
    );
    if (files.isEmpty) return;
    final track = _timeline.trackOf(music ? 'audio' : 'media');
    if (track == null) return;
    for (final picked in files) {
      final path = picked.path;
      if (path == null) continue;
      try {
        final asset = await widget.state.addAsset(path);
        final lower = asset.toLowerCase();
        final isVideo = !music &&
            ['.mp4', '.mov', '.webm', '.mkv', '.m4v'].any((ext) => lower.endsWith(ext));
        final end = math.min(music ? 10.0 : 4.0, math.max(1.0, _timeline.duration));
        track.items.add(TimelineItem(
          id: '${music ? 'a' : 'm'}${DateTime.now().microsecondsSinceEpoch}',
          start: 0,
          end: end,
          src: asset,
          type: music ? 'audio' : (isVideo ? 'video' : 'image'),
          scale: 0.6,
          gain: 0.6,
        ));
      } catch (error) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
        }
      }
    }
    setState(() => _selectedId = null);
  }

  Future<void> _save() async {
    final clip = widget.clip;
    clip.captions = _textToCaptions(_captions.text);
    final videoItems = _timeline.trackOf('video')?.items ?? const <TimelineItem>[];
    if (videoItems.isNotEmpty) {
      clip.crop = videoItems.first.crop;
      clip.canvas = videoItems.first.canvas;
    }
    clip.timeline = _timeline.toJson();
    await widget.state.saveClip(clip);
  }

  Future<void> _preview() async {
    try {
      await _save();
      final file = await widget.state.previewClip(widget.clip);
      if (mounted) setState(() => _previewPath = file.path);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }

  Future<void> _render() async {
    try {
      await _save();
      await widget.state.renderClip(widget.clip);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(widget.state.translate('common.done'))),
        );
        Navigator.of(context).pop();
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }

  // --------------------------------------------------------------------- UI

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    return Scaffold(
      appBar: AppBar(
        title: Text(state.translate('editor.title')),
        actions: [
          IconButton(
            tooltip: state.translate('editor.previewDraft'),
            onPressed: state.jobState == JobState.running ? null : _preview,
            icon: const Icon(Icons.play_circle_outline),
          ),
          IconButton(
            tooltip: state.translate('editor.save'),
            onPressed: _save,
            icon: const Icon(Icons.check),
          ),
          IconButton(
            tooltip: state.translate('clips.render'),
            onPressed: state.jobState == JobState.running ? null : _render,
            icon: const Icon(Icons.movie_creation_outlined),
          ),
        ],
      ),
      body: Column(
        children: [
          _previewBox(state),
          if (state.jobState == JobState.running)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: Tokens.space4),
              child: ProgressStrip(progress: state.jobProgress, label: state.jobStage),
            ),
          _tabBar(state),
          Expanded(child: _tabBody(state)),
        ],
      ),
    );
  }

  Widget _previewBox(AppState state) {
    final path = _previewPath;
    return Container(
      margin: const EdgeInsets.all(Tokens.space4),
      height: 220,
      decoration: BoxDecoration(
        color: Tokens.surface,
        borderRadius: BorderRadius.circular(Tokens.radius),
      ),
      clipBehavior: Clip.antiAlias,
      child: path != null
          ? VideoPreview(path: path)
          : Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.movie_outlined, color: Tokens.textDim, size: 30),
                  const SizedBox(height: Tokens.space2),
                  Text(state.translate('editor.timelineHint'),
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
                  const SizedBox(height: Tokens.space3),
                  FilledButton.icon(
                    onPressed: state.jobState == JobState.running ? null : _preview,
                    icon: const Icon(Icons.play_arrow_rounded, size: 18),
                    label: Text(state.translate('editor.previewDraft')),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _tabBar(AppState state) {
    final labels = [
      state.translate('editor.timeline'),
      state.translate('editor.text'),
      state.translate('editor.styleTab'),
    ];
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: Tokens.space4),
      child: Row(
        children: [
          for (var i = 0; i < labels.length; i++)
            Padding(
              padding: const EdgeInsets.only(right: Tokens.space2),
              child: ChoiceChip(
                label: Text(labels[i]),
                selected: _tab == i,
                onSelected: (_) => setState(() => _tab = i),
                selectedColor: Tokens.accent.withValues(alpha: 0.22),
                labelStyle: TextStyle(color: _tab == i ? Tokens.accent : Tokens.text2, fontSize: 13),
                backgroundColor: Tokens.surface2,
                side: BorderSide.none,
              ),
            ),
        ],
      ),
    );
  }

  Widget _tabBody(AppState state) {
    if (_tab == 0) return _timelineTab(state);
    if (_tab == 1) return _textTab(state);
    return _styleTab(state);
  }

  Widget _timelineTab(AppState state) {
    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        Wrap(spacing: Tokens.space2, runSpacing: Tokens.space2, children: [
          OutlinedButton.icon(
            onPressed: _addText,
            icon: const Icon(Icons.title, size: 18),
            label: Text(state.translate('editor.addText')),
          ),
          OutlinedButton.icon(
            onPressed: () => _addMediaOrMusic(music: false),
            icon: const Icon(Icons.image_outlined, size: 18),
            label: Text(state.translate('editor.addMedia')),
          ),
          OutlinedButton.icon(
            onPressed: () => _addMediaOrMusic(music: true),
            icon: const Icon(Icons.music_note_outlined, size: 18),
            label: Text(state.translate('editor.addMusic')),
          ),
        ]),
        const SizedBox(height: Tokens.space4),
        TimelineView(
          timeline: _timeline,
          selectedKind: _selectedKind,
          selectedId: _selectedId,
          onSelect: _select,
          onChange: _replace,
          onDelete: _remove,
        ),
        const SizedBox(height: Tokens.space4),
        Text(state.translate('editor.timelineHint'),
            style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
      ],
    );
  }

  Widget _textTab(AppState state) {
    final selected = _selected;
    final textItems = _timeline.trackOf('text')?.items ?? const <TimelineItem>[];
    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        if (textItems.isEmpty)
          EmptyState(state.translate('editor.noItem'))
        else
          SectionCard(
            title: state.translate('editor.addText'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final item in textItems)
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                    selected: item.id == _selectedId,
                    selectedColor: Tokens.accent,
                    leading: Icon(
                      item.id == _selectedId
                          ? Icons.radio_button_checked
                          : Icons.radio_button_unchecked,
                      size: 18,
                      color: item.id == _selectedId ? Tokens.accent : Tokens.textDim,
                    ),
                    onTap: () {
                      _select('text', item);
                      _itemText.text = item.text;
                    },
                    title: Text(item.text.isEmpty ? 'Teks' : item.text,
                        maxLines: 1, overflow: TextOverflow.ellipsis),
                    subtitle: Text('${item.start.toStringAsFixed(1)}s – ${item.end.toStringAsFixed(1)}s',
                        style: const TextStyle(fontSize: 11)),
                  ),
              ],
            ),
          ),
        if (selected != null && _selectedKind == 'text') ...[
          const SizedBox(height: Tokens.space3),
          SectionCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: _itemText,
                  maxLines: 3,
                  decoration: InputDecoration(labelText: state.translate('editor.itemText')),
                  onChanged: (value) => _replace('text', selected.copy()..text = value),
                ),
                const SizedBox(height: Tokens.space4),
                Text(state.translate('editor.template'),
                    style: const TextStyle(fontSize: 13, color: Tokens.textDim)),
                const SizedBox(height: Tokens.space2),
                _TemplateGallery(
                  selected: selected.template,
                  onPick: (template) => _replace('text', selected.copy()..template = template),
                ),
                const SizedBox(height: Tokens.space4),
                _SliderRow(
                  label: 'X',
                  value: selected.x,
                  onChanged: (value) => _replace('text', selected.copy()..x = value),
                ),
                _SliderRow(
                  label: 'Y',
                  value: selected.y,
                  onChanged: (value) => _replace('text', selected.copy()..y = value),
                ),
                const SizedBox(height: Tokens.space2),
                Row(children: [
                  Expanded(
                    child: TextFormField(
                      initialValue: selected.start.toStringAsFixed(2),
                      decoration: const InputDecoration(labelText: 'Mulai (s)'),
                      keyboardType: TextInputType.number,
                      onFieldSubmitted: (value) {
                        final parsed = double.tryParse(value);
                        if (parsed != null) _replace('text', selected.copy()..start = parsed);
                      },
                    ),
                  ),
                  const SizedBox(width: Tokens.space3),
                  Expanded(
                    child: TextFormField(
                      initialValue: selected.end.toStringAsFixed(2),
                      decoration: const InputDecoration(labelText: 'Selesai (s)'),
                      keyboardType: TextInputType.number,
                      onFieldSubmitted: (value) {
                        final parsed = double.tryParse(value);
                        if (parsed != null) _replace('text', selected.copy()..end = parsed);
                      },
                    ),
                  ),
                ]),
                const SizedBox(height: Tokens.space3),
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton.icon(
                    onPressed: () => _remove('text', selected),
                    icon: const Icon(Icons.delete_outline_rounded, size: 18),
                    label: Text(state.translate('editor.deleteItem')),
                    style: TextButton.styleFrom(foregroundColor: Tokens.danger),
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _styleTab(AppState state) {
    final videoItems = _timeline.trackOf('video')?.items ?? const <TimelineItem>[];
    final base = videoItems.isEmpty ? null : videoItems.first;
    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        SectionCard(
          title: state.translate('editor.crop'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(spacing: Tokens.space2, runSpacing: Tokens.space2, children: [
                for (final option in const [
                  ['center', 'Center 9:16'],
                  ['blur', 'Blur BG'],
                  ['fit', 'Fit (tidak memotong)'],
                  ['none', 'Letterbox'],
                ])
                  ChoiceChip(
                    label: Text(option[1]),
                    selected: (base?.crop ?? widget.clip.crop) == option[0],
                    onSelected: (_) {
                      if (base != null) _replace('video', base.copy()..crop = option[0]);
                    },
                    selectedColor: Tokens.accent.withValues(alpha: 0.22),
                    backgroundColor: Tokens.surface2,
                    labelStyle: TextStyle(
                      fontSize: 12,
                      color: (base?.crop ?? widget.clip.crop) == option[0] ? Tokens.accent : Tokens.text2,
                    ),
                    side: BorderSide.none,
                  ),
              ]),
              const SizedBox(height: Tokens.space2),
              Text(state.translate('editor.trimHint'),
                  style: const TextStyle(color: Tokens.textDim, fontSize: 11)),
            ],
          ),
        ),
        const SizedBox(height: Tokens.space3),
        SectionCard(
          child: Column(children: [
            DropdownButtonFormField<String>(
              initialValue: base?.canvas ?? widget.clip.canvas,
              decoration: const InputDecoration(labelText: 'Ukuran klip'),
              items: const [
                DropdownMenuItem(value: 'portrait', child: Text('Potrait 9:16 (TikTok/Reels)')),
                DropdownMenuItem(value: 'original', child: Text('Ukuran asli video')),
                DropdownMenuItem(value: 'square', child: Text('Kotak 1:1')),
                DropdownMenuItem(value: 'landscape', child: Text('Landscape 16:9')),
              ],
              onChanged: (value) {
                if (base != null && value != null) _replace('video', base.copy()..canvas = value);
              },
            ),
            const SizedBox(height: Tokens.space3),
            DropdownButtonFormField<String>(
              initialValue: widget.clip.audioMode,
              decoration: InputDecoration(labelText: state.translate('editor.audio')),
              items: [
                DropdownMenuItem(value: 'original', child: Text(state.translate('audio.original'))),
                DropdownMenuItem(value: 'voice', child: Text(state.translate('audio.voice'))),
                DropdownMenuItem(value: 'mix', child: Text(state.translate('audio.mix'))),
              ],
              onChanged: (value) => setState(() => widget.clip.audioMode = value ?? 'original'),
            ),
          ]),
        ),
        const SizedBox(height: Tokens.space3),
        SectionCard(
          title: state.translate('editor.style'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(state.translate('editor.template'),
                  style: const TextStyle(fontSize: 13, color: Tokens.textDim)),
              const SizedBox(height: Tokens.space2),
              _TemplateGallery(
                selected: widget.clip.subtitlePreset,
                onPick: (preset) => setState(() => widget.clip.subtitlePreset = preset),
              ),
            ],
          ),
        ),
        const SizedBox(height: Tokens.space3),
        SectionCard(
          title: state.translate('editor.captions'),
          child: TextField(
            controller: _captions,
            maxLines: 8,
            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
          ),
        ),
      ],
    );
  }
}

/// Galeri template tipografi (nama + contoh warna gaya).
class _TemplateGallery extends StatelessWidget {
  const _TemplateGallery({required this.selected, required this.onPick});

  final String selected;
  final void Function(String preset) onPick;

  @override
  Widget build(BuildContext context) {
    final presets = SubtitleBuilder.presetList();
    return Wrap(
      spacing: Tokens.space2,
      runSpacing: Tokens.space2,
      children: [
        for (final preset in presets)
          GestureDetector(
            onTap: () => onPick(preset['id']!),
            child: Container(
              width: 104,
              padding: const EdgeInsets.all(Tokens.space2),
              decoration: BoxDecoration(
                color: Tokens.surface2,
                borderRadius: BorderRadius.circular(Tokens.radiusSm),
                border: Border.all(
                  color: preset['id'] == selected ? Tokens.accent : Colors.transparent,
                  width: 1.5,
                ),
              ),
              child: Column(
                children: [
                  Text('Aa',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: preset['id'] == selected ? Tokens.accent : Tokens.text,
                      )),
                  const SizedBox(height: 2),
                  Text(preset['label']!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 11, color: Tokens.textDim)),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _SliderRow extends StatelessWidget {
  const _SliderRow({required this.label, required this.value, required this.onChanged});

  final String label;
  final double value;
  final ValueChanged<double> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(width: 18, child: Text(label, style: const TextStyle(color: Tokens.textDim, fontSize: 12))),
        Expanded(
          child: Slider(
            value: value.clamp(0.0, 1.0),
            onChanged: onChanged,
            activeColor: Tokens.accent,
          ),
        ),
        SizedBox(width: 34, child: Text(value.toStringAsFixed(2), style: const TextStyle(fontSize: 11))),
      ],
    );
  }
}
