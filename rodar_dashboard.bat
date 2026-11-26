
@echo off
chcp 65001 >nul
title IRPF 2026 - Dashboard Monitor

cd /d "%~dp0"

echo ==========================================
echo       IRPF 2026 - DASHBOARD MONITOR
echo ==========================================
echo.

if not exist "python\python.exe" (
    echo [ERRO] Python portatil nao encontrado.
    pause
    exit /b 1
)

echo Inicializando o painel interativo...
echo.

python\python.exe -m streamlit run dashboard.py --server.port 2026

pause
