package com.zwart04.studiozai

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import android.os.Environment
import android.os.StatFs
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File

/**
 * Adds a tiny device-info bridge used by the Model Manager to pick a model tier.
 * Channel: studiozai/device -> memoryInfo { totalRam, availRam, availDisk } in GB.
 */
class MainActivity : FlutterActivity() {
    private val channelName = "studiozai/device"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "memoryInfo" -> result.success(memoryInfo())
                    "freeDiskMb" -> result.success(freeDiskMb())
                    "keepAwake" -> {
                        if (call.arguments == true) window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                        else window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                        result.success(null)
                    }
                    else -> result.notImplemented()
                }
            }
    }

    /**
     * Ruang bebas (MB) di penyimpanan internal aplikasi.
     *
     * Dipakai Model Manager sebelum mengekstrak arsip besar. Sebelumnya sisi Dart
     * memakai FileStat.stat() pada sebuah folder — di Android itu selalu 0,
     * sehingga unduhan selalu ditolak dengan "tersedia 0 MB".
     */
    private fun freeDiskMb(): Double {
        val stat = StatFs(filesDir.absolutePath)
        return stat.availableBytes / (1024.0 * 1024.0)
    }

    private fun memoryInfo(): Map<String, Double> {
        val activityManager = getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memory = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memory)

        val dataDir = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            Environment.getDataDirectory()
        } else {
            File(filesDir.absolutePath)
        }
        val stat = StatFs(dataDir.path)

        val gib = 1024.0 * 1024.0 * 1024.0
        return mapOf(
            "totalRam" to memory.totalMem / gib,
            "availRam" to memory.availMem / gib,
            "availDisk" to stat.availableBytes / gib,
        )
    }
}
