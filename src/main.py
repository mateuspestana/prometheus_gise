"""Application entry points orchestrating future Prometheus workflows."""

from __future__ import annotations

from pathlib import Path


def run_pipeline(
    input_dir: Path,
    config_path: Path,
    output_path: Path,
) -> None:
    """Placeholder pipeline tying together scanning, extraction and reporting.

    This will be implemented once the underlying modules (scanner, extractor,
    regex engine, reporter) are ready.
    """

    raise NotImplementedError(
        "Pipeline execution still pending implementation. Merge the feature "
        "branches for scanning, extraction, regex and reporting before "
        "invoking the CLI."
    )
