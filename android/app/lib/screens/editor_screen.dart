import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../models.dart';
import '../services/subtitle_builder.dart';
import '../services/creator_tools.dart';
import '../services/timeline.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import '../widgets/preview_player.dart';
import '../widgets/timeline_view.dart';
import '../widgets/typography_editor.dart';
import 'models_screen.dart';
import 'creator_screen.dart';

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
  Timer? _changeTimer, _previewTimer;
  bool _previewBusy = false;
  String _lastFingerprint = '';
  String _previewMessage = '';
  String _fingerprint() => jsonEncode([
        _timeline.toJson(),
        _captions.text,
        widget.clip.captions,
        widget.clip.subtitlePreset,
        widget.clip.subtitlePosition,
        widget.clip.audioMode
      ]);

  void _schedulePreview() {
    _previewTimer?.cancel();
    _previewTimer = Timer(const Duration(milliseconds: 1000), _preview);
  }

  @override
  void initState() {
    super.initState();
    final clip = widget.clip;
    _timeline = widget.state.timelineForClip(clip);
    _captions = TextEditingController(text: _captionsToText(clip));
    _itemText = TextEditingController();
    widget.state.addListener(_stateChanged);
    final output = clip.files['mp4'];
    if (output != null && File(output).existsSync()) _previewPath = output;
    _lastFingerprint = _fingerprint();
    _schedulePreview();
    _changeTimer = Timer.periodic(const Duration(milliseconds: 350), (_) {
      final current = _fingerprint();
      if (current != _lastFingerprint) {
        _lastFingerprint = current;
        _schedulePreview();
      }
    });
  }

  void _stateChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _changeTimer?.cancel();
    _previewTimer?.cancel();
    widget.state.removeListener(_stateChanged);
    _captions.dispose();
    _itemText.dispose();
    super.dispose();
  }

  // ------------------------------------------------------------------ helpers

  String _captionsToText(Clip clip) => clip.captions
      .map((c) =>
          '${(c['start'] as num).toStringAsFixed(2)}|${(c['end'] as num).toStringAsFixed(2)}|${c['text']}')
      .join('\n');

  List<Map<String, dynamic>> _textToCaptions(String value) {
    return SubtitleBuilder.parseEditorDraft(value).asMap().entries.map((e) {
      final old = e.key < widget.clip.captions.length
          ? widget.clip.captions[e.key]
          : null;
      return old != null &&
              old['text'] == e.value['text'] &&
              old['start'] == e.value['start'] &&
              old['end'] == e.value['end']
          ? old
          : e.value;
    }).toList();
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
      _itemText.text = item.text;
    });
  }

  void _replace(String kind, TimelineItem item) {
    final track = _timeline.trackOf(kind);
    if (track == null) return;
    final index = track.items.indexWhere((entry) => entry.id == item.id);
    if (index < 0) return;
    if (kind == 'video') {
      final old = track.items[index];
      item.srcStart += item.start - old.start;
      item.end = (item.end - item.start)
          .clamp(.2, widget.state.currentProject!.duration - item.srcStart);
      item.start = 0;
    }
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
      _timeline
          .trackOf(kind)
          ?.items
          .removeWhere((entry) => entry.id == item.id);
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
    // `pickFiles` di file_picker 13 sudah mengizinkan pilih satu atau banyak
    // berkas, jadi tidak ada parameter allowMultiple.
    final files = await FilePicker.pickFiles(
        type: music ? FileType.audio : FileType.media);
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
            ['.mp4', '.mov', '.webm', '.mkv', '.m4v']
                .any((ext) => lower.endsWith(ext));
        final end =
            math.min(music ? 10.0 : 4.0, math.max(1.0, _timeline.duration));
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
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text('$error')));
        }
      }
    }
    setState(() => _selectedId = null);
  }

  Future<void> _creator() async {
    if (_previewBusy) return;
    _previewTimer?.cancel();
    _changeTimer?.cancel();
    try {
      await _save();
      if (!mounted) return;
      await Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => CreatorScreen(
              clip: widget.clip,
              timeline: _timeline,
              project: widget.state.currentProject!,
              directory:
                  widget.state.projectDir(widget.state.currentProject!))));
      if (!mounted) return;
      _captions.text = _captionsToText(widget.clip);
      await _save();
      setState(() {});
    } finally {
      if (mounted) {
        _schedulePreview();
        _changeTimer = Timer.periodic(const Duration(milliseconds: 350), (_) {
          final next = _fingerprint();
          if (next != _lastFingerprint) {
            _lastFingerprint = next;
            _schedulePreview();
          }
        });
      }
    }
  }

  Future<void> _save() async {
    final clip = widget.clip;
    if (_captions.text != _captionsToText(clip)) {
      clip.captions = _textToCaptions(_captions.text);
    }
    final videoItems =
        _timeline.trackOf('video')?.items ?? const <TimelineItem>[];
    if (videoItems.isNotEmpty) {
      clip.crop = videoItems.first.crop;
      clip.canvas = videoItems.first.canvas;
      final delta = videoItems.first.srcStart - clip.start;
      final length = videoItems.first.end - videoItems.first.start;
      final rangeChanged =
          delta.abs() > 0.000001 || (clip.duration - length).abs() > 0.000001;
      if (rangeChanged) {
        clip.captions = CreatorTools.trimRows(clip.captions, delta, length);
        clip.captionVariants = clip.captionVariants.map((lang, rows) =>
            MapEntry(lang, CreatorTools.trimRows(rows, delta, length)));
        videoItems.first.framing =
            CreatorTools.trimFraming(videoItems.first.framing, delta, length);
        _captions.text = _captionsToText(clip);
      }
      clip.start = videoItems.first.srcStart;
      clip.end = clip.start + videoItems.first.end - videoItems.first.start;
    }
    clip.timeline = _timeline.toJson();
    await widget.state.saveClip(clip);
  }

  Future<void> _saveWithFeedback() async {
    try {
      await _save();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Perubahan tersimpan.')));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }

  Future<void> _preview() async {
    if (!mounted) return;
    if (_previewBusy || widget.state.jobState == JobState.running) {
      _schedulePreview();
      return;
    }
    _previewBusy = true;
    setState(() => _previewMessage = 'Memperbarui video…');
    try {
      await _save();
      final fingerprint = _fingerprint();
      _lastFingerprint = fingerprint;
      final snapshot = Clip.fromJson(
          jsonDecode(jsonEncode(widget.clip.toJson())) as Map<String, dynamic>);
      final file = await widget.state.previewClip(snapshot);
      if (!mounted) return;
      if (fingerprint != _fingerprint()) {
        _schedulePreview();
        return;
      }
      setState(() {
        _previewPath = file.path;
        _previewMessage = '';
      });
    } catch (error) {
      if (mounted) {
        setState(() => _previewMessage = 'Perubahan belum tampil: $error');
      }
    } finally {
      _previewBusy = false;
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
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }

  Future<void> _split() async {
    try {
      await _save();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
      return;
    }
    if (!mounted) return;
    final field = TextEditingController(
        text: (widget.clip.duration / 2).toStringAsFixed(1));
    final value = await showDialog<double>(
        context: context,
        builder: (ctx) => AlertDialog(
              title: const Text('Pisahkan klip'),
              content: TextField(
                  controller: field,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                      labelText: 'Detik dari awal klip',
                      helperText:
                          'Pilih antara 0.5 dan ${(widget.clip.duration - .5).toStringAsFixed(1)}')),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text('Batal')),
                FilledButton(
                    onPressed: () {
                      final at = double.tryParse(field.text);
                      if (at != null &&
                          at >= .5 &&
                          at <= widget.clip.duration - .5) {
                        Navigator.pop(ctx, at);
                      }
                    },
                    child: const Text('Pisahkan'))
              ],
            ));
    Future<void>.delayed(const Duration(milliseconds: 250), field.dispose);
    if (value == null) return;
    await widget.state.splitClip(widget.clip, value);
    if (mounted) Navigator.pop(context);
  }

  Future<void> _generateCaptions() async {
    try {
      _previewTimer?.cancel();
      await _save();
      final count = await widget.state.generateCaptions(widget.clip);
      if (!mounted) return;
      setState(() {
        _captions.text = _captionsToText(widget.clip);
        if (count > 0 && widget.clip.subtitlePosition == 'off') {
          widget.clip.subtitlePosition = 'bottom';
        }
      });
      if (count > 0) _schedulePreview();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(count == 0
              ? 'Tidak ada ucapan terdeteksi. Subtitle yang ada tetap tersimpan.'
              : '$count subtitle siap. Pratinjau sedang diperbarui.')));
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
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
              tooltip: 'Caption per kata, terjemahan & crop',
              onPressed: state.jobState == JobState.running ? null : _creator,
              icon: const Icon(Icons.auto_fix_high)),
          IconButton(
              tooltip: 'Pisahkan klip',
              onPressed: state.jobState == JobState.running ? null : _split,
              icon: const Icon(Icons.content_cut)),
          TextButton.icon(
              onPressed: _saveWithFeedback,
              icon: const Icon(Icons.check, size: 18),
              label: const Text('Simpan'))
        ],
      ),
      bottomNavigationBar: SafeArea(
          child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              child: Row(children: [
                Expanded(
                    child: FilledButton.icon(
                        onPressed:
                            state.jobState == JobState.running ? null : _render,
                        icon: const Icon(Icons.ios_share, size: 18),
                        label: const Text('Ekspor video'))),
              ]))),
      body: Column(
        children: [
          _previewBox(state),
          if (state.jobState == JobState.running)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: Tokens.space4),
              child: ProgressStrip(
                  progress: state.jobProgress, label: state.jobStage),
            ),
          _tabBar(state),
          Expanded(child: _tabBody(state)),
        ],
      ),
    );
  }

  Widget _previewBox(AppState state) {
    final path = _previewPath ?? state.currentProject?.source;
    final height = math.min(
        360.0, math.max(210.0, MediaQuery.sizeOf(context).height * .35));
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          Tokens.space4, Tokens.space3, Tokens.space4, Tokens.space4),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Padding(
          padding: const EdgeInsets.only(bottom: Tokens.space2),
          child: Row(children: [
            const Icon(Icons.play_circle_outline_rounded,
                size: 17, color: Tokens.textDim),
            const SizedBox(width: Tokens.space2),
            const Text('Video',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
            const Spacer(),
            if (_previewMessage.isNotEmpty)
              Flexible(
                  child: Text(_previewMessage,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          fontSize: 11, color: Tokens.textDim))),
          ]),
        ),
        Container(
          width: double.infinity,
          height: height,
          decoration: BoxDecoration(
            color: Tokens.surface,
            borderRadius: BorderRadius.circular(Tokens.radius),
          ),
          clipBehavior: ui.Clip.antiAlias,
          child: path == null
              ? const Center(
                  child: Text('Video belum tersedia',
                      style: TextStyle(color: Tokens.textDim)))
              : Center(
                  child: VideoPreview(
                      key: ValueKey(path),
                      path: path,
                      startSeconds:
                          _previewPath == null ? widget.clip.start : 0,
                      endSeconds:
                          _previewPath == null ? widget.clip.end : null)),
        ),
      ]),
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
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
            color: Tokens.surface,
            borderRadius: BorderRadius.circular(Tokens.radiusSm)),
        child: Row(children: [
          for (var i = 0; i < labels.length; i++)
            Expanded(
                child: Padding(
              padding: EdgeInsets.only(right: i == labels.length - 1 ? 0 : 4),
              child: TextButton(
                onPressed: () => setState(() => _tab = i),
                style: TextButton.styleFrom(
                  foregroundColor: _tab == i ? Tokens.text : Tokens.textDim,
                  backgroundColor:
                      _tab == i ? Tokens.surface3 : Colors.transparent,
                  minimumSize: const Size(0, 38),
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(Tokens.radiusSm - 3)),
                ),
                child: Text(labels[i],
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12)),
              ),
            )),
        ]),
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
    final textItems =
        _timeline.trackOf('text')?.items ?? const <TimelineItem>[];
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
                      color: item.id == _selectedId
                          ? Tokens.accent
                          : Tokens.textDim,
                    ),
                    onTap: () {
                      _select('text', item);
                      _itemText.text = item.text;
                    },
                    title: Text(item.text.isEmpty ? 'Teks' : item.text,
                        maxLines: 1, overflow: TextOverflow.ellipsis),
                    subtitle: Text(
                        '${item.start.toStringAsFixed(1)}s – ${item.end.toStringAsFixed(1)}s',
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
                  decoration: InputDecoration(
                      labelText: state.translate('editor.itemText')),
                  onChanged: (value) =>
                      _replace('text', selected.copy()..text = value),
                ),
                const SizedBox(height: Tokens.space4),
                Text(state.translate('editor.template'),
                    style:
                        const TextStyle(fontSize: 13, color: Tokens.textDim)),
                const SizedBox(height: Tokens.space2),
                _TemplateGallery(
                  selected: selected.template,
                  onPick: (template) =>
                      _replace('text', selected.copy()..template = template),
                ),
                const SizedBox(height: Tokens.space4),
                _PositionPicker(
                  x: selected.x,
                  y: selected.y,
                  onChanged: (x, y) => _replace(
                      'text',
                      selected.copy()
                        ..x = x
                        ..y = y),
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
                        if (parsed != null) {
                          _replace('text', selected.copy()..start = parsed);
                        }
                      },
                    ),
                  ),
                  const SizedBox(width: Tokens.space3),
                  Expanded(
                    child: TextFormField(
                      initialValue: selected.end.toStringAsFixed(2),
                      decoration:
                          const InputDecoration(labelText: 'Selesai (s)'),
                      keyboardType: TextInputType.number,
                      onFieldSubmitted: (value) {
                        final parsed = double.tryParse(value);
                        if (parsed != null) {
                          _replace('text', selected.copy()..end = parsed);
                        }
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
    final videoItems =
        _timeline.trackOf('video')?.items ?? const <TimelineItem>[];
    final base = videoItems.isEmpty ? null : videoItems.first;
    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        SectionCard(
          title: state.translate('editor.crop'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                  spacing: Tokens.space2,
                  runSpacing: Tokens.space2,
                  children: [
                    for (final option in const [
                      ['center', 'Center crop'],
                      ['manual', 'Manual / keyframe'],
                      ['blur', 'Blur BG'],
                      ['fit', 'Fit (tidak memotong)'],
                      ['none', 'Letterbox'],
                    ])
                      ChoiceChip(
                        label: Text(option[1]),
                        selected: (base?.crop ?? widget.clip.crop) == option[0],
                        onSelected: (_) {
                          if (base != null) {
                            _replace('video', base.copy()..crop = option[0]);
                          }
                        },
                        selectedColor: Tokens.accent.withValues(alpha: 0.22),
                        backgroundColor: Tokens.surface2,
                        labelStyle: TextStyle(
                          fontSize: 12,
                          color: (base?.crop ?? widget.clip.crop) == option[0]
                              ? Tokens.accent
                              : Tokens.text2,
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
                DropdownMenuItem(
                    value: 'portrait',
                    child: Text('Portrait 9:16 (TikTok/Reels)')),
                DropdownMenuItem(
                    value: 'original', child: Text('Ukuran asli video')),
                DropdownMenuItem(value: 'square', child: Text('Kotak 1:1')),
                DropdownMenuItem(
                    value: 'landscape', child: Text('Landscape 16:9')),
              ],
              onChanged: (value) {
                if (base != null && value != null) {
                  _replace('video', base.copy()..canvas = value);
                }
              },
            ),
            const SizedBox(height: Tokens.space3),
            DropdownButtonFormField<String>(
              initialValue: widget.clip.audioMode,
              decoration:
                  InputDecoration(labelText: state.translate('editor.audio')),
              items: [
                DropdownMenuItem(
                    value: 'original',
                    child: Text(state.translate('audio.original'))),
                DropdownMenuItem(
                    value: 'voice',
                    child: Text(state.translate('audio.voice'))),
                DropdownMenuItem(
                    value: 'mix', child: Text(state.translate('audio.mix'))),
              ],
              onChanged: (value) =>
                  setState(() => widget.clip.audioMode = value ?? 'original'),
            ),
          ]),
        ),
        const SizedBox(height: Tokens.space3),
        SectionCard(
          title: state.translate('editor.style'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              OutlinedButton.icon(
                  onPressed: () async {
                    final id = await editTypography(context, state);
                    if (id != null && mounted) {
                      setState(() => widget.clip.subtitlePreset = id);
                    }
                  },
                  icon: const Icon(Icons.add),
                  label: const Text('Buat template sendiri')),
              DropdownButtonFormField<String>(
                  initialValue: widget.clip.subtitlePosition,
                  decoration:
                      const InputDecoration(labelText: 'Posisi subtitle'),
                  items: const [
                    DropdownMenuItem(value: 'bottom', child: Text('Bawah')),
                    DropdownMenuItem(value: 'middle', child: Text('Tengah')),
                    DropdownMenuItem(value: 'top', child: Text('Atas')),
                    DropdownMenuItem(
                        value: 'off', child: Text('Tanpa subtitle tambahan'))
                  ],
                  onChanged: (v) =>
                      setState(() => widget.clip.subtitlePosition = v!)),
              const Text(
                  'Gaya berlaku untuk semua subtitle klip ini. Video diperbarui otomatis setelah perubahan.',
                  style: TextStyle(fontSize: 12, color: Tokens.textDim)),
              Text(state.translate('editor.template'),
                  style: const TextStyle(fontSize: 13, color: Tokens.textDim)),
              const SizedBox(height: Tokens.space2),
              _TemplateGallery(
                selected: widget.clip.subtitlePreset,
                onPick: (preset) =>
                    setState(() => widget.clip.subtitlePreset = preset),
              ),
            ],
          ),
        ),
        const SizedBox(height: Tokens.space3),
        SectionCard(
          title: state.translate('editor.captions'),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text(
                'Transkrip adalah teks ucapan; subtitle menempatkan teks itu pada waktu tertentu di video. Format: mulai|selesai|teks (detik).'),
            const SizedBox(height: Tokens.space3),
            if (!state.catalog
                .any((m) => m.id == state.asrModelId && m.installed)) ...[
              Text('Model transkripsi ${state.asrModelId} belum terpasang.',
                  style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
              TextButton.icon(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute<void>(
                    builder: (_) => Scaffold(
                      appBar: AppBar(title: const Text('Model')),
                      body: ModelsScreen(state: state),
                    ),
                  ),
                ),
                icon: const Icon(Icons.download_outlined, size: 18),
                label: const Text('Pasang model transkripsi'),
              ),
            ],
            FilledButton.icon(
              onPressed: state.jobState == JobState.running ||
                      !state.catalog
                          .any((m) => m.id == state.asrModelId && m.installed)
                  ? null
                  : _generateCaptions,
              icon: const Icon(Icons.closed_caption_outlined),
              label: const Text('Buat subtitle otomatis'),
            ),
            if (state.jobState == JobState.running &&
                state.jobStage.contains('transkrip')) ...[
              const SizedBox(height: Tokens.space2),
              ProgressStrip(progress: state.jobProgress, label: state.jobStage),
            ],
            const SizedBox(height: Tokens.space3),
            TextField(
              controller: _captions,
              maxLines: 8,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
              decoration: const InputDecoration(
                labelText: 'Teks subtitle per baris',
                helperText: 'Contoh: 0.00|2.50|Halo semuanya',
                alignLabelWithHint: true,
              ),
            ),
          ]),
        ),
      ],
    );
  }
}

