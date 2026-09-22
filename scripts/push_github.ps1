# ---------------------------------------------------------------------------
#  Studio ZAI - inisialisasi git + push ke repo PRIVATE Zwart04/Studio-ZAI
#  Pakai: powershell -ExecutionPolicy Bypass -File scripts\push_github.ps1
# ---------------------------------------------------------------------------
$ErrorActionPreference = 'Stop'
$repo = 'Zwart04/Studio-ZAI'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

Write-Host "== Studio ZAI -> https://github.com/$repo (private)" -ForegroundColor Cyan

# 1. GitHub CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Host "GitHub CLI tidak ditemukan. Menginstal via winget..." -ForegroundColor Yellow
  winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
  $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User')
}

# 2. Pastikan akun Zwart04 yang aktif
$status = (gh auth status 2>&1 | Out-String)
if ($status -notmatch 'Zwart04') {
  Write-Host "Akun Zwart04 belum terdaftar di gh. Menjalankan 'gh auth login'..." -ForegroundColor Yellow
  gh auth login
} else {
  gh auth switch --user Zwart04 | Out-Null
  Write-Host "Akun aktif: Zwart04" -ForegroundColor Green
}

# 3. Repo git lokal
if (-not (Test-Path '.git')) {
  Write-Host "Menyiapkan repository git lokal..."
  git init | Out-Null
}
git add -A
$pending = (git status --porcelain | Out-String).Trim()
if ($pending) {
  git commit -m "chore: sinkronisasi kode Studio ZAI" | Out-Null
  Write-Host "Commit dibuat." -ForegroundColor Green
} else {
  Write-Host "Tidak ada perubahan untuk di-commit." -ForegroundColor DarkGray
}

# 4. Buat repo private (atau pakai yang sudah ada) lalu push
$exists = $false
try {
  gh repo view $repo --json name | Out-Null
  $exists = $true
} catch {
  $exists = $false
}

if ($exists) {
  Write-Host "Repo sudah ada. Push ke branch saat ini..."
  $remote = (git remote 2>$null) -join ','
  if ($remote -notmatch 'origin') {
    git remote add origin "https://github.com/$repo.git"
  } else {
    git remote set-url origin "https://github.com/$repo.git"
  }
  git branch -M main
  git push -u origin main
} else {
  Write-Host "Membuat repo private $repo..."
  gh repo create $repo --private --source . --remote origin --push --description "Studio ZAI - auto clip, subtitle & voiceover studio (Windows/Linux/Android, local-first)"
}

Write-Host "Selesai: https://github.com/$repo" -ForegroundColor Cyan
