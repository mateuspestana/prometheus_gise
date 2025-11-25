"""Streamlit web interface for the Prometheus Forensic Tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import streamlit as st

# Configure page first (before any heavy imports)
st.set_page_config(
    page_title="Prometheus Forensic Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants
DEFAULT_PATTERNS_PATH = Path("config/regex_patterns.json")
DEFAULT_OUTPUT_PATH = Path("outputs/prometheus_results.json")
DEFAULT_LOG_PATH = Path("outputs/logs/streamlit.log")

# Initialize session state
if "scan_running" not in st.session_state:
    st.session_state.scan_running = False
if "scan_results" not in st.session_state:
    st.session_state.scan_results = None
if "scan_summary" not in st.session_state:
    st.session_state.scan_summary = None
if "progress_info" not in st.session_state:
    st.session_state.progress_info = {"current_file": "", "progress": 0, "total": 0}
if "total_progress" not in st.session_state:
    st.session_state.total_progress = {
        "current_ufdr": 0,
        "total_ufdr": 0,
        "current_file_in_ufdr": 0,
        "total_files_in_current_ufdr": 0,
        "total_files_all_ufdr": 0,
        "processed_files_all_ufdr": 0,
    }
if "logger_configured" not in st.session_state:
    st.session_state.logger_configured = False


def build_help_content() -> str:
    """Build help content in Markdown format."""
    patterns_path = DEFAULT_PATTERNS_PATH.resolve()
    return f"""
## Guia Rápido

A Prometheus Forensic Tool automatiza a análise de pacotes `.ufdr`:
encontra arquivos, extrai dados internos e aplica padrões de regex configuráveis
para gerar um relatório consolidado.

### Fluxo de Trabalho

1. Escolha o diretório de evidências com os arquivos `.ufdr`.
2. Selecione o arquivo de padrões (por padrão: `{patterns_path}`).
3. Inicie a varredura. O pipeline consolidará todos os resultados em um único JSON e CSV.

### Padrões Regex

Os padrões ficam em `config/regex_patterns.json`. Cada entrada contém:

- **name**: identificador do padrão (ex.: `CPF`).
- **regex**: expressão regular usada na busca.
- **flags** (opcional): lista com `ignorecase`, `multiline`, `dotall` ou `unicode`.

### Módulos Implementados

- `scanner.py`: busca recursiva por `.ufdr` (F1).
- `extractor.py`: trata `.ufdr` como arquivos zip (F2).
- `regex_engine.py`: executa os padrões configurados (F4).
- `cli.py`: interface de linha de comando (F7).
- `gui.py`: interface moderna em PyQt6 (F8).
- `streamlit_app.py`: esta interface web (Streamlit).

---

