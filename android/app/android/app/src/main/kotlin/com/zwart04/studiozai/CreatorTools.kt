package com.zwart04.studiozai

import android.app.Activity
import android.graphics.Bitmap
import com.google.android.gms.tasks.Tasks
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.face.FaceDetection
import com.google.mlkit.vision.face.FaceDetectorOptions
import java.util.concurrent.TimeUnit
import android.media.MediaMetadataRetriever
import com.google.mlkit.common.model.DownloadConditions
import com.google.mlkit.nl.translate.TranslateLanguage
import com.google.mlkit.nl.translate.Translation
import com.google.mlkit.nl.translate.TranslatorOptions
import io.flutter.plugin.common.BinaryMessenger
import io.flutter.plugin.common.MethodChannel
import kotlin.math.max
import kotlin.math.roundToInt

/** On-device translation and sampled face centers. No cloud inference. */
object CreatorTools {
    fun register(activity: Activity, messenger: BinaryMessenger) {
        MethodChannel(messenger, "studiozai/creator").setMethodCallHandler { call, result ->
            when (call.method) {
                "translate" -> {
                    val source = TranslateLanguage.fromLanguageTag(call.argument<String>("source") ?: "")
                    val target = TranslateLanguage.fromLanguageTag(call.argument<String>("target") ?: "")
                    val texts = call.argument<List<String>>("texts") ?: emptyList()
                    if (source == null || target == null) {
                        result.error("language", "Bahasa tidak didukung", null)
                        return@setMethodCallHandler
                    }
                    val translator = Translation.getClient(TranslatorOptions.Builder().setSourceLanguage(source).setTargetLanguage(target).build())
                    fun fail(e: Exception) { translator.close(); result.error("translation", e.message, null) }
                    translator.downloadModelIfNeeded(DownloadConditions.Builder().build())
                        .addOnFailureListener { fail(it) }
                        .addOnSuccessListener {
                            val output = mutableListOf<String>()
                            fun next(index: Int) {
                                if (index >= texts.size) { translator.close(); result.success(output); return }
                                translator.translate(texts[index]).addOnSuccessListener { output.add(it); next(index + 1) }.addOnFailureListener { fail(it) }
                            }
                            next(0)
                        }
                }
                "trackFace" -> {
                    val path = call.argument<String>("path") ?: ""
                    val start = call.argument<Number>("start")?.toDouble() ?: 0.0
                    val end = call.argument<Number>("end")?.toDouble() ?: 0.0
                    var previousX = call.argument<Number>("x")?.toDouble() ?: 0.5
                    var previousY = call.argument<Number>("y")?.toDouble() ?: 0.4
                    Thread {
                        val retriever = MediaMetadataRetriever()
                        val detector = FaceDetection.getClient(FaceDetectorOptions.Builder()
                            .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_ACCURATE)
                            .setMinFaceSize(.04f).enableTracking().build())
                        try {
                            require(start.isFinite() && end.isFinite() && start >= 0 && end > start) { "Rentang tidak valid" }
                            retriever.setDataSource(path)
                            val keys = mutableListOf<Map<String, Double>>()
                            var detectedFrames = 0
                            var trackedId: Int? = null
                            var t = 0.0
                            val step = max(0.75, (end - start) / 180)
                            while (t < end - start) {
                                val frame = retriever.getFrameAtTime(((start + t) * 1000000).toLong(), MediaMetadataRetriever.OPTION_CLOSEST)
                                if (frame != null) {
                                    val width = minOf(960, frame.width)
                                    val height = max(2, (frame.height.toDouble() / frame.width * width).roundToInt())
                                    val scaled = Bitmap.createScaledBitmap(frame, width, height, true)
                                    try {
                                        val faces = Tasks.await(detector.process(InputImage.fromBitmap(scaled, 0)), 30, TimeUnit.SECONDS)
                                        fun distance(face: com.google.mlkit.vision.face.Face): Double {
                                            val dx = face.boundingBox.exactCenterX() / width.toDouble() - previousX
                                            val dy = face.boundingBox.exactCenterY() / height.toDouble() - previousY
                                            return dx*dx + dy*dy
                                        }
                                        val nearest = faces.firstOrNull { trackedId != null && it.trackingId == trackedId }
                                            ?: faces.minByOrNull { distance(it) }
                                        if (nearest != null && distance(nearest) <= .25*.25) {
                                            val cx = nearest.boundingBox.exactCenterX() / width.toDouble()
                                            val cy = nearest.boundingBox.exactCenterY() / height.toDouble()
                                            previousX = if (detectedFrames == 0) cx else previousX*.65+cx*.35
                                            previousY = if (detectedFrames == 0) cy else previousY*.65+cy*.35
                                            trackedId = nearest.trackingId
                                            detectedFrames++
                                        }
                                        keys.add(mapOf("time" to t, "x" to previousX, "y" to previousY))
                                    } finally {
                                        if (scaled !== frame) scaled.recycle()
                                        frame.recycle()
                                    }
                                }
                                t += step
                            }
                            require(detectedFrames > 0) { "Wajah dekat titik crop tidak terdeteksi. Pilih titik wajah atau keyframe manual." }
                            activity.runOnUiThread { result.success(mapOf("x" to keys.first()["x"], "y" to keys.first()["y"], "zoom" to 1.0, "keyframes" to keys,
                                "detector" to "ML Kit", "detected_frames" to detectedFrames, "sampled_frames" to keys.size)) }
                        } catch (e: Exception) { activity.runOnUiThread { result.error("framing", e.message, null) } }
                        finally { detector.close(); retriever.release() }
                    }.start()
                }
                else -> result.notImplemented()
            }
        }
    }
}
