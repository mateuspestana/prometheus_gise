"""Unit tests for UFDRExtractor (F2)."""

from pathlib import Path
from zipfile import ZipFile

import pytest

from src.extractor import UFDRExtractor, list_ufdr_members


def create_sample_ufdr(tmp_path: Path) -> Path:
    archive_path = tmp_path / "sample.ufdr"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("data/messages.db", "binary content")
        archive.writestr("reports/report.html", "<html></html>")
    return archive_path


def test_list_members_returns_metadata(tmp_path: Path) -> None:
    archive_path = create_sample_ufdr(tmp_path)

    members = list_ufdr_members(archive_path)

    names = {member.name for member in members}
    assert names == {"data/messages.db", "reports/report.html"}
    assert all(member.size > 0 for member in members)


def test_extract_selected(tmp_path: Path) -> None:
    archive_path = create_sample_ufdr(tmp_path)
    destination = tmp_path / "out"

    extractor = UFDRExtractor(archive_path)
    extracted = extractor.extract_selected(destination, ["data/messages.db"])

    assert extracted == [destination / "data/messages.db"]
    assert extracted[0].exists()


def test_missing_source(tmp_path: Path) -> None:
    extractor = UFDRExtractor(tmp_path / "missing.ufdr")
    with pytest.raises(FileNotFoundError):
        extractor.list_members()
