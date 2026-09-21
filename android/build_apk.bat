@echo off
REM ---------------------------------------------------------------------------
REM  Studio ZAI - build APK Android (release, split per ABI)
REM ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0app"

where flutter >nul 2>nul
if errorlevel 1 (
  echo Flutter tidak ditemukan di PATH. Instal Flutter SDK lalu jalankan "flutter doctor".
  exit /b 1
)

if not exist "android\app\src\main\kotlin" (
  echo [1/4] Membuat folder platform Android...
  call flutter create --platforms=android --org com.zwart04 --project-name studiozai .
  if errorlevel 1 exit /b 1
  echo [2/4] Menimpa berkas native Studio ZAI...
  xcopy /E /I /Y "android_overrides\*" "android\" >nul
)

echo [3/4] Memasang dependensi...
call flutter pub get
if errorlevel 1 exit /b 1

echo [4/4] Build APK release...
call flutter build apk --release --split-per-abi
if errorlevel 1 exit /b 1

echo.
echo Selesai. APK ada di: android\app\build\app\outputs\flutter-apk\
dir /b build\app\outputs\flutter-apk\*.apk
endlocal
