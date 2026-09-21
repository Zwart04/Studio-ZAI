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
    this.subtitlePreset = 'clean',
    this.audioMode = 'original',
    this.originalVolume = 0.25,
    this.voiceVolume = 1.0,
    this.captions = const [],
    this.files = const {},
    this.status = 'draft',
    this.narration = '',
  });

  int index;
  double start;
  double end;
  String title;
  double score;
  String reason;
  String crop;
  String subtitlePreset;
  String audioMode;
  double originalVolume;
  double voiceVolume;
  List<Map<String, dynamic>> captions;
  Map<String, String> files;
  String status;
  String narration;

  double get duration => (end - start).clamp(0, double.infinity);

  Map<String, dynamic> toJson() => {
        'index': index,
        'start': start,
        'end': end,
        'title': title,
        'score': score,
        'reason': reason,
        'crop': crop,
        'subtitlePreset': subtitlePreset,
        'audioMode': audioMode,
        'originalVolume': originalVolume,
        'voiceVolume': voiceVolume,
        'captions': captions,
        'files': files,
        'status': status,
        'narration': narration,
      };

  static Clip fromJson(Map<String, dynamic> json) => Clip(
        index: json['index'] as int,
        start: (json['start'] as num).toDouble(),
        end: (json['end'] as num).toDouble(),
        title: json['title'] as String? ?? '',
        score: (json['score'] as num?)?.toDouble() ?? 0,
        reason: json['reason'] as String? ?? '',
        crop: json['crop'] as String? ?? 'center',
        subtitlePreset: json['subtitlePreset'] as String? ?? 'clean',
        audioMode: json['audioMode'] as String? ?? 'original',
        originalVolume: (json['originalVolume'] as num?)?.toDouble() ?? 0.25,
        voiceVolume: (json['voiceVolume'] as num?)?.toDouble() ?? 1.0,
        captions: List<Map<String, dynamic>>.from(
            (json['captions'] as List? ?? const []).map((e) => Map<String, dynamic>.from(e as Map))),
        files: Map<String, String>.from(json['files'] as Map? ?? const {}),
        status: json['status'] as String? ?? 'draft',
        narration: json['narration'] as String? ?? '',
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
  });

  final String id;
  String title;
  String source;
  String language;
  double duration;
  bool sourceIsUrl;
  List<Clip> clips;
  DateTime? createdAt;

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'source': source,
        'language': language,
        'duration': duration,
        'sourceIsUrl': sourceIsUrl,
        'clips': clips.map((c) => c.toJson()).toList(),
        'createdAt': (createdAt ?? DateTime.now()).toIso8601String(),
      };

  static Project fromJson(Map<String, dynamic> json) => Project(
        id: json['id'] as String,
        title: json['title'] as String? ?? 'Proyek',
        source: json['source'] as String? ?? '',
        language: json['language'] as String? ?? 'id',
        duration: (json['duration'] as num?)?.toDouble() ?? 0,
        sourceIsUrl: json['sourceIsUrl'] as bool? ?? false,
        clips: (json['clips'] as List? ?? const []).map((e) => Clip.fromJson(Map<String, dynamic>.from(e as Map))).toList(),
        createdAt: DateTime.tryParse(json['createdAt'] as String? ?? ''),
      );

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
