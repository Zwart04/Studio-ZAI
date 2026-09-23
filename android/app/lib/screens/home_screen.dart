import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'images_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.state, required this.onOpenClips});

  final AppState state;
  final VoidCallback onOpenClips;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _sourceController = TextEditingController();
  int _count = 5;
  String _language = 'id';
  String _audioLanguage = '';
  String _canvas = 'portrait';
  bool _useTranscript = true;
  bool _useAi = false;

  @override
  void dispose() {
    _sourceController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final files = await FilePicker.pickFiles(type: FileType.video);
    if (files.isEmpty) return;
    final path = files.first.path;
    if (path != null) setState(() => _sourceController.text = path);
  }

  Future<void> _start() async {
    final source = _sourceController.text.trim();
    if (source.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(widget.state.translate('home.source'))),
      );
      return;
    }
    try {
      await widget.state.process(
        source: source,
        count: _count,
        language: _language,
        useTranscript: _useTranscript,
        useAi: _useAi,
        audioLanguage: _audioLanguage.isEmpty ? null : _audioLanguage,
        canvas: _canvas,
      );
      if (mounted) widget.onOpenClips();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }

  Widget _fieldPair(Widget first, Widget second) => LayoutBuilder(
        builder: (context, constraints) => constraints.maxWidth < 340
            ? Column(children: [
                first,
                const SizedBox(height: Tokens.space3),
                second,
              ])
            : Row(children: [
                Expanded(child: first),
                const SizedBox(width: Tokens.space3),
                Expanded(child: second),
              ]),
      );

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final device = state.device;
    return ListView(
      padding: const EdgeInsets.fromLTRB(
          Tokens.space4, Tokens.space4, Tokens.space4, Tokens.space8),
      children: [
        Row(children: [
          ColorFiltered(
            colorFilter: const ColorFilter.matrix([
              -1,
              0,
              0,
              0,
              255,
              0,
              -1,
              0,
              0,
              255,
              0,
              0,
              -1,
              0,
              255,
              0,
              0,
              0,
              1,
              0,
            ]),
            child: Image.asset('assets/images/logo.png',
                width: 42, height: 42, fit: BoxFit.contain),
          ),
          const SizedBox(width: Tokens.space3),
          Expanded(
              child: Text(state.translate('home.title'),
                  style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w600,
                      letterSpacing: -0.4))),
        ]),
        const SizedBox(height: Tokens.space3),
        Text(state.translate('home.lead'),
            style: const TextStyle(color: Tokens.textDim, height: 1.5)),
        const SizedBox(height: Tokens.space5),
        SectionCard(
            title: 'Video sumber',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: _sourceController,
                  decoration: const InputDecoration(
                    labelText: 'Tautan atau lokasi video',
                    hintText: 'YouTube, TikTok, Instagram, atau berkas lokal',
                    prefixIcon: Icon(Icons.link_rounded, size: 20),
                  ),
                  minLines: 1,
                  maxLines: 2,
                ),
                const SizedBox(height: Tokens.space3),
                OutlinedButton.icon(
                  onPressed: _pickFile,
                  icon: const Icon(Icons.folder_open, size: 18),
                  label: Text(state.translate('home.pick')),
                ),
                const SizedBox(height: Tokens.space2),
                const Text(
                    'Video yang sudah diunduh tersimpan di proyek dan bisa diedit lagi tanpa mengunduh ulang.',
                    style: TextStyle(
                        color: Tokens.textDim, fontSize: 12, height: 1.5)),
              ],
            )),
        const SizedBox(height: Tokens.space5),
        SectionCard(
            title: 'Hasil klip',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                    'AI menentukan awal dan akhir momen. Ubah potongan kapan saja di editor.',
                    style: TextStyle(
                        color: Tokens.textDim, fontSize: 12, height: 1.5)),
                const SizedBox(height: Tokens.space4),
                _fieldPair(
                  DropdownButtonFormField<int>(
                    initialValue: _count,
                    decoration: InputDecoration(
                        labelText: state.translate('home.count')),
                    items: const [3, 5, 8, 12]
                        .map((value) => DropdownMenuItem(
                            value: value, child: Text('$value')))
                        .toList(),
                    onChanged: (value) => setState(() => _count = value ?? 5),
                  ),
                  DropdownButtonFormField<String>(
                    initialValue: _canvas,
                    decoration:
                        const InputDecoration(labelText: 'Ukuran video'),
                    items: const [
                      DropdownMenuItem(
                          value: 'portrait', child: Text('Portrait 9:16')),
                      DropdownMenuItem(value: 'original', child: Text('Asli')),
                      DropdownMenuItem(
                          value: 'square', child: Text('Kotak 1:1')),
                      DropdownMenuItem(
                          value: 'landscape', child: Text('Landscape 16:9')),
                    ],
                    onChanged: (value) =>
                        setState(() => _canvas = value ?? 'portrait'),
                  ),
                ),
              ],
            )),
        const SizedBox(height: Tokens.space5),
        SectionCard(
            title: 'Bahasa & suara',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                    'Bahasa konten membaca ucapan. Track sumber menentukan suara yang terdengar di klip.',
                    style: TextStyle(
                        color: Tokens.textDim, fontSize: 12, height: 1.5)),
                const SizedBox(height: Tokens.space4),
                _fieldPair(
                  DropdownButtonFormField<String>(
                    initialValue: _language,
                    decoration: InputDecoration(
                        labelText: state.translate('home.lang')),
                    items: const [
                      DropdownMenuItem(value: 'id', child: Text('Indonesia')),
                      DropdownMenuItem(value: 'en', child: Text('English')),
                    ],
                    onChanged: (value) =>
                        setState(() => _language = value ?? 'id'),
                  ),
                  DropdownButtonFormField<String>(
                    initialValue: _audioLanguage,
                    decoration:
                        const InputDecoration(labelText: 'Track audio sumber'),
                    items: const [
                      DropdownMenuItem(value: '', child: Text('Bawaan video')),
                      DropdownMenuItem(value: 'id', child: Text('Indonesia')),
                      DropdownMenuItem(value: 'en', child: Text('English')),
                    ],
                    onChanged: (value) =>
                        setState(() => _audioLanguage = value ?? ''),
                  ),
                ),
                const SizedBox(height: Tokens.space4),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(Tokens.space3),
                  decoration: BoxDecoration(
                    color: Tokens.surface2,
                    borderRadius: BorderRadius.circular(Tokens.radiusSm),
                  ),
                  child: const Row(children: [
                    Icon(Icons.volume_up_outlined,
                        size: 20, color: Tokens.textDim),
                    SizedBox(width: Tokens.space3),
                    Expanded(
                        child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Audio klip · suara asli'),
                        SizedBox(height: Tokens.space1),
                        Text(
                            'Tambahkan narasi TTS di editor setelah klip dibuat.',
                            style:
                                TextStyle(color: Tokens.textDim, fontSize: 12)),
                      ],
                    )),
                  ]),
                ),
              ],
            )),
        const SizedBox(height: Tokens.space5),
        SectionCard(
            title: 'Subtitle & analisis',
            child: Column(children: [
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _useTranscript,
                onChanged: (value) => setState(() => _useTranscript = value),
                title: Text(state.translate('home.transcript'),
                    style: const TextStyle(fontSize: 14)),
                subtitle: const Text(
                    'Transkrip menyimpan ucapan; subtitle menempatkannya di video. Audio tetap sama.'),
              ),
              const Divider(height: Tokens.space5),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _useAi,
                onChanged: (value) => setState(() {
                  _useAi = value;
                  if (value) _useTranscript = true;
                }),
                title: const Text('Pilih momen dengan AI online',
                    style: TextStyle(fontSize: 14)),
                subtitle: const Text(
                    'Opsional. Transkrip dikirim ke penyedia di Pengaturan jika diaktifkan.'),
              ),
            ])),
        const SizedBox(height: Tokens.space5),
        SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: state.jobState == JobState.running ? null : _start,
              icon: const Icon(Icons.auto_awesome_outlined, size: 19),
              label: Text(state.translate('home.start')),
            )),
        if (state.jobState == JobState.running) ...[
          const SizedBox(height: Tokens.space4),
          ProgressStrip(
              progress: state.jobProgress,
              label: '${state.jobStage} ${state.jobMessage}'),
        ],
        const SizedBox(height: Tokens.space5),
        OutlinedButton.icon(
          onPressed: () => Navigator.push(
              context,
              MaterialPageRoute<void>(
                  builder: (_) => ImagesScreen(state: state))),
          icon: const Icon(Icons.image_outlined, size: 18),
          label: const Text('Buka studio gambar'),
        ),
        const SizedBox(height: Tokens.space8),
        Text('Proyek terakhir', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: Tokens.space3),
        if (state.projects.isEmpty)
          EmptyState(state.translate('clips.empty'))
        else
          ...state.projects.take(5).map((project) => Padding(
                padding: const EdgeInsets.only(bottom: Tokens.space2),
                child: Card(
                    child: ListTile(
                  title: Text(project.title,
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: Text(
                      '${project.clips.length} klip · ${formatClock(project.duration)}'),
                  trailing:
                      const Icon(Icons.chevron_right, color: Tokens.textDim),
                  onTap: () {
                    state.openProject(project);
                    widget.onOpenClips();
                  },
                )),
              )),
        const SizedBox(height: Tokens.space5),
        SectionCard(
          title: state.translate('home.device'),
          child: device == null
              ? const Text('…', style: TextStyle(color: Tokens.textDim))
              : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('${device.model} · ${device.androidVersion}'),
                  const SizedBox(height: Tokens.space1),
                  Text(
                      'RAM ${device.ramGb.toStringAsFixed(1)} GB · Disk ${device.diskFreeGb.toStringAsFixed(1)} GB',
                      style:
                          const TextStyle(color: Tokens.textDim, fontSize: 13)),
                  const SizedBox(height: Tokens.space2),
                  Wrap(
                      spacing: Tokens.space2,
                      runSpacing: Tokens.space2,
                      children: device
                          .recommendations()
                          .map((r) => Pill(r))
                          .toList()),
                ]),
        ),
      ],
    );
  }
}
