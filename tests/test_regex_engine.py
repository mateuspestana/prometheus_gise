"""Unit tests for the regex engine (F4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.regex_engine import RegexEngine


def get_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "patterns.json"


def test_engine_loads_patterns_from_config(tmp_path: Path) -> None:
    config_path = tmp_path / "patterns.json"
    config_path.write_text('{"CPF": "\\\\d{11}"}', encoding="utf-8")

    engine = RegexEngine.from_config(config_path)

    assert len(engine.patterns) == 1
    assert engine.patterns[0].name == "CPF"


def test_scan_text_returns_matches() -> None:
    engine = RegexEngine.from_config(get_config_path())
    text = "CPF: 123.456.789-00 e email teste@dominio.com"

    matches = engine.scan_text(text)
    names = {match.pattern.name for match in matches}

    assert {"CPF", "Email"}.issubset(names)

    cpf_match = next(match for match in matches if match.pattern.name == "CPF")
    assert cpf_match.value == "123.456.789-00"
    assert "CPF" in cpf_match.context


def test_scan_table_provides_location_metadata() -> None:
    engine = RegexEngine.from_config(get_config_path())

    rows = [
        {"colA": "sem dados"},
        {"colA": "Email contato@exemplo.com"},
    ]

    matches = engine.scan_table(rows)

    assert len(matches) == 1
    match = matches[0]
    assert match.pattern.name == "Email"
    assert match.location == "row=1;column=colA"
