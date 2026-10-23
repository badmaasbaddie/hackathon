Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting SwasthyaSetu AI Platform" -ForegroundColor Green
Write-Host "  AI-Powered Rural Healthcare Continuity Platform" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir\backend"

Write-Host "Launching server on http://127.0.0.1:8000 ..." -ForegroundColor Green
python -m uvicorn main:app --host 127.0.0.1 --port 8000
