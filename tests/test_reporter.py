"""Tests for the JSON reporter (F5)."""

from pathlib import Path
import json

from src.models import EvidenceMatch
from src.reporter import ResultReporter


def test_reporter_writes_matches(tmp_path: Path) -> None:
    reporter = ResultReporter(tmp_path / "outputs" / "results.json")
    match = EvidenceMatch(
        source_file="case.ufdr",
        internal_path="data/messages.db",
        pattern_type="Email",
        match_value="analyst@example.com",
        file_type="database",
    )

    reporter.add_match(match)
    reporter.write()

    output_path = tmp_path / "outputs" / "results.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload == [match.to_dict()]


def test_reporter_supports_multiple_matches(tmp_path: Path) -> None:
    reporter = ResultReporter(tmp_path / "results.json")
    matches = [
        EvidenceMatch(
            source_file="file1.ufdr",
            internal_path="db/main.db",
            pattern_type="CPF",
            match_value="123.456.789-00",
        ),
        EvidenceMatch(
            source_file="file2.ufdr",
            internal_path="report/report.html",
            pattern_type="Email",
            match_value="john@example.com",
            context="linha 42",
        ),
    ]

    reporter.extend_matches(matches)
    reporter.write()

    payload = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))

    assert payload == [match.to_dict() for match in matches]
