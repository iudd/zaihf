@echo off
chcp 65001 >nul
title Zai-2API
cls

echo ==========================================
echo          Zai-2API v2.0
echo ==========================================
echo.
echo Web UI: http://localhost:8000
echo.
echo Starting service...
echo.

start http://localhost:8000
python main.py

pause
