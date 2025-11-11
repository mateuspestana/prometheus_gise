"""Application entry points orchestrating Prometheus workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from .content_navigator import EvidencePayload, UFDRContentNavigator
from .forensics import build_evidence_match
from .logger import execute_with_resilience, get_logger
from .models import EvidenceMatch
from .regex_engine import RegexEngine
from .reporter import ResultReporter
from .scanner import UFDRScanner


def run_pipeline(
    input_dir: Path,
    config_path: Path,
    output_path: Path,
) -> Dict[str, object]:
    """Execute the complete Prometheus processing pipeline (F10)."""

    logger = get_logger()
    scanner = UFDRScanner(input_dir)
    reporter = ResultReporter(output_path)
    regex_engine = RegexEngine.from_config(config_path)

    logger.info("Iniciando varredura em %s", input_dir)
    scan_results = scanner.scan()
    ufdr_paths = [result.path for result in scan_results]
    logger.info("%d arquivo(s) .ufdr encontrado(s)", len(ufdr_paths))

    def process_file(path: Path) -> None:
        navigator = UFDRContentNavigator(path)
        for payload in navigator.collect_payloads():
            matches = _run_regex(regex_engine, payload)
            reporter.extend_matches(matches)

    failures = execute_with_resilience(ufdr_paths, action=process_file)

    output = reporter.write()
    logger.info("Matches: %d | Saída: %s", reporter.match_count, output)
    if failures:
        logger.warning("%d arquivo(s) falharam: %s", len(failures), ", ".join(path.name for path in failures))

    return {
        "processed": len(ufdr_paths),
        "failures": [str(path) for path in failures],
        "matches": reporter.match_count,
        "output": str(output),
    }


def _run_regex(regex_engine: RegexEngine, payload: EvidencePayload) -> List[EvidenceMatch]:
    if payload.payload_type == "database_row":
        rows: Iterable[Dict[str, str]] = [dict(payload.content)]  # shallow copy to keep Mapping contract
        matches = regex_engine.scan_table(rows)
    else:
        matches = regex_engine.scan_text(str(payload.content))
    return [build_evidence_match(payload, match) for match in matches]
