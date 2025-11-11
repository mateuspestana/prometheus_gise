"""Integration tests for the full Prometheus pipeline (F10)."""

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from src.logger import configure_logging
from src.main import run_pipeline
from src.text_extractor import TextExtractionResult


def _write_patterns(path: Path) -> None:
    data = {"Email": "[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\\.[A-Za-z0-9-.]+"}
    path.write_text(json.dumps(data), encoding="utf-8")


def test_run_pipeline_generates_results(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class DummyTextExtractor:
        def __init__(self, *args, **kwargs):
            pass

        def extract(self, stream, *, source_name: str) -> TextExtractionResult:
            raw = stream.read()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = ""
            return TextExtractionResult(text=text, engine="dummy")

    monkeypatch.setattr("src.content_navigator.TextExtractor", DummyTextExtractor)

    input_dir = tmp_path / "evidencias"
    input_dir.mkdir()

    valid = input_dir / "sample.ufdr"
    with ZipFile(valid, "w") as archive:
        archive.writestr("reports/report.txt", "Contato: analista@example.com")

    broken = input_dir / "corrompido.ufdr"
    broken.write_bytes(b"not a zip file")

    config_path = tmp_path / "patterns.json"
    _write_patterns(config_path)

    output_path = tmp_path / "outputs" / "prometheus_results.json"
    log_path = tmp_path / "logs" / "scan.log"
    configure_logging(verbose=False, log_path=log_path)

    summary = run_pipeline(input_dir=input_dir, config_path=config_path, output_path=output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload) == 1
    record = payload[0]
    assert record["pattern_type"] == "Email"
    assert record["match_value"] == "analista@example.com"

    assert summary["processed"] == 2
    assert len(summary["failures"]) == 1
    assert "corrompido.ufdr" in summary["failures"][0]
    assert summary["matches"] == 1
    assert Path(summary["output"]) == output_path

    assert log_path.exists()
    log_text = log_path.read_text(encoding="utf-8")
    assert "corrompido.ufdr" in log_text
