"""Regex engine responsible for executing pattern searches (F4)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence

logger = logging.getLogger(__name__)


_FLAG_TABLE: Mapping[str, int] = {
    "ignorecase": re.IGNORECASE,
    "multiline": re.MULTILINE,
    "dotall": re.DOTALL,
    "unicode": re.UNICODE,
}


@dataclass(frozen=True)
class RegexPattern:
    """Represents a single regex pattern compiled for fast reuse."""

    name: str
    expression: str
    flags: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "_compiled", re.compile(self.expression, self.flags))

    @property
    def compiled(self) -> re.Pattern[str]:
        return self._compiled

    def finditer(self, text: str) -> Iterator[re.Match[str]]:
        return self._compiled.finditer(text)


@dataclass(frozen=True)
class RegexMatch:
    """Container with a single match result and surrounding metadata."""

    pattern: RegexPattern
    value: str
    start: int
    end: int
    context: str
    location: Optional[str] = None

    def with_location(self, location: str) -> "RegexMatch":
        return replace(self, location=location)


class RegexEngine:
    """Executes compiled patterns against text fragments or tabular data."""

    def __init__(self, patterns: Sequence[RegexPattern]) -> None:
        if not patterns:
            raise ValueError("RegexEngine requires at least one pattern")
        self._patterns = list(patterns)

    @property
    def patterns(self) -> Sequence[RegexPattern]:
        return tuple(self._patterns)

    @classmethod
    def from_config(
        cls,
        config_path: Path | str,
        *,
        default_flags: int = re.IGNORECASE,
    ) -> "RegexEngine":
        config_path = Path(config_path)
        with config_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        patterns = _load_patterns(payload, default_flags=default_flags)
        logger.debug("Loaded %d regex patterns from %s", len(patterns), config_path)
        return cls(patterns)

    def scan_text(self, text: str, *, context_window: int = 40) -> List[RegexMatch]:
        matches: List[RegexMatch] = []
        for pattern in self._patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                context = _extract_context(text, start, end, context_window)
                matches.append(
                    RegexMatch(
                        pattern=pattern,
                        value=match.group(0),
                        start=start,
                        end=end,
                        context=context,
                    )
                )
        return matches

    def scan_table(
        self,
        rows: Iterable[Mapping[str, str]],
        *,
        columns: Optional[Sequence[str]] = None,
        context_window: int = 40,
    ) -> List[RegexMatch]:
        matches: List[RegexMatch] = []
        for row_index, row in enumerate(rows):
            iterable = (
                ((column, row.get(column, "")) for column in columns)
                if columns
                else row.items()
            )
            for column_name, value in iterable:
                if not isinstance(value, str):
                    continue
                for match in self.scan_text(value, context_window=context_window):
                    location = f"row={row_index};column={column_name}"
                    matches.append(match.with_location(location))
        return matches


def _extract_context(text: str, start: int, end: int, window: int) -> str:
    left = max(start - window, 0)
    right = min(end + window, len(text))
    return text[left:right]


def _load_patterns(payload: object, *, default_flags: int) -> List[RegexPattern]:
    if isinstance(payload, Mapping):
        if "patterns" in payload and isinstance(payload["patterns"], list):
            return [_pattern_from_mapping(entry, default_flags=default_flags) for entry in payload["patterns"]]
        if all(isinstance(value, str) for value in payload.values()):
            return [RegexPattern(name=key, expression=value, flags=default_flags) for key, value in payload.items()]
    if isinstance(payload, list):
        return [_pattern_from_mapping(entry, default_flags=default_flags) for entry in payload]
    raise ValueError("Unsupported patterns configuration structure")


def _pattern_from_mapping(entry: MutableMapping[str, object], *, default_flags: int) -> RegexPattern:
    if not isinstance(entry, Mapping):
        raise ValueError("Pattern entries must be mappings")

    name = entry.get("name")
    expression = entry.get("regex") or entry.get("pattern")
    if not isinstance(name, str) or not isinstance(expression, str):
        raise ValueError("Pattern entries require 'name' and 'regex' fields")

    raw_flags = entry.get("flags") or entry.get("options")
    flags = default_flags
    if isinstance(raw_flags, str):
        flags = _FLAG_TABLE.get(raw_flags.lower(), default_flags)
    elif isinstance(raw_flags, (list, tuple)):
        flags = 0
        for flag_name in raw_flags:
            if not isinstance(flag_name, str):
                raise ValueError("Regex flag names must be strings")
            key = flag_name.lower()
            if key not in _FLAG_TABLE:
                raise ValueError(f"Unsupported regex flag '{flag_name}'")
            flags |= _FLAG_TABLE[key]
    elif raw_flags is not None:
        raise ValueError("Regex flags must be a string or list of strings")

    return RegexPattern(name=name, expression=expression, flags=flags or default_flags)
