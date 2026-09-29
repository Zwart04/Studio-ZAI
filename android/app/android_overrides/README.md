# Android overrides — cara pakai

Folder ini berisi berkas native Android yang **menimpa** hasil generate Flutter.

## Langkah build (sekali saja, dari `android/app/`)

```bash
# 1. Generate folder platform (Gradle, manifest default, dll.)
flutter create --platforms=android --org com.zwart04 --project-name studiozai .

# 2. Timpa dengan berkas milik Studio ZAI
cp -r android_overrides/. android/

# 3. Pasang dependensi & build
flutter pub get
flutter build apk --release --split-per-abi
```

Windows (PowerShell):

```powershell
flutter create --platforms=android --org com.zwart04 --project-name studiozai .
Copy-Item -Recurse -Force android_overrides\* android\
flutter pub get
flutter build apk --release --split-per-abi
```

## Isi folder

| Berkas | Fungsi |
|---|---|
| `app/src/main/kotlin/com/zwart04/studiozai/MainActivity.kt` | Menambahkan MethodChannel `studiozai/device` (RAM & disk bebas) yang dipakai Manajer Model untuk memilih tier |
| `app/src/main/AndroidManifest.xml` | Izin internet + baca media, nama aplikasi "Studio ZAI" |

> Jika `flutter create` memakai `android/` yang sudah ada, langkah 1 bisa dilewati — cukup pastikan `MainActivity.kt` dan `AndroidManifest.xml` sudah tergantikan, lalu `flutter clean && flutter pub get`.

Creator tools menggunakan `com.google.mlkit:translate:17.0.3` di `android/app/build.gradle.kts`. Jika membuat ulang Gradle, tambahkan `dependencies { implementation("com.google.mlkit:translate:17.0.3") }`. Salin juga `CreatorTools.kt`; model terjemahan diunduh saat pertama digunakan.
