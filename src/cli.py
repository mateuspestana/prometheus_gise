"""Command Line Interface for the Prometheus Forensic Tool (F7)."""

from pathlib import Path
from typing import Optional

import typer

from .logger import configure_logging, get_logger
from .main import run_pipeline

app = typer.Typer(help="Prometheus Forensic Tool CLI", pretty_exceptions_enable=False)


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

    logger = configure_logging(verbose=verbose)
    ctx.obj = {"verbose": verbose, "logger": logger}


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
        help="Arquivo JSON com os padrões de regex.",
    ),
    output: Path = typer.Option(
        Path("outputs/prometheus_results.json"),
        "--output",
        "-o",
        help="Arquivo de saída JSON consolidado.",
    ),
) -> None:
    """Orquestra a execução completa da ferramenta."""

    config_path = config if config else None
    output_path = output
    verbose: bool = ctx.obj.get("verbose", False) if ctx.obj else False
    logger = get_logger()
    logger.debug(
        "CLI scan requested with input=%s config=%s output=%s verbose=%s", input, config_path, output_path, verbose
    )

    if config_path and not config_path.exists():
        raise typer.BadParameter(f"Arquivo de configuração não encontrado: {config_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        run_pipeline(input_dir=input, config_path=config_path if config_path else Path(), output_path=output_path)
    except NotImplementedError as exc:  # pragma: no cover - placeholder behaviour
        typer.secho(str(exc), fg=typer.colors.YELLOW)
        logger.warning("Pipeline ainda não implementado: %s", exc)
        raise typer.Exit(code=1) from exc


def run() -> None:
    """Helper to execute the CLI from other entry points."""

    app()


if __name__ == "__main__":
    run()
