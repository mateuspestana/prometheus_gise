"""Command Line Interface for the Prometheus Forensic Tool (F7)."""

from pathlib import Path
from typing import Dict, Optional

import typer

from .logger import configure_logging, get_logger
from .main import run_pipeline

app = typer.Typer(
    help="Prometheus Forensic Tool CLI",
    pretty_exceptions_enable=False,
    rich_markup_mode=None,
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

    progress_state: Dict[str, tuple[object, object]] = {}

    def handle_progress(event: Dict[str, object]) -> None:
        event_type = event.get("type")
        path_str = event.get("path")
        if not event_type or not path_str:
            return

        ufdr_name = Path(path_str).name

        if event_type == "ufdr-start":
            total = int(event.get("textual_total") or 0)
            if total > 0:
                bar_cm = typer.progressbar(length=total, label=f"{ufdr_name} (textual)")
                progress = bar_cm.__enter__()
                progress_state[path_str] = (bar_cm, progress)
                typer.secho(
                    f"Iniciando processamento textual de {ufdr_name}: {total} arquivo(s).",
                    fg=typer.colors.BLUE,
                    err=True,
                )
            else:
                typer.secho(
                    f"{ufdr_name}: nenhum arquivo textual elegível para processamento.",
                    fg=typer.colors.YELLOW,
                    err=True,
                )
        elif event_type == "text-progress":
            state = progress_state.get(path_str)
            index = int(event.get("index") or 0)
            total = int(event.get("total") or 0)
            engine = event.get("engine") or event.get("stage") or ""

            if state:
                _, progress = state
                stage = event.get("stage")
                if stage in {"done", "skip"}:
                    progress.update(1)

            typer.secho(
                f"{ufdr_name}: {index}/{total} via {engine or 'desconhecido'}",
                fg=typer.colors.BRIGHT_BLUE,
                err=True,
            )
        elif event_type == "ufdr-complete":
            state = progress_state.pop(path_str, None)
            if state:
                bar_cm, _ = state
                bar_cm.__exit__(None, None, None)
            typer.secho(
                f"Concluído {ufdr_name}.",
                fg=typer.colors.GREEN,
                err=True,
            )

    try:
        summary = run_pipeline(
            input_dir=input,
            config_path=config_path if config_path else Path(),
            output_path=output_path,
            progress_callback=handle_progress,
        )
    except NotImplementedError as exc:  # pragma: no cover - placeholder behaviour
        typer.secho(str(exc), fg=typer.colors.YELLOW)
        logger.warning("Pipeline ainda não implementado: %s", exc)
        raise typer.Exit(code=1) from exc
    finally:
        # Garante que barras pendentes sejam encerradas em caso de erro inesperado.
        while progress_state:
            _, (bar_cm, _) = progress_state.popitem()
            bar_cm.__exit__(None, None, None)

    typer.secho(
        f"Resultados salvos em:\n- JSON: {summary['output']}\n- CSV: {summary['csv_output']}",
        fg=typer.colors.GREEN,
    )


def run() -> None:
    """Helper to execute the CLI from other entry points."""

    app()


if __name__ == "__main__":
    run()
