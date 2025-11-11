"""Reporter responsible for consolidating Prometheus results into JSON (F5)."""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Iterable, List

from .models import EvidenceMatch

logger = logging.getLogger(__name__)


class ResultReporter:
    """Collects matches and writes them to a consolidated JSON file."""

    def __init__(self, output_path: Path | str = Path("outputs/prometheus_results.json")) -> None:
        self._output_path = Path(output_path).expanduser()
        self._matches: List[EvidenceMatch] = []

    @property
    def output_path(self) -> Path:
        return self._output_path

    def add_match(self, match: EvidenceMatch) -> None:
        self._matches.append(match)

    def extend_matches(self, matches: Iterable[EvidenceMatch]) -> None:
        self._matches.extend(matches)

    def clear(self) -> None:
        self._matches.clear()

    def write(self) -> Path:
        """Write all collected matches to disk in JSON format.

        The write is performed atomically to avoid partially written files.
        """

        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [match.to_dict() for match in self._matches]

        with tempfile.NamedTemporaryFile("w", delete=False, dir=str(self._output_path.parent), encoding="utf-8") as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp.name)

        os.replace(tmp_path, self._output_path)
        logger.info("Wrote %d consolidated match(es) to %s", len(self._matches), self._output_path)
        return self._output_path
