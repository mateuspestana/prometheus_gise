"""Database ingestion helpers for UFDR packages (F3)."""

from __future__ import annotations

import logging
import shutil
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, Mapping
from tempfile import NamedTemporaryFile

from src.extractor import UFDRExtractor, UFDRMember

logger = logging.getLogger(__name__)

SQLITE_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".s3db"}


@dataclass(frozen=True)
class DatabaseRow:
    """Single row extracted from a SQLite database inside a UFDR package."""

    source_file: Path
    internal_path: str
    table: str
    row_index: int
    values: Mapping[str, str]


class UFDRDatabaseReader:
    """High-level helper to enumerate and read SQLite databases from UFDR archives."""

    def __init__(self, extractor: UFDRExtractor) -> None:
        self._extractor = extractor

    def list_databases(self) -> Iterator[UFDRMember]:
        """Yield UFDR members that represent SQLite databases."""

        for member in self._extractor.iter_members():
            if member.is_dir:
                continue
            suffix = Path(member.name).suffix.lower()
            if suffix in SQLITE_EXTENSIONS:
                logger.debug("Identified SQLite database %s inside %s", member.name, self._extractor.ufdr_path)
                yield member

    def iter_rows(self, member: UFDRMember) -> Iterator[DatabaseRow]:
        """Iterate through every row contained in a SQLite database member."""

        with self._materialize_member(member) as sqlite_path:
            logger.debug("Materialized database %s to %s", member.name, sqlite_path)
            with self._open_connection(sqlite_path) as connection:
                tables = self._list_tables(connection)
                for table_name in tables:
                    columns = self._list_columns(connection, table_name)
                    query = f"""SELECT * FROM {self._quote_identifier(table_name)}"""
                    cursor = connection.execute(query)
                    for row_index, row in enumerate(cursor):
                        casted = self._normalize_row(dict(zip(columns, row)))
                        yield DatabaseRow(
                            source_file=self._extractor.ufdr_path,
                            internal_path=member.name,
                            table=table_name,
                            row_index=row_index,
                            values=casted,
                        )

    @contextmanager
    def _materialize_member(self, member: UFDRMember) -> Iterator[Path]:
        """Copy a UFDR member to a temporary file and yield its path."""

        suffix = Path(member.name).suffix or ".db"
        with NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            temp_path = Path(handle.name)
            with self._extractor.open_member(member.name) as member_stream:
                shutil.copyfileobj(member_stream, handle)

        try:
            yield temp_path
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:  # pragma: no cover - defensive
                logger.debug("Temporary database file %s already removed", temp_path)

    @contextmanager
    def _open_connection(self, sqlite_path: Path) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def _list_tables(self, connection: sqlite3.Connection) -> Iterator[str]:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        for row in cursor.fetchall():
            table = row["name"]
            if isinstance(table, str):
                yield table

    def _list_columns(self, connection: sqlite3.Connection, table_name: str) -> Iterator[str]:
        pragma = f"PRAGMA table_info({self._quote_identifier(table_name)})"
        cursor = connection.execute(pragma)
        for row in cursor.fetchall():
            column = row["name"]
            if isinstance(column, str):
                yield column

    def _normalize_row(self, raw_row: Dict[str, object]) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for key, value in raw_row.items():
            normalized[key] = self._normalize_value(value)
        return normalized

    @staticmethod
    def _normalize_value(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError:
                return value.decode("latin-1", errors="ignore")
        return str(value)

    @staticmethod
    def _quote_identifier(name: str) -> str:
        escaped = name.replace('"', '""')
        return f'"{escaped}"'


