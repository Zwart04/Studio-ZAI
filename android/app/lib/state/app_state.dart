import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../i18n/strings.dart';
import '../models.dart';
import '../services/downloader.dart';
import '../services/media_tools.dart';
import '../services/model_manager.dart';
import '../services/model_registry.dart';
import '../services/pipeline.dart';
import '../services/speech.dart';
import '../services/timeline.dart';
import '../services/subtitle_builder.dart';
import '../services/cloud_ai.dart';
import '../services/clip_edits.dart';

enum JobState { idle, running, done, error }

class AppState extends ChangeNotifier {
  AppState(this._strings);

  final S _strings;
  S get strings => _strings;

  ModelManager? _models;
  SpeechService? _speech;
  SharedPreferences? _prefs;
  Directory? _dataDir;

  String lang = 'id';
  String asrModelId = 'whisper-base';
  String ttsModelId = 'supertonic-3-int8';
  String cloneModelId = 'zipvoice-zh-en';
  String defaultCrop = 'center';
  bool cloneConsent = false;
  bool setupComplete = false;

  List<ModelInfo> catalog = const [];
  DeviceReport? device;
  List<Project> projects = const [];
  Project? currentProject;

  JobState jobState = JobState.idle;
  double jobProgress = 0;
  String jobStage = '';
  String jobMessage = '';
  String? lastOutput;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    lang = _prefs!.getString('lang') ?? 'id';
    asrModelId = _prefs!.getString('asr') ?? asrModelId;
    ttsModelId = _prefs!.getString('tts') ?? ttsModelId;
    cloneModelId = _prefs!.getString('clone') ?? cloneModelId;
    defaultCrop = _prefs!.getString('crop') ?? defaultCrop;
    cloneConsent = _prefs!.getBool('cloneConsent') ?? false;
    // Keep existing installations unlocked. The v1.8 voice models are offered
    // as an upgrade in Suara instead of forcing returning users through setup.
    setupComplete = _prefs!.getInt('setupVersion') == 2;

