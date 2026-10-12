import 'dart:convert';

/// Data models shared across the Android app (mirrors core/studiozai/projects.py).
class ModelInfo {
  ModelInfo({
    required this.id,
    required this.kind,
    required this.langs,
    required this.sizeMb,
    required this.license,
    required this.note,
    required this.url,
    this.archive = true,
    this.tier = 0,
    this.experimental = false,
    this.installed = false,
    this.installedMb = 0,
    this.sha256,
    this.commercialUse = 'not_assessed',
    this.licenseUrl,
    this.licenseNote = '',
    this.recommended = true,
  });

  final String id;
  final String kind; // asr | tts | clone
  final List<String> langs;
  final int sizeMb;
  final String license;
  final String note;
  final String url;
  final bool archive;
  final int tier;
  final bool experimental;
  bool installed;
  double installedMb;
  final String? sha256;

  /// allowed | unverified | restricted | not_assessed.
  final String commercialUse;
  final String? licenseUrl;
  final String licenseNote;
  final bool recommended;

  Map<String, dynamic> toJson() => {
        'id': id,
        'kind': kind,
        'langs': langs,
        'sizeMb': sizeMb,
        'license': license,
        'note': note,
        'url': url,
        'archive': archive,
        'tier': tier,
        'experimental': experimental,
        if (sha256 != null) 'sha256': sha256,
        'commercialUse': commercialUse,
        if (licenseUrl != null) 'licenseUrl': licenseUrl,
        'licenseNote': licenseNote,
        'recommended': recommended,
      };

  static ModelInfo fromJson(Map<String, dynamic> json) => ModelInfo(
        id: json['id'] as String,
        kind: json['kind'] as String,
        langs: List<String>.from(json['langs'] as List? ?? const []),
        sizeMb: json['sizeMb'] as int? ?? 0,
        license: json['license'] as String? ?? '',
        note: json['note'] as String? ?? '',
        url: json['url'] as String? ?? '',
        archive: json['archive'] as bool? ?? true,
        tier: json['tier'] as int? ?? 0,
        experimental: json['experimental'] as bool? ?? false,
        sha256: json['sha256'] as String?,
        commercialUse: json['commercialUse'] as String? ?? 'not_assessed',
        licenseUrl: json['licenseUrl'] as String?,
        licenseNote: json['licenseNote'] as String? ?? '',
        recommended: json['recommended'] as bool? ?? true,
      );
}

class Clip {
  Clip({
    required this.index,
    required this.start,
    required this.end,
    this.title = '',
    this.score = 0,
    this.reason = '',
    this.crop = 'center',
    this.canvas = 'portrait',
    this.subtitlePreset = 'clean',
    this.subtitlePosition = 'bottom',
    this.audioMode = 'original',
    this.originalVolume = 0.25,
    this.voiceVolume = 1.0,
    this.captions = const [],
    this.captionVariants = const {},
    this.captionLanguage = '',
    this.files = const {},
    this.status = 'draft',
    this.narration = '',
    this.timeline,
  });

  int index;
  double start;
  double end;
  String title;
  double score;
  String reason;
  String crop;
  String canvas;
  String subtitlePreset;
  String subtitlePosition;
  String audioMode;
  double originalVolume;
  double voiceVolume;
  List<Map<String, dynamic>> captions;
  Map<String, List<Map<String, dynamic>>> captionVariants;
  String captionLanguage;
  Map<String, String> files;
  String status;
  String narration;

  /// Editor timeline multi-track (Video / Media / Teks / Audio).
  /// Null = proyek lama, dirender dengan jalur lama (tanpa timeline).
  Map<String, dynamic>? timeline;

  double get duration => (end - start).clamp(0, double.infinity);

  Map<String, dynamic> toJson() => {
        'index': index,
        'start': start,
        'end': end,
        'title': title,
        'score': score,
        'reason': reason,
        'crop': crop,
        'canvas': canvas,
        'subtitlePreset': subtitlePreset,
        'subtitlePosition': subtitlePosition,
        'audioMode': audioMode,
        'originalVolume': originalVolume,
        'voiceVolume': voiceVolume,
        'captions': captions,
        'captionVariants': captionVariants,
        'captionLanguage': captionLanguage,
        'files': files,
        'status': status,
        'narration': narration,
        if (timeline != null) 'timeline': timeline,
      };

  static Clip fromJson(Map<String, dynamic> json) => Clip(
        index: json['index'] as int,
        start: (json['start'] as num).toDouble(),
        end: (json['end'] as num).toDouble(),
        title: json['title'] as String? ?? '',
        score: (json['score'] as num?)?.toDouble() ?? 0,
        reason: json['reason'] as String? ?? '',
        crop: json['crop'] as String? ?? 'center',
        canvas: json['canvas'] as String? ?? 'portrait',
        subtitlePreset: json['subtitlePreset'] as String? ?? 'clean',
        subtitlePosition: json['subtitlePosition'] as String? ?? 'bottom',
        audioMode: json['audioMode'] as String? ?? 'original',
        originalVolume: (json['originalVolume'] as num?)?.toDouble() ?? 0.25,
        voiceVolume: (json['voiceVolume'] as num?)?.toDouble() ?? 1.0,
        captions: List<Map<String, dynamic>>.from(
            (json['captions'] as List? ?? const [])
                .map((e) => Map<String, dynamic>.from(e as Map))),
        captionVariants: (json['captionVariants'] as Map? ?? {}).map((k, v) =>
            MapEntry('$k',
                (v as List).map((r) => Map<String, dynamic>.from(r)).toList())),
        captionLanguage: json['captionLanguage'] as String? ?? '',
        files: Map<String, String>.from(json['files'] as Map? ?? const {}),
        status: json['status'] as String? ?? 'draft',
        narration: json['narration'] as String? ?? '',
        timeline: json['timeline'] == null
            ? null
            : Map<String, dynamic>.from(json['timeline'] as Map),
      );
}

