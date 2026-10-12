@echo off
REM ---------------------------------------------------------------------------
REM  Studio ZAI - Windows build (PyInstaller one-folder)
REM  Hasil: dist\StudioZAI\StudioZAI.exe
REM ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0\..\.."

echo [1/4] Menyiapkan virtualenv...
if not exist ".venv-build" python -m venv .venv-build
call ".venv-build\Scripts\activate.bat"

echo [2/4] Memasang dependensi...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e "core[media,asr,tts,desktop,face,translation]"
if errorlevel 1 exit /b 1
python -m pip install --quiet pyinstaller
if errorlevel 1 exit /b 1

echo [3/4] Mendeteksi ffmpeg untuk dibundel...
set "STUDIOZAI_FFMPEG_DIR="
for /f "delims=" %%i in ('where ffmpeg 2^>nul') do if not defined FFMPEG_EXE set "FFMPEG_EXE=%%i"
if defined FFMPEG_EXE for %%i in ("%FFMPEG_EXE%") do set "STUDIOZAI_FFMPEG_DIR=%%~dpi"
if defined STUDIOZAI_FFMPEG_DIR (
  echo   ffmpeg dibundel dari: %STUDIOZAI_FFMPEG_DIR%
) else (
  echo   PERINGATAN: ffmpeg tidak ada di PATH - aplikasi akan mencari ffmpeg di PATH target.
)

echo [4/4] Membangun aplikasi...
python tools\fetch_llama_runtime.py
if errorlevel 1 exit /b 1
python tools\fetch_js_runtime.py
if errorlevel 1 exit /b 1
python tools\collect_runtime_notices.py
if errorlevel 1 exit /b 1
pyinstaller desktop\packaging\studiozai.spec --noconfirm --distpath dist --workpath build
if errorlevel 1 exit /b 1

echo Selesai.
echo   Aplikasi : dist\StudioZAI\StudioZAI.exe
echo   Arsip    : jalankan  python tools\zip_exe.py  untuk membuat ZIP rilis
echo   Model    : diunduh dari dalam aplikasi (halaman Model)
endlocal
