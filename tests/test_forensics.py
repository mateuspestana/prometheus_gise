"""Tests for forensic metadata utilities (F6)."""

from datetime import datetime
from pathlib import Path

from src.content_navigator import EvidencePayload
from src.forensics import build_evidence_match
from src.models import EvidenceMatch
from src.regex_engine import RegexPattern, RegexMatch


def _make_regex_match(value: str, context: str = "context", location: str | None = None) -> RegexMatch:
    pattern = RegexPattern(name="Email", expression=".+")
    match = RegexMatch(pattern=pattern, value=value, start=0, end=len(value), context=context, location=location)
    return match


def test_build_match_for_database_row() -> None:
    payload = EvidencePayload(
        source_file=Path("case.ufdr"),
        internal_path="data/messages.db",
        payload_type="database_row",
        file_type="database",
        content={"col": "value"},
        metadata={"table": "contacts", "row_index": 12},
        modified=datetime(2025, 11, 3, 18, 12, 55),
    )

    regex_match = _make_regex_match("john@example.com", context="email content", location="row=12;column=email")
    evidence = build_evidence_match(payload, regex_match)

    assert evidence.source_file == "case.ufdr"
    assert evidence.internal_path == "data/messages.db"
    assert evidence.file_type == "database"
    assert evidence.pattern_type == "Email"
    assert evidence.match_value == "john@example.com"
    assert "tabela contacts" in evidence.context
    assert evidence.timestamp == "2025-11-03T18:12:55Z"


def test_build_match_for_text_payload_without_timestamp() -> None:
    payload = EvidencePayload(
        source_file=Path("case.ufdr"),
        internal_path="reports/report.html",
        payload_type="text",
        file_type="document",
        content="lorem ipsum",
        metadata={"engine": "plain-text"},
        modified=None,
    )
    regex_match = _make_regex_match("CPF 123", context="CPF encontrado")

    evidence = build_evidence_match(payload, regex_match)

    assert evidence.source_file == "case.ufdr"
    assert evidence.internal_path == "reports/report.html"
    assert evidence.file_type == "document"
    assert evidence.context == "CPF encontrado"
    assert evidence.timestamp is None
