"""PyQt5 interface scaffold for the Prometheus Forensic Tool (F8)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)


@dataclass
class ResultRow:
    """Representation of a result entry shown in the table."""

    source_file: str
    pattern_type: str
    match_value: str
    internal_path: str
    timestamp: str


class PrometheusWindow(QMainWindow):
    """Main GUI window for Prometheus."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Prometheus Forensic Tool")
        self.resize(960, 640)

        self.input_edit = QLineEdit(self)
        self.config_edit = QLineEdit(self)
        self.progress_bar = QProgressBar(self)
        self.results_table = QTableWidget(self)

        self._setup_ui()

    def _setup_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.addLayout(self._build_path_selector("Diretório de evidências", self.input_edit, self._browse_input))
        layout.addLayout(self._build_path_selector("Arquivo de padrões", self.config_edit, self._browse_config))

        run_button = QPushButton("Iniciar Varredura", self)
        run_button.clicked.connect(self._start_scan)
        layout.addWidget(run_button)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        self._configure_table()
        layout.addWidget(self.results_table)

        export_button = QPushButton("Exportar Resultados", self)
        export_button.clicked.connect(self._export_results)
        layout.addWidget(export_button)

    def _build_path_selector(self, label_text: str, line_edit: QLineEdit, callback) -> QHBoxLayout:
        container = QHBoxLayout()
        label = QLabel(label_text, self)
        container.addWidget(label)

        line_edit.setPlaceholderText("Selecione o caminho...")
        container.addWidget(line_edit, stretch=1)

        button = QPushButton("Procurar", self)
        button.clicked.connect(callback)
        container.addWidget(button)
        return container

    def _configure_table(self) -> None:
        headers = ["Arquivo", "Tipo", "Valor", "Caminho Interno", "Timestamp"]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSortingEnabled(True)
        self.results_table.setAlternatingRowColors(True)
        header = self.results_table.horizontalHeader()
        for index in range(len(headers)):
            header.setSectionResizeMode(index, QHeaderView.Stretch)

    def _browse_input(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Selecionar diretório de evidências")
        if directory:
            self.input_edit.setText(directory)

    def _browse_config(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo de padrões", filter="JSON (*.json)")
        if file_path:
            self.config_edit.setText(file_path)

    def _start_scan(self) -> None:
        evidence_dir = Path(self.input_edit.text())
        config_file = Path(self.config_edit.text()) if self.config_edit.text() else None

        if not evidence_dir.exists() or not evidence_dir.is_dir():
            QMessageBox.warning(self, "Entrada inválida", "Selecione um diretório de evidências válido.")
            return

        if config_file and not config_file.exists():
            QMessageBox.warning(self, "Configuração inválida", "Selecione um arquivo de padrões válido.")
            return

        # Placeholder behaviour until the processing pipeline is wired in.
        self.results_table.setRowCount(0)
        self.progress_bar.setValue(0)
        QMessageBox.information(
            self,
            "Varredura pendente",
            "A lógica de processamento será integrada quando as outras funcionalidades estiverem concluídas.",
        )

    def _export_results(self) -> None:
        if self.results_table.rowCount() == 0:
            QMessageBox.information(self, "Sem dados", "Não há resultados para exportar no momento.")
            return

        target, _ = QFileDialog.getSaveFileName(self, "Salvar resultados", filter="JSON (*.json)")
        if not target:
            return

        # Placeholder for actual export logic.
        QMessageBox.information(self, "Exportação", f"Resultados seriam exportados para: {target}")

    def populate_results(self, rows: List[ResultRow]) -> None:
        """Utility helper for future integration tests."""

        self.results_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate([row.source_file, row.pattern_type, row.match_value, row.internal_path, row.timestamp]):
                self.results_table.setItem(row_index, column_index, QTableWidgetItem(value))


def run_gui() -> None:
    """Launch the PyQt5 application."""

    app = QApplication.instance() or QApplication(sys.argv)
    window = PrometheusWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_gui()
