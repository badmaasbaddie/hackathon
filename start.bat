@echo off
echo ========================================================
echo   Starting SwasthyaSetu AI Production Server
echo   AI-Powered Rural Healthcare Continuity Platform
echo ========================================================
cd /d "%~dp0backend"
echo Starting server on http://127.0.0.1:8000 ...
python -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
