#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Studio ZAI - Linux build (PyInstaller + AppImage bila linuxdeploy tersedia)
#  Hasil: dist/studio-zai.tar.gz  dan  dist/StudioZAI-x86_64.AppImage (opsional)
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "[1/5] Menyiapkan virtualenv..."
python3 -m venv .venv-build
# shellcheck disable=SC1091
source .venv-build/bin/activate

echo "[2/5] Memasang dependensi..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e "core[media,asr,tts,desktop]"
python -m pip install --quiet pyinstaller

echo "[3/5] Membangun aplikasi..."
pyinstaller desktop/packaging/studiozai.spec --noconfirm --distpath dist --workpath build

echo "[4/5] Membuat arsip tar.gz..."
tar -C dist -czf dist/studio-zai.tar.gz StudioZAI

echo "[5/5] AppImage (opsional)..."
if command -v linuxdeploy >/dev/null 2>&1; then
  rm -rf AppDir && mkdir -p AppDir/usr
  cp -r dist/StudioZAI/* AppDir/usr/
  cat > AppDir/studio-zai.desktop <<'EOF'
[Desktop Entry]
Name=Studio ZAI
Exec=StudioZAI
Icon=studiozai
Type=Application
Categories=AudioVideo;
EOF
  linuxdeploy --appdir AppDir --output appimage || echo "  (AppImage gagal dibuat - lanjut)"
else
  echo "  linuxdeploy tidak ditemukan, lewati AppImage."
fi

echo "Selesai. Artefak ada di folder dist/."
echo "Catatan: FFmpeg tidak dibundel - pastikan 'ffmpeg' tersedia di PATH."