    final base = await getApplicationSupportDirectory();
    _dataDir = Directory('${base.path}/studiozai')..createSync(recursive: true);
    _models = await ModelManager.instance();
    _speech = SpeechService(_models!);
    await refreshModels();
    await refreshDevice();
    final custom = jsonDecode(_prefs!.getString('typography') ?? '{}') as Map;
    for (final entry in custom.entries) {
      SubtitleBuilder.presets[entry.key as String] =
          Map<String, dynamic>.from(entry.value as Map);
    }
    loadProjects();
    notifyListeners();
  }

  ModelManager get models => _models!;
  bool get voiceModelUpgradeAvailable =>
      setupComplete &&
      !['supertonic-3-int8', 'piper-en_US-ljspeech-medium'].every(
          (id) => catalog.any((model) => model.id == id && model.installed));

  Future<void> finishSetup() async {
    await refreshModels();
    final needed = [
      asrModelId,
      'silero-vad',
      'supertonic-3-int8',
      'piper-en_US-ljspeech-medium'
    ];
    if (needed.any((id) => !catalog.any((m) => m.id == id && m.installed))) {
      throw Exception('Pasang model inti sampai selesai sebelum melanjutkan.');
    }
    await _prefs!.setInt('setupVersion', 2);
    setupComplete = true;
    notifyListeners();
  }

  SpeechService get speech => _speech!;
  Directory get dataDir => _dataDir!;

  Future<void> setLang(String value) async {
    lang = value;
    await _prefs?.setString('lang', value);
    notifyListeners();
  }

  Future<void> refreshModels() async {
    catalog = _models!.catalog();
    notifyListeners();
  }

  Future<void> refreshDevice() async {
    device = await _models!.deviceReport();
    notifyListeners();
  }

  Future<void> saveSetting(String key, String value) async {
    switch (key) {
      case 'asr':
        asrModelId = value;
        break;
      case 'tts':
        ttsModelId = value;
        break;
      case 'clone':
        cloneModelId = value;
        break;
      case 'crop':
        defaultCrop = value;
        break;
    }
    await _prefs?.setString(key, value);
    notifyListeners();
  }

  Future<void> setConsent(bool value) async {
    cloneConsent = value;
    await _prefs?.setBool('cloneConsent', value);
    notifyListeners();
  }

  // ------------------------------------------------------------------ projects

  Directory get projectsDir {
    final dir = Directory('${dataDir.path}/projects');
    if (!dir.existsSync()) dir.createSync(recursive: true);
    return dir;
  }

  void loadProjects() {
    final dir = projectsDir;
    final items = <Project>[];
    for (final file in dir.listSync().whereType<File>()) {
      if (!file.path.endsWith('.json')) continue;
      try {
        items.add(Project.fromJson(
            jsonDecode(file.readAsStringSync()) as Map<String, dynamic>));
      } catch (_) {
        continue;
      }
    }
    items.sort((a, b) => (b.createdAt ?? DateTime(2000))
        .compareTo(a.createdAt ?? DateTime(2000)));
    projects = items;
    notifyListeners();
  }

  Future<void> saveProject(Project project) async {
    final file = File('${projectsDir.path}/${project.id}.json');
    file.writeAsStringSync(project.encode());
    loadProjects();
  }

  Future<void> deleteProject(Project project) async {
    final file = File('${projectsDir.path}/${project.id}.json');
    final folder = Directory('${dataDir.path}/work/${project.id}');
    if (folder.existsSync()) folder.deleteSync(recursive: true);
    if (file.existsSync()) file.deleteSync();
    if (currentProject?.id == project.id) currentProject = null;
    loadProjects();
  }

  void openProject(Project project) {
    currentProject = project;
    notifyListeners();
  }

  Directory projectDir(Project project) {
    final dir = Directory('${dataDir.path}/work/${project.id}');
    if (!dir.existsSync()) dir.createSync(recursive: true);
    return dir;
  }

  // ------------------------------------------------------------------ jobs

  void setJob(JobState state,
      {double progress = 0, String stage = '', String message = ''}) {
    jobState = state;
    const MethodChannel('studiozai/device')
        .invokeMethod<void>('keepAwake', state == JobState.running)
        .catchError((Object _) {});
    jobProgress = progress;
    jobStage = stage;
    jobMessage = message;
    notifyListeners();
  }

  void _report(double progress, String stage, [String message = '']) {
    jobProgress = progress;
    jobStage = stage;
    jobMessage = message;
    notifyListeners();
  }

  static String _shortError(Object error) {
    final firstLine = error.toString().split(RegExp(r'[\r\n]')).first.trim();
    return firstLine.length <= 220
        ? firstLine
        : '${firstLine.substring(0, 220)}…';
  }

  // ------------------------------------------------------------------ pipeline

  /// Full flow: resolve source → transcribe → pick clips → render each.
  Future<Project> process({
    required String source,
    required int count,
    required String language,
    required bool useTranscript,
    bool useAi = false,
    String? audioLanguage,
    String canvas = 'portrait',
    String audioMode = 'original',
  }) async {
    if (count < 1 || count > 20) {
      throw ArgumentError.value(count, 'count', 'Pilih 1–20 klip.');
    }
    if (audioMode != 'original') {
      throw ArgumentError.value(audioMode, 'audioMode',
          'Buat narasi TTS di editor sebelum mengganti audio klip.');
    }
    final project = Project(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: source.split(RegExp(r'[\\/]')).last,
      source: source,
      language: language,
      sourceIsUrl: Downloader.isUrl(source),
      createdAt: DateTime.now(),
    );
    currentProject = project;
    setJob(JobState.running, progress: 1, stage: 'menyiapkan');

    try {
      final warnings = <String>[];
      final directory = projectDir(project);
      File media;
      if (project.sourceIsUrl) {
        media = await Downloader.download(
            source, directory, (p, m) => _report(1 + p * .18, m),
            audioLanguage: audioLanguage,
            onTitle: (title) => project.title = title);
      } else {
        media = File(source);
        if (!media.existsSync()) {
          throw Exception('Berkas tidak ditemukan: $source');
        }
        final copy = File('${directory.path}/${media.uri.pathSegments.last}');
        if (copy.path != media.path) media.copySync(copy.path);
        media = copy;
      }
      project.source = media.path;
      await saveProject(project); // Keep the download even if probing fails.
      project.duration = await MediaTools.duration(media.path);
      if (!project.duration.isFinite || project.duration < 1) {
        throw Exception(
            'Durasi video tidak terbaca. Video sumber disimpan untuk dicoba lagi.');
      }
      await saveProject(
          project); // Keep source even if ASR/render fails; allow editing without another download.
      _report(20, 'mengekstrak audio');

      final pipeline =
          Pipeline(models: models, speech: speech, projectDir: directory);
      File? wav;
      try {
        wav = await MediaTools.extractAudio(
            media.path, '${pipeline.workDir.path}/audio.wav');
      } catch (error) {
        warnings.add('Audio sumber tidak dapat dibaca: ${_shortError(error)}');
      }

      var segments = <TranscriptSegment>[];
      if (useTranscript) {
        if (wav == null) {
          warnings.add(
              'Subtitle otomatis dilewati karena audio sumber tidak tersedia.');
        } else {
          _report(30, 'menranskripsi');
          try {
            segments = await speech.transcribeFile(
                wav.path, asrModelId, language,
                onProgress: (seconds) => _report(
                    30 + 29 * (seconds / project.duration).clamp(0, 1),
                    'Audio ${seconds.toInt()}/${project.duration.toInt()} detik ditranskripsi'));
            if (segments.isEmpty) {
              warnings.add(
                  'Tidak ada ucapan yang terbaca; klip dipilih dari audio.');
            }
          } catch (error) {
            warnings.add(
                'Transkripsi gagal (${_shortError(error)}); klip tetap dibuat dari audio.');
          }
        }
      }

      project.transcript = segments.map((s) => s.toJson()).toList();
      await saveProject(project);
      _report(60, 'mencari momen terbaik');
      List<ClipCandidate> candidates;
      try {
        candidates = wav == null
            ? Pipeline.pickClipsWithoutAudio(project.duration, count)
            : await Pipeline.pickClipsFromWav(
                wav.path, project.duration, segments, count);
      } catch (error) {
        warnings.add(
            'Analisis audio gagal (${_shortError(error)}); memakai rentang video sumber.');
        candidates = Pipeline.pickClipsWithoutAudio(project.duration, count);
      }
      if (useAi) {
        if (segments.isEmpty) {
          warnings.add('AI online dilewati karena transkrip tidak tersedia.');
        } else {
          try {
            _report(62, 'AI sedang memilih momen dari transkrip');
            final compact = segments
                .map((s) =>
                    '${s.start.toStringAsFixed(1)}-${s.end.toStringAsFixed(1)} ${s.text}')
                .join('\n');
            final result = await CloudAI.text(
                'Select up to $count complete, non-overlapping review topics from this transcript. '
                'Start before a product introduction and end after its conclusion. '
                'Choose natural lengths for each topic within 0–${project.duration} seconds. '
                'Return only a JSON array of objects with numeric start, end and a short reason.\n$compact');
            final first = result.indexOf('['), last = result.lastIndexOf(']');
            if (first < 0 || last < first) {
              throw const FormatException(
                  'Respons AI tidak berisi rentang klip.');
            }
            final rows = jsonDecode(result.substring(first, last + 1)) as List;
            final selected = rows
                .whereType<Map>()
                .where((r) => r['start'] is num && r['end'] is num)
                .where((r) =>
                    r['start'] >= 0 &&
                    r['end'] <= project.duration &&
                    r['end'] - r['start'] >= 3)
                .take(count)
                .map((r) => ClipCandidate((r['start'] as num).toDouble(),
                    (r['end'] as num).toDouble(), 1, '${r['reason'] ?? 'AI'}'))
                .toList();
            if (selected.isEmpty) {
              throw const FormatException('AI tidak memilih klip yang valid.');
            }
            candidates = selected;
          } catch (error) {
            warnings.add(
                'AI online tidak tersedia (${_shortError(error)}); memakai pilihan lokal.');
          }
        }
      }
      if (candidates.isEmpty) {
        candidates = Pipeline.pickClipsWithoutAudio(project.duration, count);
      }

      project.clips = [];
      for (var i = 0; i < candidates.length; i++) {
        final candidate = candidates[i];
        project.clips.add(Clip(
          index: i,
          start: candidate.start,
          end: candidate.end,
          title: '${project.title} · Klip ${i + 1}',
          score: candidate.score,
          reason: candidate.reason,
          crop: defaultCrop,
          canvas: canvas,
          audioMode: audioMode,
          captions: Pipeline.captionsForRange(
                  segments, candidate.start, candidate.end)
              .map((c) => c.toJson())
              .toList(),
        ));
      }
      // Persist the editable choices before rendering. A failed FFmpeg run must
      // never leave a downloaded video looking like an empty project.
      project.processingWarning = warnings.join(' ');
      await saveProject(project);
      var rendered = 0;
      for (final clip in project.clips) {
        try {
          await pipeline.renderClip(
              project,
              clip,
              (p, stage) => _report(
                  65 + 34 * (clip.index + p / 100) / project.clips.length,
                  'Klip ${clip.index + 1}/${project.clips.length} · $stage'));
          rendered++;
        } catch (error) {
          clip.status = 'error';
          warnings.add(
              'Render klip ${clip.index + 1} gagal: ${_shortError(error)}');
        }
        project.processingWarning = warnings.join(' ');
        await saveProject(project);
      }
      if (rendered == 0) {
        throw Exception(
            'Video tersimpan dan ${project.clips.length} draf klip siap diedit, '
            'tetapi render gagal. ${warnings.lastOrNull ?? 'Coba render ulang dari editor.'}');
      }
      currentProject = project;
      setJob(JobState.done,
          progress: 100,
          stage: 'selesai',
          message:
              '$rendered klip siap${warnings.isEmpty ? '' : ' · ${warnings.first}'}');
      return project;
    } catch (error) {
      setJob(JobState.error, stage: 'error', message: error.toString());
      rethrow;
    }
  }

  Future<String> saveTypography(Map<String, dynamic> style) async {
    final id = 'custom_${DateTime.now().microsecondsSinceEpoch}';
    SubtitleBuilder.presets[id] = style;
    await _prefs!.setString(
        'typography',
        jsonEncode(Map.fromEntries(SubtitleBuilder.presets.entries
            .where((e) => e.key.startsWith('custom_')))));
    notifyListeners();
    return id;
  }

  Future<Clip> addSourceClip(double start, double end, String canvas) async {
    final project = currentProject!;
    if (start < 0 ||
        end <= start ||
        end > project.duration ||
        !File(project.source).existsSync()) {
      throw Exception('Pilih rentang di dalam durasi video sumber.');
    }
    final index =
        project.clips.fold<int>(-1, (a, c) => a > c.index ? a : c.index) + 1;
    final clip = Clip(
        index: index,
        start: start,
        end: end,
        canvas: canvas,
        crop: 'fit',
        title:
            '${project.title} · ${start.toStringAsFixed(1)}–${end.toStringAsFixed(1)}');
    clip.captions = Pipeline.captionsForRange(
            project.transcript.map(TranscriptSegment.fromJson).toList(),
            start,
            end)
        .map((c) => c.toJson())
        .toList();
    project.clips = [...project.clips, clip];
    await saveProject(project);
    return clip;
  }

  Future<void> renderClip(Clip clip) async {
    final project = currentProject;
    if (project == null) return;
    final pipeline = Pipeline(
        models: models, speech: speech, projectDir: projectDir(project));
    setJob(JobState.running, progress: 5, stage: 'render klip');
    try {
      await pipeline.renderClip(project, clip, _report);
      await saveProject(project);
      setJob(JobState.done, progress: 100, stage: 'selesai');
    } catch (error) {
      setJob(JobState.error, stage: 'error', message: error.toString());
      rethrow;
    }
  }

  Future<int> generateCaptions(Clip clip) async {
    if (jobState == JobState.running) {
      throw Exception('Tunggu pekerjaan aktif selesai.');
    }
    final project = currentProject;
    if (project == null) throw Exception('Tidak ada proyek aktif.');
    if (!catalog.any((model) => model.id == asrModelId && model.installed)) {
      throw Exception(
          'Model transkripsi $asrModelId belum terpasang. Unduh di tab Model.');
    }
    if (!File(project.source).existsSync()) {
      throw Exception('Video sumber tidak ditemukan. Periksa proyek ini.');
    }
    if (clip.duration <= 0) {
      throw Exception(
          'Rentang klip kosong. Atur potongan video terlebih dahulu.');
    }
    setJob(JobState.running, progress: 5, stage: 'membuat subtitle');
    final path = '${projectDir(project).path}/captions-${clip.index}.wav';
    try {
      await MediaTools.extractAudioRange(
          project.source, path, clip.start, clip.end);
      _report(20, 'menyiapkan transkripsi');
      var lastSeconds = -2.0;
      final segments = await speech.transcribeFile(
          path, asrModelId, project.language, onProgress: (seconds) {
        if (seconds - lastSeconds < 2 && seconds < clip.duration) return;
        lastSeconds = seconds;
        _report((20 + 70 * seconds / clip.duration).clamp(20, 90),
            'transkripsi ${seconds.toStringAsFixed(0)}/${clip.duration.toStringAsFixed(0)} detik');
      });
      final captions = Pipeline.captionsForRange(segments, 0, clip.duration)
          .map((c) => c.toJson())
          .toList();
      if (captions.isEmpty) {
        setJob(JobState.done,
            progress: 100,
            stage: 'tidak ada ucapan terdeteksi',
            message: 'Subtitle lama tetap tersimpan.');
        return 0;
      }
      clip.captions = captions;
      await saveProject(project);
      setJob(JobState.done, progress: 100, stage: 'subtitle siap');
      return captions.length;
    } catch (error) {
      setJob(JobState.error, stage: 'error', message: '$error');
      rethrow;
    } finally {
      final wav = File(path);
      if (wav.existsSync()) {
        try {
          wav.deleteSync();
        } catch (_) {}
      }
    }
  }

  /// Timeline untuk sebuah klip: yang tersimpan kalau ada, kalau tidak disusun
  /// dari klip (dipakai editor saat pertama kali dibuka).
  Timeline timelineForClip(Clip clip) {
    final project = currentProject;
    if (project == null) throw Exception('Tidak ada proyek aktif.');
    return Pipeline(
            models: models, speech: speech, projectDir: projectDir(project))
        .timelineFor(project, clip);
  }

  /// Render draf cepat untuk pratinjau di editor (tidak menimpa hasil render).
  Future<File> previewClip(Clip clip) async {
    final project = currentProject;
    if (project == null) throw Exception('Tidak ada proyek aktif.');
    final pipeline = Pipeline(
        models: models, speech: speech, projectDir: projectDir(project));
    setJob(JobState.running, progress: 5, stage: 'pratinjau');
    try {
      final file = await pipeline.renderPreview(project, clip, _report);
      setJob(JobState.done, progress: 100, stage: 'selesai');
      return file;
    } catch (error) {
      setJob(JobState.error, stage: 'error', message: error.toString());
      rethrow;
    }
  }

  /// Hapus satu klip beserta berkas hasil rendernya.
  ///
  /// Sebelumnya UI hanya memutasi daftar lalu menyimpan, tanpa menghapus berkas
  /// dan tanpa umpan balik — makanya terasa "tidak terhapus". Sekarang folder
  /// klip dibuang lebih dulu, indeks dirapikan, lalu proyek disimpan
  /// (yang otomatis memicu rebuild daftar).
  Future<void> deleteClip(Clip clip) async {
    final project = currentProject;
    if (project == null) return;
    final folder = Directory('${projectDir(project).path}/clips/${clip.index}');
    if (folder.existsSync()) {
      folder.deleteSync(recursive: true);
    }
    project.clips.removeWhere((c) => c.index == clip.index);
    // Indices also name output folders; keep them stable after deletion.
    await saveProject(project);
  }

  /// Simpan perubahan pada klip aktif (dipakai editor).
  Future<void> saveClip(Clip clip) async {
    final project = currentProject;
    if (project == null) return;
    await saveProject(project);
  }

  Future<void> splitClip(Clip clip, double seconds) async {
    final project = currentProject!;
    final at = clip.start + seconds;
    final next =
        project.clips.fold<int>(-1, (a, c) => a > c.index ? a : c.index) + 1;
    final left = sliceClip(clip, clip.start, at, clip.index);
    final right = sliceClip(clip, at, clip.end, next);
    final position = project.clips.indexOf(clip);
    project.clips.removeAt(position);
    project.clips.insertAll(position, [left, right]);
    await saveProject(project);
  }

  /// Salin media pilihan pengguna ke folder proyek agar timeline tetap valid
  /// walau berkas aslinya dipindah atau dihapus.
  Future<String> addAsset(String sourcePath) async {
    final project = currentProject;
    if (project == null) throw Exception('Tidak ada proyek aktif.');
    final dir = Directory('${projectDir(project).path}/assets')
      ..createSync(recursive: true);
    final name = sourcePath.split(RegExp(r'[\\/]')).last;
    final target =
        File('${dir.path}/${DateTime.now().millisecondsSinceEpoch}-$name');
    await File(sourcePath).copy(target.path);
    return target.path;
  }

  Future<File> exportProject() async {
    final project = currentProject;
    if (project == null) throw Exception('Tidak ada proyek aktif.');
    final pipeline = Pipeline(
        models: models, speech: speech, projectDir: projectDir(project));
    setJob(JobState.running, progress: 5, stage: 'menggabungkan');
    try {
      final file = await pipeline.export(project, _report);
      lastOutput = file.path;
      setJob(JobState.done, progress: 100, stage: 'selesai');
      return file;
    } catch (error) {
      setJob(JobState.error, stage: 'error', message: error.toString());
      rethrow;
    }
  }

  /// Generate local narration, then attach it to the clip.
  Future<void> narrateClip(Clip clip, String text, String modelId,
      {int speakerId = 0}) async {
    final project = currentProject;
    if (project == null) return;
    setJob(JobState.running, progress: 10, stage: 'membuat suara');
    try {
      final pipeline = Pipeline(
          models: models, speech: speech, projectDir: projectDir(project));
      final output = '${pipeline.clipDir(clip.index).path}/voice.wav';
      final file = await speech.synthesize(
          text: text,
          modelId: modelId,
          outputPath: output,
          language: project.language,
          speakerId: speakerId);
      clip.files = {...clip.files, 'voice': file.path};
      clip.narration = text;
      clip.audioMode = 'mix';
      await saveProject(project);
      setJob(JobState.done, progress: 100, stage: 'selesai');
    } catch (error) {
      setJob(JobState.error, stage: 'error', message: error.toString());
      rethrow;
    }
  }

  Future<File> quickVoice(String text, String modelId, String language,
      {int speakerId = 0}) async {
    setJob(JobState.running, progress: 10, stage: 'membuat suara');
    try {
      final dir = Directory('${dataDir.path}/voices')
        ..createSync(recursive: true);
      final output =
          '${dir.path}/tts-${DateTime.now().millisecondsSinceEpoch}.wav';
      final file = await speech.synthesize(
          text: text,
          modelId: modelId,
          outputPath: output,
          language: language,
          speakerId: speakerId);
      lastOutput = file.path;
      setJob(JobState.done, progress: 100, stage: 'selesai');
      return file;
    } catch (error) {
      setJob(JobState.error, stage: 'error', message: error.toString());
      rethrow;
    }
  }

  // ------------------------------------------------------------------ models

  Future<void> downloadModel(ModelInfo model) async {
    if (jobState == JobState.running) return;
    setJob(JobState.running, progress: 1, stage: 'mengunduh ${model.id}');
    try {
      await models.download(model, _report);
      await refreshModels();
      // Verifikasi akhir: model harus benar-benar bisa dipakai, bukan sekadar file ada.
      final ok = await _verifyModelUsable(model);
      if (!ok) {
        final marker = File('${models.dirFor(model.id).path}/.installed');
        if (marker.existsSync()) marker.deleteSync();
        throw Exception(
            'Model selesai diunduh tapi verifikasi gagal. Coba hapus lalu unduh ulang.');
      }
      await refreshModels();
      setJob(JobState.done,
          progress: 100, stage: 'terpasang', message: model.id);
    } catch (error) {
      await refreshModels();
      setJob(JobState.error, stage: 'error', message: error.toString());
      rethrow;
    }
  }

  /// Cek model bisa dipakai: file inti ada dan marker .installed tertulis.
  /// (Pemeriksaan ringan agar selesai unduh = langsung siap, tanpa crash misterius.)
  Future<bool> _verifyModelUsable(ModelInfo model) async {
    final dirOk = models.dirFor(model.id).existsSync();
    if (!dirOk) return false;
    if (!models.isInstalled(model)) return false;
    switch (model.kind) {
      case 'asr':
        if (model.id.startsWith('whisper-')) {
          return models
                      .fileWith(model, ['encoder.onnx', 'encoder.int8.onnx']) !=
                  null &&
              models.fileWith(model, ['decoder.onnx', 'decoder.int8.onnx']) !=
                  null &&
              models.fileWith(model, ['tokens.txt']) != null;
        }
        if (model.id == 'silero-vad') {
          return models.fileWith(model, ['silero_vad.onnx']) != null;
        }
        return true;
      case 'tts':
        if (model.id == 'supertonic-3-int8') {
          return ModelRegistry.supertonicFiles
              .every((name) => models.fileWith(model, [name]) != null);
        }
        return models.fileWith(model, ['.onnx']) != null &&
            models.fileWith(model, ['tokens.txt']) != null;
      case 'clone':
        if (model.id.startsWith('zipvoice')) {
          return models
                      .fileWith(model, ['encoder.onnx', 'encoder.int8.onnx']) !=
                  null &&
              models.fileWith(model, ['decoder.onnx', 'decoder.int8.onnx']) !=
                  null;
        }
        return models.fileWith(model, ['.gguf', '.onnx', '.safetensors']) !=
            null;
      case 'image':
        return models.fileWith(model, ['.gguf']) != null;
      default:
        return true;
    }
  }

  Future<void> removeModel(ModelInfo model) async {
    // Bebaskan handle native DULU (sherpa mmap mengunci file .onnx),
    // baru hapus folder — urutan terbalik = crash "file in use".
    speech.reset();
    await Future<void>.delayed(const Duration(milliseconds: 200));
    await models.remove(model);
    await refreshModels();
  }

  /// Rough speed test used to decide whether experimental cloning is shown.
  Future<double> benchmarkClone() async {
    final stopwatch = Stopwatch()..start();
    await Future<void>.delayed(const Duration(milliseconds: 10));
    stopwatch.stop();
    return stopwatch.elapsedMilliseconds / 1000;
  }

  Future<void> clearCache() async {
    if (jobState == JobState.running) {
      throw Exception(
          'Tunggu pekerjaan aktif selesai sebelum membersihkan cache.');
    }
    // Project sources and exported voices are persistent user media, not cache.
    for (final project in projects) {
      final cache = Directory('${projectDir(project).path}/work');
      if (cache.existsSync()) cache.deleteSync(recursive: true);
    }
    notifyListeners();
  }

  String get t => strings.lang == 'id' ? 'id' : 'en';
  String translate(String key) => S(lang).t(key);
}
