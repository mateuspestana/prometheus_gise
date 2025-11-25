"""Reporter responsible for consolidating Prometheus results into JSON (F5/F10)."""

import csv
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Iterable, List, Sequence

from .models import EvidenceMatch

logger = logging.getLogger(__name__)


class ResultReporter:
    """Collects matches and writes them to consolidated files."""

    def __init__(
        self,
        output_path: Path | str = Path("outputs/prometheus_results.json"),
        *,
        csv_output_path: Path | str | None = None,
    ) -> None:
        self._output_path = Path(output_path).expanduser()
        self._csv_output_path = (
            Path(csv_output_path).expanduser()
            if csv_output_path is not None
            else self._output_path.with_suffix(".csv")
        )
        self._matches: List[EvidenceMatch] = []

    @property
    def output_path(self) -> Path:
        return self._output_path

    @property
    def csv_output_path(self) -> Path:
        return self._csv_output_path

    @property
    def match_count(self) -> int:
        return len(self._matches)

    def add_match(self, match: EvidenceMatch) -> None:
        self._matches.append(match)

    def extend_matches(self, matches: Iterable[EvidenceMatch]) -> None:
        self._matches.extend(matches)

    def clear(self) -> None:
        self._matches.clear()

    def write(self) -> dict[str, Path]:
        """Write all collected matches to disk in JSON and CSV format."""

        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        json_path = self._write_json()
        csv_path = self._write_csv()
        logger.info(
            "Wrote %d consolidated match(es) to %s and %s",
            len(self._matches),
            json_path,
            csv_path,
        )
        return {"json": json_path, "csv": csv_path}

    def _write_json(self) -> Path:
        data = [match.to_dict() for match in self._matches]

        with tempfile.NamedTemporaryFile("w", delete=False, dir=str(self._output_path.parent), encoding="utf-8") as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp.name)

        os.replace(tmp_path, self._output_path)
        return self._output_path

    def _write_csv(self) -> Path:
        fieldnames: Sequence[str] = [
            "source_file",
            "internal_path",
            "pattern_type",
            "match_value",
            "file_type",
            "context",
            "timestamp",
        ]

        self._csv_output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=str(self._csv_output_path.parent), encoding="utf-8", newline="") as tmp:
            writer = csv.DictWriter(tmp, fieldnames=fieldnames)
            writer.writeheader()
            for match in self._matches:
                row = {key: getattr(match, key) for key in fieldnames}
                writer.writerow(row)
            tmp_path = Path(tmp.name)

        os.replace(tmp_path, self._csv_output_path)
        return self._csv_output_path
