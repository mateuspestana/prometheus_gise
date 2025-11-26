@echo off
REM Script para executar CLI do Prometheus Forensic Tool
REM Uso: run_cli.bat
REM Requisitos:
REM - Ambiente virtual .venv criado
REM - Dependencias instaladas

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo Erro: Ambiente virtual .venv nao encontrado.
    echo Por favor, crie o ambiente virtual primeiro:
    echo   python -m venv .venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

REM Set PYTHONPATH to include the project root directory
REM This ensures that 'src' module can be imported correctly
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

REM Check if cli.py exists
if not exist "src\cli.py" (
    echo Erro: src\cli.py nao encontrado.
    pause
    exit /b 1
)

echo.
echo ==============================================
echo Prometheus Forensic Tool - CLI
echo ==============================================
echo.

REM Ask for input directory
set /p INPUT_DIR="Digite o caminho do diretorio com arquivos .ufdr: "

REM Validate input
if "!INPUT_DIR!"=="" (
    echo Erro: Caminho nao pode estar vazio.
    pause
    exit /b 1
)

REM Expand user path if needed (handles ~)
if "!INPUT_DIR:~0,1!"=="~" (
    set "INPUT_DIR=%USERPROFILE%!INPUT_DIR:~1!"
)

REM Check if directory exists
if not exist "!INPUT_DIR!" (
    echo Erro: Diretorio nao encontrado: !INPUT_DIR!
    pause
    exit /b 1
)

REM Check if it's actually a directory
if not exist "!INPUT_DIR!\" (
    echo Erro: O caminho especificado nao e um diretorio: !INPUT_DIR!
    pause
    exit /b 1
)

echo.
echo Executando varredura em: !INPUT_DIR!
echo.

REM Run CLI scan command
python -m src.cli scan -i "!INPUT_DIR!"

echo.
pause

