@echo off
setlocal
echo ========================================================
echo   SwasthyaSetu AI - local demo (fictional data)
echo ========================================================
set ROOT=%~dp0

echo Installing backend dependencies...
python -m pip install -q -r "%ROOT%backend\requirements.txt" || goto :error

if not exist "%ROOT%frontend\dist\index.html" (
  echo Building frontend...
  pushd "%ROOT%frontend"
  if not exist node_modules call npm install || goto :error
  call npm run build || goto :error
  popd
)

cd /d "%ROOT%backend"
echo Seeding clean demo database...
python seed_data.py || goto :error
echo Open http://127.0.0.1:8000 in your browser (Ctrl+C to stop)
python -m uvicorn main:app --host 127.0.0.1 --port 8000
goto :eof

:error
echo Startup failed - see the message above.
pause
exit /b 1
