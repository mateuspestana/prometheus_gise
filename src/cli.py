"""Command Line Interface for the Prometheus Forensic Tool (F7)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import typer

from .main import run_pipeline

app = typer.Typer(help="Prometheus Forensic Tool CLI")


def configure_logging(verbose: bool) -> None:
    """Configure logging based on the verbosity flag."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s - %(message)s",
    )


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Mostra logs detalhados durante a execução.",
    ),
) -> None:
    """Callback global usado para inicializar configurações compartilhadas."""

    configure_logging(verbose)
    ctx.obj = {"verbose": verbose}


@app.command(help="Executa a varredura forense completa.")
def scan(
    ctx: typer.Context,
    input: Path = typer.Option(
        ..., "--input", "-i", exists=True, file_okay=False, dir_okay=True, resolve_path=True, help="Diretório com arquivos .ufdr."
    ),
    config: Optional[Path] = typer.Option(
        Path("config/patterns.json"),
        "--config",
        "-c",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Arquivo JSON com os padrões de regex.",
    ),
    output: Path = typer.Option(
        Path("outputs/prometheus_results.json"),
        "--output",
        "-o",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Arquivo de saída JSON consolidado.",
    ),
) -> None:
    """Orquestra a execução completa da ferramenta."""

    verbose: bool = ctx.obj.get("verbose", False) if ctx.obj else False
    logging.getLogger(__name__).debug(
        "CLI scan requested with input=%s config=%s output=%s verbose=%s", input, config, output, verbose
    )

    if config and not config.exists():
        raise typer.BadParameter(f"Arquivo de configuração não encontrado: {config}")

    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        run_pipeline(input_dir=input, config_path=config if config else Path(), output_path=output)
    except NotImplementedError as exc:  # pragma: no cover - placeholder behaviour
        typer.secho(str(exc), fg=typer.colors.YELLOW)
        raise typer.Exit(code=1) from exc


def run() -> None:
    """Helper to execute the CLI from other entry points."""

    app()


if __name__ == "__main__":
    run()
