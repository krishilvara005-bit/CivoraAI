@echo off
ping -n 7 127.0.0.1 > nul
echo --- Flask backend ---
curl -s http://localhost:5000/api/health
echo.
echo --- Gateway ---
curl -s -o nul -w "gateway_status=%%{http_code}" http://localhost:8080/
echo.
echo --- Vite frontend ---
curl -s -o nul -w "vite_status=%%{http_code}" http://localhost:5173/
echo.