class Project {
  Project({
    required this.id,
    required this.title,
    required this.source,
    this.language = 'id',
    this.duration = 0,
    this.sourceIsUrl = false,
    this.clips = const [],
    this.createdAt,
    this.transcript = const [],
    this.processingWarning = '',
    this.online = false,
    this.sourceUrl = '',
    this.audioPath = '',
    this.segments = const {},
    this.processingMode = 'legacy',
    this.audioLanguage = '',
    this.execution = const {},
  });

  final String id;
  String title;
  String source;
  String language;
  double duration;
  bool sourceIsUrl;
  List<Clip> clips;
  DateTime? createdAt;
  List<Map<String, dynamic>> transcript;
  String processingWarning;
  String processingMode;
  String audioLanguage;
  Map<String, dynamic> execution;

  /// Mode online: audio diunduh dulu; video klip hanya diunduh saat render.
  bool online;

  /// Tautan asli (YouTube) bila [online] aktif dan video belum diunduh penuh.
  String sourceUrl;

  /// Berkas audio lokal yang diunduh untuk transkrip.
  String audioPath;

  /// Cache segmen video per clip, dipakai saat render di mode online.
  /// Nilainya peta {"path": String, "start": double, "end": double}.
  Map<String, dynamic> segments;

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'source': source,
        'language': language,
        'duration': duration,
        'sourceIsUrl': sourceIsUrl,
        'transcript': transcript,
        'processingWarning': processingWarning,
        'processingMode': processingMode,
        'audioLanguage': audioLanguage,
        'execution': execution,
        'clips': clips.map((c) => c.toJson()).toList(),
        'createdAt': (createdAt ?? DateTime.now()).toIso8601String(),
        'online': online,
        'sourceUrl': sourceUrl,
        'audioPath': audioPath,
        'segments': segments,
      };

  static Project fromJson(Map<String, dynamic> json) => Project(
        id: json['id'] as String,
        title: json['title'] as String? ?? 'Proyek',
        source: json['source'] as String? ?? '',
        language: json['language'] as String? ?? 'id',
        duration: (json['duration'] as num?)?.toDouble() ?? 0,
        sourceIsUrl: json['sourceIsUrl'] as bool? ?? false,
        transcript: List<Map<String, dynamic>>.from(
            (json['transcript'] as List? ?? [])
                .map((e) => Map<String, dynamic>.from(e as Map))),
        processingWarning: json['processingWarning'] as String? ?? '',
        processingMode: json['processingMode'] as String? ?? 'legacy',
        audioLanguage: json['audioLanguage'] as String? ?? '',
        execution: Map<String, dynamic>.from(json['execution'] as Map? ?? {}),
        clips: (json['clips'] as List? ?? const [])
            .map((e) => Clip.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
        createdAt: DateTime.tryParse(json['createdAt'] as String? ?? ''),
        online: json['online'] as bool? ?? false,
        sourceUrl: json['sourceUrl'] as String? ?? '',
        audioPath: json['audioPath'] as String? ?? '',
        segments: Map<String, dynamic>.from(json['segments'] as Map? ?? {}),
      );

  /// Cache segmen video untuk [index]. Mengembalikan peta
  /// {"path", "start", "end"} atau null bila belum ada.
  Map<String, dynamic>? segmentFor(int index) {
    final entry = segments['$index'];
    if (entry is! Map) return null;
    return Map<String, dynamic>.from(entry);
  }

  /// Simpan/memperbarui cache segmen untuk [index].
  void storeSegment(int index, String path, double start, double end) {
    segments = Map<String, dynamic>.from(segments)
      ..['$index'] = {'path': path, 'start': start, 'end': end};
  }

  void clearSegment(int index) {
    segments = Map<String, dynamic>.from(segments)..remove('$index');
  }

  String encode() => jsonEncode(toJson());
}

class DeviceReport {
  DeviceReport({
    required this.model,
    required this.androidVersion,
    required this.ramGb,
    required this.diskFreeGb,
    required this.abis,
  });

  final String model;
  final String androidVersion;
  final double ramGb;
  final double diskFreeGb;
  final List<String> abis;

  List<String> recommendations() {
    final notes = <String>[];
    if (ramGb < 6) {
      notes.add('RAM < 6GB -> Whisper tiny, tanpa kloning');
    } else {
      notes.add('RAM >= 6GB -> Whisper base + ZipVoice (EN)');
    }
    if (diskFreeGb < 3) {
      notes.add('Ruang kosong < 3GB -> hapus model yang tidak dipakai');
    }
    return notes;
  }
}
