@echo off
chcp 65001 >nul
title Monitor IRPF - Busca Saldo

cd /d "%~dp0"

python\python.exe busca_saldo_imposto.py

pause
