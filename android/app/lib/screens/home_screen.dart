import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

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
  bool _useTranscript = true;

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
        Text(state.translate('home.title'),
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.4)),
        const SizedBox(height: Tokens.space2),
        Text(state.translate('home.lead'), style: const TextStyle(color: Tokens.textDim)),
        const SizedBox(height: Tokens.space4),
        SectionCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
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
                    Text('RAM ${device.ramGb} GB · Disk ${device.diskFreeGb.toStringAsFixed(1)} GB',
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
