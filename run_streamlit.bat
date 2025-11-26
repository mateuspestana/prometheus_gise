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
echo Prometheus Forensic Tool - Streamlit Setup
echo ==============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Erro: Python nao encontrado. Por favor, instale Python 3.10+ primeiro.
    pause
    exit /b 1
)

REM Check and install uv if needed
REM Initialize UV_CMD variable
set "UV_CMD="

REM Add common uv installation paths to PATH first
set "PATH=%PATH%;%USERPROFILE%\.cargo\bin;%LOCALAPPDATA%\Programs\uv"

REM Try to run uv --version to check if it's available
uv --version >nul 2>&1
if not errorlevel 1 (
    set "UV_CMD=uv"
    echo uv ja esta instalado
    goto :uv_ready
)

REM Check if uv exists in common installation paths
if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
    set "UV_CMD=%USERPROFILE%\.cargo\bin\uv.exe"
    set "PATH=%PATH%;%USERPROFILE%\.cargo\bin"
    echo uv encontrado em .cargo\bin
    goto :uv_ready
)

if exist "%LOCALAPPDATA%\Programs\uv\uv.exe" (
    set "UV_CMD=%LOCALAPPDATA%\Programs\uv\uv.exe"
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\uv"
    echo uv encontrado em Programs\uv
    goto :uv_ready
)

REM uv not found, try to install
echo uv nao encontrado. Instalando uv...
python -m pip install --user uv
if errorlevel 1 (
    echo Falha ao instalar uv via pip. Tentando via PowerShell...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    REM Update PATH after PowerShell installation
    set "PATH=%PATH%;%USERPROFILE%\.cargo\bin;%LOCALAPPDATA%\Programs\uv"
)

REM Verify uv installation by trying to run it or find it
uv --version >nul 2>&1
if not errorlevel 1 (
    set "UV_CMD=uv"
    echo uv instalado com sucesso!
    goto :uv_ready
)

REM Check again in common paths after installation
if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
    set "UV_CMD=%USERPROFILE%\.cargo\bin\uv.exe"
    echo uv encontrado apos instalacao
    goto :uv_ready
)

if exist "%LOCALAPPDATA%\Programs\uv\uv.exe" (
    set "UV_CMD=%LOCALAPPDATA%\Programs\uv\uv.exe"
    echo uv encontrado apos instalacao
    goto :uv_ready
)

echo Erro: Falha ao instalar ou encontrar uv. Por favor, instale manualmente:
echo    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
echo    Ou reinicie o terminal apos a instalacao.
pause
exit /b 1

:uv_ready
echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Criando ambiente virtual (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo Erro: Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
    echo Ambiente virtual criado!
) else (
    echo Ambiente virtual (.venv) ja existe
)

echo.

REM Determine Python executable path
set "PYTHON_EXE=.venv\Scripts\python.exe"
set "PIP_EXE=.venv\Scripts\pip.exe"

REM Verify virtual environment exists
if not exist "%PYTHON_EXE%" (
    echo Erro: Ambiente virtual nao foi criado corretamente.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo.

REM Install dependencies
if exist "requirements.txt" (
    echo Instalando dependencias de requirements.txt...
    
    REM Install pdfminer.six separately using uv pip (uv has issues with dotted package names)
    if defined UV_CMD (
        echo    Instalando pdfminer.six com uv pip...
        "%UV_CMD%" pip install --python "%PYTHON_EXE%" "pdfminer.six>=20221105,<2025.0"
        if errorlevel 1 (
            echo    Aviso: Falha ao instalar pdfminer.six com uv pip
        )
    ) else (
        echo    Aviso: uv nao encontrado. Pulando instalacao de pdfminer.six
    )
    
    REM Install other dependencies using uv or pip
    if defined UV_CMD (
        echo    Instalando dependencias com uv pip...
        "%UV_CMD%" pip install --python "%PYTHON_EXE%" -r requirements.txt
        if errorlevel 1 (
            echo    uv falhou, tentando com pip...
            "%PIP_EXE%" install -r requirements.txt
        )
    ) else (
        echo    Instalando dependencias com pip...
        "%PIP_EXE%" install -r requirements.txt
    )
    echo Dependencias instaladas!
) else (
    echo Aviso: requirements.txt nao encontrado. Pulando instalacao de dependencias.
)

echo.

REM Check if streamlit_app.py exists
if not exist "src\streamlit_app.py" (
    echo Erro: src\streamlit_app.py nao encontrado.
    pause
    exit /b 1
)

REM Verify streamlit is installed
"%PYTHON_EXE%" -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Erro: Streamlit nao esta instalado.
    echo    Tentando instalar streamlit...
    "%PIP_EXE%" install streamlit
    if errorlevel 1 (
        echo Falha ao instalar streamlit.
        pause
        exit /b 1
    )
)

echo.
echo Iniciando servidor Streamlit...
echo ==============================================
echo Acesse: http://localhost:8501
echo Pressione Ctrl+C para parar o servidor.
echo.

REM Set PYTHONPATH to include the project root directory
REM This ensures that 'src' module can be imported correctly
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

REM Run Streamlit using Python module execution
REM This ensures proper module resolution
"%PYTHON_EXE%" -m streamlit run src/streamlit_app.py --server.port 8501 --server.address localhost --server.headless true --browser.gatherUsageStats false

pause
