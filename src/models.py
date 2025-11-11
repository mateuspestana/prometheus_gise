"""Core data models for Prometheus forensic results (F5/F6)."""

from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class EvidenceMatch:
    """Normalized representation of a consolidated match."""

    source_file: str
    internal_path: str
    pattern_type: str
    match_value: str
    file_type: Optional[str] = None
    context: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}
