import 'package:flutter/material.dart';

import '../services/timeline.dart';
import '../theme/tokens.dart';

/// Timeline multi-track sederhana: satu baris per track, blok bisa digeser
/// (ubah waktu) dan ditarik tepinya (ubah durasi).
///
/// Skala waktu dipaskan ke lebar layar (tanpa zoom) — untuk klip pendek
/// (15-60 detik) ini paling mudah dipakai dengan satu tangan.
class TimelineView extends StatelessWidget {
  const TimelineView({
    super.key,
    required this.timeline,
    required this.selectedKind,
    required this.selectedId,
    required this.onSelect,
    required this.onChange,
    required this.onDelete,
  });

  final Timeline timeline;
  final String? selectedKind;
  final String? selectedId;
  final void Function(String kind, TimelineItem item) onSelect;
  final void Function(String kind, TimelineItem item) onChange;
  final void Function(String kind, TimelineItem item) onDelete;

  static const _kindOrder = ['video', 'media', 'text', 'audio'];

  static const _kindColor = <String, Color>{
    'video': Tokens.accent,
    'media': Tokens.purple,
    'text': Tokens.green,
    'audio': Tokens.orange,
  };

  @override
  Widget build(BuildContext context) {
    final duration = timeline.duration <= 0 ? 1.0 : timeline.duration;
    final tracks = <TimelineTrack>[
      for (final kind in _kindOrder)
        timeline.trackOf(kind) ?? TimelineTrack(id: kind, kind: kind),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Ruler(duration: duration),
        const SizedBox(height: 6),
        for (final track in tracks) ...[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 54,
                child: Padding(
                  padding: const EdgeInsets.only(top: 14),
                  child: Text(_kindLabel(track.kind),
                      style:
                          const TextStyle(fontSize: 11, color: Tokens.textDim)),
                ),
              ),
              Expanded(
                child: _TrackRow(
                  track: track,
                  duration: duration,
                  selectedId: selectedKind == track.kind ? selectedId : null,
                  color: _kindColor[track.kind] ?? Tokens.accent,
                  onSelect: (item) => onSelect(track.kind, item),
                  onChange: (item) => onChange(track.kind, item),
                  onDelete: (item) => onDelete(track.kind, item),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
        ],
      ],
    );
  }

  static String _kindLabel(String kind) {
    switch (kind) {
      case 'video':
        return 'Video';
      case 'media':
        return 'Media';
      case 'text':
        return 'Teks';
      default:
        return 'Audio';
    }
  }
}

class _Ruler extends StatelessWidget {
  const _Ruler({required this.duration});

  final double duration;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 54),
      child: Row(
        children: [
          Expanded(child: Container(height: 1, color: Tokens.separator)),
          const SizedBox(width: 6),
          Text('${duration.toStringAsFixed(1)}s',
              style: const TextStyle(fontSize: 10, color: Tokens.textDim2)),
        ],
      ),
    );
  }
}

class _TrackRow extends StatelessWidget {
  const _TrackRow({
    required this.track,
    required this.duration,
    required this.selectedId,
    required this.color,
    required this.onSelect,
    required this.onChange,
    required this.onDelete,
  });

