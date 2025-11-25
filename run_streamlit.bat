@echo off
REM Script to run Streamlit app for Prometheus Forensic Tool
REM Usage: run_streamlit.bat
REM This script will:
REM 1. Install uv if not present
REM 2. Create .venv if it doesn't exist
REM 3. Install requirements.txt
REM 4. Run Streamlit

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo 🔍 Prometheus Forensic Tool - Streamlit Setup
echo ==============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Erro: Python nao encontrado. Por favor, instale Python 3.10+ primeiro.
    pause
    exit /b 1
)

REM Check and install uv if needed
where uv >nul 2>&1
if errorlevel 1 (
    echo 📦 uv nao encontrado. Instalando uv...
    python -m pip install --user uv
    if errorlevel 1 (
        echo ⚠️  Falha ao instalar uv via pip. Tentando via PowerShell...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    )
    
    REM Verify uv installation
    where uv >nul 2>&1
    if errorlevel 1 (
        REM Try adding common paths
        set "PATH=%PATH%;%USERPROFILE%\.cargo\bin;%LOCALAPPDATA%\Programs\uv"
        where uv >nul 2>&1
        if errorlevel 1 (
            echo ❌ Erro: Falha ao instalar uv. Por favor, instale manualmente:
            echo    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
            pause
            exit /b 1
        )
    )
    echo ✅ uv instalado com sucesso!
) else (
    echo ✅ uv ja esta instalado
)

echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Criando ambiente virtual (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Erro: Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
    echo ✅ Ambiente virtual criado!
) else (
    echo ✅ Ambiente virtual (.venv) ja existe
)

echo.

REM Determine Python executable path
set "PYTHON_EXE=.venv\Scripts\python.exe"
set "PIP_EXE=.venv\Scripts\pip.exe"

REM Verify virtual environment exists
if not exist "%PYTHON_EXE%" (
    echo ❌ Erro: Ambiente virtual nao foi criado corretamente.
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo.

REM Install dependencies
if exist "requirements.txt" (
    echo 📥 Instalando dependencias de requirements.txt...
    
    REM Install pdfminer.six separately using uv pip (uv has issues with dotted package names)
    where uv >nul 2>&1
    if not errorlevel 1 (
        echo    Instalando pdfminer.six com uv pip...
        uv pip install --python "%PYTHON_EXE%" "pdfminer.six>=20221105,<2025.0"
        if errorlevel 1 (
            echo    ⚠️  Aviso: Falha ao instalar pdfminer.six com uv pip
        )
    ) else (
        echo    ⚠️  Aviso: uv nao encontrado. Pulando instalacao de pdfminer.six
    )
    
    REM Install other dependencies using uv or pip
    where uv >nul 2>&1
    if not errorlevel 1 (
        echo    Instalando dependencias com uv pip...
        uv pip install --python "%PYTHON_EXE%" -r requirements.txt
        if errorlevel 1 (
            echo    ⚠️  uv falhou, tentando com pip...
            "%PIP_EXE%" install -r requirements.txt
        )
    ) else (
        echo    Instalando dependencias com pip...
        "%PIP_EXE%" install -r requirements.txt
    )
    echo ✅ Dependencias instaladas!
) else (
    echo ⚠️  Aviso: requirements.txt nao encontrado. Pulando instalacao de dependencias.
)

echo.

REM Check if streamlit_app.py exists
if not exist "src\streamlit_app.py" (
    echo ❌ Erro: src\streamlit_app.py nao encontrado.
    pause
    exit /b 1
)

REM Verify streamlit is installed
"%PYTHON_EXE%" -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ❌ Erro: Streamlit nao esta instalado.
    echo    Tentando instalar streamlit...
    "%PIP_EXE%" install streamlit
    if errorlevel 1 (
        echo ❌ Falha ao instalar streamlit.
        pause
        exit /b 1
    )
)

echo.
echo 🚀 Iniciando servidor Streamlit...
echo ==============================================
echo 📍 Acesse: http://localhost:8501
echo ⏹️  Pressione Ctrl+C para parar o servidor.
echo.

REM Run Streamlit
"%PYTHON_EXE%" -m streamlit run src/streamlit_app.py ^
    --server.port 8501 ^
    --server.address localhost ^
    --server.headless true ^
    --browser.gatherUsageStats false

pause
