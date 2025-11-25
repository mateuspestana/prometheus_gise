"""Smoke tests for the CLI entry point (F7)."""

from pathlib import Path
import re

import pytest
import typer
from typer.testing import CliRunner

from src import cli

_typer_version = tuple(int(part) for part in typer.__version__.split(".")[:2])
if _typer_version < (0, 10):  # pragma: no cover - compat com Typer legado
    pytest.skip("Typer < 0.10 não suporta os testes atuais da CLI", allow_module_level=True)

runner = CliRunner()


ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(value: str) -> str:
    return ANSI_PATTERN.sub("", value)


def test_scan_command_runs_pipeline_successfully(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    config_path = tmp_path / "patterns.json"
    config_path.write_text(
        '{"patterns": [{"name": "dummy", "pattern": "teste", "flags": ""}]}',
        encoding="utf-8",
    )

    output_path = tmp_path / "results.json"

    result = runner.invoke(
        cli.app,
        [
            "scan",
            "--input",
            str(input_dir),
            "--config",
            str(config_path),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "[]"


def test_scan_command_errors_when_config_missing(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    missing_config = tmp_path / "missing.json"

    result = runner.invoke(
        cli.app,
        [
            "scan",
            "--input",
            str(input_dir),
            "--config",
            str(missing_config),
        ],
    )

    assert result.exit_code != 0
    error_text = strip_ansi(result.stderr)
    assert "Arquivo de configuração não encontrado" in error_text
