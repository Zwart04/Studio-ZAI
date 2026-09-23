import 'dart:async';
import 'dart:ffi';
import 'dart:io';
import 'dart:isolate';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:ffi/ffi.dart';

/// Generates an image on the phone with the CPU build of stable-diffusion.cpp.
/// The weights are downloaded separately; neither the prompt nor the image is
/// sent to a server. Only sendable values cross the isolate boundary.
class LocalImage {
  static const modelFileName = 'sdxs-512-tinySDdistilled_Q8_0.gguf';
  static const modelBytes = 682847200;

  static Future<File> generate(
      String prompt, Directory dataDir, File modelFile) async {
    final cleanPrompt = prompt.trim();
    if (cleanPrompt.isEmpty || cleanPrompt.length > 2000) {
      throw ArgumentError('Tulis deskripsi gambar (maksimum 2.000 karakter).');
    }
    if (!Platform.isAndroid) {
      throw UnsupportedError('Model gambar ini hanya tersedia di APK Android.');
    }
    if (!await modelFile.exists() || await modelFile.length() != modelBytes) {
      throw StateError(
          'Unduh model gambar SDXS-512 lebih dulu di halaman Model.');
    }

    final port = ReceivePort();
    Isolate? worker;
    try {
      worker = await Isolate.spawn<List<Object>>(_localImageWorker,
          <Object>[modelFile.path, cleanPrompt, port.sendPort]);
      final result = await port.first.timeout(const Duration(minutes: 8));
      if (result is! Map) {
        throw StateError('Mesin gambar lokal tidak mengirim hasil.');
      }
      if (result['error'] case final String message) {
        throw StateError('Gambar lokal gagal: $message');
      }
      final width = result['width'] as int;
      final height = result['height'] as int;
      final rgba =
          (result['rgba'] as TransferableTypedData).materialize().asUint8List();
      if (width != 512 || height != 512 || rgba.length != width * height * 4) {
        throw StateError('Hasil gambar lokal tidak valid.');
      }
      final codec = await _decodeRgba(rgba, width, height);
      final png = await codec.toByteData(format: ui.ImageByteFormat.png);
      codec.dispose();
      if (png == null) throw StateError('Tidak dapat menyimpan hasil PNG.');
      final folder = Directory('${dataDir.path}/images');
      await folder.create(recursive: true);
      final file = File(
          '${folder.path}/image-${DateTime.now().microsecondsSinceEpoch}.png');
      await file.writeAsBytes(png.buffer.asUint8List(), flush: true);
      return file;
    } on TimeoutException {
      throw TimeoutException(
          'Pembuatan gambar melebihi 8 menit. Coba perangkat dengan RAM lebih besar.');
    } finally {
      worker?.kill(priority: Isolate.immediate);
      port.close();
    }
  }
}

Future<ui.Image> _decodeRgba(Uint8List rgba, int width, int height) {
  final result = Completer<ui.Image>();
  ui.decodeImageFromPixels(
      rgba, width, height, ui.PixelFormat.rgba8888, result.complete);
  return result.future;
}

final class _SdImage extends Struct {
  @Uint32()
  external int width;
  @Uint32()
  external int height;
  @Uint32()
  external int channel;
  external Pointer<Uint8> data;
  external Pointer<Void> userdata;
}

typedef _CreateContextNative = Pointer<Void> Function(
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Bool,
    Bool,
    Bool,
    Int32,
    Int32,
    Int32,
    Int32,
    Bool,
    Bool,
    Bool,
    Bool);
typedef _CreateContextDart = Pointer<Void> Function(
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    bool,
    bool,
    bool,
    int,
    int,
    int,
    int,
    bool,
    bool,
    bool,
    bool);

typedef _Txt2ImgNative = Pointer<_SdImage> Function(
    Pointer<Void>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    Int32,
    Float,
    Float,
    Float,
    Int32,
    Int32,
    Int32,
    Int32,
    Int64,
    Int32,
    Pointer<_SdImage>,
    Float,
    Float,
    Bool,
    Pointer<Utf8>,
    Pointer<Int32>,
    IntPtr,
    Float,
    Float,
    Float);
typedef _Txt2ImgDart = Pointer<_SdImage> Function(
    Pointer<Void>,
    Pointer<Utf8>,
    Pointer<Utf8>,
    int,
    double,
    double,
    double,
    int,
    int,
    int,
    int,
    int,
    int,
    Pointer<_SdImage>,
    double,
    double,
    bool,
    Pointer<Utf8>,
    Pointer<Int32>,
    int,
    double,
    double,
    double);

/// This is a top-level entry point: sending a bound instance method would
/// transitively send Flutter's binding and fail with an unsendable object.
void _localImageWorker(List<Object> request) {
  final modelPath = request[0] as String;
  final prompt = request[1] as String;
  final reply = request[2] as SendPort;
  Pointer<Void>? context;
  Pointer<_SdImage>? images;
  void Function(Pointer<Void>)? freeContext;
  final model = modelPath.toNativeUtf8();
  final empty = ''.toNativeUtf8();
  final text = prompt.toNativeUtf8();
  try {
    final library = DynamicLibrary.open('libstable-diffusion.so');
    final create = library
        .lookupFunction<_CreateContextNative, _CreateContextDart>('new_sd_ctx');
    final generate =
        library.lookupFunction<_Txt2ImgNative, _Txt2ImgDart>('txt2img');
    freeContext = library.lookupFunction<Void Function(Pointer<Void>),
        void Function(Pointer<Void>)>('free_sd_ctx');

    // SDXS needs exactly one diffusion step at CFG 1. The Q8 model is already
    // quantized, so wtype=39 means no second quantization (matching this engine).
    context = create(
        model,
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
        true,
        true,
        false,
        Platform.numberOfProcessors.clamp(1, 4),
        39,
        0,
        0,
        true,
        false,
        true,
        true);
    if (context.address == 0) {
      throw StateError(
          'Model tidak dapat dimuat. Periksa RAM dan berkas model.');
    }
    images = generate(context, text, empty, 1, 1.0, 3.5, 0.0, 512, 512, 0, 1,
        -1, 1, nullptr, 0.9, 1.0, false, empty, nullptr, 0, 0.0, 0.0, 0.0);
    if (images.address == 0) {
      throw StateError('Mesin gambar tidak menghasilkan gambar.');
    }
    final first = images.ref;
    if (first.width != 512 ||
        first.height != 512 ||
        (first.channel != 3 && first.channel != 4) ||
        first.data.address == 0) {
      throw StateError('Format gambar dari model tidak valid.');
    }
    final rgb =
        first.data.asTypedList(first.width * first.height * first.channel);
    final rgba = Uint8List(first.width * first.height * 4);
    for (var i = 0; i < first.width * first.height; i++) {
      rgba[i * 4] = rgb[i * first.channel];
      rgba[i * 4 + 1] = rgb[i * first.channel + 1];
      rgba[i * 4 + 2] = rgb[i * first.channel + 2];
      rgba[i * 4 + 3] = first.channel == 4 ? rgb[i * 4 + 3] : 255;
    }
    reply.send(<String, Object>{
      'width': first.width,
      'height': first.height,
      'rgba': TransferableTypedData.fromList([rgba]),
    });
  } catch (error) {
    reply.send(<String, Object>{'error': error.toString()});
  } finally {
    if (images != null && images.address != 0) {
      if (images.ref.data.address != 0) calloc.free(images.ref.data);
      calloc.free(images);
    }
    if (context != null && context.address != 0) freeContext?.call(context);
    calloc.free(model);
    calloc.free(empty);
    calloc.free(text);
  }
}
