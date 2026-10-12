import 'dart:io';
import 'dart:typed_data';

/// Bounded PCM16 mono reader. Audio analysis must not materialize hour-long WAVs.
Iterable<Float32List> readWavChunks(String path,
    {int sampleCount = 16000}) sync* {
  if (sampleCount <= 0) throw ArgumentError.value(sampleCount);
  final file = File(path).openSync();
  try {
    final header = file.readSync(12);
    if (header.length != 12 ||
        String.fromCharCodes(header.sublist(0, 4)) != 'RIFF' ||
        String.fromCharCodes(header.sublist(8)) != 'WAVE') {
      throw const FormatException('WAV tidak valid.');
    }
    var validPcm = false;
    while (file.positionSync() + 8 <= file.lengthSync()) {
      final chunk = file.readSync(8);
      final name = String.fromCharCodes(chunk.sublist(0, 4));
      final size = ByteData.sublistView(chunk).getUint32(4, Endian.little);
      final next = file.positionSync() + size + (size.isOdd ? 1 : 0);
      if (name == 'fmt ') {
        final fmt = file.readSync(size < 16 ? size : 16);
        if (fmt.length < 16) {
          throw const FormatException('Format WAV terpotong.');
        }
        final data = ByteData.sublistView(fmt);
        validPcm = data.getUint16(0, Endian.little) == 1 &&
            data.getUint16(2, Endian.little) == 1 &&
            data.getUint16(14, Endian.little) == 16;
      } else if (name == 'data') {
        if (!validPcm) {
          throw const FormatException('WAV harus PCM 16-bit mono.');
        }
        if (size.isOdd || file.positionSync() + size > file.lengthSync()) {
          throw const FormatException('Audio WAV terpotong.');
        }
        var left = size;
        while (left > 0) {
          final count = left < sampleCount * 2 ? left : sampleCount * 2;
          final bytes = file.readSync(count);
          if (bytes.length != count) {
            throw const FormatException('Audio WAV terpotong.');
          }
          final data = ByteData.sublistView(bytes);
          final samples = Float32List(count ~/ 2);
          for (var i = 0; i < samples.length; i++) {
            samples[i] = data.getInt16(i * 2, Endian.little) / 32768.0;
          }
          yield samples;
          left -= count;
        }
        return;
      }
      file.setPositionSync(next);
    }
    throw const FormatException('Data WAV tidak ditemukan.');
  } finally {
    file.closeSync();
  }
}
