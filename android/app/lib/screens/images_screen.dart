import 'dart:io';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import '../services/cloud_ai.dart';
import '../state/app_state.dart';
import 'cloud_settings_screen.dart';

class ImagesScreen extends StatefulWidget {
  const ImagesScreen({super.key, required this.state});
  final AppState state;
  @override
  State<ImagesScreen> createState() => _ImagesScreenState();
}

class _ImagesScreenState extends State<ImagesScreen> {
  final _prompt = TextEditingController();
  bool _busy = false;
  List<File> _images = [];
  @override
  void initState() {
    super.initState();
    _refresh();
  }

  void _refresh() {
    final directory = Directory('${widget.state.dataDir.path}/images');
    _images = directory.existsSync()
        ? directory
            .listSync()
            .whereType<File>()
            .where((f) => f.path.endsWith('.png'))
            .toList()
        : [];
    _images.sort((a, b) => b.path.compareTo(a.path));
  }

  @override
  void dispose() {
    _prompt.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    setState(() => _busy = true);
    try {
      await CloudAI.image(_prompt.text, widget.state.dataDir);
      if (mounted) setState(_refresh);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Gambar'), actions: [
          IconButton(
              tooltip: 'Penyedia AI',
              icon: const Icon(Icons.tune),
              onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute<void>(
                      builder: (_) => const CloudSettingsScreen())))
        ]),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          const Text(
              'Buat ilustrasi dari deskripsi. Pilih layanan online atau server Stable Diffusion milikmu di pengaturan.'),
          const SizedBox(height: 16),
          TextField(
              controller: _prompt,
              maxLines: 4,
              decoration: const InputDecoration(
                  labelText: 'Deskripsi gambar',
                  hintText: 'Contoh: studio minimalis dengan cahaya pagi')),
          const SizedBox(height: 12),
          FilledButton.icon(
              onPressed: _busy ? null : _generate,
              icon: const Icon(Icons.auto_awesome_outlined),
              label: Text(_busy ? 'Membuat gambar…' : 'Buat gambar')),
          if (_busy)
            const Padding(
                padding: EdgeInsets.all(16), child: LinearProgressIndicator()),
          const SizedBox(height: 20),
          for (final file in _images)
            Card(
                child: Column(children: [
              ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.file(file,
                      fit: BoxFit.contain, height: 300, cacheWidth: 768)),
              Row(mainAxisAlignment: MainAxisAlignment.end, children: [
                TextButton.icon(
                    onPressed: () => SharePlus.instance
                        .share(ShareParams(files: [XFile(file.path)])),
                    icon: const Icon(Icons.ios_share),
                    label: const Text('Simpan / bagikan')),
                IconButton(
                    tooltip: 'Hapus gambar',
                    icon: const Icon(Icons.delete_outline),
                    onPressed: () async {
                      final remove = await showDialog<bool>(
                          context: context,
                          builder: (ctx) => AlertDialog(
                                  title: const Text('Hapus gambar?'),
                                  actions: [
                                    TextButton(
                                        onPressed: () =>
                                            Navigator.pop(ctx, false),
                                        child: const Text('Batal')),
                                    FilledButton(
                                        onPressed: () =>
                                            Navigator.pop(ctx, true),
                                        child: const Text('Hapus'))
                                  ]));
                      if (remove != true) return;
                      await file.delete();
                      final meta = File('${file.path}.json');
                      if (await meta.exists()) await meta.delete();
                      if (mounted) setState(_refresh);
                    }),
              ]),
            ])),
        ]),
      );
}
