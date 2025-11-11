"""Data models for consolidated Prometheus results."""

from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class EvidenceMatch:
    """Representation of a single consolidated evidence match."""

    source_file: str
    internal_path: str
    pattern_type: str
    match_value: str
    file_type: Optional[str] = None
    context: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        payload = asdict(self)
        # remove keys with None values to keep output compact
        return {key: value for key, value in payload.items() if value is not None}
