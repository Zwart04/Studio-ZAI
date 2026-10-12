import 'dart:io';

import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

import '../theme/tokens.dart';
import 'live_video_subtitle.dart';

/// Pemutar pratinjau untuk berkas hasil render.
///
/// Kalau pemutar gagal dibuat (codec tidak didukung perangkat), tampilkan pesan
/// + tombol bagikan supaya berkasnya tetap bisa dibuka di aplikasi lain.
class VideoPreview extends StatefulWidget {
  const VideoPreview({
    super.key,
    required this.path,
    this.onShare,
    this.startSeconds = 0,
    this.endSeconds,
    this.targetAspectRatio,
    this.fit = BoxFit.contain,
    this.captions = const [],
    this.subtitlePosition = 'bottom',
  });

  final String path;
  final List<Map<String, dynamic>> captions;
  final String subtitlePosition;
  final double? targetAspectRatio;
  final BoxFit fit;
  final double startSeconds;
  final double? endSeconds;
  final VoidCallback? onShare;

  @override
  State<VideoPreview> createState() => _VideoPreviewState();
}

class _VideoPreviewState extends State<VideoPreview>
    with WidgetsBindingObserver {
  VideoPlayerController? _controller;
  Object? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _open();
  }

  Future<void> _open() async {
    final file = File(widget.path);
    if (!file.existsSync()) {
      setState(() => _error = 'Berkas belum ada.');
      return;
    }
    try {
      final controller = VideoPlayerController.file(file);
      _controller = controller;
      await controller.initialize();
      if (!mounted || _controller != controller) return;
      await controller.setLooping(false);
      await controller.seekTo(
        Duration(milliseconds: (widget.startSeconds * 1000).round()),
      );
      controller.addListener(() {
        final end = widget.endSeconds;
        if (end != null &&
            controller.value.isPlaying &&
            controller.value.position.inMilliseconds >= end * 1000) {
          controller.pause();
          controller.seekTo(
            Duration(milliseconds: (widget.startSeconds * 1000).round()),
          );
        }
      });
      if (!mounted || _controller != controller) return;
      setState(() => _controller = controller);
    } catch (error) {
      if (mounted) setState(() => _error = error);
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.pause();
    _controller?.dispose();
    _controller = null;
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant VideoPreview oldWidget) {
    super.didUpdateWidget(oldWidget);
    final controller = _controller;
    if (controller != null &&
        controller.value.isInitialized &&
        oldWidget.startSeconds != widget.startSeconds) {
      final seconds = controller.value.position.inMilliseconds / 1000;
      if (seconds < widget.startSeconds ||
          widget.endSeconds != null && seconds >= widget.endSeconds!) {
        controller.seekTo(
            Duration(milliseconds: (widget.startSeconds * 1000).round()));
      }
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) _controller?.pause();
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    if (_error != null) return _fallback();
    if (controller == null || !controller.value.isInitialized) {
      return const SizedBox(
        height: 260,
        child: Center(child: CircularProgressIndicator()),
      );
    }
    final ratio = controller.value.aspectRatio;
    return AspectRatio(
      aspectRatio: widget.targetAspectRatio ?? (ratio <= 0 ? 9 / 16 : ratio),
      child: GestureDetector(
        onTap: () => setState(() {
          if (controller.value.isPlaying) {
            controller.pause();
          } else {
            final end = widget.endSeconds ??
                controller.value.duration.inMilliseconds / 1000;
            if (controller.value.position.inMilliseconds >= end * 1000 - 50) {
              controller.seekTo(
                Duration(milliseconds: (widget.startSeconds * 1000).round()),
              );
            }
            controller.play();
          }
        }),
        child: Stack(
          alignment: Alignment.center,
          children: [
            Positioned.fill(
              child: ClipRect(
                child: FittedBox(
                  fit: widget.fit,
                  child: SizedBox(
                    width: controller.value.size.width,
                    height: controller.value.size.height,
                    child: VideoPlayer(controller),
                  ),
                ),
              ),
            ),
            Positioned.fill(
                child: LiveVideoSubtitle(
                    player: controller,
                    captions: widget.captions,
                    startSeconds: widget.startSeconds,
                    position: widget.subtitlePosition)),
            Positioned(
              left: 8,
              right: 8,
              bottom: 0,
              child: ValueListenableBuilder<VideoPlayerValue>(
                valueListenable: controller,
                builder: (context, value, _) {
                  final start = widget.startSeconds;
                  final end =
                      widget.endSeconds ?? value.duration.inMilliseconds / 1000;
                  final duration = (end - start).clamp(.01, double.infinity);
                  final position =
                      (value.position.inMilliseconds / 1000 - start).clamp(
                    0.0,
                    duration,
                  );
                  String time(double n) =>
                      '${n ~/ 60}:${(n.toInt() % 60).toString().padLeft(2, '0')}';
                  return Row(
                    children: [
                      Text(
                        '${time(position)} / ${time(duration)}',
                        style: const TextStyle(
                          fontSize: 10,
                          shadows: [Shadow(blurRadius: 3)],
                        ),
                      ),
                      Expanded(
                        child: Slider(
                          value: position,
                          max: duration,
                          onChanged: (v) => controller.seekTo(
                            Duration(
                              milliseconds: ((start + v) * 1000).round(),
                            ),
                          ),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
            ValueListenableBuilder<VideoPlayerValue>(
              valueListenable: controller,
              builder: (context, value, _) => AnimatedOpacity(
                opacity: value.isPlaying ? 0 : 1,
                duration: Tokens.motion,
                child: const DecoratedBox(
                  decoration: BoxDecoration(
                    color: Color(0x66000000),
                    shape: BoxShape.circle,
                  ),
                  child: Padding(
                    padding: EdgeInsets.all(12),
                    child: Icon(Icons.play_arrow_rounded, size: 34),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _fallback() {
    return Container(
      padding: const EdgeInsets.all(Tokens.space4),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.videocam_off_outlined,
            color: Tokens.textDim,
            size: 32,
          ),
          const SizedBox(height: Tokens.space2),
          const Text(
            'Pratinjau tidak bisa diputar di perangkat ini.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Tokens.textDim, fontSize: 13),
          ),
          if (widget.onShare != null) ...[
            const SizedBox(height: Tokens.space3),
            OutlinedButton.icon(
              onPressed: widget.onShare,
              icon: const Icon(Icons.ios_share_rounded, size: 18),
              label: const Text('Bagikan berkas'),
            ),
          ],
        ],
      ),
    );
  }
}
