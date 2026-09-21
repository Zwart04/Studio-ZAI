import 'dart:io';

import 'package:flutter/material.dart';

import '../models.dart';
import '../theme/tokens.dart';

class SectionCard extends StatelessWidget {
  const SectionCard({super.key, required this.child, this.title});

  final Widget child;
  final String? title;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Tokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (title != null) ...[
              Text(title!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              const SizedBox(height: Tokens.space3),
            ],
            child,
          ],
        ),
      ),
    );
  }
}

class Pill extends StatelessWidget {
  const Pill(this.text, {super.key, this.tone = 'neutral'});

  final String text;
  final String tone;

  @override
  Widget build(BuildContext context) {
    final color = switch (tone) {
      'ok' => Tokens.green,
      'warn' => Tokens.orange,
      'danger' => Tokens.red,
      'info' => Tokens.accent,
      _ => Tokens.textDim,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: Tokens.space2, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(Tokens.radiusPill),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(text, style: TextStyle(color: color, fontSize: 12)),
    );
  }
}

class ProgressStrip extends StatelessWidget {
  const ProgressStrip({super.key, required this.progress, required this.label});

  final double progress;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Tokens.textDim, fontSize: 13)),
        const SizedBox(height: Tokens.space2),
        ClipRRect(
          borderRadius: BorderRadius.circular(Tokens.radiusPill),
          child: LinearProgressIndicator(
            value: (progress / 100).clamp(0, 1),
            minHeight: 4,
            backgroundColor: Tokens.surface2,
            valueColor: const AlwaysStoppedAnimation(Tokens.accent),
          ),
        ),
      ],
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState(this.message, {super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: Tokens.space8, horizontal: Tokens.space4),
      decoration: BoxDecoration(
        border: Border.all(color: Tokens.separator),
        borderRadius: BorderRadius.circular(Tokens.radius),
      ),
      child: Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Tokens.textDim)),
    );
  }
}

String formatClock(double seconds) {
  final total = seconds.round();
  final minutes = total ~/ 60;
  final rest = total % 60;
  return '$minutes:${rest.toString().padLeft(2, '0')}';
}

class ClipTile extends StatelessWidget {
  const ClipTile({
    super.key,
    required this.clip,
    required this.onEdit,
    required this.onRender,
    required this.onShare,
    required this.onDelete,
    required Map<String, String> labels,
  }) : _labels = labels;

  final Clip clip;
  final VoidCallback onEdit;
  final VoidCallback onRender;
  final VoidCallback onShare;
  final VoidCallback onDelete;
  final Map<String, String> _labels;

  @override
  Widget build(BuildContext context) {
    final thumbPath = clip.files['thumb'];
    final ready = (clip.files['mp4'] ?? '').isNotEmpty && File(clip.files['mp4']!).existsSync();
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AspectRatio(
            aspectRatio: 9 / 16,
            child: ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(Tokens.radius)),
              child: thumbPath != null && File(thumbPath).existsSync()
                  ? Image.file(File(thumbPath), fit: BoxFit.cover)
                  : Container(color: Tokens.surface2),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(Tokens.space3),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(clip.title.isEmpty ? 'Klip ${clip.index + 1}' : clip.title,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                const SizedBox(height: 2),
                Text('${formatClock(clip.start)}–${formatClock(clip.end)} · ${clip.score.toStringAsFixed(2)}',
                    style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
                const SizedBox(height: Tokens.space2),
                Row(children: [
                  Pill(ready ? _labels['ready'] ?? 'siap' : _labels['draft'] ?? 'draft', tone: ready ? 'ok' : 'warn'),
                  const SizedBox(width: Tokens.space2),
                  Pill(clip.crop),
                ]),
                const SizedBox(height: Tokens.space3),
                Wrap(spacing: Tokens.space2, children: [
                  TextButton(onPressed: onEdit, child: Text(_labels['edit'] ?? 'Edit')),
                  TextButton(onPressed: onRender, child: Text(_labels['render'] ?? 'Render')),
                  TextButton(onPressed: onShare, child: Text(_labels['share'] ?? 'Share')),
                  TextButton(
                    onPressed: onDelete,
                    style: TextButton.styleFrom(foregroundColor: Tokens.danger),
                    child: Text(_labels['delete'] ?? 'Delete'),
                  ),
                ]),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
