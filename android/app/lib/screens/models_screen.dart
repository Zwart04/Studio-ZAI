import 'package:flutter/material.dart';

import '../models.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class ModelsScreen extends StatelessWidget {
  const ModelsScreen({super.key, required this.state});

  final AppState state;

  @override
  Widget build(BuildContext context) {
    final device = state.device;
    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        Text(state.translate('models.title'),
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.4)),
        const SizedBox(height: Tokens.space2),
        Text(state.translate('models.lead'), style: const TextStyle(color: Tokens.textDim)),
        const SizedBox(height: Tokens.space4),
        SectionCard(
          title: state.translate('models.build'),
          child: device == null
              ? const Text('…', style: TextStyle(color: Tokens.textDim))
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${device.model} · ${device.androidVersion}'),
                    Text('RAM ${device.ramGb} GB · Disk bebas ${device.diskFreeGb.toStringAsFixed(1)} GB',
                        style: const TextStyle(color: Tokens.textDim, fontSize: 13)),
                    Text('ABI: ${device.abis.join(', ')}', style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
                    const SizedBox(height: Tokens.space2),
                    Wrap(
                      spacing: Tokens.space2,
                      runSpacing: Tokens.space2,
                      children: device.recommendations().map((r) => Badge(r)).toList(),
                    ),
                  ],
                ),
        ),
        if (state.jobState != JobState.idle) ...[
          const SizedBox(height: Tokens.space3),
          ProgressStrip(progress: state.jobProgress, label: '${state.jobStage} ${state.jobMessage}'),
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
    final busy = state.jobState == JobState.running;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Tokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(model.id, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                ),
                if (model.experimental) const Badge('eksperimental', tone: 'warn'),
              ],
            ),
            const SizedBox(height: Tokens.space1),
            Text('${model.kind} · ${model.sizeMb} MB · ${model.license}',
                style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
            const SizedBox(height: Tokens.space1),
            Text(model.note, style: const TextStyle(color: Tokens.textDim, fontSize: 12)),
            const SizedBox(height: Tokens.space3),
            Row(
              children: [
                if (model.installed)
                  const Badge('terpasang', tone: 'ok')
                else
                  FilledButton(
                    onPressed: busy
                        ? null
                        : () async {
                            try {
                              await state.downloadModel(model);
                            } catch (error) {
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
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