*Desenvolvido por Matheus C. Pestana (GENI/UFF).*
"""


def get_logger():
    """Get or configure logger lazily."""
    if not st.session_state.logger_configured:
        from src.logger import configure_logging
        # Streamlit sempre usa modo verboso para mostrar logs no terminal
        logger = configure_logging(verbose=True, log_path=DEFAULT_LOG_PATH)
        st.session_state.logger_configured = True
        return logger
    else:
        from src.logger import get_logger as _get_logger
        return _get_logger()


def main() -> None:
    """Main Streamlit application."""
    # Header
    st.title("🔍 Prometheus Forensic Tool")
    st.markdown("**Análise moderna de pacotes UFDR**")
    st.markdown("---")

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuração")

        # Input directory
        input_dir = st.text_input(
            "Diretório de evidências",
            value="",
            help="Caminho para o diretório contendo arquivos .ufdr",
        )

        # Config file
        config_file = st.text_input(
            "Arquivo de padrões",
            value=str(DEFAULT_PATTERNS_PATH) if DEFAULT_PATTERNS_PATH.exists() else "",
            help="Caminho para o arquivo JSON com padrões regex",
        )

        st.markdown("---")
        
        # Extension selector
        from src.content_navigator import TEXTUAL_EXTENSIONS, IMAGE_EXTENSIONS
        
        all_extensions = sorted(list(TEXTUAL_EXTENSIONS | IMAGE_EXTENSIONS))
        # Default: all textual extensions, no image extensions
        default_selected = sorted(list(TEXTUAL_EXTENSIONS))
        
        selected_extensions = st.multiselect(
            "Extensões a processar",
            options=all_extensions,
            default=default_selected,
            help="Selecione quais tipos de arquivo processar. Por padrão, apenas arquivos textuais (sem imagens).",
        )
        
        st.markdown("---")

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            scan_button = st.button("🚀 Iniciar varredura", type="primary", use_container_width=True)
        with col2:
            if st.button("📄 Ver patterns.json", use_container_width=True):
                if DEFAULT_PATTERNS_PATH.exists():
                    with open(DEFAULT_PATTERNS_PATH, "r", encoding="utf-8") as f:
                        st.code(f.read(), language="json")
                else:
                    st.warning("Arquivo patterns.json não encontrado.")

        st.markdown("---")

        # Help section
        with st.expander("📖 Guia Rápido"):
            st.markdown(build_help_content())

    # Main content area
    if scan_button and not st.session_state.scan_running:
        # Lazy import run_pipeline only when scan is triggered
        from src.main import run_pipeline
        
        logger = get_logger()
        
        # Validate inputs
        evidence_dir = Path(input_dir).expanduser() if input_dir else None
        config_path = Path(config_file).expanduser() if config_file else DEFAULT_PATTERNS_PATH

        logger.info("=" * 80)
        logger.info("🔍 Prometheus Forensic Tool - Iniciando varredura via Streamlit")
        logger.info("   Diretório de entrada: %s", evidence_dir)
        logger.info("   Arquivo de padrões: %s", config_path)
        logger.info("   Arquivo de saída: %s", DEFAULT_OUTPUT_PATH)
        logger.info("=" * 80)

        if not evidence_dir or not evidence_dir.exists() or not evidence_dir.is_dir():
            logger.error("❌ Diretório de evidências inválido: %s", evidence_dir)
            st.error("❌ Selecione um diretório de evidências válido.")
            return

        if config_path and not config_path.exists():
            logger.error("❌ Arquivo de padrões não encontrado: %s", config_path)
            st.error("❌ Arquivo de padrões não encontrado.")
            return

        # Convert selected extensions to set
        allowed_extensions_set = set(selected_extensions) if selected_extensions else None
        if allowed_extensions_set:
            logger.info("📋 Extensões selecionadas: %s", ", ".join(sorted(allowed_extensions_set)))
        else:
            logger.warning("⚠️  Nenhuma extensão selecionada - nenhum arquivo será processado")
            st.warning("⚠️  Nenhuma extensão selecionada. Selecione pelo menos uma extensão para processar.")
            return

        # Initialize total progress tracking
        # First, count total UFDR files and their internal files
        from src.scanner import UFDRScanner
        from src.content_navigator import UFDRContentNavigator
        
        logger.info("📂 Contando arquivos UFDR e seus conteúdos...")
        with st.spinner("Contando arquivos UFDR e seus conteúdos..."):
            scanner = UFDRScanner(evidence_dir)
            scan_results = scanner.scan()
            ufdr_paths = [result.path for result in scan_results]
            total_ufdr = len(ufdr_paths)
            
            # Count total files in all UFDRs (only those matching selected extensions)
            total_files_all = 0
            for ufdr_path in ufdr_paths:
                try:
                    navigator = UFDRContentNavigator(ufdr_path, allowed_extensions=allowed_extensions_set)
                    plan = navigator.plan_processing()
                    total_files_all += len(plan.textual_members)
                except Exception as e:
                    logger.warning("Erro ao contar arquivos em %s: %s", ufdr_path, e)
        
        if total_ufdr == 0:
            st.warning("⚠️  Nenhum arquivo UFDR encontrado no diretório especificado.")
            return
        
        if total_files_all == 0:
            st.warning("⚠️  Nenhum arquivo textual encontrado nos UFDRs com as extensões selecionadas.")
            return
        
        # Start scan
        st.session_state.scan_running = True
        st.session_state.scan_results = None
        st.session_state.scan_summary = None
        st.session_state.progress_info = {"current_file": "", "progress": 0, "total": 0}
        
        st.session_state.total_progress = {
            "current_ufdr": 0,
            "total_ufdr": total_ufdr,
            "current_file_in_ufdr": 0,
            "total_files_in_current_ufdr": 0,
            "total_files_all_ufdr": total_files_all,
            "processed_files_all_ufdr": 0,
        }
        
        logger.info("📊 Total de arquivos UFDR: %d", total_ufdr)
        logger.info("📊 Total de arquivos textuais em todos os UFDRs: %d", total_files_all)
        
        # Show progress section immediately (before processing starts)
        # Use empty placeholders that can be updated
        st.markdown("### 📊 Progresso da Varredura")
        progress_bar_placeholder = st.empty()
        progress_metrics_placeholder = st.empty()
        progress_status_placeholder = st.empty()
        
        # Initialize progress display
        progress_bar_placeholder.progress(0.0, text="Iniciando processamento...")
        with progress_metrics_placeholder.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Arquivos UFDR", f"0/{total_ufdr}")
            with col2:
                st.metric("Arquivos textuais", f"0/{total_files_all}")
            with col3:
                st.metric("Progresso geral", "0%")
        progress_status_placeholder.info("📁 Preparando processamento...")
        
        # Store placeholders in session state for callback updates
        st.session_state.progress_bar_placeholder = progress_bar_placeholder
        st.session_state.progress_metrics_placeholder = progress_metrics_placeholder
        st.session_state.progress_status_placeholder = progress_status_placeholder

        # Create output directory
        DEFAULT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        logger.info("📂 Diretório de saída criado/preparado: %s", DEFAULT_OUTPUT_PATH.parent)

        # Progress callback for Streamlit
        # Note: Streamlit updates UI only at the end of script execution
        # So we store progress in session_state and display it after
        def handle_progress(event: Dict[str, object]) -> None:
            event_type = event.get("type")
            path_str = event.get("path")
            if not event_type or not path_str:
                return

            ufdr_name = Path(path_str).name
            full_path = Path(path_str)
            total_progress = st.session_state.total_progress

            if event_type == "ufdr-start":
                total = int(event.get("textual_total") or 0)
                total_progress["current_ufdr"] += 1
                total_progress["current_file_in_ufdr"] = 0
                total_progress["total_files_in_current_ufdr"] = total
                
                logger.info("")
                logger.info("=" * 80)
                logger.info("📦 Processando UFDR [%d/%d]: %s", 
                           total_progress["current_ufdr"], 
                           total_progress["total_ufdr"], 
                           ufdr_name)
                logger.info("   Caminho completo: %s", full_path)
                logger.info("   Arquivos textuais encontrados: %d", total)
                
                st.session_state.progress_info = {
                    "current_file": ufdr_name,
                    "progress": 0,
                    "total": total,
                }
                
                # Update progress display
                total_files = total_progress["total_files_all_ufdr"]
                if total_files > 0:
                    processed = total_progress["processed_files_all_ufdr"]
                    progress_value = processed / total_files
                    progress_bar_placeholder = st.session_state.get("progress_bar_placeholder")
                    progress_metrics_placeholder = st.session_state.get("progress_metrics_placeholder")
                    progress_status_placeholder = st.session_state.get("progress_status_placeholder")
                    
                    if progress_bar_placeholder:
                        progress_bar_placeholder.progress(progress_value, text=f"Processando UFDR {total_progress['current_ufdr']}/{total_progress['total_ufdr']}")
                    if progress_metrics_placeholder:
                        with progress_metrics_placeholder.container():
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Arquivos UFDR", f"{total_progress['current_ufdr']}/{total_progress['total_ufdr']}")
                            with col2:
                                st.metric("Arquivos textuais", f"{processed}/{total_files}")
                            with col3:
                                st.metric("Progresso geral", f"{int(progress_value * 100)}%")
                    if progress_status_placeholder:
                        progress_status_placeholder.info(f"📁 Processando UFDR: {ufdr_name} (0/{total})")
            elif event_type == "text-progress":
                total = int(event.get("total") or total_progress["total_files_in_current_ufdr"] or 1)
                index = int(event.get("index") or 0)
                engine = event.get("engine") or event.get("stage") or ""
                member = event.get("member", "")
                member_name = Path(member).name if member else f"arquivo {index}"
                
                # Update progress - calculate total files processed across all UFDRs
                # Files from previous UFDRs + current file index in current UFDR
                total_progress["current_file_in_ufdr"] = index
                
                # Calculate total processed: files from completed UFDRs + current file index
                # For now, we'll approximate: processed_files_all_ufdr + current_file_in_ufdr
                # This will be more accurate when ufdr-complete is called
                total_files = total_progress["total_files_all_ufdr"]
                processed_approx = total_progress["processed_files_all_ufdr"] + index
                progress_value = min(processed_approx / total_files if total_files > 0 else 0.0, 1.0)
                
                logger.info("   [%d/%d] Processando: %s (engine: %s)", index, total, member_name, engine or "desconhecido")
                
                st.session_state.progress_info = {
                    "current_file": ufdr_name,
                    "progress": index,
                    "total": total,
                    "engine": engine,
                }
                
                # Update progress display
                progress_bar_placeholder = st.session_state.get("progress_bar_placeholder")
                progress_metrics_placeholder = st.session_state.get("progress_metrics_placeholder")
                progress_status_placeholder = st.session_state.get("progress_status_placeholder")
                
                if progress_bar_placeholder:
                    progress_bar_placeholder.progress(progress_value, text=f"Processando arquivo {index}/{total} em {ufdr_name}")
                if progress_metrics_placeholder:
                    with progress_metrics_placeholder.container():
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Arquivos UFDR", f"{total_progress['current_ufdr']}/{total_progress['total_ufdr']}")
                        with col2:
                            st.metric("Arquivos textuais", f"{processed_approx}/{total_files}")
                        with col3:
                            st.metric("Progresso geral", f"{int(progress_value * 100)}%")
                if progress_status_placeholder:
                    status_text = f"📁 UFDR: {ufdr_name} | Arquivo: {index}/{total}"
                    if engine:
                        status_text += f" | Engine: {engine}"
                    progress_status_placeholder.info(status_text)
            elif event_type == "ufdr-complete":
                # Mark current UFDR as complete - all its files are done
                total_progress["processed_files_all_ufdr"] += total_progress["total_files_in_current_ufdr"]
                total_progress["current_file_in_ufdr"] = total_progress["total_files_in_current_ufdr"]
                
                logger.info("✅ Concluído: %s", ufdr_name)
                logger.info("=" * 80)
                
                st.session_state.progress_info = {
                    "current_file": ufdr_name,
                    "progress": total_progress["total_files_in_current_ufdr"],
                    "total": total_progress["total_files_in_current_ufdr"],
                }
                
                # Update progress display
                total_files = total_progress["total_files_all_ufdr"]
                if total_files > 0:
                    processed = total_progress["processed_files_all_ufdr"]
                    progress_value = min(processed / total_files, 1.0)
                    
                    progress_bar_placeholder = st.session_state.get("progress_bar_placeholder")
                    progress_metrics_placeholder = st.session_state.get("progress_metrics_placeholder")
                    progress_status_placeholder = st.session_state.get("progress_status_placeholder")
                    
                    if progress_bar_placeholder:
                        progress_bar_placeholder.progress(progress_value, text=f"Concluído UFDR {total_progress['current_ufdr']}/{total_progress['total_ufdr']}")
                    if progress_metrics_placeholder:
                        with progress_metrics_placeholder.container():
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Arquivos UFDR", f"{total_progress['current_ufdr']}/{total_progress['total_ufdr']}")
                            with col2:
                                st.metric("Arquivos textuais", f"{processed}/{total_files}")
                            with col3:
                                st.metric("Progresso geral", f"{int(progress_value * 100)}%")
                    if progress_status_placeholder:
                        progress_status_placeholder.success(f"✅ Concluído: {ufdr_name}")

        try:
            logger.info("🚀 Iniciando pipeline de processamento...")
            # Run pipeline with progress callback
            # Note: Progress updates are stored in session_state
            # Streamlit will show them after the function completes
            summary = run_pipeline(
                input_dir=evidence_dir,
                config_path=config_path,
                output_path=DEFAULT_OUTPUT_PATH,
                progress_callback=handle_progress,
                allowed_extensions=allowed_extensions_set,
            )

            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ Pipeline concluído com sucesso!")
            logger.info("   Arquivos processados: %d", summary.get("processed", 0))
            logger.info("   Ocorrências encontradas: %d", summary.get("matches", 0))
            failures = summary.get("failures", [])
            if failures:
                logger.warning("   ⚠️  Arquivos com falhas: %d", len(failures))
                for failure in failures:
                    logger.warning("      - %s", Path(failure).name)
            logger.info("   JSON: %s", summary.get("output", ""))
            logger.info("   CSV: %s", summary.get("csv_output", ""))
            logger.info("=" * 80)
            logger.info("")

            st.session_state.scan_summary = summary

            # Load results
            if DEFAULT_OUTPUT_PATH.exists():
                with DEFAULT_OUTPUT_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info("📄 Resultados carregados: %d entradas", len(data))
            else:
                data = []
                logger.warning("⚠️  Arquivo de resultados não encontrado: %s", DEFAULT_OUTPUT_PATH)

            st.session_state.scan_results = data
            st.session_state.scan_running = False
            
            # Update progress to 100%
            progress_bar_placeholder = st.session_state.get("progress_bar_placeholder")
            progress_metrics_placeholder = st.session_state.get("progress_metrics_placeholder")
            progress_status_placeholder = st.session_state.get("progress_status_placeholder")
            
            # Get total_progress from session_state
            total_progress = st.session_state.get("total_progress", {})
            
            if progress_bar_placeholder:
                progress_bar_placeholder.progress(1.0, text="Varredura concluída!")
            if progress_metrics_placeholder:
                with progress_metrics_placeholder.container():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Arquivos UFDR", f"{total_progress.get('total_ufdr', 0)}/{total_progress.get('total_ufdr', 0)}")
                    with col2:
                        st.metric("Arquivos textuais", f"{total_progress.get('total_files_all_ufdr', 0)}/{total_progress.get('total_files_all_ufdr', 0)}")
                    with col3:
                        st.metric("Progresso geral", "100%")
            if progress_status_placeholder:
                progress_status_placeholder.success("✅ Varredura concluída com sucesso!")

            st.success("✅ Varredura concluída com sucesso!")

        except Exception as exc:
            logger.exception("❌ Erro ao executar a varredura")
            st.session_state.scan_running = False
            st.error(f"❌ Erro ao executar a varredura: {exc}")

    # Display results
    if st.session_state.scan_results is not None:
        st.markdown("---")
        st.header("📊 Resultados")

        summary = st.session_state.scan_summary
        if summary:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Arquivos processados", summary.get("processed", 0))
            with col2:
                st.metric("Ocorrências encontradas", summary.get("matches", 0))
            with col3:
                failures_count = len(summary.get("failures", []))
                st.metric("Falhas", failures_count)

            if failures_count > 0:
                st.warning(f"⚠️ {failures_count} arquivo(s) falharam durante o processamento.")

        # Results table - lazy import pandas only when displaying results
        if len(st.session_state.scan_results) > 0:
            import pandas as pd
            
            df = pd.DataFrame(st.session_state.scan_results)
            # Reorder columns for better display
            column_order = ["source_file", "pattern_type", "match_value", "internal_path", "timestamp"]
            available_columns = [col for col in column_order if col in df.columns]
            if available_columns:
                df = df[available_columns]
            else:
                df = df[[col for col in df.columns]]

            st.dataframe(df, use_container_width=True, height=400)
            
            # Show CSV content in expandable section
            csv_path = summary.get("csv_output") if summary else None
            if csv_path and Path(csv_path).exists():
                st.markdown("---")
                st.markdown("#### 📄 Visualização do CSV")
                with st.expander("📄 Ver conteúdo completo do CSV", expanded=True):
                    # Show CSV as dataframe
                    try:
                        df_csv = pd.read_csv(csv_path)
                        st.dataframe(df_csv, use_container_width=True, height=400)
                    except Exception as e:
                        logger.warning("Erro ao ler CSV como DataFrame: %s", e)
                        # Fallback: show raw CSV content
                        with open(csv_path, "r", encoding="utf-8") as f:
                            csv_content = f.read()
                        st.code(csv_content, language="csv")

            # Download buttons
            st.markdown("---")
            st.markdown("#### 💾 Download de Resultados")
            col1, col2 = st.columns(2)

            json_path = summary.get("output") if summary else str(DEFAULT_OUTPUT_PATH)

            with col1:
                if Path(json_path).exists():
                    with open(json_path, "r", encoding="utf-8") as f:
                        json_data = f.read()
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name="prometheus_results.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                else:
                    st.info("Arquivo JSON não encontrado")

            with col2:
                if csv_path and Path(csv_path).exists():
                    with open(csv_path, "r", encoding="utf-8") as f:
                        csv_data = f.read()
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name="prometheus_results.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    st.info("Arquivo CSV não encontrado")
        else:
            st.info("ℹ️ Nenhuma ocorrência encontrada nos arquivos processados.")

    elif st.session_state.scan_running:
        # Show progress during scan
        info = st.session_state.progress_info
        total_progress = st.session_state.total_progress
        
        # Calculate overall progress
        # Progress = (arquivos textuais processados) / (total de arquivos textuais)
        # We only count textual files since they're what take time to process
        total_files = total_progress["total_files_all_ufdr"]
        if total_files > 0:
            # Files from completed UFDRs + current file index in current UFDR
            processed_files = total_progress["processed_files_all_ufdr"] + total_progress["current_file_in_ufdr"]
            overall_progress = processed_files / total_files if total_files > 0 else 0.0
            
            # Always show progress bar
            st.progress(overall_progress)
            
            # Show detailed progress
            st.markdown("### 📊 Progresso da Varredura")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Arquivos UFDR",
                    f"{total_progress['current_ufdr']}/{total_progress['total_ufdr']}",
                    delta=None
                )
            with col2:
                st.metric(
                    "Arquivos textuais",
                    f"{processed_files}/{total_files}",
                    delta=None
                )
            with col3:
                percentage = int(overall_progress * 100)
                st.metric(
                    "Progresso geral",
                    f"{percentage}%",
                    delta=None
                )
            
            # Current file info
            if info.get("current_file"):
                status_text = f"📁 **UFDR atual:** {info['current_file']}"
                if info["total"] > 0:
                    status_text += f" | **Arquivo:** {info['progress']}/{info['total']}"
                if "engine" in info and info["engine"]:
                    status_text += f" | **Engine:** {info['engine']}"
                st.info(status_text)
            else:
                st.info("📁 Preparando processamento...")
        else:
            st.info("📁 Preparando: Iniciando varredura...")
            if total_progress["total_ufdr"] > 0:
                st.metric("Arquivos UFDR encontrados", total_progress["total_ufdr"])
            else:
                st.warning("⚠️  Nenhum arquivo UFDR encontrado no diretório especificado.")


if __name__ == "__main__":
    main()
