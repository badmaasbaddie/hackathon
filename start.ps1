Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting SwasthyaSetu AI Platform" -ForegroundColor Green
Write-Host "  Govt. of Maharashtra Hacktoberfest" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir\backend"

Write-Host "Seeding database..." -ForegroundColor Gray
python seed_data.py

Write-Host "Launching server on http://127.0.0.1:8000 ..." -ForegroundColor Green
python -m uvicorn main:app --host 127.0.0.1 --port 8000
