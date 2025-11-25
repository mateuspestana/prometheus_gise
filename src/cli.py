"""Command Line Interface for the Prometheus Forensic Tool (F7)."""

from pathlib import Path
from typing import Dict, Optional

import typer

from src.logger import configure_logging, get_logger
from src.main import run_pipeline

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

    # Mostrar informações iniciais
    typer.secho(
        f"\n🔍 Prometheus Forensic Tool - Iniciando varredura",
        fg=typer.colors.CYAN,
        bold=True,
        err=True,
    )
    typer.secho(
        f"   Diretório de entrada: {input}",
        fg=typer.colors.WHITE,
        err=True,
    )
    typer.secho(
        f"   Arquivo de padrões: {config_path if config_path else 'padrão'}",
        fg=typer.colors.WHITE,
        err=True,
    )
    typer.secho(
        f"   Arquivo de saída: {output_path}",
        fg=typer.colors.WHITE,
        err=True,
    )
    typer.secho(
        f"   Modo verboso: {'SIM' if verbose else 'NÃO'}",
        fg=typer.colors.WHITE,
        err=True,
    )

    if config_path and not config_path.exists():
        raise typer.BadParameter(f"Arquivo de configuração não encontrado: {config_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    typer.secho(
        f"\n📂 Buscando arquivos .ufdr em: {input}\n",
        fg=typer.colors.YELLOW,
        err=True,
    )

    progress_state: Dict[str, tuple[object, object]] = {}
    
    # Flag para verificar se algum arquivo foi encontrado
    files_found = False

    def handle_progress(event: Dict[str, object]) -> None:
        event_type = event.get("type")
        path_str = event.get("path")
        if not event_type or not path_str:
            return

        ufdr_name = Path(path_str).name
        full_path = Path(path_str)

        if event_type == "ufdr-start":
            total = int(event.get("textual_total") or 0)
            typer.secho(
                f"\n{'='*80}",
                fg=typer.colors.CYAN,
                err=True,
            )
            typer.secho(
                f"📦 Processando UFDR: {ufdr_name}",
                fg=typer.colors.CYAN,
                bold=True,
                err=True,
            )
            typer.secho(
                f"   Caminho completo: {full_path}",
                fg=typer.colors.WHITE,
                err=True,
            )
            if total > 0:
                bar_cm = typer.progressbar(length=total, label=f"{ufdr_name} (textual)")
                progress = bar_cm.__enter__()
                progress_state[path_str] = (bar_cm, progress)
                typer.secho(
                    f"   📄 Encontrados {total} arquivo(s) textual(is) para processar",
                    fg=typer.colors.BLUE,
                    err=True,
                )
            else:
                typer.secho(
                    f"   ⚠️  Nenhum arquivo textual elegível para processamento.",
                    fg=typer.colors.YELLOW,
                    err=True,
                )
        elif event_type == "text-progress":
            state = progress_state.get(path_str)
            index = int(event.get("index") or 0)
            total = int(event.get("total") or 0)
            engine = event.get("engine") or event.get("stage") or ""
            member = event.get("member", "")

            if state:
                _, progress = state
                stage = event.get("stage")
                if stage in {"done", "skip"}:
                    progress.update(1)

            # Mostrar detalhes do arquivo sendo processado
            member_name = Path(member).name if member else f"arquivo {index}"
            typer.secho(
                f"   [{index}/{total}] Processando: {member_name}",
                fg=typer.colors.BRIGHT_BLUE,
                err=True,
            )
            if engine:
                typer.secho(
                    f"       → Engine: {engine}",
                    fg=typer.colors.WHITE,
                    err=True,
                )
        elif event_type == "ufdr-complete":
            state = progress_state.pop(path_str, None)
            if state:
                bar_cm, _ = state
                bar_cm.__exit__(None, None, None)
            typer.secho(
                f"✅ Concluído: {ufdr_name}",
                fg=typer.colors.GREEN,
                bold=True,
                err=True,
            )
            typer.secho(
                f"{'='*80}\n",
                fg=typer.colors.CYAN,
                err=True,
            )

    try:
        # Verificar se há arquivos antes de processar
        from src.scanner import UFDRScanner
        scanner = UFDRScanner(input)
        scan_results = scanner.scan()
        ufdr_paths = [result.path for result in scan_results]
        
        if not ufdr_paths:
            typer.secho(
                f"\n⚠️  Nenhum arquivo .ufdr encontrado em: {input}",
                fg=typer.colors.YELLOW,
                bold=True,
                err=True,
            )
            typer.secho(
                f"   Verifique se o diretório está correto e contém arquivos .ufdr",
                fg=typer.colors.WHITE,
                err=True,
            )
            raise typer.Exit(code=1)
        
        files_found = True
        typer.secho(
            f"✅ Encontrados {len(ufdr_paths)} arquivo(s) .ufdr para processar\n",
            fg=typer.colors.GREEN,
            err=True,
        )
        
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

    # Resumo final
    typer.secho(
        f"\n{'='*80}",
        fg=typer.colors.CYAN,
        err=True,
    )
    typer.secho(
        f"✅ Varredura concluída com sucesso!",
        fg=typer.colors.GREEN,
        bold=True,
        err=True,
    )
    typer.secho(
        f"   Arquivos processados: {summary.get('processed', 0)}",
        fg=typer.colors.WHITE,
        err=True,
    )
    typer.secho(
        f"   Ocorrências encontradas: {summary.get('matches', 0)}",
        fg=typer.colors.WHITE,
        err=True,
    )
    failures = summary.get("failures", [])
    if failures:
        typer.secho(
            f"   ⚠️  Arquivos com falhas: {len(failures)}",
            fg=typer.colors.YELLOW,
            err=True,
        )
        for failure in failures:
            typer.secho(
                f"      - {Path(failure).name}",
                fg=typer.colors.YELLOW,
                err=True,
            )
    typer.secho(
        f"\n📄 Resultados salvos em:",
        fg=typer.colors.CYAN,
        err=True,
    )
    typer.secho(
        f"   - JSON: {summary['output']}",
        fg=typer.colors.GREEN,
        err=True,
    )
    typer.secho(
        f"   - CSV: {summary['csv_output']}",
        fg=typer.colors.GREEN,
        err=True,
    )
    typer.secho(
        f"{'='*80}\n",
        fg=typer.colors.CYAN,
        err=True,
    )


def run() -> None:
    """Helper to execute the CLI from other entry points."""

    app()


if __name__ == "__main__":
    run()
