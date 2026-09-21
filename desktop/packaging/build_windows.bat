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
python -m pip install --quiet -e "core[media,asr,tts,desktop]"
python -m pip install --quiet pyinstaller

echo [3/4] Membangun aplikasi...
pyinstaller desktop\packaging\studiozai.spec --noconfirm --distpath dist --workpath build

echo [4/4] Selesai.
echo   Aplikasi : dist\StudioZAI\StudioZAI.exe
echo   Catatan  : FFmpeg tidak dibundel. Pastikan ffmpeg ada di PATH komputer target.
echo              Model diunduh dari dalam aplikasi (halaman Model).
endlocal
