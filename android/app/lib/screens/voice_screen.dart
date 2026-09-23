import 'dart:io';
import 'dart:async';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'package:record/record.dart';
import '../services/cloud_ai.dart';
import '../services/voice_reference.dart';
import 'cloud_settings_screen.dart';
import 'models_screen.dart';

import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class VoiceScreen extends StatefulWidget {
  const VoiceScreen({super.key, required this.state});

  final AppState state;

  @override
  State<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends State<VoiceScreen> {
  final _text = TextEditingController();
  final _cloneText = TextEditingController();
  final _sample = TextEditingController();
  final _sampleText = TextEditingController();
  String _modelId = '';
  int _speakerId = 0;
  String _language = 'id';
  String? _lastFile;
  String? _samplePath;
  bool _cloning = false;
  bool _online = false, _generating = false, _recording = false;
  bool _preparingSample = false;
  String _voice = 'marin';
  final _recorder = AudioRecorder();
  Timer? _timer;

  @override
  void dispose() {
    _timer?.cancel();
    _recorder.dispose();
    _text.dispose();
    _cloneText.dispose();
    _sample.dispose();
    _sampleText.dispose();
    super.dispose();
  }

  Future<void> _pickSample() async {
    try {
      // FileType.audio can hide WhatsApp/M4A/OGG recordings on Android file
      // providers. Decode the selected file rather than trusting its suffix.
      final files = await FilePicker.pickFiles(type: FileType.any);
      if (files.isEmpty || !mounted) return;
      setState(() => _preparingSample = true);
      final dir = Directory('${widget.state.dataDir.path}/voices/references');
      final file = await VoiceReference.importFile(files.first, dir);
      final previous = _samplePath;
      if (previous != null &&
          previous.startsWith('${dir.path}/') &&
          previous != file.path) {
        try {
          await File(previous).delete();
        } catch (_) {}
      }
      if (mounted) {
        setState(() {
          _samplePath = file.path;
          _sample.text = files.first.name;
        });
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    } finally {
      if (mounted) setState(() => _preparingSample = false);
    }
  }

  Future<void> _record() async {
    try {
      if (_recording) {
        _timer?.cancel();
        final path = await _recorder.stop();
        if (mounted) {
          setState(() {
            _recording = false;
            if (path != null) {
              _samplePath = path;
              _sample.text = 'Rekaman mikrofon · 30 detik maks.';
            }
          });
        }
        return;
      }
      if (!await _recorder.hasPermission()) {
        throw Exception('Izin mikrofon diperlukan untuk merekam.');
      }
      final dir = Directory('${widget.state.dataDir.path}/voices')
        ..createSync(recursive: true);
      await _recorder.start(
          const RecordConfig(
              encoder: AudioEncoder.wav, sampleRate: 24000, numChannels: 1),
          path:
              '${dir.path}/sample-${DateTime.now().millisecondsSinceEpoch}.wav');
      if (!mounted) {
        await _recorder.stop();
        return;
      }
      setState(() => _recording = true);
      _timer = Timer(const Duration(seconds: 30), () {
        if (_recording) _record();
      });
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final ttsModels = state.catalog.where((m) => m.kind == 'tts').toList();
    final installed = ttsModels
        .where((m) =>
            m.installed &&
            (m.id == 'supertonic-3-int8' ||
                m.id.startsWith(_language == 'id' ? 'piper-id_' : 'piper-en_')))
        .toList();
    final preferred =
        _language == 'id' ? 'supertonic-3-int8' : 'piper-en_US-ljspeech-medium';
    installed.sort((a, b) {
      if (a.id == preferred) return -1;
      if (b.id == preferred) return 1;
      return a.id.compareTo(b.id);
    });
    final cloneInstalled =
        state.catalog.any((m) => m.id == 'zipvoice-zh-en' && m.installed);
    _modelId = installed.any((m) => m.id == _modelId)
        ? _modelId
        : (installed.isEmpty ? '' : installed.first.id);
    final selectedModel = installed.where((m) => m.id == _modelId).firstOrNull;

    return ListView(
      padding: const EdgeInsets.all(Tokens.space4),
      children: [
        Text(state.translate('voice.title'),
            style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w600,
                letterSpacing: -0.4)),
        const SizedBox(height: Tokens.space2),
        Text(state.translate('voice.lead'),
            style: const TextStyle(color: Tokens.textDim)),
        const SizedBox(height: Tokens.space4),
        if (state.voiceModelUpgradeAvailable) ...[
          SectionCard(
            title: 'Pilihan suara baru',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Model suara yang sudah terpasang tetap bisa dipakai. Supertonic 3 (Indonesia/English) dan Piper LJSpeech (English) tersedia sebagai pembaruan opsional.',
                  style: TextStyle(color: Tokens.textDim, fontSize: 12),
                ),
                const SizedBox(height: Tokens.space2),
                OutlinedButton.icon(
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute<void>(
                      builder: (_) => Scaffold(
                        appBar: AppBar(title: const Text('Model')),
                        body: ModelsScreen(state: state),
                      ),
                    ),
                  ),
                  icon: const Icon(Icons.download_outlined, size: 18),
                  label: const Text('Lihat model suara baru'),
                ),
              ],
            ),
          ),
          const SizedBox(height: Tokens.space4),
        ],
        SectionCard(
          title: state.translate('voice.generate'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<bool>(
                  initialValue: _online,
                  decoration: const InputDecoration(labelText: 'Mesin suara'),
                  items: const [
                    DropdownMenuItem(
                        value: false, child: Text('Lokal · offline')),
                    DropdownMenuItem(
                        value: true, child: Text('Online · opsional'))
                  ],
                  onChanged: (value) =>
                      setState(() => _online = value ?? false)),
              if (_online) ...[
                const SizedBox(height: Tokens.space3),
                DropdownButtonFormField<String>(
                    initialValue: _voice,
                    decoration:
                        const InputDecoration(labelText: 'Karakter suara'),
                    items: CloudAI.voices
                        .map((v) => DropdownMenuItem(value: v, child: Text(v)))
                        .toList(),
                    onChanged: (value) =>
                        setState(() => _voice = value ?? 'marin')),
                TextButton(
                    onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute<void>(
                            builder: (_) => const CloudSettingsScreen())),
                    child:
                        const Text('Atur API key · teks dikirim ke penyedia')),
              ],
              const SizedBox(height: Tokens.space4),
              TextField(
                  controller: _text,
                  maxLines: 4,
                  decoration: const InputDecoration(
                      labelText: 'Teks narasi',
                      helperText: 'Teks ini dipakai untuk TTS di bagian ini.')),
              const SizedBox(height: Tokens.space4),
              Row(children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _language,
                    decoration: InputDecoration(
                        labelText: state.translate('voice.lang')),
                    items: const [
                      DropdownMenuItem(value: 'id', child: Text('Indonesia')),
                      DropdownMenuItem(value: 'en', child: Text('English')),
                    ],
                    onChanged: (value) => setState(() {
                      _language = value ?? 'id';
                      _modelId = '';
                    }),
                  ),
                ),
                if (!_online) ...[
                  const SizedBox(width: Tokens.space3),
                  Expanded(
                    child: installed.isEmpty
                        ? const Text('Belum ada model suara terpasang.',
                            style:
                                TextStyle(color: Tokens.textDim, fontSize: 12))
                        : DropdownButtonFormField<String>(
                            key: ValueKey('local-voice-$_language'),
                            initialValue: _modelId,
                            decoration: InputDecoration(
                                labelText: state.translate('voice.model')),
                            items: installed
                                .map((m) => DropdownMenuItem(
                                    value: m.id,
                                    child: Text(
                                        m.id == 'supertonic-3-int8'
                                            ? 'Supertonic 3 · 10 suara'
                                            : '${m.id.replaceFirst('piper-', '').replaceAll('-medium', '')}${m.recommended ? '' : ' · lama'}',
                                        overflow: TextOverflow.ellipsis)))
                                .toList(),
                            onChanged: (value) =>
                                setState(() => _modelId = value ?? ''),
                          ),
                  ),
                ],
              ]),
              if (!_online && _modelId == 'supertonic-3-int8') ...[
                const SizedBox(height: Tokens.space3),
                DropdownButtonFormField<int>(
                  initialValue: _speakerId,
                  decoration:
                      const InputDecoration(labelText: 'Karakter suara'),
                  items: List.generate(
                      10,
                      (sid) => DropdownMenuItem(
                            value: sid,
                            child: Text('Suara ${sid + 1}'),
                          )),
                  onChanged: (value) => setState(() => _speakerId = value ?? 0),
                ),
                const SizedBox(height: Tokens.space2),
                const Text(
                    'Sepuluh karakter suara tersedia untuk Indonesia dan English.',
                    style: TextStyle(color: Tokens.textDim, fontSize: 12)),
              ],
              if (!_online && selectedModel != null) ...[
                const SizedBox(height: Tokens.space2),
                Text(
                  selectedModel.licenseNote.isNotEmpty
                      ? selectedModel.licenseNote
                      : 'Periksa lisensi model sebelum publikasi.',
                  style: const TextStyle(color: Tokens.textDim, fontSize: 12),
                ),
              ],
              const SizedBox(height: Tokens.space4),
              FilledButton(
                onPressed: (!_online && installed.isEmpty) ||
                        _generating ||
                        state.jobState == JobState.running
                    ? null
                    : () async {
                        // Messenger diambil SEBELUM await supaya `context` tidak
                        // dipakai lagi setelah jeda async.
                        final messenger = ScaffoldMessenger.of(context);
                        try {
                          setState(() => _generating = true);
                          final file = _online
                              ? await CloudAI.speech(
                                  _text.text, _voice, _language, state.dataDir)
                              : await state.quickVoice(
                                  _text.text, _modelId, _language,
                                  speakerId: _speakerId);
                          if (!mounted) return;
                          setState(() => _lastFile = file.path);
                        } catch (error) {
                          messenger
                              .showSnackBar(SnackBar(content: Text('$error')));
                        } finally {
                          if (mounted) setState(() => _generating = false);
                        }
                      },
                child: Text(_generating
                    ? 'Membuat suara…'
                    : state.translate('voice.generate')),
              ),
              if (state.jobState == JobState.running) ...[
                const SizedBox(height: Tokens.space3),
                ProgressStrip(
                    progress: state.jobProgress, label: state.jobStage),
              ],
              if (_lastFile != null) ...[
                const SizedBox(height: Tokens.space3),
                Row(children: [
                  const Icon(Icons.graphic_eq, color: Tokens.success, size: 18),
                  const SizedBox(width: Tokens.space2),
                  Expanded(
                      child: Text(File(_lastFile!).uri.pathSegments.last,
                          style: const TextStyle(fontSize: 12))),
                  TextButton(
                    onPressed: () => SharePlus.instance
                        .share(ShareParams(files: [XFile(_lastFile!)])),
                    child: Text(state.translate('clips.share')),
                  ),
                ]),
              ],
            ],
          ),
        ),
        const SizedBox(height: Tokens.space5),
        SectionCard(
          title: state.translate('voice.clone'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Pill('eksperimental', tone: 'warn'),
              const SizedBox(height: Tokens.space2),
              Text(
                state.translate('voice.experimentalNote'),
                style: const TextStyle(color: Tokens.textDim, fontSize: 12),
              ),
              const SizedBox(height: Tokens.space3),
              TextField(
                controller: _sample,
                readOnly: true,
                decoration: InputDecoration(
                  labelText: state.translate('voice.sample'),
                  helperText:
                      'Pilih audio apa saja atau rekam 4–30 detik. Audio diubah ke WAV lokal.',
                ),
              ),
              const SizedBox(height: Tokens.space2),
              Wrap(
                spacing: Tokens.space2,
                runSpacing: Tokens.space2,
                children: [
                  OutlinedButton.icon(
                    onPressed:
                        _preparingSample || _recording ? null : _pickSample,
                    icon: const Icon(Icons.audiotrack, size: 18),
                    label: Text(_preparingSample
                        ? 'Menyiapkan rekaman…'
                        : state.translate('voice.pickSample')),
                  ),
                  OutlinedButton.icon(
                      onPressed: _preparingSample ? null : _record,
                      icon: Icon(_recording ? Icons.stop : Icons.mic_none),
                      label: Text(_recording
                          ? 'Selesai · maks. 30 detik'
                          : 'Rekam mikrofon')),
                ],
              ),
              const SizedBox(height: Tokens.space3),
              const Text(
                  'ZipVoice memakai rekaman contoh dan transkripnya untuk meniru warna suara. Hasil teks baru didukung English/Mandarin; kloning Indonesia belum tersedia di model lokal ringan.',
                  style: TextStyle(color: Tokens.textDim, fontSize: 12)),
              if (!cloneInstalled) ...[
                const SizedBox(height: Tokens.space2),
                const Text(
                    'Pasang ZipVoice (EN/ZH) di tab Model sebelum membuat kloning.',
                    style: TextStyle(color: Tokens.textDim, fontSize: 12)),
              ],
              const SizedBox(height: Tokens.space3),
              TextField(
                controller: _sampleText,
                decoration: InputDecoration(
                  labelText: state.translate('voice.sampleText'),
                  hintText: 'tulis persis kata yang terdengar pada contoh',
                ),
              ),
              const SizedBox(height: Tokens.space3),
              TextField(
                controller: _cloneText,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Teks baru yang akan dibacakan',
                  hintText: 'Write the new English sentence here',
                  helperText:
                      'Berbeda dari transkrip contoh: ini isi suara hasil kloning.',
                ),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: state.cloneConsent,
                onChanged: (value) => state.setConsent(value),
                title: Text(state.translate('voice.consent'),
                    style: const TextStyle(fontSize: 13)),
              ),
              OutlinedButton(
                onPressed: !state.cloneConsent ||
                        !cloneInstalled ||
                        _cloning ||
                        _preparingSample ||
                        state.jobState == JobState.running
                    ? null
                    : () async {
                        // Messenger diambil SEBELUM await supaya `context` tidak
                        // dipakai lagi setelah jeda async.
                        final messenger = ScaffoldMessenger.of(context);
                        try {
                          setState(() => _cloning = true);
                          final file = await state.speech.cloneWithZipVoice(
                            text: _cloneText.text,
                            referenceWav: _samplePath ?? '',
                            referenceText: _sampleText.text,
                            outputPath: '${state.dataDir.path}/voices/clone-'
                                '${DateTime.now().millisecondsSinceEpoch}.wav',
                          );
                          if (!mounted) return;
                          setState(() {
                            _cloning = false;
                            _lastFile = file.path;
                          });
                          messenger.showSnackBar(
                            SnackBar(
                                content: Text(state.translate('common.done'))),
                          );
                        } catch (error) {
                          if (mounted) setState(() => _cloning = false);
                          messenger
                              .showSnackBar(SnackBar(content: Text('$error')));
                        }
                      },
                child: _cloning
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(state.translate('voice.clone')),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
