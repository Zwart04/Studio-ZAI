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
    if (path != null) {
      setState(() => _sourceController.text = path);
    }
  }

  Future<void> _start() async {
    final source = _sourceController.text.trim();
    if (source.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(widget.state.translate('home.source'))),
      );
      return;
    }
    final state = widget.state;
    try {
      await state.process(
        source: source,
        count: _count,
        language: _language,
        useTranscript: _useTranscript,
        useAi: _useAi,
        audioLanguage: _audioLanguage.isEmpty ? null : _audioLanguage,
        canvas: _canvas,
      );
      if (!mounted) return;
      widget.onOpenClips();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final device = state.device;
    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        Row(
          children: [
            ColorFiltered(colorFilter: const ColorFilter.matrix([-1,0,0,0,255,0,-1,0,0,255,0,0,-1,0,255,0,0,0,1,0]), child: Image.asset('assets/images/logo.png', width: 44, height: 44, fit: BoxFit.contain)),
            const SizedBox(width: Tokens.space3),
            Expanded(
              child: Text(state.translate('home.title'),
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.4)),
            ),
          ],
        ),
        const SizedBox(height: Tokens.space2),
        Text(state.translate('home.lead'), style: const TextStyle(color: Tokens.textDim)),
        const SizedBox(height: Tokens.space3),
        OutlinedButton.icon(onPressed: () => Navigator.push(context, MaterialPageRoute<void>(builder: (_) => ImagesScreen(state: state))), icon: const Icon(Icons.image_outlined), label: const Text('Studio gambar')),
        const SizedBox(height: Tokens.space4),
        SectionCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SwitchListTile(contentPadding: EdgeInsets.zero, title: const Text('Pilih momen dengan AI'), subtitle: const Text('Opsional · atur penyedia di Pengaturan. Transkrip dikirim ke penyedia pilihanmu.'), value: _useAi, onChanged: (v) => setState(() { _useAi = v; if (v) _useTranscript = true; })),
              TextField(
                controller: _sourceController,
                decoration: InputDecoration(
                  labelText: state.translate('home.source'),
                  hintText: 'https://youtube.com/watch?v=…',
                ),
                maxLines: 2,
                minLines: 1,
              ),
              const SizedBox(height: Tokens.space2),
              OutlinedButton.icon(
                onPressed: _pickFile,
                icon: const Icon(Icons.folder_open, size: 18),
                label: Text(state.translate('home.pick')),
              ),
              const SizedBox(height: Tokens.space4),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _language,
                      decoration: InputDecoration(labelText: state.translate('home.lang')),
                      items: const [
                        DropdownMenuItem(value: 'id', child: Text('Indonesia')),
                        DropdownMenuItem(value: 'en', child: Text('English')),
                      ],
                      onChanged: (value) => setState(() => _language = value ?? 'id'),
                    ),
                  ),
                  const SizedBox(width: Tokens.space3),
                  Expanded(
                    child: DropdownButtonFormField<int>(
                      initialValue: _count,
                      decoration: InputDecoration(labelText: state.translate('home.count')),
                      items: const [3, 5, 8, 12]
                          .map((value) => DropdownMenuItem(value: value, child: Text('$value')))
                          .toList(),
                      onChanged: (value) => setState(() => _count = value ?? 5),
                    ),
                  ),
                ],
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _useTranscript,
                onChanged: (value) => setState(() => _useTranscript = value),
                title: Text(state.translate('home.transcript'), style: const TextStyle(fontSize: 14)),
                subtitle: const Text('Transkrip = teks ucapan. Subtitle = teks bertiming di video. Bahasa transkrip tidak mengganti atau menerjemahkan suara.'),
              ),
              DropdownButtonFormField<String>(
                initialValue: _audioLanguage,
                decoration: const InputDecoration(labelText: 'Track audio YouTube', helperText: 'Memilih dub yang tersedia di video sumber.'),
                items: const [
                  DropdownMenuItem(value: '', child: Text('Audio bawaan')),
                  DropdownMenuItem(value: 'id', child: Text('Indonesia')),
                  DropdownMenuItem(value: 'en', child: Text('English')),
                ],
                onChanged: (value) => setState(() => _audioLanguage = value ?? ''),
              ),
              const SizedBox(height: Tokens.space3),
              DropdownButtonFormField<String>(
                initialValue: _canvas,
                decoration: const InputDecoration(labelText: 'Ukuran video'),
                items: const [
                  DropdownMenuItem(value: 'portrait', child: Text('Portrait 9:16')),
                  DropdownMenuItem(value: 'original', child: Text('Asli (rasio sumber)')),
                  DropdownMenuItem(value: 'square', child: Text('Kotak 1:1')),
                  DropdownMenuItem(value: 'landscape', child: Text('Landscape 16:9')),
                ],
                onChanged: (value) => setState(() => _canvas = value ?? 'portrait'),
              ),
              const SizedBox(height: Tokens.space2),
              FilledButton(
                onPressed: state.jobState == JobState.running ? null : _start,
                child: Text(state.translate('home.start')),
              ),
              if (state.jobState == JobState.running) ...[
                const SizedBox(height: Tokens.space3),
                ProgressStrip(progress: state.jobProgress, label: '${state.jobStage} ${state.jobMessage}'),
              ],
            ],
          ),
        ),
        const SizedBox(height: Tokens.space4),
        SectionCard(
          title: state.translate('home.device'),
          child: device == null
              ? const Text('…', style: TextStyle(color: Tokens.textDim))
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${device.model} · ${device.androidVersion}'),
                    const SizedBox(height: Tokens.space1),
                    Text('RAM ${device.ramGb.toStringAsFixed(1)} GB · Disk ${device.diskFreeGb.toStringAsFixed(1)} GB',
                        style: const TextStyle(color: Tokens.textDim, fontSize: 13)),
                    const SizedBox(height: Tokens.space2),
                    Wrap(
                      spacing: Tokens.space2,
                      runSpacing: Tokens.space2,
                      children: device.recommendations().map((r) => Pill(r)).toList(),
                    ),
                  ],
                ),
        ),
        const SizedBox(height: Tokens.space4),
        Text('${state.projects.length} proyek', style: const TextStyle(color: Tokens.textDim, fontSize: 13)),
        const SizedBox(height: Tokens.space2),
        if (state.projects.isEmpty)
          EmptyState(state.translate('clips.empty'))
        else
          ...state.projects.take(5).map((project) => Card(
                child: ListTile(
                  title: Text(project.title, maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: Text('${project.clips.length} klip · ${formatClock(project.duration)}'),
                  trailing: const Icon(Icons.chevron_right, color: Tokens.textDim),
                  onTap: () {
                    state.openProject(project);
                    widget.onOpenClips();
                  },
                ),
              )),
      ],
    );
  }
}
