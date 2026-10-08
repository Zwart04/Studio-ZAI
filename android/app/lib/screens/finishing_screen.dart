import 'dart:io';

import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';

import '../models.dart';
import '../services/timeline.dart';
import '../state/app_state.dart';

class FinishingScreen extends StatefulWidget {
  const FinishingScreen({
    super.key,
    required this.state,
    required this.clip,
    required this.timeline,
  });
  final AppState state;
  final Clip clip;
  final Timeline timeline;
  @override
  State<FinishingScreen> createState() => _FinishingScreenState();
}

class _FinishingScreenState extends State<FinishingScreen> {
  late TextEditingController title, watermark;
  bool titleEnabled = false;
  String preset = 'viral_yellow', kind = 'none', logo = '';
  double seconds = 3,
      titleSize = 86,
      titleX = .5,
      titleY = .16,
      wmSize = 38,
      wmScale = .18,
      wmX = .85,
      wmY = .1,
      opacity = .75;
  @override
  void initState() {
    super.initState();
    final texts = widget.timeline.trackOf('text')!.items;
    final opening = texts.where((i) => i.id == 'creator_title').firstOrNull;
    final mark = [
      ...texts,
      ...widget.timeline.trackOf('media')!.items,
    ].where((i) => i.id == 'creator_watermark').firstOrNull;
    title = TextEditingController(text: opening?.text ?? widget.clip.title);
    watermark = TextEditingController(text: mark?.text ?? '@namamu');
    titleEnabled = opening != null;
    preset = opening?.template ?? preset;
    seconds = (opening?.end ?? 3).clamp(.2, widget.clip.duration);
    titleSize = (opening?.fontSize ?? 0) > 0 ? opening!.fontSize : 86;
    if (opening == null) titleSize = 86;
    titleX = opening?.x ?? titleX;
    titleY = opening?.y ?? titleY;
    kind = mark?.type ?? 'none';
    logo = mark?.src ?? '';
    wmX = mark?.x ?? wmX;
    wmY = mark?.y ?? wmY;
    opacity = mark?.opacity ?? opacity;
    wmScale = mark?.scale ?? wmScale;
    wmSize = (mark?.fontSize ?? 0) > 0 ? mark!.fontSize : 38;
  }

  @override
  void dispose() {
    title.dispose();
    watermark.dispose();
    super.dispose();
  }

