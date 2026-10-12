import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:video_player/video_player.dart';
import 'live_subtitle.dart';

class LiveVideoSubtitle extends StatefulWidget {
  const LiveVideoSubtitle(
      {super.key,
      required this.player,
      required this.captions,
      this.startSeconds = 0,
      this.position = 'bottom'});
  final ValueListenable<VideoPlayerValue> player;
  final List<Map<String, dynamic>> captions;
  final double startSeconds;
  final String position;
  @override
  State<LiveVideoSubtitle> createState() => _LiveVideoSubtitleState();
}

class _LiveVideoSubtitleState extends State<LiveVideoSubtitle>
    with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  Duration _lastTick = Duration.zero, _anchor = Duration.zero;
  int _lastPaint = 0;
  double _sourcePosition = 0, _now = 0;
  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_tick);
    widget.player.addListener(_capture);
    _capture();
  }

  void _capture() {
    final value = widget.player.value;
    final animate = value.isPlaying &&
        !value.isBuffering &&
        widget.captions.isNotEmpty &&
        widget.position != 'off';
    final reported = value.position.inMilliseconds / 1000;
    if (!animate || !_ticker.isActive || reported != _sourcePosition) {
      _sourcePosition = reported;
      _now = reported;
      _anchor = _lastTick;
    }
    if (animate && !_ticker.isActive) {
      _lastTick = _anchor = Duration.zero;
      _lastPaint = 0;
      _ticker.start();
    } else if (!animate) {
      _ticker.stop();
    }
    if (mounted) setState(() {});
  }

  void _tick(Duration elapsed) {
    _lastTick = elapsed;
    if (elapsed.inMilliseconds - _lastPaint < 33) return;
    _lastPaint = elapsed.inMilliseconds;
    final duration = widget.player.value.duration.inMilliseconds / 1000;
    final predicted = _sourcePosition +
        (elapsed - _anchor).inMicroseconds /
            1000000 *
            widget.player.value.playbackSpeed;
    setState(() => _now = predicted.clamp(0.0, duration));
  }

  @override
  void didUpdateWidget(covariant LiveVideoSubtitle oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.player != widget.player) {
      oldWidget.player.removeListener(_capture);
      widget.player.addListener(_capture);
    }
    _capture();
  }

  @override
  void dispose() {
    widget.player.removeListener(_capture);
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => LiveSubtitle(
      captions: widget.captions,
      seconds: _now - widget.startSeconds,
      position: widget.position);
}
