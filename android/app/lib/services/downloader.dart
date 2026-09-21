import 'dart:io';

import 'package:youtubedl_android/youtubedl_android.dart';

/// Downloads YouTube / TikTok / Instagram media with a bundled yt-dlp.
class Downloader {
  static bool _ready = false;

  static Future<void> init() async {
    if (_ready) return;
    await YoutubeDL.init();
    _ready = true;
  }

  static bool isUrl(String value) =>
      value.startsWith('http://') || value.startsWith('https://');

  static Future<File> download(
    String url,
    Directory outDir,
    void Function(double, String) onProgress,
  ) async {
    await init();
    outDir.createSync(recursive: true);
    final template = '${outDir.path}/%(title).60s.%(ext)s';

    final response = await YoutubeDL.getInstance().execute(
      url: url,
      command: '-f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4 '
          '--no-playlist --restrict-filenames -o "$template"',
      onProgress: (progress, eta, line) {
        final fraction = double.tryParse(progress.replaceAll('%', '')) ?? 0;
        onProgress(fraction, 'mengunduh video');
      },
    );

    if (response.exitCode != 0) {
      throw Exception('Unduhan gagal. Pastikan link publik atau update yt-dlp. ${response.out ?? ''}');
    }
    final files = outDir
        .listSync()
        .whereType<File>()
        .where((f) => f.path.endsWith('.mp4') || f.path.endsWith('.mkv') || f.path.endsWith('.webm'))
        .toList()
      ..sort((a, b) => b.statSync().modified.compareTo(a.statSync().modified));
    if (files.isEmpty) throw Exception('Berkas hasil unduhan tidak ditemukan.');
    onProgress(100, 'selesai');
    return files.first;
  }
}
