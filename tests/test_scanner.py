"""Unit tests for the UFDRScanner (F1)."""

from pathlib import Path

import pytest

from src.scanner import UFDRScanner, find_ufdr_files


def test_scan_discovers_ufdr_files(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()

    (evidence_dir / "file1.ufdr").write_text("dummy")
    nested = evidence_dir / "nested"
    nested.mkdir()
    (nested / "file2.UFDR").write_text("dummy")
    (nested / "ignore.txt").write_text("not an ufdr")

    results = UFDRScanner(evidence_dir).scan()

    paths = {result.path.name for result in results}
    assert paths == {"file1.ufdr", "file2.UFDR"}


def test_find_ufdr_files_wrapper(tmp_path: Path) -> None:
    (tmp_path / "example.ufdr").write_text("dummy")
    files = find_ufdr_files(tmp_path)

    assert len(files) == 1
    assert files[0].name == "example.ufdr"


def test_invalid_root(tmp_path: Path) -> None:
    scanner = UFDRScanner(tmp_path / "missing")
    with pytest.raises(FileNotFoundError):
        list(scanner.iter_scan())
