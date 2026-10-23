# SwasthyaSetu AI - local demo launcher (Windows PowerShell)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Installing backend dependencies..." -ForegroundColor Gray
python -m pip install -q -r "$root\backend\requirements.txt"

if (-not (Test-Path "$root\frontend\dist\index.html") -or $args -contains "--rebuild") {
    Write-Host "Building frontend..." -ForegroundColor Gray
    Push-Location "$root\frontend"
    if (-not (Test-Path "node_modules")) { npm install }
    npm run build
    Pop-Location
}

Set-Location "$root\backend"
Write-Host "Seeding clean demo database (fictional data)..." -ForegroundColor Gray
python seed_data.py

Write-Host "Open http://127.0.0.1:8000 in your browser (Ctrl+C to stop)" -ForegroundColor Green
python -m uvicorn main:app --host 127.0.0.1 --port 8000
