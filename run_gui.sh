#!/bin/bash
cd "$(dirname "$0")"

# Find Python version dynamically
PYTHON_VERSION=$("./.venv/bin/python" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
QT_PLUGINS_DIR="$PWD/.venv/lib/python${PYTHON_VERSION}/site-packages/PyQt6/Qt6/plugins"

# Set Qt plugin paths before Python starts
export QT_PLUGIN_PATH="$QT_PLUGINS_DIR"
export QT_QPA_PLATFORM_PLUGIN_PATH="$QT_PLUGINS_DIR/platforms"
# On macOS, help plugins find Qt frameworks via @rpath
if [[ "$OSTYPE" == "darwin"* ]]; then
    export DYLD_FRAMEWORK_PATH="$PWD/.venv/lib/python${PYTHON_VERSION}/site-packages/PyQt6/Qt6/lib"
fi
export PYTHONPATH="$PWD"

# Verify plugin directory exists
if [ ! -d "$QT_PLUGINS_DIR" ]; then
    echo "Warning: Qt plugins directory not found: $QT_PLUGINS_DIR" >&2
    echo "Attempting to find plugins automatically..." >&2
fi

./.venv/bin/python -m src.gui