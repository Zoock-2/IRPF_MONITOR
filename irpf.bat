@echo off
chcp 65001 >nul
title Monitor IRPF - Execucao Automatica

cd /d "%~dp0"

:loop
echo.
echo ==============================
echo Iniciando execucao: %date% %time%
echo ==============================
echo.

if not exist "python\python.exe" (
    echo [ERRO] Python portatil nao encontrado.
    pause
    exit /b 1
)

echo [1/2] Executando monitoramento principal...
python\python.exe main.py

echo.
echo [2/2] Buscando saldo de imposto...
python\python.exe busca_saldo_imposto.py

echo.
echo ==============================
echo Execucao finalizada: %date% %time%
echo Aguardando 5 minutos...
echo ==============================

timeout /t 300 /nobreak >nul

goto loop
