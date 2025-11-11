"""Tests for logging utilities (F9)."""

import logging
from pathlib import Path

import pytest

from src.logger import configure_logging, execute_with_resilience, get_logger


def test_configure_logging_creates_file(tmp_path: Path) -> None:
    log_path = tmp_path / "outputs" / "logs" / "scan.log"
    logger = configure_logging(verbose=False, log_path=log_path)

    logger.info("mensagem de teste")
    logger.handlers[0].flush()  # ensure file handler writes data

    assert log_path.exists()
    assert "mensagem de teste" in log_path.read_text(encoding="utf-8")


def test_execute_with_resilience_logs_errors(tmp_path: Path) -> None:
    configure_logging(verbose=False, log_path=tmp_path / "scan.log")
    logger = get_logger()

    processed: list[str] = []

    def action(item: str) -> None:
        if item == "boom":
            raise ValueError("falha")
        processed.append(item)

    failures = execute_with_resilience(["ok", "boom", "ok2"], action=action)

    assert processed == ["ok", "ok2"]
    assert failures == ["boom"]

    logger.handlers[0].flush()
    log_text = (tmp_path / "scan.log").read_text(encoding="utf-8")
    assert "falha" in log_text
