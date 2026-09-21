import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../i18n/strings.dart';
import '../models.dart';
import '../services/downloader.dart';
import '../services/media_tools.dart';
import '../services/model_manager.dart';
import '../services/pipeline.dart';
import '../services/speech.dart';
import '../services/subtitle_builder.dart';

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
  String ttsModelId = 'piper-id_ID-news_tts-medium';
  String cloneModelId = 'zipvoice-zh-en';
  String defaultCrop = 'center';
  bool cloneConsent = false;

  List<ModelInfo> catalog = const [];
  DeviceReport? device;
  List<Project> projects = const [];
  Project? currentProject;

  JobState jobState = JobState.idle;
  double jobProgress = 0;
  String jobStage = '';
  String jobMessage = '';
  String? lastOutput;

  bool ytDlpReady = false;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    lang = _prefs!.getString('lang') ?? 'id';
    asrModelId = _prefs!.getString('asr') ?? asrModelId;
    ttsModelId = _prefs!.getString('tts') ?? ttsModelId;
    cloneModelId = _prefs!.getString('clone') ?? cloneModelId;
    defaultCrop = _prefs!.getString('crop') ?? defaultCrop;
    cloneConsent = _prefs!.getBool('cloneConsent') ?? false;

    final base = await getApplicationSupportDirectory();
    _dataDir = Directory('${base.path}/studiozai')..createSync(recursive: true);
    _models = await ModelManager.instance();
    _speech = SpeechService(_models!);
    await refreshModels();
    await refreshDevice();
    loadProjects();
    notifyListeners();
  }

  ModelManager get models => _models!;
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
        items.add(Project.fromJson(jsonDecode(file.readAsStringSync()) as Map<String, dynamic>));
      } catch (_) {
        continue;
      }
    }
    items.sort((a, b) => (b.createdAt ?? DateTime(2000)).compareTo(a.createdAt ?? DateTime(2000)));
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
    if (file.existsSync()) file.deleteSync();
    final folder = Directory('${dataDir.path}/work/${project.id}');
    if (folder.existsSync()) folder.deleteSync(recursive: true);
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

  void setJob(JobState state, {double progress = 0, String stage = '', String message = ''}) {
    jobState = state;
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

  // ------------------------------------------------------------------ pipeline

  /// Full flow: resolve source → transcribe → pick clips → render each.
  Future<Project> process({
    required String source,
    required int count,
    required String language,
    required bool useTranscript,
  }) async {
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
      final directory = projectDir(project);
      File media;
      if (project.sourceIsUrl) {
        media = await Downloader.download(source, directory, _report);
        ytDlpReady = true;
      } else {
        media = File(source);
        if (!media.existsSync()) throw Exception('Berkas tidak ditemukan: $source');
        final copy = File('${directory.path}/${media.uri.pathSegments.last}');
        if (copy.path != media.path) media.copySync(copy.path);
        media = copy;
      }
      project.source = media.path;
      project.duration = await MediaTools.duration(media.path);
      _report(20, 'mengekstrak audio');

      final pipeline = Pipeline(models: models, speech: speech, projectDir: directory);
      final wav = await MediaTools.extractAudio(media.path, '${pipeline.workDir.path}/audio.wav');

      var segments = <TranscriptSegment>[];
      if (useTranscript) {
        _report(30, 'menranskripsi');
        await speech.loadAsr(asrModelId);
        segments = await speech.transcribeWav(wav.path, language: language);
      }

      _report(60, 'mencari momen terbaik');
      final samples = MediaTools.readWavSamples(wav.path);
      final candidates = Pipeline.pickClips(
        samples: samples,
        sampleRate: 16000,
        duration: project.duration,
        segments: segments,
        count: count,
      );

      project.clips = [];
      for (var i = 0; i < candidates.length; i++) {
        final candidate = candidates[i];
        project.clips.add(Clip(
          index: i,
          start: candidate.start,
          end: candidate.end,
          title: 'Klip ${i + 1}',
          score: candidate.score,
          reason: candidate.reason,
          crop: defaultCrop,
          captions: Pipeline.captionsForRange(segments, candidate.start, candidate.end).map((c) => c.toJson()).toList(),
        ));
      }

      for (final clip in project.clips) {
        await pipeline.renderClip(project, clip, _report);
      }
      await saveProject(project);
      currentProject = project;
      setJob(JobState.done, progress: 100, stage: 'selesai', message: '${project.clips.length} klip siap');
      return project;
    } catch (error) {
      setJob(JobState.error, stage: 'error', message: error.toString());
      rethrow;
    }
  }

  Future<void> renderClip(Clip clip) async {
    final project = currentProject;
    if (project == null) return;
    final pipeline = Pipeline(models: models, speech: speech, projectDir: projectDir(project));
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

  Future<File> exportProject() async {
    final project = currentProject;
    if (project == null) throw Exception('Tidak ada proyek aktif.');
    final pipeline = Pipeline(models: models, speech: speech, projectDir: projectDir(project));
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

  /// Narration for a clip: generate with Piper, then attach to the clip.
  Future<void> narrateClip(Clip clip, String text, String modelId) async {
    final project = currentProject;
    if (project == null) return;
    setJob(JobState.running, progress: 10, stage: 'membuat suara');
    try {
      final pipeline = Pipeline(models: models, speech: speech, projectDir: projectDir(project));
      final output = '${pipeline.clipDir(clip.index).path}/voice.wav';
      final file = await speech.synthesize(text: text, modelId: modelId, outputPath: output);
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

  Future<File> quickVoice(String text, String modelId, String language) async {
    setJob(JobState.running, progress: 10, stage: 'membuat suara');
    try {
      final dir = Directory('${dataDir.path}/voices')..createSync(recursive: true);
      final output = '${dir.path}/tts-${DateTime.now().millisecondsSinceEpoch}.wav';
      final file = await speech.synthesize(text: text, modelId: modelId, outputPath: output);
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
    setJob(JobState.running, progress: 1, stage: 'mengunduh ${model.id}');
    try {
      await models.download(model, _report);
      await refreshModels();
      setJob(JobState.done, progress: 100, stage: 'terpasang', message: model.id);
    } catch (error) {
      setJob(JobState.error, stage: 'error', message: error.toString());
      rethrow;
    }
  }

  Future<void> removeModel(ModelInfo model) async {
    await models.remove(model);
    speech.reset();
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
    final cache = Directory('${dataDir.path}/work');
    if (cache.existsSync()) cache.deleteSync(recursive: true);
    final voices = Directory('${dataDir.path}/voices');
    if (voices.existsSync()) voices.deleteSync(recursive: true);
    notifyListeners();
  }

  String get t => strings.lang == 'id' ? 'id' : 'en';
  String translate(String key) => S(lang).t(key);
}
