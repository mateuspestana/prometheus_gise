"""Utilities for configuring Qt plugins across platforms and deployment modes."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def configure_qt_plugins() -> Optional[Path]:
    """
    Configure Qt plugin paths for development and PyInstaller executables.
    
    Detects the environment automatically and sets up plugin paths for:
    - Development mode (venv)
    - PyInstaller executables (Windows, Linux, macOS)
    
    Returns:
        Path to the configured plugin directory, or None if not found.
    """
    plugin_path: Optional[Path] = None
    
    # Check if running as PyInstaller executable
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # PyInstaller executable mode
        base_path = Path(sys._MEIPASS)
        # PyInstaller places plugins in _internal/PyQt6/Qt6/plugins
        possible_paths = [
            base_path / "_internal" / "PyQt6" / "Qt6" / "plugins",
            base_path / "PyQt6" / "Qt6" / "plugins",
        ]
        for path in possible_paths:
            if path.exists() and path.is_dir():
                plugin_path = path.resolve()
                break
    else:
        # Development mode - find plugins in venv
        # Start from this file's location and search for venv
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        
        # Try to find Python version and venv
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        # Try PyQt6 first (newer, better macOS support)
        venv_plugin_path = project_root / ".venv" / "lib" / f"python{python_version}" / "site-packages" / "PyQt6" / "Qt6" / "plugins"
        
        if venv_plugin_path.exists():
            plugin_path = venv_plugin_path.resolve()
        else:
            # Fallback: search for PyQt6 in any Python version in venv
            venv_lib = project_root / ".venv" / "lib"
            if venv_lib.exists():
                for py_dir in venv_lib.glob("python*"):
                    candidate = py_dir / "site-packages" / "PyQt6" / "Qt6" / "plugins"
                    if candidate.exists():
                        plugin_path = candidate.resolve()
                        break
    
    if plugin_path is None:
        # Last resort: try to find PyQt6 in sys.path
        for path_str in sys.path:
            path = Path(path_str)
            if path.exists():
                candidate = path / "PyQt6" / "Qt6" / "plugins"
                if candidate.exists():
                    plugin_path = candidate.resolve()
                    break
    
    if plugin_path and plugin_path.exists():
        plugin_path_str = str(plugin_path.resolve())
        platforms_path = plugin_path / "platforms"
        platforms_path_str = str(platforms_path.resolve()) if platforms_path.exists() else plugin_path_str
        
        # Set environment variables (must be done before importing PyQt6)
        # Qt checks these variables very early, so they must be set before any Qt imports
        os.environ["QT_PLUGIN_PATH"] = plugin_path_str
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_path_str
        
        # On macOS, also set DYLD_FRAMEWORK_PATH to help plugins find Qt frameworks
        # The plugins use @rpath which resolves relative to the Qt frameworks location
        if sys.platform == "darwin":
            qt_lib_path = plugin_path.parent.parent / "lib"
            if qt_lib_path.exists():
                qt_lib_path_str = str(qt_lib_path.resolve())
                os.environ["DYLD_FRAMEWORK_PATH"] = qt_lib_path_str
                # Also try setting DYLD_LIBRARY_PATH as fallback
                if "DYLD_LIBRARY_PATH" in os.environ:
                    os.environ["DYLD_LIBRARY_PATH"] = f"{qt_lib_path_str}:{os.environ['DYLD_LIBRARY_PATH']}"
                else:
                    os.environ["DYLD_LIBRARY_PATH"] = qt_lib_path_str
        
        # Don't try to import PyQt6 here - it may not be available yet
        # The environment variables should be sufficient
        return plugin_path
    
    return None

