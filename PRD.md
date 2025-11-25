Product Requirements Document (PRD)

Projeto: Prometheus Forensic Tool (PFT)

Versão: 1.1

Data: 03/11/2025

Responsável: Matheus Pestana


🧭 1. Visão Geral

A Prometheus Forensic Tool (PFT) é uma aplicação forense multiplataforma desenvolvida em Python, concebida para automatizar a análise de arquivos .ufdr — pacotes extraídos pela ferramenta Cellebrite UFED.

Seu propósito é localizar e ler automaticamente os .ufdr em diretórios e subdiretórios, extrair seus bancos de dados e conteúdos textuais, e executar buscas baseadas em expressões regulares (regex) predefinidas no arquivo /config/patterns.json.

Os resultados consolidados são exportados em um único arquivo JSON unificado, que centraliza todas as correspondências encontradas, indicando a origem (arquivo-fonte, caminho interno, timestamp e tipo de dado identificado).


⚙️ 2. Objetivos do Produto
	1.	Automatizar a varredura e extração de dados de múltiplos .ufdr.
	2.	Centralizar todos os resultados em um único arquivo JSON consolidado.
	3.	Permitir configuração de padrões de regex por meio de arquivo externo (config/patterns.json).
	4.	Suportar execução em CLI (linha de comando) e GUI (interface gráfica).
	5.	Garantir compatibilidade total com macOS, Windows e Linux.
	6.	Manter logs e cadeia de custódia dos resultados (sem enviar dados para fora).


🧩 3. Escopo Funcional

3.1 Funcionalidades Principais

ID	Função	Descrição
F1	Busca recursiva	Percorre pastas e subpastas, identificando arquivos .ufdr.
F2	Leitura de .ufdr	Trata .ufdr como .zip, abrindo e mapeando seus conteúdos.
F3	Leitura interna de bancos de dados	Identifica e acessa .db / .sqlite / .sqlite3 dentro dos pacotes.
	F3.1 Se não houver um arquivo .db ou .sqlite ou .sqlite3 dentro do .ufdr, ele deve rastrear todos os arquivos que possuem texto (.eml, .pdf, .xlsx, .csv, .ics, .vcf, para extrair os textos e aplicar F4). 
F4	Motor de Regex	Executa padrões do arquivo config/patterns.json em texto e tabelas.
F5	Consolidação de Resultados	Cria um único arquivo JSON com todos os resultados encontrados.
F6	Metadados Forenses	Adiciona a cada resultado: nome do arquivo .ufdr, caminho interno, nome do arquivo analisado, tipo de dado identificado, timestamp e contexto textual.
F7	CLI Completa	Uso via terminal com parâmetros configuráveis (--input, --output, --config, --verbose).
F8	Interface Gráfica (GUI)	Interface simples (PyQt) para seleção de pastas e exibição do progresso e resultados.
F9	Gestão de Erros e Logs	Continua execução mesmo em caso de falhas, gerando logs detalhados.
F10	Relatório Consolidado Único	Saída em JSON unificado: outputs/prometheus_results.json.


🧱 4. Arquitetura Técnica

4.1. Linguagem e Frameworks
	•	Linguagem: Python 3.10+
	•	Bibliotecas Principais:
	•	zipfile, sqlite3, os, re, json, pathlib, logging
	•	argparse ou click (CLI)
	•	tkinter ou PyQt5 (GUI)
	•	rich (para logs e exibição colorida)

4.2. Estrutura de Diretórios

prometheus_forensic_tool/
│
├── src/
│   ├── main.py
│   ├── cli.py
│   ├── gui.py
│   ├── scanner.py
│   ├── extractor.py
│   ├── regex_engine.py
│   ├── reporter.py
│   └── logger.py
│
├── config/
│   └── patterns.json
│
├── outputs/
│   ├── logs/
│   │   └── scan.log
│   └── prometheus_results.json
│
├── tests/
│   └── test_regex_engine.py
│
└── README.md


⸻

⚙️ 5. Arquivo de Padrões (config/patterns.json)

O arquivo JSON define os padrões a serem buscados.
Exemplo:

