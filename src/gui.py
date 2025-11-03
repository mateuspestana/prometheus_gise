"""Modern PyQt5 interface for the Prometheus Forensic Tool (F8 refresh)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont, QPalette, QColor, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

DEFAULT_PATTERNS_PATH = Path("config/patterns.json")
APP_ICON_PATH = Path("icon.png")


@dataclass
class ResultRow:
    """Representation of a result entry shown in the results grid."""

    source_file: str
    pattern_type: str
    match_value: str
    internal_path: str
    timestamp: str


class PrometheusWindow(QMainWindow):
    """Main GUI window for Prometheus with a modern, user-friendly layout."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Prometheus Forensic Tool")
        self.resize(1100, 680)
        self._apply_palette()
        self._apply_icon()

        self.input_edit = QLineEdit(self)
        self.config_edit = QLineEdit(self)
        self.progress_bar = QProgressBar(self)
        self.status_label = QLabel("Pronto para iniciar.", self)
        self.results_table = QTableWidget(self)
        self.help_view = QTextBrowser(self)

        self._build_ui()
        self._configure_table()
        self._configure_help()
        self._load_default_paths()

    # ------------------------------------------------------------------ UI ---
    def _apply_palette(self) -> None:
        """Apply a subtle neo-dark palette to give a modern feel."""

        palette = QPalette()
        background = QColor(30, 34, 45)
        surface = QColor(40, 44, 55)
        text = QColor(236, 239, 244)

        palette.setColor(QPalette.Window, background)
        palette.setColor(QPalette.Base, surface)
        palette.setColor(QPalette.AlternateBase, QColor(46, 50, 63))
        palette.setColor(QPalette.Text, text)
        palette.setColor(QPalette.WindowText, text)
        palette.setColor(QPalette.Button, surface)
        palette.setColor(QPalette.ButtonText, text)
        palette.setColor(QPalette.Highlight, QColor(110, 174, 236))
        palette.setColor(QPalette.HighlightedText, QColor(16, 20, 29))

        self.setPalette(palette)
        self.setStyleSheet(
            "QLineEdit, QTextBrowser { border: 1px solid #4f566b; border-radius: 6px; padding: 6px; }"
            "QPushButton { background-color: #4c82ff; border-radius: 6px; padding: 8px 14px; color: #ecf0f4; }"
            "QPushButton:hover { background-color: #386ef5; }"
            "QGroupBox { border: 1px solid #4f566b; border-radius: 8px; margin-top: 12px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 6px; }"
            "QTableWidget { gridline-color: #3d4354; selection-background-color: #6eaef0; selection-color: #10141d; }"
        )

    def _apply_icon(self) -> None:
        """Load and apply the application icon when available."""

        if APP_ICON_PATH.exists():
            icon = QIcon(str(APP_ICON_PATH.resolve()))
            self.setWindowIcon(icon)

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_splitter(), stretch=1)

    def _build_header(self) -> QWidget:
        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Prometheus Forensic Tool", header)
        title_font = QFont("Segoe UI", 22, QFont.Bold)
        title.setFont(title_font)

        subtitle = QLabel("Análise moderna de pacotes UFDR", header)
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #9aa3ba;")

        title_block = QVBoxLayout()
        title_block.setContentsMargins(0, 0, 0, 0)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        header_layout.addLayout(title_block, stretch=1)

        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setStyleSheet("color: #9aa3ba;")
        header_layout.addWidget(self.status_label, stretch=0)

        return header

    def _build_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self._build_inputs_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        return splitter

    def _build_inputs_panel(self) -> QWidget:
        panel = QFrame(self)
        panel.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_paths_group())
        layout.addWidget(self._build_actions_group())
        layout.addStretch(1)
        layout.addWidget(self._build_about_box())

        return panel

    def _build_paths_group(self) -> QGroupBox:
        group = QGroupBox("Fontes de dados")
        form = QFormLayout(group)
        form.setSpacing(10)

        self.input_edit.setPlaceholderText("Selecione o diretório de evidências (.ufdr)")
        browse_input = QPushButton("Procurar…", group)
        browse_input.clicked.connect(self._browse_input)

        input_row = self._combine_line_button(self.input_edit, browse_input)
        form.addRow("Diretório de evidências", input_row)

        self.config_edit.setPlaceholderText("Arquivo de padrões (config/patterns.json)")
        browse_config = QPushButton("Procurar…", group)
        browse_config.clicked.connect(self._browse_config)
        config_row = self._combine_line_button(self.config_edit, browse_config)
        form.addRow("Arquivo de padrões", config_row)

        return group

    def _build_actions_group(self) -> QGroupBox:
        group = QGroupBox("Execução")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        run_button = QPushButton("Iniciar varredura", group)
        run_button.clicked.connect(self._start_scan)

        open_patterns_button = QPushButton("Abrir patterns.json", group)
        open_patterns_button.clicked.connect(self._open_patterns_file)

        layout.addWidget(run_button)
        layout.addWidget(open_patterns_button)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFormat("Aguardando execução…")
        layout.addWidget(self.progress_bar)

        return group

    def _build_about_box(self) -> QGroupBox:
        box = QGroupBox("Sobre o Prometheus")
        layout = QVBoxLayout(box)
        layout.setSpacing(6)
        about = QLabel(
            "Desenvolvido por Matheus C. Pestana (GENI/UFF).\n"
            "Interface moderna para apoiar varredura forense de pacotes UFDR."
        )
        about.setWordWrap(True)
        about.setStyleSheet("color: #b2bad6;")
        layout.addWidget(about)
        return box

    def _build_right_panel(self) -> QWidget:
        container = QFrame(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        tabs = QTabWidget(container)
        tabs.addTab(self._build_results_tab(), "Resultados")
        tabs.addTab(self._build_help_tab(), "Ajuda")
        layout.addWidget(tabs)

        return container

    def _build_results_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.results_table, stretch=1)

        export_button = QPushButton("Exportar resultados", tab)
        export_button.clicked.connect(self._export_results)
        export_button.setStyleSheet("QPushButton { background-color: #3fbdb0; color: #102533; }")
        layout.addWidget(export_button, alignment=Qt.AlignRight)

        return tab

    def _build_help_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.help_view)
        return tab

    def _combine_line_button(self, line_edit: QLineEdit, button: QPushButton) -> QWidget:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(line_edit, stretch=1)
        layout.addWidget(button)
        return container

    def _configure_table(self) -> None:
        headers = ["Arquivo", "Tipo", "Valor", "Caminho Interno", "Timestamp"]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        header = self.results_table.horizontalHeader()
        for index in range(len(headers)):
            header.setSectionResizeMode(index, QHeaderView.Stretch)

    def _configure_help(self) -> None:
        self.help_view.setOpenExternalLinks(True)
        self.help_view.setReadOnly(True)
        self.help_view.setStyleSheet("background-color: #262b39; color: #d5daec;")
        self.help_view.setHtml(self._build_help_text())

    def _build_help_text(self) -> str:
        patterns_path = DEFAULT_PATTERNS_PATH.resolve()
        return f"""
        <h2 style='color:#eff3ff;'>Guia Rápido</h2>
        <p>A Prometheus Forensic Tool automatiza a análise de pacotes <code>.ufdr</code>:
        encontra arquivos, extrai dados internos e aplica padrões de regex configuráveis
        para gerar um relatório consolidado.</p>

        <h3 style='color:#eff3ff;'>Fluxo de Trabalho</h3>
        <ol>
            <li>Escolha o diretório de evidências com os arquivos <code>.ufdr</code>.</li>
            <li>Selecione o arquivo de padrões (por padrão: <code>{patterns_path}</code>).</li>
            <li>Inicie a varredura. O pipeline definitivo consolidará todos os resultados em um único JSON.</li>
        </ol>

        <h3 style='color:#eff3ff;'>Padrões Regex</h3>
        <p>Os padrões ficam em <code>config/patterns.json</code>. Cada entrada contém:</p>
        <ul>
            <li><b>name</b>: identificador do padrão (ex.: <code>CPF</code>).</li>
            <li><b>regex</b>: expressão regular usada na busca.</li>
            <li><b>flags</b> (opcional): lista com <code>ignorecase</code>, <code>multiline</code>, <code>dotall</code> ou <code>unicode</code>.</li>
        </ul>
        <p>Use o botão "Abrir patterns.json" para revisar ou editar o arquivo padrão.</p>

        <h3 style='color:#eff3ff;'>Módulos Implementados</h3>
        <ul>
            <li><code>scanner.py</code>: busca recursiva por <code>.ufdr</code> (F1).</li>
            <li><code>extractor.py</code>: trata <code>.ufdr</code> como arquivos <i>zip</i> (F2).</li>
            <li><code>regex_engine.py</code>: executa os padrões configurados (F4).</li>
            <li><code>cli.py</code>: interface de linha de comando (F7).</li>
            <li><code>gui.py</code>: esta interface moderna em PyQt5 (F8).</li>
        </ul>

        <h3 style='color:#eff3ff;'>Status do Projeto</h3>
        <p>O pipeline completo ainda será integrado em <code>run_pipeline</code>. Até lá, use os módulos individuais
        para validar resultados ou experimentar com dados de teste.</p>

        <p style='margin-top:16px;color:#a7b2d6;'>Desenvolvido por Matheus C. Pestana (GENI/UFF).</p>
        """

    def _load_default_paths(self) -> None:
        if DEFAULT_PATTERNS_PATH.exists():
            self.config_edit.setText(str(DEFAULT_PATTERNS_PATH.resolve()))

    # --------------------------------------------------------------- Actions ---
    def _browse_input(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Selecionar diretório de evidências")
        if directory:
            self.input_edit.setText(directory)

    def _browse_config(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo de padrões",
            str(DEFAULT_PATTERNS_PATH.parent.resolve()),
            "JSON (*.json)",
        )
        if file_path:
            self.config_edit.setText(file_path)

    def _start_scan(self) -> None:
        evidence_dir = Path(self.input_edit.text()).expanduser()
        config_file = Path(self.config_edit.text()).expanduser() if self.config_edit.text() else None

        if not evidence_dir.exists() or not evidence_dir.is_dir():
            QMessageBox.warning(self, "Entrada inválida", "Selecione um diretório de evidências válido.")
            return

        if config_file and not config_file.exists():
            QMessageBox.warning(self, "Configuração inválida", "Selecione um arquivo de padrões válido.")
            return

        self.results_table.setRowCount(0)
        self.progress_bar.setValue(15)
        self.progress_bar.setFormat("Executando pipeline…")
        self.status_label.setText("Executando varredura (pipeline ainda em implementação)…")

        QMessageBox.information(
            self,
            "Varredura pendente",
            "A lógica de processamento completa será integrada quando as funcionalidades restantes estiverem prontas.\n"
            "Utilize os módulos individuais (scanner, extractor, regex) para testes aprofundados.",
        )

        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Aguardando execução…")
        self.status_label.setText("Pronto para iniciar.")

    def _open_patterns_file(self) -> None:
        if not DEFAULT_PATTERNS_PATH.exists():
            QMessageBox.information(self, "Arquivo ausente", "O arquivo config/patterns.json ainda não existe.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(DEFAULT_PATTERNS_PATH.resolve())))

    def _export_results(self) -> None:
        if self.results_table.rowCount() == 0:
            QMessageBox.information(self, "Sem dados", "Não há resultados para exportar no momento.")
            return

        target, _ = QFileDialog.getSaveFileName(self, "Salvar resultados", filter="JSON (*.json)")
        if not target:
            return

        QMessageBox.information(
            self,
            "Exportação",
            f"Resultados seriam exportados para: {target}\n"
            "Integração final ocorrerá após conclusão do pipeline.",
        )

    # ------------------------------------------------------------- Helpers ---
    def populate_results(self, rows: List[ResultRow]) -> None:
        """Fill the results table with pre-collected rows (used in tests/demo)."""

        self.results_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(
                [row.source_file, row.pattern_type, row.match_value, row.internal_path, row.timestamp]
            ):
                self.results_table.setItem(row_index, column_index, QTableWidgetItem(value))

    # --------------------------------------------------------------- Entry ---


def run_gui() -> None:
    """Launch the PyQt5 application."""

    app = QApplication.instance() or QApplication(sys.argv)

    if APP_ICON_PATH.exists():
        icon = QIcon(str(APP_ICON_PATH.resolve()))
        app.setWindowIcon(icon)

    window = PrometheusWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_gui()
