import 'dart:io';

import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

import '../models.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import '../widgets/preview_player.dart';
import 'editor_screen.dart';
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
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(project.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
                  Text('${project.clips.length} klip · ${formatClock(project.duration)}',
                      style: const TextStyle(color: Tokens.textDim, fontSize: 13)),
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
        const SizedBox(height:12),
        OutlinedButton.icon(onPressed: state.jobState == JobState.running ? null : ()=>openSourceEditor(context,state), icon:const Icon(Icons.content_cut),label:const Text('Ambil bagian video sumber')),
        if (state.jobState == JobState.running) ...[
          const SizedBox(height: Tokens.space3),
          ProgressStrip(progress: state.jobProgress, label: '${state.jobStage} ${state.jobMessage}'),
        ],
        const SizedBox(height: Tokens.space4),
        if (project.clips.isEmpty)
          EmptyState(state.translate('clips.empty'))
        else
          ...project.clips.map((clip) => Padding(
                padding: const EdgeInsets.only(bottom: Tokens.space4),
                child: ClipTile(
                  clip: clip,
                  labels: labels,
                  onPreview: () => _preview(context, clip),
                  onEdit: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => EditorScreen(state: state, clip: clip),
                  )),
                  onRender: () async {
                    try {
                      await state.renderClip(clip);
                    } catch (error) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
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

  Future<void> _preview(BuildContext context, Clip clip) async {
    final path = clip.files['mp4'];
    if (path == null || !File(path).existsSync()) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.translate('clips.renderFirst'))),
      );
      return;
    }
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Tokens.bgElevated,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(Tokens.radiusLg)),
      ),
      builder: (_) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(Tokens.space4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(clip.title.isEmpty ? 'Klip ${clip.index + 1}' : clip.title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: Tokens.space3),
              ClipRRect(
                borderRadius: BorderRadius.circular(Tokens.radius),
                child: VideoPreview(path: path, onShare: () => _share(clip)),
              ),
              const SizedBox(height: Tokens.space3),
              Row(mainAxisAlignment: MainAxisAlignment.end, children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(state.translate('common.close')),
                ),
              ]),
            ],
          ),
        ),
      ),
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
    await SharePlus.instance.share(ShareParams(files: [XFile(path)], text: clip.title));
  }

  Future<void> _export(BuildContext context, Project project) async {
    try {
      await state.exportProject();
      if (context.mounted && state.lastOutput != null) {
        await SharePlus.instance.share(ShareParams(files: [XFile(state.lastOutput!)]));
      }
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }
}
