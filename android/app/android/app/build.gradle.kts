plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.zwart04.studiozai"
    // Android 17 (API 37). The SDK ships it as platform "android-37.0",
    // so the minor version has to be stated explicitly for AGP 9.
    compileSdk = 37
    compileSdkMinor = 0

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "com.zwart04.studiozai"
        // Android 8.0+ keeps the app light while covering virtually every device.
        minSdk = 26
        targetSdk = 37
        versionCode = flutter.versionCode
        versionName = flutter.versionName
        // NOTE: do not add `ndk { abiFilters }` here - Flutter sets its own from
        // --split-per-abi / --target-platform, and Gradle rejects both at once.
    }

    packaging {
        // yt-dlp (bundled Python) and ffmpeg-kit need their native libraries extracted.
        jniLibs {
            useLegacyPackaging = true
        }
        resources {
            excludes += setOf(
                "META-INF/DEPENDENCIES",
                "META-INF/LICENSE",
                "META-INF/LICENSE.txt",
                "META-INF/NOTICE",
                "META-INF/NOTICE.txt",
                "META-INF/*.kotlin_module",
            )
        }
    }

    buildTypes {
        release {
            // Signed with the debug key so the APK installs straight from GitHub.
            // See docs/BUILD.md for creating your own release keystore.
            signingConfig = signingConfigs.getByName("debug")
            isMinifyEnabled = false
            isShrinkResources = false
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}

dependencies {
    implementation("com.google.mlkit:translate:17.0.3")
    implementation("com.google.mlkit:face-detection:16.1.7")
}