{
  "CPF": "\\b\\d{3}\\.\\d{3}\\.\\d{3}\\-\\d{2}\\b",
  "CNPJ": "\\b\\d{2}\\.\\d{3}\\.\\d{3}\\/\\d{4}\\-\\d{2}\\b",
  "Email": "[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+",
  "Telefone": "\\(\\d{2}\\)\\s?\\d{4,5}\\-\\d{4}",
  "Placa": "[A-Z]{3}\\-\\d{4}",
  "IMEI": "\\b\\d{15}\\b"
}


⸻

📦 6. Saída Esperada (JSON Consolidado)

Arquivo único:
outputs/prometheus_results.json

Formato:

[
  {
    "source_file": "evidencia_01.ufdr",
    "internal_path": "data/messages.db",
    "file_type": "database",
    "pattern_type": "Email",
    "match_value": "exemplo@dominio.com",
    "context": "tabela contacts, linha 12",
    "timestamp": "2025-11-03T18:12:55Z"
  },
  {
    "source_file": "evidencia_02.ufdr",
    "internal_path": "report/report.html",
    "file_type": "text/html",
    "pattern_type": "CPF",
    "match_value": "123.456.789-00",
    "context": "linha 42 do arquivo",
    "timestamp": "2025-11-03T18:13:12Z"
  }
]

Todos os resultados de todos os .ufdr são reunidos nesse único arquivo, permitindo análises agregadas e buscas posteriores.

⸻

💻 7. Interface de Linha de Comando (CLI)

Exemplo de uso:

$ prometheus scan --input /evidencias --config config/patterns.json --output outputs/prometheus_results.json --verbose

Parâmetros:

Parâmetro	Descrição
--input	Caminho base da pasta com arquivos .ufdr
--config	Caminho do arquivo JSON de padrões regex
--output	Caminho do JSON consolidado de saída
--verbose	Exibe logs detalhados no terminal


⸻

🪟 8. Interface Gráfica (GUI)

Objetivo: permitir operação sem linha de comando.

Componentes:
	•	Seletor de diretório (Browse)
	•	Campo de caminho do arquivo de configuração
	•	Botão Iniciar Varredura
	•	Barra de progresso com contador de .ufdr
	•	Tabela de resultados (com filtro por tipo de dado)
	•	Botão Exportar Resultados (gera prometheus_results.json)

Framework sugerido: PyQt5 (profissional).

⸻

🧩 9. Requisitos Não-Funcionais

Categoria	Descrição
Performance	Processar 100 arquivos .ufdr em até 15 min (média).
Portabilidade	Rodar em macOS, Windows e Linux (empacotável com PyInstaller).
Resiliência	Se um .ufdr falhar, logar erro e continuar execução.
Usabilidade	CLI simples e GUI limpa.
Segurança	Nenhum dado sai do ambiente local.
Extensibilidade	Suporte a inclusão de novos padrões regex.


⸻

📜 10. Logs e Auditoria

Cada execução gera:

outputs/logs/scan.log

Formato do log:

[2025-11-03 18:14:12] INFO - Iniciando varredura em /evidencias
[2025-11-03 18:14:25] INFO - 5 arquivos .ufdr encontrados
[2025-11-03 18:15:02] INFO - Matches: 248 | Saída: outputs/prometheus_results.json


⸻

🧠 11. Fluxo Operacional
	1.	Usuário executa via CLI ou abre GUI.
	2.	Ferramenta percorre diretórios recursivamente.
	3.	Cada .ufdr é aberto como .zip.
	4.	Busca-se dentro dele arquivos .db .
	5.	O motor de regex aplica os padrões definidos.
	6.	Cada correspondência é registrada com metadados.
	7.	Ao final, todos os resultados são unificados em prometheus_results.json.

⸻

🧭 12. Próximos Passos de Implementação
	1.	Criar estrutura base (src/, config/, outputs/).
	2.	Implementar módulos:
	•	scanner.py → busca recursiva
	•	extractor.py → unzip + mapeamento interno
	•	regex_engine.py → execução de padrões
	•	reporter.py → consolidação única
	3.	Implementar CLI (Typer).
	4.	Adicionar GUI (PyQt5).
	5.	Criar testes unitários.
	6.	Documentar uso e empacotar (PyInstaller).

⸻

💬 13. Tagline do Projeto

“Prometheus Forensic Tool — revelando o que está oculto nas camadas dos dados.”