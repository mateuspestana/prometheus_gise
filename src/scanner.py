"""Filesystem scanner responsible for locating UFDR evidence packages.

This module implements the product requirement F1 (Busca Recursiva).
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Iterable, Iterator, List

logger = logging.getLogger(__name__)

UFDR_EXTENSION = ".ufdr"


@dataclass(frozen=True)
class ScanResult:
    """Describes a single UFDR file discovered during a scan."""

    path: Path


class UFDRScanner:
    """Recursively searches for UFDR evidence files.

    Parameters
    ----------
    root : Path | str
        Root directory where the recursive search starts.
    follow_symlinks : bool, optional
        Whether to follow symbolic links while walking the filesystem.
    """

    def __init__(self, root: Path | str, *, follow_symlinks: bool = False) -> None:
        self.root = Path(root).expanduser()
        self.follow_symlinks = follow_symlinks

    def validate_root(self) -> None:
        """Validate scanner prerequisites before executing a scan."""

        if not self.root.exists():
            raise FileNotFoundError(f"Root path '{self.root}' does not exist")

        if not self.root.is_dir():
            raise NotADirectoryError(f"Root path '{self.root}' is not a directory")

    def scan(self) -> List[ScanResult]:
        """Run a recursive scan and return all discovered UFDR files."""

        results = list(self.iter_scan())
        logger.info("Found %d UFDR file(s) under %s", len(results), self.root)
        return results

    def iter_scan(self) -> Iterator[ScanResult]:
        """Yield scan results one by one, handling permission errors gracefully."""

        self.validate_root()

        def on_error(exc: OSError) -> None:
            logger.warning("Unable to access %s: %s", getattr(exc, "filename", "<unknown>"), exc)

        for directory, _, filenames in os.walk(self.root, onerror=on_error, followlinks=self.follow_symlinks):
            dir_path = Path(directory)
            for filename in filenames:
                if filename.lower().endswith(UFDR_EXTENSION):
                    file_path = dir_path / filename
                    logger.debug("Discovered UFDR file: %s", file_path)
                    yield ScanResult(path=file_path)

    @staticmethod
    def list_paths(results: Iterable[ScanResult]) -> List[Path]:
        """Convenience helper to get plain paths from ScanResult objects."""

        return [result.path for result in results]


def find_ufdr_files(root: Path | str, *, follow_symlinks: bool = False) -> List[Path]:
    """Public helper that returns a list of UFDR file paths under ``root``.

    This wrapper is intended for simpler call-sites that do not require the
    additional metadata exposed by :class:`UFDRScanner`.
    """

    scanner = UFDRScanner(root, follow_symlinks=follow_symlinks)
    return UFDRScanner.list_paths(scanner.iter_scan())
