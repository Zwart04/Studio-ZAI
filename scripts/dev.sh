#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Studio ZAI - mode dev desktop (venv + install + jalankan app)
#  Pakai: ./scripts/dev.sh [extras] [port]
# ---------------------------------------------------------------------------
set -euo pipefail
EXTRAS="${1:-dev}"
PORT="${2:-8737}"
cd "$(dirname "$0")/.."

if [ ! -d .venv-build ]; then
  echo "Membuat virtualenv..."
  python3 -m venv .venv-build
fi

source .venv-build/bin/activate
echo "Memasang dependensi (extras: $EXTRAS)..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e "core[$EXTRAS]"

echo "Menjalankan Studio ZAI di http://127.0.0.1:$PORT"
python -m studiozai serve --port "$PORT"
