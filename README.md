# Prometheus Forensic Tool

Ferramenta de análise forense automatizada para pacotes UFDR (Cellebrite).

## Visão Geral

A Prometheus Forensic Tool automatiza a análise de pacotes `.ufdr`, extraindo conteúdo interno, executando buscas por regex configuráveis e consolidando resultados em formatos JSON e CSV.

## Instalação no Windows

### Pré-requisitos

1. **Python 3.12+**
   - Recomendado: Instalar Python pela [Microsoft Store](https://apps.microsoft.com/detail/9NRWMJP3717K)
   - Alternativa: [python.org](https://www.python.org/downloads/)

2. **uv** (gerenciador de pacotes Python)
   - Instale via PowerShell:
     ```powershell
     powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - Ou via pip:
     ```cmd
     python -m pip install --user uv
     ```
   - Documentação: https://github.com/astral-sh/uv

### Instalação Manual (se `run_streamlit.bat` não funcionar)

Se o script `run_streamlit.bat` não funcionar, siga estes passos:

1. **Abra o PowerShell ou CMD** no diretório do projeto

2. **Crie o ambiente virtual:**
   ```cmd
   uv venv .venv --python 3.12
   ```

3. **Ative o ambiente virtual:**
   ```cmd
   .venv\Scripts\activate
   ```

4. **Instale as dependências:**
   
   Instale as dependências:
   ```cmd
   uv pip install --python .venv\Scripts\python.exe -r requirements.txt
   ```
   
   Se o `uv` não estiver disponível, use `pip`:
   ```cmd
   pip install -r requirements.txt
   ```

5. **Execute o Streamlit:**
   ```cmd
   python -m streamlit run src\streamlit_app.py 
   ```

6. **Acesse a aplicação:**
   - Abra seu navegador em: http://localhost:8501

### Script Simplificado (`run.bat`)

Para facilitar, você pode usar o script `run.bat` que apenas ativa o ambiente virtual e executa o Streamlit:

```cmd
run.bat
```

Este script assume que:
- O ambiente virtual `.venv` já foi criado
- As dependências já foram instaladas

## Uso

### Interface Web (Streamlit)

1. Execute `run_streamlit.bat` ou `run.bat`
2. Acesse http://localhost:8501 no navegador
3. Selecione o diretório com arquivos `.ufdr`
4. Escolha as extensões de arquivo a processar
5. Clique em "Iniciar varredura"
6. Aguarde o processamento e visualize os resultados

### Interface de Linha de Comando (CLI)

```cmd
python -m src.cli --verbose scan -i "caminho\para\evidencias" -c "config\regex_patterns.json" -o "outputs\resultados.json"
```

Para mais detalhes sobre o CLI, consulte `CLI_USAGE.md`.

### Interface Gráfica (PyQt6)

```cmd
python -m src.gui
```

Ou use o script:
```cmd
run_gui.sh
```

## Estrutura do Projeto

```
Prometheus/
├── src/                    # Código-fonte
│   ├── scanner.py         # Busca arquivos .ufdr
│   ├── extractor.py       # Extrai conteúdo de .ufdr
│   ├── content_navigator.py # Navega conteúdo interno
│   ├── text_extractor.py  # Extrai texto de vários formatos
│   ├── regex_engine.py    # Executa padrões regex
│   ├── main.py            # Pipeline principal
│   ├── cli.py             # Interface CLI
│   ├── gui.py             # Interface PyQt6
│   └── streamlit_app.py   # Interface web Streamlit
├── config/                # Arquivos de configuração
│   └── regex_patterns.json
├── outputs/               # Resultados gerados
├── requirements.txt       # Dependências Python
├── run_streamlit.bat      # Script completo (Windows)
├── run_streamlit.sh       # Script completo (Linux/macOS)
├── run.bat                # Script simplificado (Windows)
└── README.md              # Este arquivo
```

## Configuração de Padrões Regex

Os padrões de busca são configurados em `config/regex_patterns.json`. Cada entrada contém:

- **name**: identificador do padrão (ex.: `CPF`, `Email`)
- **regex**: expressão regular
- **flags** (opcional): `ignorecase`, `multiline`, `dotall`, `unicode`

Exemplo:
```json
{
  "patterns": [
    {
      "name": "CPF",
      "regex": "\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}",
      "flags": []
    }
  ]
}
```

## Formatos de Saída

A ferramenta gera dois arquivos de saída:

1. **JSON** (`prometheus_results.json`): Estruturado, completo
2. **CSV** (`prometheus_results.csv`): Planilha, fácil de analisar

Ambos contêm as mesmas informações sobre ocorrências encontradas.

## Solução de Problemas

### Erro: "no module named 'src'"

Certifique-se de que o `PYTHONPATH` inclui o diretório raiz do projeto:
```cmd
set PYTHONPATH=%CD%;%PYTHONPATH%
```

### Erro ao instalar `pdfminer.six` com `uv`

Use `uv pip` em vez de `uv` diretamente:
```cmd
uv pip install --python .venv\Scripts\python.exe "pdfminer.six>=20221105,<2025.0"
```

### Streamlit não inicia

Verifique se o Streamlit está instalado:
```cmd
.venv\Scripts\pip.exe install streamlit
```

### Ambiente virtual não encontrado

Recrie o ambiente virtual:
```cmd
python -m venv .venv
.venv\Scripts\activate
```

## Desenvolvimento

### Executar Testes

```cmd
set QT_QPA_PLATFORM=offscreen
python -m pytest tests/ -v
```

### Gerar Executáveis

Futuramente, versões executáveis serão geradas.

## Licença

Desenvolvido por Matheus C. Pestana (GENI/UFF).

