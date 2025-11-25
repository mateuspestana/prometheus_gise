"""Tests for Qt utilities module."""

from pathlib import Path
import sys

import pytest

from src.qt_utils import configure_qt_plugins


def test_configure_qt_plugins_in_development() -> None:
    """Test that configure_qt_plugins finds plugins in development mode."""
    # Should not be running as PyInstaller executable
    assert not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))
    
    plugin_path = configure_qt_plugins()
    
    # Should find plugins in venv
    assert plugin_path is not None
    assert plugin_path.exists()
    assert plugin_path.is_dir()
    assert "PyQt6" in str(plugin_path)
    assert "plugins" in str(plugin_path)


def test_configure_qt_plugins_sets_environment() -> None:
    """Test that configure_qt_plugins sets environment variables."""
    import os
    from PyQt6.QtCore import QCoreApplication
    
    # Clear any existing configuration
    if "QT_PLUGIN_PATH" in os.environ:
        del os.environ["QT_PLUGIN_PATH"]
    QCoreApplication.setLibraryPaths([])
    
    plugin_path = configure_qt_plugins()
    
    if plugin_path:
        # Check environment variable is set
        assert "QT_PLUGIN_PATH" in os.environ
        assert os.environ["QT_PLUGIN_PATH"] == str(plugin_path)
        
        # Check library paths are set
        library_paths = QCoreApplication.libraryPaths()
        assert len(library_paths) > 0
        assert str(plugin_path) in library_paths

