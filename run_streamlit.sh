#!/bin/bash
# Script to run Streamlit app for Prometheus Forensic Tool
# Usage: ./run_streamlit.sh
# This script will:
# 1. Install uv if not present
# 2. Create .venv if it doesn't exist
# 3. Install requirements.txt
# 4. Run Streamlit

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 Prometheus Forensic Tool - Streamlit Setup"
echo "=============================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Erro: Python não encontrado. Por favor, instale Python 3.10+ primeiro."
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check and install uv if needed
if ! command -v uv &> /dev/null; then
    echo "📦 uv não encontrado. Instalando uv..."
    if command -v pip3 &> /dev/null; then
        $PYTHON_CMD -m pip install --user uv
    elif command -v pip &> /dev/null; then
        $PYTHON_CMD -m pip install --user uv
    else
        echo "⚠️  pip não encontrado. Tentando instalar uv via curl..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    # Verify uv installation
    if ! command -v uv &> /dev/null; then
        echo "❌ Erro: Falha ao instalar uv. Por favor, instale manualmente:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    echo "✅ uv instalado com sucesso!"
else
    echo "✅ uv já está instalado"
fi

echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Criando ambiente virtual (.venv)..."
    $PYTHON_CMD -m venv .venv --python 3.12
    echo "✅ Ambiente virtual criado!"
else
    echo "✅ Ambiente virtual (.venv) já existe"
fi

echo ""

# Determine Python executable path
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    PYTHON_EXE=".venv/Scripts/python.exe"
    PIP_EXE=".venv/Scripts/pip.exe"
else
    PYTHON_EXE=".venv/bin/python"
    PIP_EXE=".venv/bin/pip"
fi

# Activate virtual environment
if [ -f "$PYTHON_EXE" ]; then
    echo "🔧 Ativando ambiente virtual..."
    source .venv/bin/activate 2>/dev/null || true
else
    echo "❌ Erro: Ambiente virtual não foi criado corretamente."
    exit 1
fi

echo ""

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "📥 Instalando dependências de requirements.txt..."
    
    # Install pdfminer.six separately using uv pip (uv has issues with dotted package names)
    if command -v uv &> /dev/null; then
        echo "   Instalando pdfminer.six com uv pip..."
        uv pip install --python "$PYTHON_EXE" "pdfminer.six>=20221105,<2025.0" || {
            echo "   ⚠️  Aviso: Falha ao instalar pdfminer.six com uv pip"
        }
    else
        echo "   ⚠️  Aviso: uv não encontrado. Pulando instalação de pdfminer.six"
    fi
    
    # Install other dependencies using uv or pip
    if command -v uv &> /dev/null; then
        echo "   Instalando dependências com uv pip..."
        uv pip install --python "$PYTHON_EXE" -r requirements.txt || {
            echo "   ⚠️  uv falhou, tentando com pip..."
            $PIP_EXE install -r requirements.txt
        }
    else
        echo "   Instalando dependências com pip..."
        $PIP_EXE install -r requirements.txt
    fi
    echo "✅ Dependências instaladas!"
else
    echo "⚠️  Aviso: requirements.txt não encontrado. Pulando instalação de dependências."
fi

echo ""

# Check if streamlit_app.py exists
if [ ! -f "src/streamlit_app.py" ]; then
    echo "❌ Erro: src/streamlit_app.py não encontrado."
    exit 1
fi

# Verify streamlit is installed
if ! $PYTHON_EXE -c "import streamlit" 2>/dev/null; then
    echo "❌ Erro: Streamlit não está instalado."
    echo "   Tentando instalar streamlit..."
    $PIP_EXE install streamlit || {
        echo "❌ Falha ao instalar streamlit."
        exit 1
    }
fi

echo ""
echo "🚀 Iniciando servidor Streamlit..."
echo "=============================================="
echo "📍 Acesse: http://localhost:8501"
echo "⏹️  Pressione Ctrl+C para parar o servidor."
echo ""

# Run Streamlit
$PYTHON_EXE -m streamlit run src/streamlit_app.py \
    --server.port 8501 \
    --server.address localhost \
    --server.headless true \
    --browser.gatherUsageStats false

