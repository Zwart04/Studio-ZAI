import 'dart:io';

import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

import '../models.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'editor_screen.dart';

class ClipsScreen extends StatelessWidget {
  const ClipsScreen({super.key, required this.state});

  final AppState state;

  @override
  Widget build(BuildContext context) {
    final project = state.currentProject;
    final labels = {
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
                  Text(project.title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
                  Text('${project.clips.length} klip · ${formatClock(project.duration)}',
                      style: const TextStyle(color: Tokens.textDim, fontSize: 13)),
                ],
              ),
            ),
            OutlinedButton(
              onPressed: () => _export(context, project),
              child: Text(state.translate('clips.title')),
            ),
          ],
        ),
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
                  onEdit: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => EditorScreen(state: state, clip: clip),
                  )),
                  onRender: () async {
                    try {
                      await state.renderClip(clip);
                      await state.saveProject(project);
                    } catch (error) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
                      }
                    }
                  },
                  onShare: () => _share(clip),
                  onDelete: () async {
                    project.clips.removeWhere((c) => c.index == clip.index);
                    for (var i = 0; i < project.clips.length; i++) {
                      project.clips[i].index = i;
                    }
                    await state.saveProject(project);
                  },
                ),
              )),
      ],
    );
  }

  Future<void> _share(Clip clip) async {
    final path = clip.files['mp4'];
    if (path == null || !File(path).existsSync()) return;
    await Share.shareXFiles([XFile(path)], text: clip.title);
  }

  Future<void> _export(BuildContext context, Project project) async {
    try {
      await state.exportProject();
      if (context.mounted && state.lastOutput != null) {
        await Share.shareXFiles([XFile(state.lastOutput!)]);
      }
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }
}
