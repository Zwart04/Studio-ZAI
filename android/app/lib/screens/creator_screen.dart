import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart' hide Caption;
import 'package:share_plus/share_plus.dart';
import '../models.dart';
import '../services/creator_tools.dart';
import '../services/subtitle_builder.dart';
import '../services/timeline.dart';

class CreatorScreen extends StatefulWidget {
  const CreatorScreen(
      {super.key,
      required this.clip,
      required this.timeline,
      required this.project,
      required this.directory});
  final Clip clip;
  final Timeline timeline;
  final Project project;
  final Directory directory;
  @override
  State<CreatorScreen> createState() => _CreatorScreenState();
}

class _CreatorScreenState extends State<CreatorScreen> {
  late List<Map<String, dynamic>> rows, original;
  late Map<String, dynamic> framing;
  late Map<String, List<Map<String, dynamic>>> variants;
  late String language;
  late TextEditingController title;
  late VideoPlayerController video;
  int cue = 0, word = -1, revision = 0;
  double time = 0;
  bool busy = false, ready = false;
  String message = '', source = 'id', target = 'en';
  TimelineItem get base => widget.timeline.trackOf('video')!.items.first;
  T clone<T>(Object value) => jsonDecode(jsonEncode(value)) as T;
  @override
  void initState() {
    super.initState();
    rows = (jsonDecode(jsonEncode(widget.clip.captions)) as List)
        .map((r) => Map<String, dynamic>.from(r))
        .toList();
    original = rows
        .map((r) => Map<String, dynamic>.from(jsonDecode(jsonEncode(r))))
        .toList();
    framing = Map<String, dynamic>.from(jsonDecode(jsonEncode(
        base.framing.isEmpty
            ? {'x': .5, 'y': .5, 'zoom': 1.0, 'keyframes': []}
            : base.framing)));
    title = TextEditingController(text: widget.clip.title);
    language = widget.clip.captionLanguage.isEmpty
        ? widget.project.language
        : widget.clip.captionLanguage;
    source = language;
    variants = (jsonDecode(jsonEncode(widget.clip.captionVariants)) as Map).map(
        (k, v) => MapEntry('$k',
            (v as List).map((r) => Map<String, dynamic>.from(r)).toList()));
    variants[language] = rows;
    video = VideoPlayerController.file(File(widget.project.source));
    video.initialize().then((_) async {
      await video.setVolume(0);
      await video
          .seekTo(Duration(milliseconds: (widget.clip.start * 1000).round()));
      if (mounted) setState(() => ready = true);
    }).catchError((Object e) {
      if (mounted) setState(() => message = '$e');
    });
  }

  @override
  void dispose() {
    video.dispose();
    title.dispose();
    super.dispose();
  }

  Map<String, dynamic>? get row => rows.isEmpty ? null : rows[cue];
  Map<String, dynamic>? get item =>
      row == null ? null : (word < 0 ? row : CreatorTools.words(row!)[word]);
  Map<String, dynamic> get style => {
        ...Map<String, dynamic>.from(row?['style'] as Map? ?? {}),
        ...Map<String, dynamic>.from(item?['style'] as Map? ?? {})
      };
  void setStyle(String name, dynamic value) {
    if (item == null) return;
    setState(() =>
        item!['style'] = {...(item!['style'] as Map? ?? {}), name: value});
  }

  Future<void> seek(double value) async {
    setState(() => time = value.clamp(0, widget.clip.duration));
    if (ready) {
      await video.seekTo(
          Duration(milliseconds: ((widget.clip.start + time) * 1000).round()));
    }
  }

