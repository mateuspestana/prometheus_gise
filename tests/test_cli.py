"""Smoke tests for the CLI entry point (F7)."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from src import cli

runner = CliRunner()


def test_scan_command_fails_until_pipeline_ready(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    config_path = tmp_path / "patterns.json"
    config_path.write_text("{}")

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

    assert result.exit_code == 1
    assert "Pipeline execution still pending implementation" in result.stdout


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
    assert "Arquivo de configuração não encontrado" in result.stdout
