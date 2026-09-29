package com.zwart04.studiozai

import android.app.Activity
import android.graphics.Bitmap
import android.graphics.PointF
import android.media.FaceDetector
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
                    var previousY = 0.4
                    Thread {
                        val retriever = MediaMetadataRetriever()
                        try {
                            require(start.isFinite() && end.isFinite() && start >= 0 && end > start) { "Rentang tidak valid" }
                            retriever.setDataSource(path)
                            val keys = mutableListOf<Map<String, Double>>()
                            var t = 0.0
                            val step = max(0.75, (end - start) / 180)
                            while (t < end - start) {
                                val frame = retriever.getFrameAtTime(((start + t) * 1000000).toLong(), MediaMetadataRetriever.OPTION_CLOSEST)
                                if (frame != null) {
                                    val width = 480
                                    val height = max(2, (frame.height.toDouble() / frame.width * width).roundToInt())
                                    val scaled = Bitmap.createScaledBitmap(frame, width, height, true)
                                    val rgb = scaled.copy(Bitmap.Config.RGB_565, false)
                                    val faces = arrayOfNulls<FaceDetector.Face>(8)
                                    val count = FaceDetector(width, height, 8).findFaces(rgb, faces)
                                    val centers = (0 until count).mapNotNull { faces[it] }.filter { it.confidence() >= .3f }.map { face ->
                                        val point = PointF(); face.getMidPoint(point)
                                        Pair(point.x / width.toDouble(), point.y / height.toDouble())
                                    }
                                    val nearest = centers.minByOrNull { (it.first - previousX)*(it.first - previousX) + (it.second - previousY)*(it.second - previousY) }
                                    if (nearest != null) {
                                        previousX = if (keys.isEmpty()) nearest.first else previousX*.65+nearest.first*.35
                                        previousY = if (keys.isEmpty()) nearest.second else previousY*.65+nearest.second*.35
                                        keys.add(mapOf("time" to t, "x" to previousX, "y" to previousY))
                                    }
                                    rgb.recycle(); if (scaled !== frame) scaled.recycle(); frame.recycle()
                                }
                                t += step
                            }
                            require(keys.isNotEmpty()) { "Wajah tidak terdeteksi. Gunakan keyframe manual." }
                            activity.runOnUiThread { result.success(mapOf("x" to keys.first()["x"], "y" to keys.first()["y"], "zoom" to 1.0, "keyframes" to keys)) }
                        } catch (e: Exception) { activity.runOnUiThread { result.error("framing", e.message, null) } }
                        finally { retriever.release() }
                    }.start()
                }
                else -> result.notImplemented()
            }
        }
    }
}
