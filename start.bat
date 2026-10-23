@echo off
echo ========================================================
echo   Starting SwasthyaSetu AI Production Server
echo   Govt. of Maharashtra Hacktoberfest
echo ========================================================
cd /d "%~dp0backend"
echo Seeding clean demo database...
python seed_data.py
echo Starting server on http://127.0.0.1:8000 ...
python -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
