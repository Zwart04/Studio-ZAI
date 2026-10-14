import 'dart:io';

import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'package:file_picker/file_picker.dart';

import '../models.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'editor_screen.dart';
import 'gallery_screen.dart';
import '../widgets/source_editor.dart';

class ClipsScreen extends StatelessWidget {
  const ClipsScreen({super.key, required this.state});

  final AppState state;

  @override
  Widget build(BuildContext context) {
    final project = state.currentProject;
    final labels = {
      'preview': state.translate('clips.preview'),
      'edit': state.translate('clips.edit'),
      'render': state.translate('clips.render'),
      'share': state.translate('clips.share'),
      'delete': state.translate('clips.delete'),
      'ready': state.translate('models.installed'),
      'draft': 'draft',
    };

    if (project == null) {
      return Padding(
        padding: const EdgeInsets.all(Tokens.space4),
        child: EmptyState(state.translate('clips.empty')),
      );
    }

    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        if (!project.online)
          OutlinedButton.icon(
              onPressed: state.jobState == JobState.running
                  ? null
                  : () async {
                      final files =
                          await FilePicker.pickFiles(type: FileType.video);
                      final path = files.firstOrNull?.path;
                      if (path == null) return;
                      try {
                        await state.relinkSource(path);
                      } catch (error) {
                        if (context.mounted) {
                          ScaffoldMessenger.of(context)
                              .showSnackBar(SnackBar(content: Text('$error')));
                        }
                      }
                    },
              icon: const Icon(Icons.link),
              label: const Text('Tautkan ulang video yang dipindah')),
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(project.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          fontSize: 20, fontWeight: FontWeight.w600)),
                  Text(
                      '${project.clips.length} klip · ${formatClock(project.duration)}',
                      style:
                          const TextStyle(color: Tokens.textDim, fontSize: 13)),
                ],
              ),
            ),
            const SizedBox(width: Tokens.space2),
            OutlinedButton(
              onPressed: () => _export(context, project),
              child: Text(state.translate('clips.title')),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (project.transcript.isNotEmpty)
          ExpansionTile(
            initiallyExpanded: project.execution['task'] == 'transcript',
            title: Text('Transkrip · ${project.transcript.length} bagian'),
            children: [
              SizedBox(
                  height: 320,
                  child: ListView.builder(
                    itemCount: project.transcript.length,
                    itemBuilder: (context, index) {
                      final row = project.transcript[index];
                      return ListTile(
                          title: SelectableText(row['text'] as String? ?? ''),
                          subtitle: Text(
                              formatClock((row['start'] as num).toDouble())));
                    },
                  )),
            ],
          ),
        FilledButton.icon(
            onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (_) => Scaffold(
                        appBar: AppBar(title: const Text('Ekspor batch')),
                        body: GalleryScreen(state: state, project: project)))),
            icon: const Icon(Icons.video_library),
            label: const Text('Pilih momen & ekspor banyak format')),
        OutlinedButton.icon(
            onPressed: state.jobState == JobState.running
                ? null
                : () => openSourceEditor(context, state),
            icon: const Icon(Icons.content_cut),
            label: const Text('Ambil bagian video sumber')),
        if (project.processingWarning.isNotEmpty) ...[
          const SizedBox(height: Tokens.space4),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(Tokens.space4),
            decoration: BoxDecoration(
              color: Tokens.surface2,
              borderRadius: BorderRadius.circular(Tokens.radiusSm),
            ),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Icon(Icons.info_outline_rounded,
                  size: 19, color: Tokens.textDim),
              const SizedBox(width: Tokens.space3),
              Expanded(
                  child: Text(project.processingWarning,
                      style: const TextStyle(fontSize: 13, height: 1.45))),
            ]),
          ),
        ],
        if (state.jobState == JobState.running) ...[
          const SizedBox(height: Tokens.space3),
          ProgressStrip(
              progress: state.jobProgress,
              label: '${state.jobStage} ${state.jobMessage}'),
        ],
        const SizedBox(height: Tokens.space4),
        if (project.clips.isEmpty)
          SectionCard(
            title: state.jobState == JobState.running
                ? 'Sedang membuat klip'
                : 'Belum ada klip',
            child: Text(
                state.jobState == JobState.running
                    ? 'Video sumber tersimpan. Klip akan muncul setelah pemrosesan selesai.'
                    : 'Video sumber tetap tersimpan. Ambil bagian video secara manual tanpa mengunduhnya lagi.',
                style: const TextStyle(color: Tokens.textDim, height: 1.5)),
          )
        else
          ...project.clips.map((clip) => Padding(
                padding: const EdgeInsets.only(bottom: Tokens.space4),
                child: ClipTile(
                  clip: clip,
                  labels: labels,
                  onEdit: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => EditorScreen(state: state, clip: clip),
                  )),
                  onRender: () async {
                    try {
                      await state.renderClip(clip);
                    } catch (error) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context)
                            .showSnackBar(SnackBar(content: Text('$error')));
                      }
                    }
                  },
                  onShare: () => _share(clip),
                  onDelete: () => _confirmDelete(context, clip),
                ),
              )),
      ],
    );
  }

  Future<void> _confirmDelete(BuildContext context, Clip clip) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: Tokens.surface,
        title: Text(state.translate('clips.delete')),
        content: Text(state.translate('clips.deleteConfirm')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(state.translate('common.cancel')),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Tokens.danger),
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(state.translate('clips.delete')),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await state.deleteClip(clip);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.translate('clips.deleted'))),
      );
    }
  }

  Future<void> _share(Clip clip) async {
    final path = clip.files['mp4'];
    if (path == null || !File(path).existsSync()) return;
    await SharePlus.instance
        .share(ShareParams(files: [XFile(path)], text: clip.title));
  }

  Future<void> _export(BuildContext context, Project project) async {
    try {
      await state.exportProject();
      if (context.mounted && state.lastOutput != null) {
        await SharePlus.instance
            .share(ShareParams(files: [XFile(state.lastOutput!)]));
      }
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }
}
