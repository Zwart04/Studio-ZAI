import 'dart:io';
import '../services/clip_archive.dart';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import '../models.dart';
import '../state/app_state.dart';
import '../widgets/preview_player.dart';
import 'editor_screen.dart';

class GalleryScreen extends StatefulWidget {
  const GalleryScreen({super.key, required this.state, this.project});
  final AppState state;
  final Project? project;
  @override
  State<GalleryScreen> createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<GalleryScreen> {
  final selected = <String>{}, formats = <String>{'portrait'};
  String query = '';
  bool ranked = true, onlyReady = false;
  bool zipping = false;

  Future<void> zipSelected() async {
    setState(() => zipping = true);
    try {
      final files = <String, String>{};
      for (final entry in all.where((e) => selected.contains(keyOf(e)))) {
        for (final fmt in formats) {
          final path = entry.$2.files['mp4_$fmt'];
          if (path == null || !File(path).existsSync()) {
            throw Exception('Render semua klip dan format pilihan dahulu.');
          }
          final root = widget.state.projectDir(entry.$1).absolute.path;
          if (!File(path)
              .resolveSymbolicLinksSync()
              .startsWith('$root${Platform.pathSeparator}')) {
            throw Exception('Berkas ekspor di luar proyek.');
          }
          files[path] = '${entry.$1.id}-${entry.$2.index + 1}-$fmt.mp4';
        }
      }
      if (files.isEmpty) throw Exception('Pilih klip dan format.');
      final directory = Directory('${widget.state.dataDir.path}/exports')
        ..createSync(recursive: true);
      final output =
          '${directory.path}/clips-${DateTime.now().microsecondsSinceEpoch}.zip';
      await ClipArchive.create(files, output);
      await SharePlus.instance
          .share(ShareParams(files: [XFile(output)], text: 'Klip Studio ZAI'));
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    } finally {
      if (mounted) setState(() => zipping = false);
    }
  }

  String keyOf((Project, Clip) e) => '${e.$1.id}/${e.$2.index}';
  List<(Project, Clip)> get all => [
        for (final p in widget.project == null
            ? widget.state.projects
            : [widget.project!])
          for (final c in p.clips) (p, c)
      ];
  List<MapEntry<String, String>> outputs(Clip c) => c.files.entries
      .where((e) =>
          (e.key == 'mp4' || e.key.startsWith('mp4_')) &&
          File(e.value).existsSync())
      .toList();
  Future<void> batch() async {
    try {
      await widget.state.batchRender(
          all.where((e) => selected.contains(keyOf(e))).toList(),
          formats.toList());
      if (mounted) setState(() {});
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
      listenable: widget.state,
      builder: (context, _) {
        final rows = all
            .where((e) =>
                ('${e.$1.title} ${e.$2.title}')
                    .toLowerCase()
                    .contains(query.toLowerCase()) &&
                (!onlyReady || outputs(e.$2).isNotEmpty))
            .toList();
        rows.sort((a, b) => ranked
            ? b.$2.score.compareTo(a.$2.score)
            : (b.$1.createdAt ?? DateTime(1970))
                .compareTo(a.$1.createdAt ?? DateTime(1970)));
        final busy = widget.state.jobState == JobState.running || zipping;
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text(
              widget.project == null
                  ? 'Galeri semua proyek'
                  : 'Pilih momen & format',
              style:
                  const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const Text(
              'Putar, edit judul dan caption, atau render beberapa format dari sumber yang tersimpan.'),
          const SizedBox(height: 16),
          TextField(
              decoration: const InputDecoration(
                  labelText: 'Cari judul atau proyek',
                  prefixIcon: Icon(Icons.search)),
              onChanged: (s) => setState(() => query = s)),
          Wrap(spacing: 8, children: [
            FilterChip(
                label: const Text('Skor tertinggi'),
                selected: ranked,
                onSelected: (v) => setState(() => ranked = v)),
            FilterChip(
                label: const Text('Sudah dirender'),
                selected: onlyReady,
                onSelected: (v) => setState(() => onlyReady = v))
          ]),
          Wrap(spacing: 8, children: [
            for (final f in {
              'portrait': '9:16',
              'square': '1:1',
              'landscape': '16:9'
            }.entries)
              FilterChip(
                  label: Text(f.value),
                  selected: formats.contains(f.key),
                  onSelected: busy
                      ? null
                      : (v) => setState(() {
                            if (v) {
                              formats.add(f.key);
                            } else {
                              formats.remove(f.key);
                            }
                          }))
          ]),
          Wrap(spacing: 8, children: [
            TextButton(
                onPressed: busy
                    ? null
                    : () => setState(() => selected.addAll(rows.map(keyOf))),
                child: const Text('Pilih semua')),
            TextButton(
                onPressed: busy ? null : () => setState(() => selected.clear()),
                child: const Text('Kosongkan')),
            FilledButton.icon(
                onPressed:
                    busy || selected.isEmpty || formats.isEmpty ? null : batch,
                icon: const Icon(Icons.movie_creation_outlined),
                label: Text(
                    'Render ${all.where((e) => selected.contains(keyOf(e))).length * formats.length} video')),
            OutlinedButton.icon(
                onPressed: busy || selected.isEmpty || formats.isEmpty
                    ? null
                    : zipSelected,
                icon: const Icon(Icons.folder_zip_outlined),
                label: Text(zipping ? 'Mengemas…' : 'Bagikan ZIP pilihan'))
          ]),
          if (busy) ...[
            LinearProgressIndicator(value: widget.state.jobProgress / 100),
            Text(widget.state.jobStage)
          ],
          if (rows.isEmpty)
            const Padding(
                padding: EdgeInsets.all(30),
                child: Text(
                    'Belum ada klip yang cocok. Impor video dan deteksi momen terlebih dahulu.')),
          ...rows.map((entry) {
            final p = entry.$1, c = entry.$2, files = outputs(c);
            final thumb = c.files['thumb'] ??
                c.files['thumb_portrait'] ??
                c.files['thumb_square'] ??
                c.files['thumb_landscape'];
            return Card(
                margin: const EdgeInsets.symmetric(vertical: 8),
                child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          CheckboxListTile(
                              contentPadding: EdgeInsets.zero,
                              controlAffinity: ListTileControlAffinity.leading,
                              value: selected.contains(keyOf(entry)),
                              onChanged: busy
                                  ? null
                                  : (v) => setState(() {
                                        if (v == true) {
                                          selected.add(keyOf(entry));
                                        } else {
                                          selected.remove(keyOf(entry));
                                        }
                                      }),
                              title: Text(c.title,
                                  maxLines: 2, overflow: TextOverflow.ellipsis),
                              subtitle: Text(
                                  '${p.title} · ${c.duration.toStringAsFixed(1)}s · skor ${(c.score * 100).round()}')),
                          if (thumb != null && File(thumb).existsSync())
                            Center(
                                child: Image.file(File(thumb),
                                    height: 145, fit: BoxFit.contain)),
                          Text(c.reason,
                              style: Theme.of(context).textTheme.bodySmall),
                          Wrap(spacing: 8, children: [
                            TextButton.icon(
                                onPressed: busy
                                    ? null
                                    : () {
                                        widget.state.currentProject = p;
                                        Navigator.push(
                                            context,
                                            MaterialPageRoute(
                                                builder: (_) => EditorScreen(
                                                    state: widget.state,
                                                    clip: c))).then((_) {
                                          if (mounted) setState(() {});
                                        });
                                      },
                                icon: const Icon(Icons.edit),
                                label: const Text('Edit / judul')),
                            TextButton.icon(
                                onPressed: () => showDialog(
                                    context: context,
                                    builder: (_) => Dialog(
                                        child: Padding(
                                            padding: const EdgeInsets.all(12),
                                            child: VideoPreview(
                                                path: files.isEmpty
                                                    ? p.source
                                                    : files.first.value,
                                                startSeconds:
                                                    files.isEmpty ? c.start : 0,
                                                endSeconds: files.isEmpty
                                                    ? c.end
                                                    : null)))),
                                icon: const Icon(Icons.play_arrow),
                                label: const Text('Putar')),
                            for (final f in files)
                              TextButton.icon(
                                  onPressed: () => SharePlus.instance.share(
                                      ShareParams(
                                          files: [XFile(f.value)],
                                          text: c.title)),
                                  icon: const Icon(Icons.ios_share, size: 16),
                                  label: Text(f.key == 'mp4'
                                      ? 'MP4'
                                      : f.key.substring(4))),
                          ]),
                        ])));
          }),
        ]);
      });
}
