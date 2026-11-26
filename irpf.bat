@echo off
title Monitor IRPF Loop

:loop
echo ==============================
echo Iniciando execucao: %date% %time%
echo ==============================

cd /d "C:\Users\backup\Documents\monitor_irpf"

python main.py
python busca_saldo_imposto.py
echo.
echo Execucao finalizada. Aguardando 5 minutos...
timeout /t 300 /nobreak > nul

goto loop