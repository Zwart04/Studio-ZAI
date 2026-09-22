import 'package:flutter/material.dart';

import '../state/app_state.dart';

/// First-run setup remains open until required downloads have been verified.
class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key, required this.state});
  final AppState state;

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  bool _busy = false;
  bool _includeClone = true;
  String? _error;

  Future<void> _install() async {
    setState(() { _busy = true; _error = null; });
    final state = widget.state;
    try {
      final ids = [state.asrModelId, 'silero-vad', 'piper-id_ID-news_tts-medium', 'piper-en_US-lessac-medium', if (_includeClone) state.cloneModelId];
      for (final id in ids) {
        final model = state.models.find(id);
        if (model == null) throw Exception('Model tidak ditemukan: $id');
        if (!state.models.isInstalled(model)) await state.downloadModel(model);
      }
      await state.finishSetup();
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final ids = [state.asrModelId, 'silero-vad', 'piper-id_ID-news_tts-medium', 'piper-en_US-lessac-medium', if (_includeClone) state.cloneModelId];
    return PopScope(
      canPop: false,
      child: Scaffold(
        appBar: AppBar(title: const Text('Setup awal Studio ZAI')),
        body: ListView(padding: const EdgeInsets.all(24), children: [
          const Text('Siapkan fitur sebelum mulai', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          const Text('FFmpeg untuk edit/render sudah termasuk APK. Unduh model di bawah sekali untuk transkrip, subtitle otomatis, dan suara Indonesia/Inggris. Tetap buka aplikasi selama pemasangan; unduhan terputus bisa dilanjutkan.'),
          const SizedBox(height: 16),
          for (final id in ids)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Icon(state.catalog.any((m) => m.id == id && m.installed) ? Icons.check_circle : Icons.download),
              title: Text(id),
              subtitle: Text(state.models.find(id)?.note ?? ''),
              trailing: Text('~${state.models.find(id)?.sizeMb.round() ?? 0} MB'),
            ),
          CheckboxListTile(
            value: _includeClone,
            onChanged: _busy ? null : (value) => setState(() => _includeClone = value ?? true),
            title: const Text('Pasang kloning suara juga'),
            subtitle: const Text('ZipVoice mendukung Inggris. Jika dilewati, fitur kloning perlu unduhan dari halaman Model sebelum digunakan.'),
          ),
          if (_busy) ...[
            LinearProgressIndicator(value: state.jobProgress.clamp(0, 100) / 100),
            const SizedBox(height: 12),
            Text('${state.jobStage} ${state.jobProgress.toStringAsFixed(0)}%'),
          ],
          if (_error != null) Padding(padding: const EdgeInsets.symmetric(vertical: 12), child: Text(_error!, style: const TextStyle(color: Colors.redAccent))),
          const SizedBox(height: 20),
          FilledButton(onPressed: _busy ? null : _install, child: Text(_error == null ? 'Unduh, verifikasi, dan mulai' : 'Coba lagi / lanjutkan unduhan')),
        ]),
      ),
    );
  }
}