  final TimelineTrack track;
  final double duration;
  final String? selectedId;
  final Color color;
  final void Function(TimelineItem item) onSelect;
  final void Function(TimelineItem item) onChange;
  final void Function(TimelineItem item) onDelete;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        return Container(
          height: 40,
          decoration: BoxDecoration(
            color: Tokens.surface2.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(Tokens.radiusSm),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(Tokens.radiusSm),
            child: Stack(
              children: [
                if (track.items.isEmpty)
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Padding(
                      padding: EdgeInsets.only(left: 10),
                      child: Text('—',
                          style:
                              TextStyle(color: Tokens.textDim2, fontSize: 11)),
                    ),
                  ),
                for (final item in track.items)
                  Positioned(
                    left: (item.start / duration * width).clamp(0.0, width),
                    width: ((item.end - item.start) / duration * width)
                        .clamp(28.0, width),
                    top: 4,
                    bottom: 4,
                    child: _TimelineBlock(
                      key: ValueKey('${track.kind}-${item.id}'),
                      item: item,
                      selected: item.id == selectedId,
                      color: color,
                      pixelsPerSecond: width / duration,
                      onSelect: () => onSelect(item),
                      onChange: onChange,
                      onDelete: () => onDelete(item),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _TimelineBlock extends StatefulWidget {
  const _TimelineBlock({
    super.key,
    required this.item,
    required this.selected,
    required this.color,
    required this.pixelsPerSecond,
    required this.onSelect,
    required this.onChange,
    required this.onDelete,
  });

  final TimelineItem item;
  final bool selected;
  final Color color;
  final double pixelsPerSecond;
  final VoidCallback onSelect;
  final void Function(TimelineItem item) onChange;
  final VoidCallback onDelete;

  @override
  State<_TimelineBlock> createState() => _TimelineBlockState();
}

class _TimelineBlockState extends State<_TimelineBlock> {
  /// Salinan item saat drag dimulai, supaya akumulasi delta tidak menumpuk.
  TimelineItem? _origin;

  void _begin() {
    _origin = widget.item.copy();
    widget.onSelect();
  }

  void _move(double deltaSeconds) {
    final origin = _origin;
    if (origin == null) return;
    final length = origin.end - origin.start;
    final start = (origin.start + deltaSeconds).clamp(0.0, 3600.0);
    widget.onChange(origin.copy()
      ..start = start
      ..end = start + length);
  }

  void _resize(double deltaSeconds, {required bool fromStart}) {
    final origin = _origin;
    if (origin == null) return;
    final updated = origin.copy();
    if (fromStart) {
      updated.start =
          (origin.start + deltaSeconds).clamp(0.0, origin.end - 0.3);
    } else {
      updated.end =
          (origin.end + deltaSeconds).clamp(origin.start + 0.3, 3600.0);
    }
    widget.onChange(updated);
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    final accent = widget.color;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () {
        widget.onSelect();
        _showActions(context);
      },
      onHorizontalDragStart: (_) => _begin(),
      onHorizontalDragUpdate: (details) =>
          _move((details.primaryDelta ?? 0) / widget.pixelsPerSecond),
      onHorizontalDragEnd: (_) => _origin = null,
      child: Stack(
        children: [
          Container(
            decoration: BoxDecoration(
              color: accent.withValues(alpha: widget.selected ? 0.42 : 0.22),
              borderRadius: BorderRadius.circular(Tokens.radiusSm - 2),
              border: Border.all(
                color: widget.selected ? accent : accent.withValues(alpha: 0.5),
                width: widget.selected ? 1.6 : 1,
              ),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 6),
            alignment: Alignment.centerLeft,
            child: Text(
              _label(item),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 11, color: Tokens.text),
            ),
          ),
          // Tepi kiri/kanan untuk mengubah durasi.
          Align(
            alignment: Alignment.centerLeft,
            child: _Handle(
              onDrag: (delta) =>
                  _resize(delta / widget.pixelsPerSecond, fromStart: true),
              onBegin: _begin,
            ),
          ),
          Align(
            alignment: Alignment.centerRight,
            child: _Handle(
              onDrag: (delta) =>
                  _resize(delta / widget.pixelsPerSecond, fromStart: false),
              onBegin: _begin,
            ),
          ),
        ],
      ),
    );
  }

  String _label(TimelineItem item) {
    if (item.text.isNotEmpty) return item.text;
    if (item.src.isEmpty) return '—';
    return item.src.split(RegExp(r'[\\/]')).last;
  }

  Future<void> _showActions(BuildContext context) async {
    final remove = await showModalBottomSheet<bool>(
      context: context,
      backgroundColor: Tokens.bgElevated,
      shape: const RoundedRectangleBorder(
        borderRadius:
            BorderRadius.vertical(top: Radius.circular(Tokens.radiusLg)),
      ),
      builder: (sheetContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.delete_outline_rounded,
                  color: Tokens.danger),
              title: const Text('Hapus item'),
              onTap: () => Navigator.of(sheetContext).pop(true),
            ),
            ListTile(
              leading: const Icon(Icons.close, color: Tokens.textDim),
              title: const Text('Tutup'),
              onTap: () => Navigator.of(sheetContext).pop(false),
            ),
          ],
        ),
      ),
    );
    if (remove == true) widget.onDelete();
  }
}

class _Handle extends StatelessWidget {
  const _Handle({required this.onDrag, required this.onBegin});

  final void Function(double delta) onDrag;
  final VoidCallback onBegin;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onHorizontalDragStart: (_) => onBegin(),
      onHorizontalDragUpdate: (details) => onDrag(details.primaryDelta ?? 0),
      child: Container(
        width: 14,
        color: Colors.transparent,
        alignment: Alignment.center,
        child: Container(
            width: 2, height: 16, color: Colors.white.withValues(alpha: 0.55)),
      ),
    );
  }
}
