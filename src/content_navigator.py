"""High-level navigator orchestrating UFDR content ingestion (F3/F3.1)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Literal, Mapping

from .database_reader import UFDRDatabaseReader
from .extractor import UFDRExtractor, UFDRMember
from .text_extractor import MissingDependencyError, TextExtractor

logger = logging.getLogger(__name__)

TEXTUAL_EXTENSIONS = {
    ".txt",
    ".csv",
    ".tsv",
    ".json",
    ".xml",
    ".html",
    ".htm",
    ".md",
    ".rtf",
    ".pdf",
    ".eml",
    ".msg",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".ics",
    ".vcf",
    ".epub",
    ".odt",
    ".odp",
    ".ods",
    ".log",
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".heic",
    ".heif",
    ".tiff",
    ".tif",
    ".bmp",
    ".gif",
    ".webp",
}


@dataclass(frozen=True)
class EvidencePayload:
    """Resulting artifact produced by the navigator."""

    source_file: Path
    internal_path: str
    payload_type: Literal["database_row", "text"]
    file_type: str
    content: Mapping[str, str] | str
    metadata: Mapping[str, object]
    modified: datetime | None


class UFDRContentNavigator:
    """Coordinate ingestion of UFDR content, prioritizing databases."""

    def __init__(self, ufdr_path: Path | str) -> None:
        self._extractor = UFDRExtractor(ufdr_path)
        self._database_reader = UFDRDatabaseReader(self._extractor)
        self._text_extractor = TextExtractor()

    def collect_payloads(self) -> Iterator[EvidencePayload]:
        """Yield structured payloads from an UFDR archive."""

        members = list(self._extractor.iter_members())
        database_members = [member for member in members if self._is_database(member)]

        if database_members:
            logger.info(
                "Processando %d banco(s) de dados em %s",
                len(database_members),
                self._extractor.ufdr_path,
            )
            for member in database_members:
                yield from self._collect_database_rows(member)
            return

        textual_members = [
            member
            for member in members
            if not member.is_dir and self._is_textual(member)
        ]

        if not textual_members:
            logger.info("Nenhum banco de dados ou arquivo textual identificado em %s", self._extractor.ufdr_path)
            return

        logger.info(
            "Nenhum banco de dados encontrado; processando %d arquivos textuais/imagens em %s",
            len(textual_members),
            self._extractor.ufdr_path,
        )
        for member in textual_members:
            payload = self._collect_text_payload(member)
            if payload is not None and payload.content:
                yield payload

    def _collect_database_rows(self, member: UFDRMember) -> Iterator[EvidencePayload]:
        for row in self._database_reader.iter_rows(member):
            yield EvidencePayload(
                source_file=row.source_file,
                internal_path=row.internal_path,
                payload_type="database_row",
                file_type="database",
                content=row.values,
                metadata={
                    "table": row.table,
                    "row_index": row.row_index,
                },
                modified=member.modified,
            )

    def _collect_text_payload(self, member: UFDRMember) -> EvidencePayload | None:
        try:
            with self._extractor.open_member(member.name) as stream:
                result = self._text_extractor.extract(stream, source_name=member.name)
        except MissingDependencyError as exc:
            logger.warning("Dependência ausente ao processar %s: %s", member.name, exc)
            return None
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Falha ao extrair texto de %s: %s", member.name, exc)
            return None

        if not result.text.strip():
            logger.debug("Arquivo %s não produziu texto relevante", member.name)
            return None

        return EvidencePayload(
            source_file=self._extractor.ufdr_path,
            internal_path=member.name,
            payload_type="text",
            file_type=self._guess_file_type(member),
            content=result.text,
            metadata={"engine": result.engine},
            modified=member.modified,
        )

    @staticmethod
    def _is_database(member: UFDRMember) -> bool:
        suffix = Path(member.name).suffix.lower()
        return not member.is_dir and suffix in {".db", ".sqlite", ".sqlite3", ".s3db"}

    @staticmethod
    def _is_textual(member: UFDRMember) -> bool:
        suffix = Path(member.name).suffix.lower()
        return suffix in TEXTUAL_EXTENSIONS or suffix in IMAGE_EXTENSIONS

    @staticmethod
    def _guess_file_type(member: UFDRMember) -> str:
        suffix = Path(member.name).suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            return "image"
        if suffix in TEXTUAL_EXTENSIONS:
            if suffix in {".pdf", ".doc", ".docx", ".ppt", ".pptx"}:
                return "document"
            if suffix in {".xls", ".xlsx", ".ods"}:
                return "spreadsheet"
            if suffix in {".eml", ".msg"}:
                return "email"
            if suffix in {".ics"}:
                return "calendar"
            if suffix in {".vcf"}:
                return "contact"
            return "text"
        return "binary"
