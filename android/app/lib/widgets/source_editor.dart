import 'package:flutter/material.dart';

import '../state/app_state.dart';
import '../screens/editor_screen.dart';
import 'preview_player.dart';

Future<void> openSourceEditor(BuildContext context, AppState state) async {
  final project = state.currentProject!;
  final start = TextEditingController(text: '0');
  final end = TextEditingController(
    text: '${project.duration < 30 ? project.duration : 30}',
  );
  var canvas = 'portrait';
  String? error;
  final clip = await showDialog<dynamic>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, update) => AlertDialog(
        title: const Text('Ambil bagian video'),
        content: SizedBox(
          width: 480,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                SizedBox(
                  height: 180,
                  child: VideoPreview(path: project.source),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Video sudah tersimpan. Pilih waktu dalam detik tanpa mengunduh lagi.',
                ),
                TextField(
                  controller: start,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(labelText: 'Mulai (detik)'),
                ),
                TextField(
                  controller: end,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: InputDecoration(
                    labelText:
                        'Selesai · maks. ${project.duration.toStringAsFixed(1)}',
                  ),
                ),
                DropdownButtonFormField<String>(
                  initialValue: canvas,
                  decoration: const InputDecoration(labelText: 'Kanvas'),
                  items: const [
                    DropdownMenuItem(value: 'original', child: Text('Asli')),
                    DropdownMenuItem(
                      value: 'portrait',
                      child: Text('Portrait 9:16'),
                    ),
                    DropdownMenuItem(value: 'square', child: Text('Kotak 1:1')),
                    DropdownMenuItem(
                      value: 'landscape',
                      child: Text('Landscape 16:9'),
                    ),
                  ],
                  onChanged: (value) => canvas = value ?? 'original',
                ),
                if (error != null) Text(error!),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () async {
              try {
                final clip = await state.addSourceClip(
                  double.tryParse(start.text) ?? -1,
                  double.tryParse(end.text) ?? -1,
                  canvas,
                );
                if (dialogContext.mounted) {
                  Navigator.pop(dialogContext, clip);
                }
              } catch (e) {
                update(() => error = '$e');
              }
            },
            child: const Text('Buat & edit'),
          ),
        ],
      ),
    ),
  );
  // Dialog route may still be animating when its Future completes.
  await Future<void>.delayed(const Duration(milliseconds: 250));
  start.dispose();
  end.dispose();
  if (clip != null && context.mounted) {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => EditorScreen(state: state, clip: clip),
      ),
    );
  }
}
