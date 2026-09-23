import 'dart:io';

import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

import '../models.dart';
import '../services/cloud_ai.dart';
import '../services/local_image.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
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
  bool _online = false;
  List<File> _images = [];

  ModelInfo? get _localModel {
    for (final model in widget.state.catalog) {
      if (model.id == 'sdxs-512') return model;
    }
    return null;
  }

  void _stateChanged() {
    if (mounted) setState(() {});
  }

  @override
  void initState() {
    super.initState();
    widget.state.addListener(_stateChanged);
    _refresh();
  }

  void _refresh() {
    final directory = Directory('${widget.state.dataDir.path}/images');
    _images = directory.existsSync()
        ? directory
            .listSync()
            .whereType<File>()
            .where((file) => file.path.toLowerCase().endsWith('.png'))
            .toList()
        : [];
    _images.sort((a, b) => b.path.compareTo(a.path));
  }

  @override
  void dispose() {
    widget.state.removeListener(_stateChanged);
    _prompt.dispose();
    super.dispose();
  }

  Future<void> _installModel() async {
    final model = _localModel;
    if (model == null) return;
    try {
      await widget.state.downloadModel(model);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }

  Future<void> _generate() async {
    if (_prompt.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Tulis deskripsi gambar lebih dulu.')),
      );
      return;
    }
    setState(() => _busy = true);
    try {
      if (_online) {
        await CloudAI.image(_prompt.text, widget.state.dataDir);
      } else {
        final model = _localModel;
        if (model == null || !model.installed) {
          throw StateError('Unduh model gambar lokal lebih dulu.');
        }
        final modelFile = File('${widget.state.models.dirFor(model.id).path}'
            '/${LocalImage.modelFileName}');
        await LocalImage.generate(
            _prompt.text, widget.state.dataDir, modelFile);
      }
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

  Future<void> _remove(File file) async {
    final remove = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Hapus gambar?'),
        content: const Text(
            'Berkas gambar dan informasi pembuatannya ikut dihapus.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Batal')),
          FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Hapus')),
        ],
      ),
    );
    if (remove != true) return;
    await file.delete();
    final metadata = File('${file.path}.json');
    if (await metadata.exists()) await metadata.delete();
    if (mounted) setState(_refresh);
  }

  @override
  Widget build(BuildContext context) {
    final model = _localModel;
    final jobRunning = widget.state.jobState == JobState.running;
    final localSupported =
        widget.state.device?.abis.contains('arm64-v8a') == true;
    return Scaffold(
      appBar: AppBar(title: const Text('Studio gambar')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            Tokens.space4, Tokens.space4, Tokens.space4, Tokens.space8),
        children: [
          const Text('Buat gambar dari teks',
              style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w600,
                  letterSpacing: -0.3)),
          const SizedBox(height: Tokens.space2),
          const Text(
              'Model lokal berjalan di perangkatmu. Layanan online tersedia sebagai pilihan.',
              style: TextStyle(color: Tokens.textDim, height: 1.5)),
          const SizedBox(height: Tokens.space5),
          Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
                color: Tokens.surface,
                borderRadius: BorderRadius.circular(Tokens.radiusSm)),
            child: Row(children: [
              _modeButton(
                  'Lokal · offline', Icons.phone_android_rounded, false),
              _modeButton('Online · opsional', Icons.cloud_outlined, true),
            ]),
          ),
          const SizedBox(height: Tokens.space5),
          if (!_online)
            SectionCard(
                title: 'Model gambar lokal',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      const Icon(Icons.auto_awesome_outlined,
                          color: Tokens.textDim, size: 21),
                      const SizedBox(width: Tokens.space3),
                      Expanded(
                          child: Text(model?.id ?? 'SDXS-512',
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600))),
                      if (model?.installed == true)
                        const Pill('Siap', tone: 'ok'),
                    ]),
                    const SizedBox(height: Tokens.space3),
                    Text(
                        widget.state.device == null
                            ? 'Memeriksa kemampuan perangkat…'
                            : !localSupported
                                ? 'Model gambar lokal ini memerlukan perangkat Android arm64. Gunakan mode online pada perangkat ini.'
                                : model?.installed == true
                                    ? 'Gambar 512 × 512 dibuat tanpa mengirim deskripsi ke internet.'
                                    : 'Unduh model satu kali (sekitar 683 MB). Sesudah terpasang, pembuatan gambar berjalan offline.',
                        style: const TextStyle(
                            color: Tokens.textDim, fontSize: 13, height: 1.5)),
                    if (localSupported && model?.installed != true) ...[
                      const SizedBox(height: Tokens.space4),
                      SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                            onPressed: model == null || jobRunning
                                ? null
                                : _installModel,
                            icon: const Icon(Icons.download_rounded, size: 18),
                            label: const Text('Unduh model lokal · 683 MB'),
                          )),
                    ],
                    if (jobRunning) ...[
                      const SizedBox(height: Tokens.space4),
                      ProgressStrip(
                          progress: widget.state.jobProgress,
                          label:
                              '${widget.state.jobStage} ${widget.state.jobMessage}'),
                    ],
                  ],
                ))
          else
            SectionCard(
                title: 'Penyedia online',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                        'Deskripsi gambar dikirim ke penyedia yang kamu pilih. API key diatur terpisah.',
                        style: TextStyle(
                            color: Tokens.textDim, fontSize: 13, height: 1.5)),
                    const SizedBox(height: Tokens.space3),
                    OutlinedButton.icon(
                      onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute<void>(
                              builder: (_) => const CloudSettingsScreen())),
                      icon: const Icon(Icons.tune_rounded, size: 18),
                      label: const Text('Atur penyedia & API key'),
                    ),
                  ],
                )),
          const SizedBox(height: Tokens.space5),
          SectionCard(
              title: 'Deskripsi gambar',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: _prompt,
                    minLines: 3,
                    maxLines: 6,
                    maxLength: 2000,
                    decoration: const InputDecoration(
                        hintText:
                            'Contoh: studio produk minimalis dengan cahaya pagi'),
                  ),
                  const SizedBox(height: Tokens.space3),
                  SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        onPressed: _busy ||
                                jobRunning ||
                                (!_online &&
                                    (!localSupported ||
                                        model?.installed != true))
                            ? null
                            : _generate,
                        icon: const Icon(Icons.auto_awesome_outlined, size: 18),
                        label: Text(_busy ? 'Membuat gambar…' : 'Buat gambar'),
                      )),
                  if (_busy) ...[
                    const SizedBox(height: Tokens.space3),
                    const LinearProgressIndicator(),
                    const SizedBox(height: Tokens.space2),
                    Text(
                        _online
                            ? 'Menunggu hasil dari penyedia online…'
                            : 'Membuat gambar di perangkat. Proses ini bisa berlangsung beberapa menit.',
                        style: const TextStyle(
                            color: Tokens.textDim, fontSize: 12, height: 1.4)),
                  ],
                ],
              )),
          const SizedBox(height: Tokens.space8),
          Text('Hasil tersimpan',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: Tokens.space3),
          if (_images.isEmpty)
            const EmptyState('Belum ada gambar. Hasilmu akan tampil di sini.')
          else
            ..._images.map(_imageCard),
        ],
      ),
    );
  }

  Widget _modeButton(String label, IconData icon, bool online) => Expanded(
        child: TextButton.icon(
          onPressed: _busy ? null : () => setState(() => _online = online),
          icon: Icon(icon, size: 17),
          label: Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12)),
          style: TextButton.styleFrom(
            foregroundColor: _online == online ? Tokens.text : Tokens.textDim,
            backgroundColor:
                _online == online ? Tokens.surface3 : Colors.transparent,
            padding: const EdgeInsets.symmetric(horizontal: 6),
            minimumSize: const Size(0, 42),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(Tokens.radiusSm - 3)),
          ),
        ),
      );

  Widget _imageCard(File file) => Padding(
        padding: const EdgeInsets.only(bottom: Tokens.space3),
        child: Card(
            child: Padding(
          padding: const EdgeInsets.all(Tokens.space3),
          child: Column(children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(Tokens.radiusSm),
              child: Image.file(file,
                  fit: BoxFit.contain, height: 300, cacheWidth: 768),
            ),
            const SizedBox(height: Tokens.space2),
            Row(children: [
              Expanded(
                  child: Text(file.uri.pathSegments.last,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          color: Tokens.textDim, fontSize: 12))),
              IconButton(
                tooltip: 'Bagikan gambar',
                onPressed: () => SharePlus.instance
                    .share(ShareParams(files: [XFile(file.path)])),
                icon: const Icon(Icons.ios_share_rounded),
              ),
              IconButton(
                tooltip: 'Hapus gambar',
                onPressed: () => _remove(file),
                icon: const Icon(Icons.delete_outline_rounded),
              ),
            ]),
          ]),
        )),
      );
}