/// Render previews use the same bundled fonts and palette as the ASS exporter.
class _TemplateGallery extends StatefulWidget {
  const _TemplateGallery({required this.selected, required this.onPick});
  final String selected;
  final ValueChanged<String> onPick;
  @override
  State<_TemplateGallery> createState() => _TemplateGalleryState();
}

class _TemplateGalleryState extends State<_TemplateGallery> {
  String category = 'Pop';
  Color hex(Object? value, Color fallback) {
    final text = value?.toString().replaceFirst('#', '');
    return text != null && text.length == 6
        ? Color(0xff000000 | int.parse(text, radix: 16))
        : fallback;
  }

  @override
  Widget build(BuildContext context) {
    final entries = SubtitleBuilder.presets.entries.where((e) =>
        category == 'Semua' ||
        (e.value['category'] ?? 'Essential') == category);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(children: [
            for (final c in [
              'Semua',
              'Pop',
              'Neon',
              'Editorial',
              'Label',
              'Essential',
              'Custom'
            ])
              Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: ChoiceChip(
                      label: Text(c),
                      selected: category == c,
                      onSelected: (_) => setState(() => category = c))),
          ])),
      const SizedBox(height: 12),
      LayoutBuilder(
          builder: (context, constraints) =>
              Wrap(spacing: 10, runSpacing: 10, children: [
                for (final entry in entries)
                  SizedBox(
                      width: (constraints.maxWidth - 10) / 2,
                      child: Material(
                        color: Tokens.surface2,
                        borderRadius: BorderRadius.circular(12),
                        child: InkWell(
                            borderRadius: BorderRadius.circular(12),
                            onTap: () => widget.onPick(entry.key),
                            child: Container(
                              decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                      color: widget.selected == entry.key
                                          ? Tokens.accent
                                          : Tokens.separator)),
                              child: Column(children: [
                                Container(
                                    height: 88,
                                    padding: const EdgeInsets.all(10),
                                    alignment: Alignment.center,
                                    child: Container(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 5, vertical: 2),
                                        color: entry.value['border'] == 3
                                            ? hex(
                                                entry.value['preview_outline'],
                                                Colors.black)
                                            : null,
                                        child: Text(
                                            entry.value['sample'] as String? ??
                                                'Tell your story',
                                            textAlign: TextAlign.center,
                                            maxLines: 2,
                                            overflow: TextOverflow.ellipsis,
                                            style: TextStyle(
                                                fontFamily: entry.value['font']
                                                        as String? ??
                                                    'Roboto',
                                                fontSize: 23,
                                                height: 1.1,
                                                fontWeight: FontWeight.w700,
                                                fontStyle:
                                                    entry.value['italic'] ==
                                                            true
                                                        ? FontStyle.italic
                                                        : FontStyle.normal,
                                                color: hex(
                                                    entry
                                                        .value['preview_color'],
                                                    Colors.white),
                                                shadows:
                                                    entry.value['border'] == 3
                                                        ? null
                                                        : [
                                                            Shadow(
                                                                color: hex(
                                                                    entry.value[
                                                                        'preview_outline'],
                                                                    Colors
                                                                        .black),
                                                                blurRadius:
                                                                    category ==
                                                                            'Neon'
                                                                        ? 12
                                                                        : 2,
                                                                offset:
                                                                    const Offset(
                                                                        1, 1))
                                                          ])))),
                                Padding(
                                    padding: const EdgeInsets.fromLTRB(
                                        10, 0, 10, 10),
                                    child: Row(children: [
                                      Expanded(
                                          child: Text(
                                              entry.value['label'] as String,
                                              style: const TextStyle(
                                                  fontSize: 11,
                                                  color: Tokens.text2),
                                              overflow: TextOverflow.ellipsis)),
                                      Icon(
                                          widget.selected == entry.key
                                              ? Icons.check_circle
                                              : Icons.add,
                                          size: 15,
                                          color: widget.selected == entry.key
                                              ? Tokens.accent
                                              : Tokens.textDim),
                                    ])),
                              ]),
                            )),
                      )),
              ])),
    ]);
  }
}

