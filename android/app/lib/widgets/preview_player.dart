import 'dart:io';

import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

import '../theme/tokens.dart';

/// Pemutar pratinjau untuk berkas hasil render.
///
/// Kalau pemutar gagal dibuat (codec tidak didukung perangkat), tampilkan pesan
/// + tombol bagikan supaya berkasnya tetap bisa dibuka di aplikasi lain.
class VideoPreview extends StatefulWidget {
  const VideoPreview({super.key, required this.path, this.onShare});

  final String path;
  final VoidCallback? onShare;

  @override
  State<VideoPreview> createState() => _VideoPreviewState();
}

class _VideoPreviewState extends State<VideoPreview> {
  VideoPlayerController? _controller;
  Object? _error;

  @override
  void initState() {
    super.initState();
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
      await controller.initialize();
      await controller.setLooping(true);
      await controller.play();
      if (!mounted) {
        await controller.dispose();
        return;
      }
      setState(() => _controller = controller);
    } catch (error) {
      if (mounted) setState(() => _error = error);
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    if (_error != null) return _fallback();
    if (controller == null) {
      return const SizedBox(height: 260, child: Center(child: CircularProgressIndicator()));
    }
    final ratio = controller.value.aspectRatio;
    return AspectRatio(
      aspectRatio: ratio <= 0 ? 9 / 16 : ratio,
      child: GestureDetector(
        onTap: () => setState(
          () => controller.value.isPlaying ? controller.pause() : controller.play(),
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            VideoPlayer(controller),
            ValueListenableBuilder<VideoPlayerValue>(
              valueListenable: controller,
              builder: (context, value, _) => AnimatedOpacity(
                opacity: value.isPlaying ? 0 : 1,
                duration: Tokens.motion,
                child: const DecoratedBox(
                  decoration: BoxDecoration(color: Color(0x66000000), shape: BoxShape.circle),
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
          const Icon(Icons.videocam_off_outlined, color: Tokens.textDim, size: 32),
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
