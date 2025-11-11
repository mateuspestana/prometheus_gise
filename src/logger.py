"""Centralized logging utilities with resilience helpers (F9/F10)."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Iterable, List, TypeVar

T = TypeVar("T")

LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
DEFAULT_LOG_PATH = Path("outputs/logs/scan.log")


def configure_logging(*, verbose: bool = False, log_path: Path | str = DEFAULT_LOG_PATH) -> logging.Logger:
    """Configure the Prometheus logger with file + console handlers."""

    log_path = Path(log_path).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("prometheus")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    file_handler = RotatingFileHandler(log_path, maxBytes=1_048_576, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.debug("Logging configured. verbose=%s log_path=%s", verbose, log_path)
    return logger


def get_logger() -> logging.Logger:
    """Return the Prometheus logger (configure it first)."""

    return logging.getLogger("prometheus")


def execute_with_resilience(
    items: Iterable[T],
    *,
    action: Callable[[T], None],
    on_error: Callable[[T, Exception], None] | None = None,
) -> List[T]:
    """Execute *action* for each item, logging errors and returning failed items."""

    logger = get_logger()
    failures: List[T] = []
    for item in items:
        try:
            action(item)
        except Exception as exc:  # pragma: no cover - defensive path tested separately
            failures.append(item)
            if on_error:
                on_error(item, exc)
            logger.exception("Falha ao processar %s", item)
    return failures
