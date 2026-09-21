import 'package:flutter/material.dart';

import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key, required this.state});

  final AppState state;

  @override
  Widget build(BuildContext context) {
    final asr = state.catalog.where((m) => m.kind == 'asr' && m.id != 'silero-vad').toList();
    final tts = state.catalog.where((m) => m.kind == 'tts').toList();
    final clones = state.catalog.where((m) => m.kind == 'clone').toList();

    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        Text(state.translate('settings.title'),
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.4)),
        const SizedBox(height: Tokens.space4),
        SectionCard(
          child: Column(
            children: [
              DropdownButtonFormField<String>(
                initialValue: state.lang,
                decoration: InputDecoration(labelText: state.translate('settings.language')),
                items: const [
                  DropdownMenuItem(value: 'id', child: Text('Indonesia')),
                  DropdownMenuItem(value: 'en', child: Text('English')),
                ],
                onChanged: (value) => state.setLang(value ?? 'id'),
              ),
              const SizedBox(height: Tokens.space3),
              DropdownButtonFormField<String>(
                initialValue: asr.any((m) => m.id == state.asrModelId) ? state.asrModelId : asr.first.id,
                decoration: InputDecoration(labelText: state.translate('settings.asr')),
                items: asr.map((m) => DropdownMenuItem(value: m.id, child: Text(m.id))).toList(),
                onChanged: (value) => state.saveSetting('asr', value ?? state.asrModelId),
              ),
              const SizedBox(height: Tokens.space3),
              DropdownButtonFormField<String>(
                initialValue: tts.any((m) => m.id == state.ttsModelId) ? state.ttsModelId : tts.first.id,
                decoration: InputDecoration(labelText: state.translate('settings.tts')),
                items: tts.map((m) => DropdownMenuItem(value: m.id, child: Text(m.id))).toList(),
                onChanged: (value) => state.saveSetting('tts', value ?? state.ttsModelId),
              ),
              const SizedBox(height: Tokens.space3),
              DropdownButtonFormField<String>(
                initialValue: clones.any((m) => m.id == state.cloneModelId) ? state.cloneModelId : clones.first.id,
                decoration: InputDecoration(labelText: state.translate('settings.clone')),
                items: clones.map((m) => DropdownMenuItem(value: m.id, child: Text(m.id))).toList(),
                onChanged: (value) => state.saveSetting('clone', value ?? state.cloneModelId),
              ),
              const SizedBox(height: Tokens.space3),
              DropdownButtonFormField<String>(
                initialValue: state.defaultCrop,
                decoration: InputDecoration(labelText: state.translate('settings.crop')),
                items: const [
                  DropdownMenuItem(value: 'center', child: Text('Center 9:16')),
                  DropdownMenuItem(value: 'blur', child: Text('Blur background')),
                ],
                onChanged: (value) => state.saveSetting('crop', value ?? 'center'),
              ),
            ],
          ),
        ),
        const SizedBox(height: Tokens.space3),
        SectionCard(
          title: 'Privasi',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Studio ZAI tidak mengirim data apa pun ke internet kecuali video yang kamu minta '
                'untuk diunduh dan model yang kamu unduh sendiri. Tidak ada telemetri.',
                style: TextStyle(color: Tokens.textDim, fontSize: 12),
              ),
              const SizedBox(height: Tokens.space3),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: state.cloneConsent,
                onChanged: (value) => state.setConsent(value),
                title: Text(state.translate('voice.consent'), style: const TextStyle(fontSize: 13)),
              ),
            ],
          ),
        ),
        const SizedBox(height: Tokens.space3),
        SectionCard(
          title: 'Tentang',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Studio ZAI 1.0.0', style: TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: Tokens.space1),
              const Text('Lisensi MIT · model: Piper (MIT), Whisper (MIT), ZipVoice (Apache-2.0), Chatterbox (MIT)',
                  style: TextStyle(color: Tokens.textDim, fontSize: 12)),
              const SizedBox(height: Tokens.space2),
              Text('Data: ${state.dataDir.path}', style: const TextStyle(color: Tokens.textDim, fontSize: 11)),
            ],
          ),
        ),
        const SizedBox(height: Tokens.space4),
        OutlinedButton(
          onPressed: () => state.clearCache(),
          child: Text(state.translate('settings.clearCache')),
        ),
      ],
    );
  }
}
