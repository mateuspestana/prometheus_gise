"""Utilities for creating forensic metadata-rich results (F6)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .content_navigator import EvidencePayload
from .models import EvidenceMatch
from .regex_engine import RegexMatch


def build_evidence_match(payload: EvidencePayload, regex_match: RegexMatch) -> EvidenceMatch:
    """Combine navigator payload and regex match into an EvidenceMatch."""

    source_file = Path(payload.source_file).name
    internal_path = payload.internal_path
    file_type = payload.file_type
    pattern_type = regex_match.pattern.name
    match_value = regex_match.value
    context = _compose_context(payload, regex_match)
    timestamp = _format_timestamp(payload.modified)

    return EvidenceMatch(
        source_file=source_file,
        internal_path=internal_path,
        file_type=file_type,
        pattern_type=pattern_type,
        match_value=match_value,
        context=context,
        timestamp=timestamp,
    )


def _compose_context(payload: EvidencePayload, regex_match: RegexMatch) -> Optional[str]:
    pieces: list[str] = []

    # Add structural hints for database rows
    if payload.payload_type == "database_row":
        table = payload.metadata.get("table")
        row_index = payload.metadata.get("row_index")
        if table:
            pieces.append(f"tabela {table}")
        if row_index is not None:
            pieces.append(f"linha {row_index}")

    # Append regex location metadata when available
    if regex_match.location:
        pieces.append(regex_match.location)

    # Finally include textual context window
    if regex_match.context:
        pieces.append(regex_match.context.strip())

    if not pieces:
        return None
    return " | ".join(pieces)


def _format_timestamp(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
