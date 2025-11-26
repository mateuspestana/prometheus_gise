@echo off
REM Script simplificado para executar Streamlit
REM Uso: run_streamlit.bat
REM Requisitos:
REM - Ambiente virtual .venv criado
REM - Dependencias instaladas

setlocal

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

REM Check if streamlit_app.py exists
if not exist "src\streamlit_app.py" (
    echo Erro: src\streamlit_app.py nao encontrado.
    pause
    exit /b 1
)

REM Run Streamlit using Python module execution
echo.
echo Iniciando servidor Streamlit...
echo Acesse: http://localhost:8501
echo Pressione Ctrl+C para parar o servidor.
echo.

python -m streamlit run src\streamlit_app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

pause
