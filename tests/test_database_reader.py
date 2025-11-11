"""Tests for UFDR database and text ingestion (F3/F3.1)."""

from __future__ import annotations

import io
import sqlite3
from pathlib import Path
from zipfile import ZipFile

import pytest

from src.content_navigator import UFDRContentNavigator, TextExtractor
from src.database_reader import UFDRDatabaseReader
from src.text_extractor import TextExtractionResult
from src.extractor import UFDRExtractor


def _build_sqlite_file(db_path: Path) -> None:
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, body TEXT)")
    connection.execute("INSERT INTO messages (body) VALUES ('primeira mensagem')")
    connection.execute("INSERT INTO messages (body) VALUES ('segunda mensagem')")
    connection.commit()
    connection.close()


def _create_ufdr_with_database(tmp_path: Path) -> Path:
    db_file = tmp_path / "messages.db"
    _build_sqlite_file(db_file)

    archive_path = tmp_path / "archive.ufdr"
    with ZipFile(archive_path, "w") as archive:
        archive.write(db_file, arcname="data/messages.db")
    return archive_path


def _create_ufdr_with_text(tmp_path: Path, file_name: str, content: str) -> Path:
    archive_path = tmp_path / "archive.ufdr"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(file_name, content)
    return archive_path


def test_database_reader_returns_rows(tmp_path: Path) -> None:
    archive_path = _create_ufdr_with_database(tmp_path)

    extractor = UFDRExtractor(archive_path)
    reader = UFDRDatabaseReader(extractor)
    databases = list(reader.list_databases())

    assert len(databases) == 1
    rows = list(reader.iter_rows(databases[0]))
    assert len(rows) == 2

    first_row = rows[0]
    assert first_row.table == "messages"
    assert first_row.values["body"] == "primeira mensagem"


def test_content_navigator_prioritizes_databases(tmp_path: Path) -> None:
    archive_path = _create_ufdr_with_database(tmp_path)
    navigator = UFDRContentNavigator(archive_path)

    payloads = list(navigator.collect_payloads())
    assert len(payloads) == 2
    assert all(payload.payload_type == "database_row" for payload in payloads)
    assert payloads[0].metadata["table"] == "messages"
    assert payloads[0].file_type == "database"


def test_content_navigator_fallback_to_text(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    archive_path = _create_ufdr_with_text(tmp_path, "report.txt", "conteúdo de teste")

    class DummyTextExtractor:
        def __init__(self, *args, **kwargs):
            pass

        def extract(self, stream, *, source_name: str):
            return TextExtractionResult(text="conteúdo extraído", engine="dummy")

    monkeypatch.setattr("src.content_navigator.TextExtractor", DummyTextExtractor)

    navigator = UFDRContentNavigator(archive_path)
    payloads = list(navigator.collect_payloads())

    assert len(payloads) == 1
    payload = payloads[0]
    assert payload.payload_type == "text"
    assert payload.content == "conteúdo extraído"
    assert payload.file_type == "text"


def test_text_extractor_prefers_unstructured(monkeypatch: pytest.MonkeyPatch) -> None:
    extractor = TextExtractor()

    monkeypatch.setattr(TextExtractor, "_try_unstructured", lambda self, path: "texto primário")

    stream = io.BytesIO(b"dados qualquer")
    result = extractor.extract(stream, source_name="documento.txt")

    assert result.engine == "unstructured"
    assert result.text == "texto primário"


def test_text_extractor_returns_empty_when_unstructured_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    extractor = TextExtractor()
    monkeypatch.setattr(TextExtractor, "_try_unstructured", lambda self, path: "")

    stream = io.BytesIO(b"dados qualquer")
    result = extractor.extract(stream, source_name="documento.pdf")

    assert result.engine == "unstructured"
    assert result.text == ""
