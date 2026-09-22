import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:studiozai/services/media_tools.dart';
import 'package:studiozai/services/pipeline.dart';
import 'package:studiozai/services/wav_chunks.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('Streaming PCM matches the original reader and clip selection', () async {
    final folder = Directory.systemTemp.createTempSync('studio-wav-');
    addTearDown(() => folder.deleteSync(recursive:true));
    final path = '${folder.path}/sample.wav';
    final input = Float32List.fromList(List.generate(16000*45, (i) => (i % 101)/101-.5));
    await MediaTools.writeWav(path,input,16000);
    final expected = MediaTools.readWavSamples(path);
    final actual = readWavChunks(path,sampleCount:8000).expand((chunk) => chunk).toList();
    expect(actual,orderedEquals(expected));
    final whole = Pipeline.pickClips(samples:expected,sampleRate:16000,duration:45,count:2);
    final bounded = await Pipeline.pickClipsFromWav(path,45,[],2);
    expect(bounded.map((c) => [c.start,c.end,c.score]).toList(),whole.map((c) => [c.start,c.end,c.score]).toList());
  });
  test('A 65 minute WAV stays bounded to one second per chunk', () async {
    final folder = Directory.systemTemp.createTempSync('studio-hour-');
    addTearDown(() => folder.deleteSync(recursive:true));
    final path = '${folder.path}/hour.wav';
    await MediaTools.writeWav(path,Float32List(0),16000);
    const seconds = 65*60, bytes = seconds*16000*2;
    final file = File(path).openSync(mode:FileMode.append);
    file.truncateSync(44+bytes);
    final field=ByteData(4)..setUint32(0,36+bytes,Endian.little);
    file.setPositionSync(4);file.writeFromSync(field.buffer.asUint8List());
    field.setUint32(0,bytes,Endian.little);
    file.setPositionSync(40);file.writeFromSync(field.buffer.asUint8List());file.closeSync();
    var count=0,total=0;
    for(final chunk in readWavChunks(path)) { expect(chunk.length,lessThanOrEqualTo(16000));count++;total+=chunk.length; }
    expect(count,seconds);expect(total,seconds*16000);
  });
  test('Truncated WAV is rejected', () async {
    final folder=Directory.systemTemp.createTempSync('studio-truncated-');
    addTearDown(() => folder.deleteSync(recursive:true));
    final path='${folder.path}/bad.wav';
    await MediaTools.writeWav(path,Float32List(100),16000);
    final f=File(path).openSync(mode:FileMode.append);f.truncateSync(50);f.closeSync();
    expect(() => readWavChunks(path).toList(),throwsFormatException);
  });
}