  Widget slider(
    String label,
    double value,
    double min,
    double max,
    ValueChanged<double> changed,
  ) =>
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$label · ${value.toStringAsFixed(2)}'),
          Slider(
            value: value.clamp(min, max),
            min: min,
            max: max,
            onChanged: (v) => setState(() => changed(v)),
          ),
        ],
      );
  Future<void> pickLogo() async {
    try {
      final files = await FilePicker.pickFiles(type: FileType.image);
      if (files.isEmpty || files.first.path == null) return;
      final path = await widget.state.addAsset(files.first.path!);
      if (mounted) setState(() => logo = path);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  void save() {
    if (kind == 'image' && logo.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pilih logo terlebih dahulu.')),
      );
      return;
    }
    for (final k in ['text', 'media']) {
      widget.timeline.trackOf(k)!.items.removeWhere(
            (i) => ['creator_title', 'creator_watermark'].contains(i.id),
          );
    }
    if (titleEnabled && title.text.trim().isNotEmpty) {
      widget.timeline.trackOf('text')!.items.add(
            TimelineItem(
              id: 'creator_title',
              type: 'text',
              start: 0,
              end: seconds,
              text: title.text.trim(),
              template: preset,
              x: titleX,
              y: titleY,
              fontSize: titleSize,
            ),
          );
      widget.clip.title = title.text.trim();
    }
    if (kind != 'none') {
      widget.timeline.trackOf(kind == 'text' ? 'text' : 'media')!.items.add(
            TimelineItem(
              id: 'creator_watermark',
              type: kind,
              start: 0,
              end: widget.clip.duration,
              text: watermark.text.trim(),
              src: logo,
              template: 'clean',
              fontSize: wmSize,
              scale: wmScale,
              opacity: opacity,
              x: wmX,
              y: wmY,
            ),
          );
    }
    Navigator.pop(context, true);
  }

  @override
  Widget build(BuildContext context) => DefaultTabController(
        length: 2,
        child: Scaffold(
          appBar: AppBar(
            title: const Text('Judul & watermark'),
            bottom: const TabBar(
              tabs: [
                Tab(text: 'Judul pembuka'),
                Tab(text: 'Watermark'),
              ],
            ),
            actions: [
              TextButton(onPressed: save, child: const Text('Terapkan'))
            ],
          ),
          body: TabBarView(
            children: [
              ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  SwitchListTile(
                    title: const Text('Tampilkan judul di atas video'),
                    value: titleEnabled,
                    onChanged: (v) => setState(() => titleEnabled = v),
                  ),
                  TextField(
                    controller: title,
                    maxLines: 3,
                    decoration:
                        const InputDecoration(labelText: 'Judul / hook'),
                  ),
                  OutlinedButton(
                    onPressed: () {
                      final rows = widget.clip.captions;
                      final row = rows
                              .where(
                                (r) => RegExp(
                                  r'\?|kenapa|bagaimana|rahasia|why|how',
                                  caseSensitive: false,
                                ).hasMatch('${r['text']}'),
                              )
                              .firstOrNull ??
                          rows.firstOrNull;
                      if (row != null) {
                        title.text = '${row['text']}'
                            .split(RegExp(r'\s+'))
                            .take(12)
                            .join(' ');
                      }
                      setState(() => titleEnabled = true);
                    },
                    child: const Text('Buat judul dari ucapan'),
                  ),
                  DropdownButtonFormField<String>(
                    initialValue: preset,
                    decoration:
                        const InputDecoration(labelText: 'Preset judul'),
                    items: const [
                      DropdownMenuItem(
                        value: 'viral_yellow',
                        child: Text('Hook kuning'),
                      ),
                      DropdownMenuItem(
                        value: 'yellow_label',
                        child: Text('Kartu kuning'),
                      ),
                      DropdownMenuItem(value: 'clean', child: Text('Minimal')),
                      DropdownMenuItem(value: 'cyan_neon', child: Text('Neon')),
                    ],
                    onChanged: (v) => setState(() => preset = v!),
                  ),
                  slider(
                    'Durasi judul (detik)',
                    seconds,
                    .2,
                    widget.clip.duration,
                    (v) => seconds = v,
                  ),
                  slider(
                      'Ukuran font', titleSize, 14, 160, (v) => titleSize = v),
                  slider('Posisi X', titleX, .05, .95, (v) => titleX = v),
                  slider('Posisi Y', titleY, .05, .95, (v) => titleY = v),
                  const Text(
                    'Preview dan ekspor memakai judul yang sama. Tekan Terapkan untuk melihat video di editor.',
                  ),
                ],
              ),
              ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  DropdownButtonFormField<String>(
                    initialValue: kind,
                    decoration:
                        const InputDecoration(labelText: 'Jenis watermark'),
                    items: const [
                      DropdownMenuItem(
                        value: 'none',
                        child: Text('Tanpa watermark'),
                      ),
                      DropdownMenuItem(value: 'text', child: Text('Tulisan')),
                      DropdownMenuItem(
                          value: 'image', child: Text('Logo gambar')),
                    ],
                    onChanged: (v) => setState(() => kind = v!),
                  ),
                  if (kind == 'text')
                    TextField(
                      controller: watermark,
                      decoration: const InputDecoration(
                        labelText: 'Tulisan watermark',
                      ),
                    ),
                  if (kind == 'image') ...[
                    OutlinedButton.icon(
                      onPressed: pickLogo,
                      icon: const Icon(Icons.image),
                      label: const Text('Pilih logo'),
                    ),
                    if (logo.isNotEmpty)
                      Image.file(File(logo), height: 100, fit: BoxFit.contain),
                    slider('Lebar logo', wmScale, .05, .7, (v) => wmScale = v),
                  ],
                  if (kind == 'text')
                    slider('Ukuran font', wmSize, 14, 160, (v) => wmSize = v),
                  if (kind != 'none') ...[
                    slider('Opacity', opacity, .05, 1, (v) => opacity = v),
                    slider('Posisi X', wmX, 0, 1, (v) => wmX = v),
                    slider('Posisi Y', wmY, 0, 1, (v) => wmY = v),
                    const Text(
                      'Watermark tampil sepanjang klip. PNG transparan mempertahankan transparansi logo.',
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      );
}
