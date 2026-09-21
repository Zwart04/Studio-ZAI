#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Studio ZAI - build APK Android (release, split per ABI)
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/app"

if ! command -v flutter >/dev/null 2>&1; then
  echo "Flutter tidak ditemukan di PATH. Instal Flutter SDK lalu jalankan 'flutter doctor'."
  exit 1
fi

if [ ! -d android/app/src/main/kotlin ]; then
  echo "[1/4] Membuat folder platform Android..."
  flutter create --platforms=android --org com.zwart04 --project-name studiozai .
  echo "[2/4] Menimpa berkas native Studio ZAI..."
  cp -r android_overrides/. android/
fi

echo "[3/4] Memasang dependensi..."
flutter pub get

echo "[4/4] Build APK release..."
flutter build apk --release --split-per-abi

echo
echo "Selesai. APK ada di: android/app/build/app/outputs/flutter-apk/"
ls -1 build/app/outputs/flutter-apk/*.apk || true
