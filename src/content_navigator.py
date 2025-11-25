"""High-level navigator orchestrating UFDR content ingestion (F3/F6)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator, Literal, Mapping, Sequence

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


@dataclass(frozen=True)
class TextualProgressEvent:
    """Progress information for textual extraction inside an UFDR."""

    member: UFDRMember
    index: int
    total: int
    stage: Literal["start", "done", "skip"]
    engine: str | None = None


@dataclass(frozen=True)
class NavigatorPlan:
    """Partition of UFDR members for processing."""

    members: Sequence[UFDRMember]
    database_members: Sequence[UFDRMember]
    textual_members: Sequence[UFDRMember]


class UFDRContentNavigator:
    """Coordinate ingestion of UFDR content, prioritizing databases."""

    def __init__(self, ufdr_path: Path | str) -> None:
        self._extractor = UFDRExtractor(ufdr_path)
        self._database_reader = UFDRDatabaseReader(self._extractor)
        self._text_extractor = TextExtractor()

    def plan_processing(self) -> NavigatorPlan:
        """Return the members partitioned by type for progress planning."""

        members = list(self._extractor.iter_members())
        database_members = [member for member in members if self._is_database(member)]
        textual_members = [
            member
            for member in members
            if not member.is_dir and self._is_textual(member)
        ]
        return NavigatorPlan(
            members=members,
            database_members=database_members,
            textual_members=textual_members,
        )

    def collect_payloads(
        self,
        plan: NavigatorPlan | None = None,
        progress_callback: Callable[[TextualProgressEvent], None] | None = None,
    ) -> Iterator[EvidencePayload]:
        """Yield structured payloads from an UFDR archive."""

        plan = plan or self.plan_processing()
        database_members = plan.database_members
        textual_members = plan.textual_members

        if database_members:
            logger.info(
                "Processando %d banco(s) de dados em %s",
                len(database_members),
                self._extractor.ufdr_path,
            )
            for member in database_members:
                yield from self._collect_database_rows(member)

        if textual_members:
            if database_members:
                logger.info(
                    "Processando também %d arquivo(s) textual(is)/imagem(ns) em %s",
                    len(textual_members),
                    self._extractor.ufdr_path,
                )
            else:
                logger.info(
                    "Nenhum banco de dados encontrado; processando %d arquivos textuais/imagens em %s",
                    len(textual_members),
                    self._extractor.ufdr_path,
                )

            total = len(textual_members)
            for index, member in enumerate(textual_members, start=1):
                if progress_callback:
                    progress_callback(
                        TextualProgressEvent(
                            member=member,
                            index=index,
                            total=total,
                            stage="start",
                            engine=None,
                        )
                    )

                payload_result = self._collect_text_payload(member)
                if payload_result is not None:
                    payload, engine = payload_result
                    if progress_callback:
                        progress_callback(
                            TextualProgressEvent(
                                member=member,
                                index=index,
                                total=total,
                                stage="done",
                                engine=engine,
                            )
                        )
                    yield payload
                else:
                    if progress_callback:
                        progress_callback(
                            TextualProgressEvent(
                                member=member,
                                index=index,
                                total=total,
                                stage="skip",
                                engine=None,
                            )
                        )
        elif not database_members:
            logger.info("Nenhum banco de dados ou arquivo textual identificado em %s", self._extractor.ufdr_path)

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

    def _collect_text_payload(self, member: UFDRMember) -> tuple[EvidencePayload, str] | None:
        try:
            logger.debug("Extraindo texto de %s", member.name)
            with self._extractor.open_member(member.name) as stream:
                result = self._text_extractor.extract(stream, source_name=member.name)
            logger.debug("Extração concluída para %s (engine: %s, tamanho: %d)", member.name, result.engine, len(result.text))
        except MissingDependencyError as exc:
            logger.warning("Dependência ausente ao processar %s: %s", member.name, exc)
            return None
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Falha ao extrair texto de %s: %s", member.name, exc, exc_info=True)
            return None

        if not result.text.strip():
            logger.debug("Arquivo %s não produziu texto relevante", member.name)
            return None

        payload = EvidencePayload(
            source_file=self._extractor.ufdr_path,
            internal_path=member.name,
            payload_type="text",
            file_type=self._guess_file_type(member),
            content=result.text,
            metadata={"engine": result.engine},
            modified=member.modified,
        )
        return payload, result.engine

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
