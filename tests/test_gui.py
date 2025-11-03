"""Smoke tests for the PyQt5 GUI scaffold (F8)."""

import sys

import pytest

pytest.importorskip("PyQt5")

from PyQt5.QtWidgets import QApplication

from src.gui import PrometheusWindow, ResultRow


def test_window_initializes_and_populates_table() -> None:
    app = QApplication.instance() or QApplication(sys.argv)

    window = PrometheusWindow()
    rows = [
        ResultRow("file.ufdr", "Email", "john@example.com", "data/messages.db", "2025-01-01T12:00:00Z"),
        ResultRow("file2.ufdr", "CPF", "123.456.789-00", "report/report.html", "2025-01-02T08:30:00Z"),
    ]

    window.populate_results(rows)

    assert window.results_table.rowCount() == len(rows)
    assert window.results_table.columnCount() == 5

    window.close()
    window.deleteLater()
