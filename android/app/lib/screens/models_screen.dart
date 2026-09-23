import 'package:flutter/material.dart';

import '../models.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

/// Kotak peringatan bergaris merah untuk kegagalan unduh/ekstrak model.
class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(Tokens.space3),
      decoration: BoxDecoration(
        color: Tokens.danger.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(Tokens.radiusSm),
        border: Border.all(color: Tokens.danger.withValues(alpha: 0.35)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, color: Tokens.danger, size: 18),
          const SizedBox(width: Tokens.space2),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Unduhan gagal',
                    style: TextStyle(
                        color: Tokens.danger,
                        fontSize: 13,
                        fontWeight: FontWeight.w600)),
                const SizedBox(height: 2),
                Text(message,
                    style: const TextStyle(color: Tokens.text2, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class ModelsScreen extends StatelessWidget {
  const ModelsScreen({super.key, required this.state});

  final AppState state;

  String _licenseLabel(ModelInfo model) => switch (model.commercialUse) {
        'allowed' => model.license == 'OpenRAIL-M'
            ? 'Komersial bersyarat'
            : 'Komersial diizinkan',
        'restricted' => 'Bukan untuk komersial',
        'unverified' => 'Hak komersial belum jelas',
        _ => 'Lisensi: ${model.license}',
      };

  Future<void> _showLicense(BuildContext context, ModelInfo model) =>
      showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: Text(model.id),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${_licenseLabel(model)} · ${model.license}'),
                if (model.licenseNote.isNotEmpty) ...[
                  const SizedBox(height: Tokens.space2),
                  Text(model.licenseNote),
                ],
                if (model.licenseUrl != null) ...[
                  const SizedBox(height: Tokens.space2),
                  const Text('Sumber lisensi:',
                      style: TextStyle(color: Tokens.textDim)),
                  SelectableText(model.licenseUrl!),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Tutup'),
            ),
          ],
        ),
      );

  @override
  Widget build(BuildContext context) {
    final device = state.device;
    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        Text(state.translate('models.title'),
            style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w600,
                letterSpacing: -0.4)),
        const SizedBox(height: Tokens.space2),
        Text(state.translate('models.lead'),
            style: const TextStyle(color: Tokens.textDim)),
        const SizedBox(height: Tokens.space4),
        SectionCard(
          title: state.translate('models.build'),
          child: device == null
              ? const Text('…', style: TextStyle(color: Tokens.textDim))
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${device.model} · ${device.androidVersion}'),
                    Text(
                        'RAM ${device.ramGb.toStringAsFixed(1)} GB · Disk bebas ${device.diskFreeGb.toStringAsFixed(1)} GB',
                        style: const TextStyle(
                            color: Tokens.textDim, fontSize: 13)),
                    Text('ABI: ${device.abis.join(', ')}',
                        style: const TextStyle(
                            color: Tokens.textDim, fontSize: 12)),
                    const SizedBox(height: Tokens.space2),
                    Wrap(
                      spacing: Tokens.space2,
                      runSpacing: Tokens.space2,
                      children:
                          device.recommendations().map((r) => Pill(r)).toList(),
                    ),
                  ],
                ),
        ),
        if (state.jobState != JobState.idle) ...[
          const SizedBox(height: Tokens.space3),
          ProgressStrip(
              progress: state.jobProgress,
              label: '${state.jobStage} ${state.jobMessage}'),
        ],
        if (state.jobState == JobState.error) ...[
          const SizedBox(height: Tokens.space3),
          _ErrorBanner(message: state.jobMessage),
        ],
        const SizedBox(height: Tokens.space4),
        ...state.catalog.map((model) => Padding(
              padding: const EdgeInsets.only(bottom: Tokens.space3),
              child: _modelCard(context, model),
            )),
        const SizedBox(height: Tokens.space4),
        OutlinedButton(
          onPressed: () => state.clearCache(),
          child: Text(state.translate('settings.clearCache')),
        ),
      ],
    );
  }

  Widget _modelCard(BuildContext context, ModelInfo model) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Tokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(model.id,
                      style: const TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w600)),
                ),
                if (!model.recommended)
                  Pill(
                      model.id == 'piper-id_ID-news_tts-medium'
                          ? 'opsional'
                          : 'model lama',
                      tone: 'warn'),
                if (model.experimental)
                  const Pill('eksperimental', tone: 'warn'),
              ],
            ),
            const SizedBox(height: Tokens.space1),
            Text('${model.kind} · ${model.sizeMb} MB · ${model.license}',
                style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
            const SizedBox(height: Tokens.space1),
            Text(model.note,
                style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
            if (model.kind == 'tts' || model.kind == 'clone') ...[
              const SizedBox(height: Tokens.space2),
              Row(children: [
                Flexible(
                  child: Text(_licenseLabel(model),
                      style: const TextStyle(
                          color: Tokens.text2,
                          fontSize: 12,
                          fontWeight: FontWeight.w600)),
                ),
                IconButton(
                    tooltip: 'Detail lisensi',
                    visualDensity: VisualDensity.compact,
                    icon: const Icon(Icons.info_outline, size: 18),
                    onPressed: () => _showLicense(context, model)),
              ]),
            ],
            const SizedBox(height: Tokens.space3),
            Row(
              children: [
                if (model.installed)
                  const Pill('terpasang', tone: 'ok')
                else if (state.jobState == JobState.running)
                  const Pill('menunggu…', tone: 'info')
                else
                  FilledButton(
                    onPressed: () async {
                      try {
                        await state.downloadModel(model);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                                content: Text(
                                    '${model.id} terpasang dan siap dipakai')),
                          );
                        }
                      } catch (error) {
                        if (context.mounted) {
                          ScaffoldMessenger.of(context)
                              .showSnackBar(SnackBar(content: Text('$error')));
                        }
                      }
                    },
                    child: Text(state.translate('models.download')),
                  ),
                const Spacer(),
                if (model.installed)
                  TextButton(
                    onPressed: () => state.removeModel(model),
                    style: TextButton.styleFrom(foregroundColor: Tokens.danger),
                    child: Text(state.translate('models.remove')),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
