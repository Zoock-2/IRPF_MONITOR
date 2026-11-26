
@echo off
chcp 65001 >nul
setlocal

title Instalador Python Portatil

cd /d "%~dp0"

echo.
echo ==========================================
echo       INSTALADOR PYTHON PORTATIL
echo ==========================================
echo.

:: ==========================================
:: CONFIGURACOES
:: ==========================================

set "ARQUIVO_PYTHON=python.tar.gz"
set "PASTA_PYTHON=python"
set "ARQUIVO_REQ=requirements.txt"

:: ==========================================
:: VERIFICAR ARQUIVOS
:: ==========================================

if not exist "%ARQUIVO_PYTHON%" (
    echo [ERRO] Arquivo %ARQUIVO_PYTHON% nao encontrado.
    pause
    exit /b 1
)

if not exist "%ARQUIVO_REQ%" (
    echo [ERRO] requirements.txt nao encontrado.
    pause
    exit /b 1
)

where tar >nul 2>&1

if errorlevel 1 (
    echo [ERRO] TAR nao encontrado no Windows.
    pause
    exit /b 1
)

:: ==========================================
:: EXTRAIR PYTHON
:: ==========================================

if not exist "%PASTA_PYTHON%\python.exe" (

    echo [1/3] Extraindo Python portatil...
    echo.

    if exist "%PASTA_PYTHON%" (
        echo Removendo extracao anterior...
        rmdir /s /q "%PASTA_PYTHON%"
    )

    tar -xzf "%ARQUIVO_PYTHON%"

    if errorlevel 1 (
        echo [ERRO] Falha ao extrair Python.
        pause
        exit /b 1
    )

) else (
    echo [1/3] Python ja esta extraido.
)

:: ==========================================
:: VERIFICAR INTERPRETADOR
:: ==========================================

if not exist "%PASTA_PYTHON%\python.exe" (
    echo.
    echo [ERRO] python.exe nao encontrado.
    echo Verifique a estrutura do arquivo TAR.
    pause
    exit /b 1
)

echo.
echo Versao do Python:

"%PASTA_PYTHON%\python.exe" --version

if errorlevel 1 (
    echo [ERRO] Python nao conseguiu iniciar.
    pause
    exit /b 1
)

:: ==========================================
:: VERIFICAR PIP
:: ==========================================

echo.
echo [2/3] Verificando pip...

"%PASTA_PYTHON%\python.exe" -m pip --version

if errorlevel 1 (
    echo [ERRO] Pip nao esta disponivel.
    echo Verifique a distribuicao Python baixada.
    pause
    exit /b 1
)

:: ==========================================
:: INSTALAR REQUIREMENTS
:: ==========================================

echo.
echo [3/3] Instalando dependencias...
echo.

"%PASTA_PYTHON%\python.exe" -m pip install -r "%ARQUIVO_REQ%" --default-timeout=120 --retries=10

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

:: ==========================================
:: FINALIZACAO
:: ==========================================

echo.
echo ==========================================
echo       INSTALACAO CONCLUIDA!
echo ==========================================
echo.
echo Python instalado:
echo %CD%\%PASTA_PYTHON%
echo.
echo Para executar o programa, utilize:
echo executar.bat
echo.

pause
exit /b 0
```