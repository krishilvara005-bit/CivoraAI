@echo off
cd /d "%~dp0"

echo Starting Flask backend on :5000 ...
start "civora-backend" cmd /k "cd /d %~dp0backend && python -m flask --app wsgi run --port 5000 --debug"

echo Starting Node gateway on :8080 ...
start "civora-gateway" cmd /k "cd /d %~dp0gateway && node src/index.js"

echo Starting Vite frontend on :5173 ...
start "civora-frontend" cmd /k "cd /d %~dp0frontend && node node_modules\vite\bin\vite.js"

echo.
echo All three servers are starting in separate windows.
echo   Frontend (Vite):   http://localhost:5173
echo   Gateway:           http://localhost:8080
echo   Backend (Flask):   http://localhost:5000
echo.
echo Open http://localhost:5173 in your browser.
