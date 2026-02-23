@echo off
title CAD Builder Server
cd /d "C:\Users\robmi\CAD BUILDER"

echo ========================================
echo   CAD Builder - Starting...
echo ========================================
echo.

:: Start API server in background
start /b "" ".venv\Scripts\python.exe" -m uvicorn services.api.main:app --host 0.0.0.0 --port 8080 > logs\api.log 2>&1

:: Wait for API
echo Waiting for API server...
:waitloop
timeout /t 2 /nobreak >nul
curl -sf http://localhost:8080/api/health >nul 2>&1
if errorlevel 1 goto waitloop
echo API server ready!
echo.

:: Start permanent Cloudflare tunnel (cadbuilder.dev)
echo Starting Cloudflare tunnel for cadbuilder.dev...
cloudflared tunnel run cadbuilder 2> logs\tunnel.log
