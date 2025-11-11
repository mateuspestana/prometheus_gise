"""Text extraction utilities for UFDR evidence files (F3.1)."""

import logging
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import BinaryIO, Iterator

logger = logging.getLogger(__name__)


class MissingDependencyError(RuntimeError):
    """Raised when an optional dependency required for extraction is missing."""


@dataclass(frozen=True)
class TextExtractionResult:
    """Normalized text extracted from an evidence file."""

    text: str
    engine: str


class TextExtractor:
    """Extract textual content using unstructured only."""

    def __init__(self) -> None:
        self._partition_fn = None

    def extract(self, stream: BinaryIO, *, source_name: str) -> TextExtractionResult:
        """Return extracted text from the provided binary stream."""

        suffix = Path(source_name).suffix or ".bin"
        with self._materialize_stream(stream, suffix=suffix) as temp_path:
            text = self._try_unstructured(temp_path)
            return TextExtractionResult(text=text, engine="unstructured")

    @contextmanager
    def _materialize_stream(self, stream: BinaryIO, *, suffix: str) -> Iterator[Path]:
        with NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            temp_path = Path(handle.name)
            if hasattr(stream, "seek"):
                try:
                    stream.seek(0)
                except (OSError, AttributeError):
                    logger.debug("Stream for %s is not seekable; proceeding from current position", suffix)
            shutil.copyfileobj(stream, handle)

        try:
            yield temp_path
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:  # pragma: no cover
                logger.debug("Temporary text file %s already removed", temp_path)

    def _try_unstructured(self, path: Path) -> str:
        try:
            partition = self._load_unstructured()
        except MissingDependencyError:
            return ""

        try:
            elements = partition(filename=str(path))
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("unstructured failed for %s: %s", path, exc)
            return ""

        texts = []
        for element in elements:
            text = getattr(element, "text", None)
            if isinstance(text, str) and text.strip():
                texts.append(text)
        return "\n".join(texts)

    def _load_unstructured(self):
        if self._partition_fn is not None:
            return self._partition_fn

        try:
            from unstructured.partition.auto import partition  # type: ignore[import]
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise MissingDependencyError(
                "O pacote 'unstructured' é necessário para extração textual."
            ) from exc

        self._partition_fn = partition
        return partition

