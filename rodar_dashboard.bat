@echo off
title IRPF 2026 - Dashboard Monitor
cd /d "c:\Users\backup\OneDrive - CONTABS ASSESSORIA CONTABIL SOCIEDADE SIMPLES\Documents\monitor_irpf"
echo Inicializando o painel interativo...
streamlit run dashboard.py --server.port 2026

