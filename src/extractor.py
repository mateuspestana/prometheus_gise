"""UFDR extractor module implementing PRD requirement F2.

Handles UFDR packages as ZipFile archives to enumerate and extract their contents.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence
from zipfile import BadZipFile, ZipFile

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UFDRMember:
    """Metadata for a single member inside an UFDR archive."""

    name: str
    size: int
    compressed_size: int
    is_dir: bool
    modified: datetime | None


class UFDRExtractor:
    """Open and interact with UFDR (zip) evidence files."""

    def __init__(self, ufdr_path: Path | str, *, encoding: str = "utf-8") -> None:
        self.ufdr_path = Path(ufdr_path).expanduser()
        self.encoding = encoding

    def validate_source(self) -> None:
        """Ensure the UFDR source file exists and can be read."""

        if not self.ufdr_path.exists():
            raise FileNotFoundError(f"UFDR file '{self.ufdr_path}' does not exist")

        if not self.ufdr_path.is_file():
            raise IsADirectoryError(f"UFDR path '{self.ufdr_path}' is not a file")

    def iter_members(self) -> Iterator[UFDRMember]:
        """Yield metadata for every member contained in the UFDR archive."""

        self.validate_source()

        try:
            with ZipFile(self.ufdr_path) as archive:
                for info in archive.infolist():
                    modified = None
                    try:
                        modified = datetime(*info.date_time)
                    except (TypeError, ValueError):
                        logger.debug("Member %s missing valid timestamp", info.filename)

                    yield UFDRMember(
                        name=info.filename,
                        size=info.file_size,
                        compressed_size=info.compress_size,
                        is_dir=info.is_dir(),
                        modified=modified,
                    )
        except BadZipFile as exc:
            logger.error("File %s is not a valid UFDR/zip archive", self.ufdr_path)
            raise

    def list_members(self) -> List[UFDRMember]:
        """Return all members as a list."""

        members = list(self.iter_members())
        logger.info("Indexed %d entries in %s", len(members), self.ufdr_path)
        return members

    def extract_all(self, destination: Path | str) -> List[Path]:
        """Extract the entire UFDR archive to the given destination directory."""

        self.validate_source()
        destination_path = Path(destination).expanduser()
        destination_path.mkdir(parents=True, exist_ok=True)

        extracted: List[Path] = []
        try:
            with ZipFile(self.ufdr_path) as archive:
                for member in archive.infolist():
                    archive.extract(member, path=destination_path)
                    extracted.append(destination_path / member.filename)
        except BadZipFile:
            logger.error("Failed to extract invalid UFDR archive %s", self.ufdr_path)
            raise

        return extracted

    def extract_selected(self, destination: Path | str, members: Sequence[str]) -> List[Path]:
        """Extract only specific members from the archive."""

        if not members:
            return []

        self.validate_source()
        destination_path = Path(destination).expanduser()
        destination_path.mkdir(parents=True, exist_ok=True)

        extracted: List[Path] = []
        try:
            with ZipFile(self.ufdr_path) as archive:
                for name in members:
                    archive.extract(name, path=destination_path)
                    extracted.append(destination_path / name)
        except BadZipFile:
            logger.error("Failed to extract members from invalid UFDR archive %s", self.ufdr_path)
            raise

        return extracted


def list_ufdr_members(ufdr_path: Path | str) -> List[UFDRMember]:
    """Convenience function that returns metadata for every UFDR member."""

    extractor = UFDRExtractor(ufdr_path)
    return extractor.list_members()
