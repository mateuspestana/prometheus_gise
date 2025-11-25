# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

datas = [('config', 'config')]
binaries = []
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'src.qt_utils',
    'src.main',
    'src.logger',
    'src.scanner',
    'src.extractor',
    'src.content_navigator',
    'src.text_extractor',
    'src.regex_engine',
    'src.reporter',
    'src.forensics',
    'src.models',
    'src.database_reader',
]

# Let PyInstaller's built-in hooks handle PyQt6 collection automatically
# This avoids symlink conflicts with Qt frameworks on macOS
# The hooks will properly handle framework structure and symlinks


a = Analysis(
    ['src/gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'heapq',  # Built-in module, no hook needed
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Use onedir mode (not onefile) for macOS .app bundles
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # This enables onedir mode
    name='Prometheus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid binary corruption on macOS
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.png'],
)

# Collect all binaries and data files separately (onedir mode)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX to avoid binary corruption on macOS
    upx_exclude=[],
    name='Prometheus',
)

# Create .app bundle for macOS
app = BUNDLE(
    coll,
    name='Prometheus.app',
    icon='icon.png',
    bundle_identifier='com.prometheus.forensic',
)
