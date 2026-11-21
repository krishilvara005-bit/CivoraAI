@echo off
echo --- Flask /api/health ---
curl -s http://localhost:5000/api/health
echo.
echo --- Gateway /api/health ---
curl -s http://localhost:8080/api/health
echo.
echo --- Vite ---
curl -s -o nul -w "vite_http_status=%%{http_code}" http://localhost:5173/
echo.

