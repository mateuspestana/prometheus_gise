"""Application entry points orchestring Prometheus workflows."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from src.content_navigator import EvidencePayload, UFDRContentNavigator
from src.forensics import build_evidence_match
from src.logger import execute_with_resilience, get_logger
from src.models import EvidenceMatch
from src.regex_engine import RegexEngine
from src.reporter import ResultReporter
from src.scanner import UFDRScanner


ProgressCallback = Callable[[Dict[str, object]], None]


def run_pipeline(
    input_dir: Path,
    config_path: Path,
    output_path: Path,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    allowed_extensions: Optional[set[str]] = None,
) -> Dict[str, object]:
    """Execute the complete Prometheus processing pipeline (F10)."""

    logger = get_logger()
    scanner = UFDRScanner(input_dir)
    
    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_path.parent
    output_stem = output_path.stem  # e.g., "prometheus_results"
    output_suffix = output_path.suffix  # e.g., ".json"
    
    # Create paths with timestamp
    json_path = output_dir / f"{output_stem}_{timestamp}{output_suffix}"
    csv_path = output_dir / f"{output_stem}_{timestamp}.csv"
    
    reporter = ResultReporter(json_path, csv_output_path=csv_path)
    regex_engine = RegexEngine.from_config(config_path)

    logger.info("Iniciando varredura em %s", input_dir)
    logger.debug("Configuração de padrões: %s", config_path)
    logger.debug("Arquivo de saída: %s", output_path)
    
    scan_results = scanner.scan()
    ufdr_paths = [result.path for result in scan_results]
    logger.info("%d arquivo(s) .ufdr encontrado(s)", len(ufdr_paths))
    
    # Log detalhado dos arquivos encontrados (sempre mostrar, não só em debug)
    if ufdr_paths:
        logger.info("Arquivos encontrados:")
        for idx, result in enumerate(scan_results, 1):
            logger.info("  [%d/%d] %s", idx, len(ufdr_paths), result.path)
    else:
        logger.warning("Nenhum arquivo .ufdr encontrado em %s", input_dir)

    def emit(event: Dict[str, object]) -> None:
        if progress_callback:
            progress_callback(event)

    def process_file(path: Path) -> None:
        navigator = UFDRContentNavigator(path, allowed_extensions=allowed_extensions)
        plan = navigator.plan_processing()
        emit(
            {
                "type": "ufdr-start",
                "path": str(path),
                "textual_total": len(plan.textual_members),
            }
        )

        def on_text_progress(event) -> None:
            emit(
                {
                    "type": "text-progress",
                    "path": str(path),
                    "member": event.member.name,
                    "index": event.index,
                    "total": event.total,
                    "stage": event.stage,
                    "engine": event.engine,
                }
            )

        for payload in navigator.collect_payloads(plan=plan, progress_callback=on_text_progress):
            matches = _run_regex(regex_engine, payload)
            reporter.extend_matches(matches)

        emit({"type": "ufdr-complete", "path": str(path)})

    failures = execute_with_resilience(ufdr_paths, action=process_file)

    outputs = reporter.write()
    logger.info(
        "Matches: %d | Saídas: JSON=%s CSV=%s",
        reporter.match_count,
        outputs["json"],
        outputs["csv"],
    )
    if failures:
        logger.warning("%d arquivo(s) falharam: %s", len(failures), ", ".join(path.name for path in failures))

    return {
        "processed": len(ufdr_paths),
        "failures": [str(path) for path in failures],
        "matches": reporter.match_count,
        "output": str(outputs["json"]),
        "csv_output": str(outputs["csv"]),
    }


def _run_regex(regex_engine: RegexEngine, payload: EvidencePayload) -> List[EvidenceMatch]:
    if payload.payload_type == "database_row":
        rows: Iterable[Dict[str, str]] = [dict(payload.content)]  # shallow copy to keep Mapping contract
        matches = regex_engine.scan_table(rows)
    else:
        matches = regex_engine.scan_text(str(payload.content))
    return [build_evidence_match(payload, match) for match in matches]