class _PositionPicker extends StatelessWidget {
  const _PositionPicker(
      {required this.x, required this.y, required this.onChanged});
  final double x, y;
  final void Function(double x, double y) onChanged;
  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Posisi teks',
              style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: Tokens.space1),
          const Text('Sentuh atau geser titik di kanvas.',
              style: TextStyle(fontSize: 12, color: Tokens.textDim)),
          const SizedBox(height: Tokens.space3),
          Center(
              child: SizedBox(
            width: 112,
            height: 184,
            child: LayoutBuilder(builder: (context, constraints) {
              void move(Offset point) => onChanged(
                    (point.dx / constraints.maxWidth).clamp(0.06, 0.94),
                    (point.dy / constraints.maxHeight).clamp(0.06, 0.94),
                  );
              return Semantics(
                label: 'Posisi teks dalam kanvas',
                child: GestureDetector(
                  onTapDown: (details) => move(details.localPosition),
                  onPanUpdate: (details) => move(details.localPosition),
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: Tokens.surface2,
                      border: Border.all(color: Tokens.surface3),
                      borderRadius: BorderRadius.circular(Tokens.radiusSm),
                    ),
                    child: Stack(children: [
                      Positioned(
                        left: x * (constraints.maxWidth - 22),
                        top: y * (constraints.maxHeight - 22),
                        child: Container(
                          width: 22,
                          height: 22,
                          decoration: BoxDecoration(
                            color: Tokens.accent,
                            borderRadius: BorderRadius.circular(7),
                          ),
                          child: const Icon(Icons.title,
                              size: 14, color: Tokens.text),
                        ),
                      ),
                    ]),
                  ),
                ),
              );
            }),
          )),
          const SizedBox(height: Tokens.space3),
          Row(children: [
            for (final entry in const [
              ('Atas', .18),
              ('Tengah', .5),
              ('Bawah', .82),
            ])
              Expanded(
                  child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 3),
                child: OutlinedButton(
                  onPressed: () => onChanged(x, entry.$2),
                  style: OutlinedButton.styleFrom(
                    backgroundColor: (y - entry.$2).abs() < .08
                        ? Tokens.surface3
                        : Tokens.surface2,
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                  ),
                  child: Text(entry.$1, style: const TextStyle(fontSize: 12)),
                ),
              )),
          ]),
          ExpansionTile(
            tilePadding: EdgeInsets.zero,
            childrenPadding: const EdgeInsets.only(bottom: Tokens.space3),
            title: const Text('Posisi presisi', style: TextStyle(fontSize: 13)),
            children: [
              Row(children: [
                Expanded(
                    child: TextFormField(
                  key: ValueKey('x$x'),
                  initialValue: (x * 100).round().toString(),
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'X (%)'),
                  onFieldSubmitted: (value) {
                    final parsed = double.tryParse(value);
                    if (parsed != null) {
                      onChanged((parsed / 100).clamp(0, 1), y);
                    }
                  },
                )),
                const SizedBox(width: Tokens.space3),
                Expanded(
                    child: TextFormField(
                  key: ValueKey('y$y'),
                  initialValue: (y * 100).round().toString(),
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Y (%)'),
                  onFieldSubmitted: (value) {
                    final parsed = double.tryParse(value);
                    if (parsed != null) {
                      onChanged(x, (parsed / 100).clamp(0, 1));
                    }
                  },
                )),
              ])
            ],
          ),
        ],
      );
}