  Widget number(String label, double value, ValueChanged<double> changed,
          {double min = 0, double max = 86400}) =>
      TextFormField(
          key: ValueKey('$label-$cue-$word-$revision'),
          initialValue: value.toStringAsFixed(2),
          decoration: InputDecoration(labelText: label),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          onChanged: (s) {
            final n = double.tryParse(s);
            if (n != null && n.isFinite) changed(n.clamp(min, max));
          });
  Future<void> run(Future<void> Function() action) async {
    setState(() => busy = true);
    try {
      await action();
    } catch (e) {
      if (mounted) setState(() => message = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => DefaultTabController(
      length: 2,
      child: Scaffold(
          appBar: AppBar(
              title: const Text('Creator tools'),
              bottom: const TabBar(tabs: [
                Tab(text: 'Caption per kata'),
                Tab(text: 'Crop & keyframe')
              ]),
              actions: [
                TextButton(
                    onPressed: busy
                        ? null
                        : () {
                            variants[language] = rows;
                            widget.clip.captionVariants = variants;
                            widget.clip.captionLanguage = language;
                            widget.clip.captions = rows;
                            widget.clip.title = title.text;
                            base.framing = framing;
                            if (framing['enabled'] == true) {
                              base.crop = 'manual';
                            }
                            Navigator.pop(context, true);
                          },
                    child: const Text('Simpan'))
              ]),
          body: Column(children: [
            if (busy) const LinearProgressIndicator(),
            if (message.isNotEmpty)
              Padding(padding: const EdgeInsets.all(12), child: Text(message)),
            Expanded(child: TabBarView(children: [captions(), crop()]))
          ])));
  Widget captions() {
    final selected = item, s = style;
    return ListView(padding: const EdgeInsets.all(16), children: [
      DropdownButtonFormField<String>(
          key: ValueKey('language-$language'),
          initialValue: language,
          decoration:
              const InputDecoration(labelText: 'Versi subtitle tersimpan'),
          items: variants.keys
              .map((l) => DropdownMenuItem(
                  value: l, child: Text(CreatorTools.languages[l] ?? l)))
              .toList(),
          onChanged: busy
              ? null
              : (v) => setState(() {
                    variants[language] = rows;
                    language = v!;
                    source = language;
                    rows = variants[language]!;
                    cue = 0;
                    word = -1;
                    revision++;
                  })),
      TextField(
          controller: title,
          decoration: const InputDecoration(labelText: 'Judul / hook klip')),
      const SizedBox(height: 16),
      const Text(
          'Pilih baris lalu kata. Timing kata tanpa timestamp dan hasil terjemahan diperkirakan; koreksi di sini.'),
      if (rows.isEmpty)
        const Padding(
            padding: EdgeInsets.all(24),
            child: Text('Buat subtitle otomatis di editor terlebih dahulu.')),
      if (rows.isNotEmpty) ...[
        DropdownButtonFormField<int>(
            key: ValueKey('cue-$revision'),
            initialValue: cue,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Baris caption'),
            items: List.generate(
                rows.length,
                (i) => DropdownMenuItem(
                    value: i,
                    child: Text('${i + 1}. ${rows[i]['text']}',
                        overflow: TextOverflow.ellipsis))),
            onChanged: (i) => setState(() {
                  cue = i!;
                  word = -1;
                })),
        const SizedBox(height: 12),
        Container(
            padding: const EdgeInsets.all(20),
            color: Colors.black,
            child: Text.rich(
                TextSpan(
                    children: CreatorTools.words(row!).map((w) {
                  final ws = {
                    ...(row!['style'] as Map? ?? {}),
                    ...(w['style'] as Map? ?? {})
                  };
                  return TextSpan(
                      text: '${w['word']} ',
                      style: TextStyle(
                          fontFamily: ws['font'] ?? 'Inter',
                          fontSize:
                              CreatorTools.value(ws['size'], 56, 14, 160) / 2,
                          fontWeight: ws['bold'] == true
                              ? FontWeight.bold
                              : FontWeight.normal,
                          color: color('${ws['color'] ?? '#ffffff'}')));
                }).toList()),
                textAlign: TextAlign.center)),
        Wrap(spacing: 6, children: [
          ChoiceChip(
              label: const Text('Seluruh baris'),
              selected: word < 0,
              onSelected: (_) => setState(() => word = -1)),
          ...CreatorTools.words(row!).asMap().entries.map((e) => ChoiceChip(
              label: Text('${e.value['word']}'),
              selected: word == e.key,
              onSelected: (_) => setState(() => word = e.key)))
        ]),
        TextFormField(
            key: ValueKey('text-$cue-$word-$revision'),
            initialValue: '${selected?[word < 0 ? 'text' : 'word'] ?? ''}',
            decoration: const InputDecoration(labelText: 'Teks'),
            onChanged: (v) {
              if (selected == null) return;
              selected[word < 0 ? 'text' : 'word'] = v;
              if (word < 0) {
                selected['words'] = <Map<String, dynamic>>[];
              } else {
                row!['text'] =
                    CreatorTools.words(row!).map((w) => w['word']).join(' ');
              }
            }),
        Row(children: [
          Expanded(
              child: number('Mulai', (selected!['start'] as num).toDouble(),
                  (v) => selected['start'] = v,
                  max: (selected['end'] as num).toDouble() - .01)),
          const SizedBox(width: 12),
          Expanded(
              child: number('Selesai', (selected['end'] as num).toDouble(),
                  (v) => selected['end'] = v,
                  min: (selected['start'] as num).toDouble() + .01,
                  max: widget.clip.duration))
        ]),
        DropdownButtonFormField<String>(
            key: ValueKey('font-$cue-$word-${s['font']}'),
            initialValue: s['font'] ?? 'Inter',
            decoration: const InputDecoration(labelText: 'Font'),
            items: CreatorTools.fonts
                .map((f) => DropdownMenuItem(value: f, child: Text(f)))
                .toList(),
            onChanged: (v) => setStyle('font', v)),
        number('Ukuran font', CreatorTools.value(s['size'], 56, 14, 160),
            (v) => setStyle('size', v),
            min: 14, max: 160),
        TextFormField(
            key: ValueKey('color-$cue-$word-$revision'),
            initialValue: s['color'] ?? '#ffffff',
            decoration: const InputDecoration(labelText: 'Warna #RRGGBB'),
            onChanged: (v) {
              if (RegExp(r'^#[0-9a-fA-F]{6}$').hasMatch(v)) {
                setStyle('color', v);
              }
            }),
        SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Tebal'),
            value: s['bold'] == true,
            onChanged: (v) => setStyle('bold', v)),
        DropdownButtonFormField<String>(
            key: ValueKey('anim-$cue-$word-${s['animation']}'),
            initialValue: s['animation'] ?? 'none',
            decoration: const InputDecoration(labelText: 'Animasi'),
            items: ['none', 'pop', 'fade', 'rise', 'zoom', 'type']
                .map((a) => DropdownMenuItem(value: a, child: Text(a)))
                .toList(),
            onChanged: (v) => setStyle('animation', v)),
        for (final axis in ['x', 'y'])
          number(
              'Posisi ${axis.toUpperCase()} (%)',
              CreatorTools.value((row!['style'] as Map?)?[axis],
                      axis == 'x' ? .5 : .82, .05, .95) *
                  100,
              (v) => setState(() => row!['style'] = {
                    ...(row!['style'] as Map? ?? {}),
                    axis: v / 100
                  }),
              min: 5,
              max: 95),
        OutlinedButton(
            onPressed: () {
              final selectedStyle = Map<String, dynamic>.from(style);
              setState(() {
                for (final r in rows) {
                  r['style'] = Map<String, dynamic>.from(selectedStyle);
                }
                word = -1;
                revision++;
              });
            },
            child: const Text('Terapkan gaya ke semua caption')),
      ],
      const Divider(height: 32),
      const Text('Terjemahan lokal',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      const Text(
          'Model diunduh saat pertama digunakan. Terjemahan selanjutnya berjalan di perangkat. Susunan kata baru memakai timing perkiraan.'),
      for (final isSource in [true, false])
        DropdownButtonFormField<String>(
            key: ValueKey('translate-$isSource-${isSource ? source : target}'),
            initialValue: isSource ? source : target,
            decoration: InputDecoration(labelText: isSource ? 'Dari' : 'Ke'),
            items: CreatorTools.languages.entries
                .map(
                    (e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
                .toList(),
            onChanged: (v) => setState(() {
                  if (isSource) {
                    source = v!;
                  } else {
                    target = v!;
                  }
                })),
      FilledButton(
          onPressed: busy || rows.isEmpty
              ? null
              : () => run(() async {
                    setState(() => message =
                        'Mengunduh model jika diperlukan, lalu menerjemahkan…');
                    final translated =
                        await CreatorTools.translate(rows, source, target);
                    if (mounted) {
                      setState(() {
                        variants[language] = rows;
                        language = target;
                        source = language;
                        rows = translated;
                        variants[language] = rows;
                        cue = 0;
                        word = -1;
                        revision++;
                        message =
                            'Terjemahan siap. Simpan untuk menerapkan ke video.';
                      });
                    }
                  }),
          child: const Text('Unduh model & terjemahkan')),
      TextButton(
          onPressed: busy
              ? null
              : () => setState(() {
                    language = widget.clip.captionLanguage.isEmpty
                        ? widget.project.language
                        : widget.clip.captionLanguage;
                    source = language;
                    rows = original
                        .map((r) => Map<String, dynamic>.from(
                            jsonDecode(jsonEncode(r))))
                        .toList();
                    cue = 0;
                    word = -1;
                    revision++;
                  }),
          child: const Text('Pulihkan caption awal')),
      OutlinedButton.icon(
          onPressed: rows.isEmpty
              ? null
              : () => run(() async {
                    final captions = rows.map(Caption.fromJson).toList();
                    final out = Directory(
                        '${widget.directory.path}/translations/${DateTime.now().millisecondsSinceEpoch}')
                      ..createSync(recursive: true);
                    final srt = File('${out.path}/$language.srt')
                      ..writeAsStringSync(SubtitleBuilder.toSrt(captions));
                    final vtt = File('${out.path}/$language.vtt')
                      ..writeAsStringSync(
                          'WEBVTT\n\n${SubtitleBuilder.toSrt(captions).replaceAllMapped(RegExp(r'(\d\d:\d\d:\d\d),(\d{3})'), (m) => '${m[1]}.${m[2]}')}');
                    await SharePlus.instance.share(
                        ShareParams(files: [XFile(srt.path), XFile(vtt.path)]));
                  }),
          icon: const Icon(Icons.download),
          label: const Text('Ekspor SRT + VTT tanpa render video')),
    ]);
  }

  Color color(String hex) =>
      Color(int.tryParse(hex.replaceFirst('#', 'ff'), radix: 16) ?? 0xffffffff);
  Widget crop() {
    final sw = ready ? video.value.size.width : 1920.0,
        sh = ready ? video.value.size.height : 1080.0,
        ratio = {
              'portrait': 9 / 16,
              'square': 1.0,
              'landscape': 16 / 9,
              'original': sw / sh
            }[base.canvas] ??
            9 / 16,
        zoom = CreatorTools.value(framing['zoom'], 1, 1, 4),
        w = math.min(sw, sh * ratio) / zoom / sw,
        h = math.min(sh, sw / ratio) / zoom / sh;
    final keys = (framing['keyframes'] as List? ?? []);
    return ListView(padding: const EdgeInsets.all(16), children: [
      const Text(
          'Seret kotak pada video sumber. Tambahkan keyframe untuk mengikuti subjek. Waktu relatif terhadap klip.'),
      const SizedBox(height: 12),
      AspectRatio(
          aspectRatio: sw / sh,
          child: LayoutBuilder(builder: (context, c) {
            void move(Offset p) => setState(() {
                  framing['x'] = (p.dx / c.maxWidth).clamp(0, 1);
                  framing['y'] = (p.dy / c.maxHeight).clamp(0, 1);
                  framing['enabled'] = true;
                });
            return GestureDetector(
                onPanUpdate: (d) => move(d.localPosition),
                onTapDown: (d) => move(d.localPosition),
                child: Stack(children: [
                  if (ready)
                    VideoPlayer(video)
                  else
                    const Center(child: CircularProgressIndicator()),
                  Positioned(
                      left: (CreatorTools.value(framing['x'], .5, 0, 1) - w / 2)
                              .clamp(0, 1 - w) *
                          c.maxWidth,
                      top: (CreatorTools.value(framing['y'], .5, 0, 1) - h / 2)
                              .clamp(0, 1 - h) *
                          c.maxHeight,
                      width: w * c.maxWidth,
                      height: h * c.maxHeight,
                      child: Container(
                          decoration: BoxDecoration(
                              border: Border.all(
                                  color: Colors.lightGreenAccent, width: 2),
                              color: Colors.lightGreenAccent
                                  .withValues(alpha: .12))))
                ]));
          })),
      Text(
          '${time.toStringAsFixed(1)} / ${widget.clip.duration.toStringAsFixed(1)} detik'),
      Slider(
          value: time,
          max: math.max(.1, widget.clip.duration),
          onChanged: seek),
      Text('Zoom ${zoom.toStringAsFixed(2)}×'),
      Slider(
          value: zoom,
          min: 1,
          max: 4,
          onChanged: (v) => setState(() {
                framing['zoom'] = v;
                framing['enabled'] = true;
              })),
      FilledButton(
          onPressed: () => setState(() {
                keys.removeWhere(
                    (k) => ((k['time'] as num) - time).abs() < .01);
                keys.add({
                  'time': time,
                  'x': framing['x'] ?? .5,
                  'y': framing['y'] ?? .5
                });
                keys.sort(
                    (a, b) => (a['time'] as num).compareTo(b['time'] as num));
                framing['keyframes'] = keys;
                framing['enabled'] = true;
              }),
          child: const Text('＋ Keyframe di waktu ini')),
      Wrap(
          spacing: 8,
          children: keys
              .map((k) => InputChip(
                  label: Text('${(k['time'] as num).toStringAsFixed(1)}s'),
                  onPressed: () {
                    setState(() {
                      framing['x'] = k['x'];
                      framing['y'] = k['y'];
                    });
                    seek((k['time'] as num).toDouble());
                  },
                  onDeleted: () => setState(() => keys.remove(k))))
              .toList()),
      OutlinedButton(
          onPressed: busy
              ? null
              : () => run(() async {
                    setState(() => message =
                        'Mengikuti wajah. Periksa keyframe ketika ada beberapa orang.');
                    final result = await CreatorTools.channel
                        .invokeMapMethod<String, dynamic>('trackFace', {
                      'path': widget.project.source,
                      'start': widget.clip.start,
                      'end': widget.clip.end,
                      'x': framing['x'] ?? .5
                    });
                    if (result == null) {
                      throw Exception('Pelacakan tidak menghasilkan keyframe');
                    }
                    if (mounted) {
                      setState(() {
                        framing = {...result, 'enabled': true, 'zoom': zoom};
                        message = 'Keyframe wajah siap ditinjau.';
                      });
                    }
                  }),
          child: const Text('Ikuti wajah otomatis')),
      TextButton(
          onPressed: () => setState(() => framing = {
                'x': .5,
                'y': .5,
                'zoom': 1.0,
                'keyframes': [],
                'enabled': true
              }),
          child: const Text('Reset ke tengah')),
      const Text(
          'Pelacakan mengikuti wajah terdekat dengan posisi awal, bukan identitas pembicara.'),
    ]);
  }
}
