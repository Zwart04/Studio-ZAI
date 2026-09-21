# ---------------------------------------------------------------------------
#  Studio ZAI - mode dev desktop (venv + install + jalankan app)
#  Pakai: powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 [-Extras "clone"]
# ---------------------------------------------------------------------------
param(
  [string]$Extras = 'dev',
  [int]$Port = 8737
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location "$root\core"

if (-not (Test-Path '.venv')) {
  Write-Host "Membuat virtualenv..." -ForegroundColor Cyan
  python -m venv .venv
}

$python = ".\.venv\Scripts\python.exe"
Write-Host "Memasang dependensi (extras: $Extras)..." -ForegroundColor Cyan
& $python -m pip install --quiet --upgrade pip
& $python -m pip install --quiet -e ".[$Extras]"

Write-Host "Menjalankan Studio ZAI di http://127.0.0.1:$Port" -ForegroundColor Green
& $python -m studiozai serve --port $Port
