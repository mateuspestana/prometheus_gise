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

### Scripts de Execução

O projeto inclui scripts prontos para facilitar a execução. **Importante:** Todos os scripts assumem que o ambiente virtual `.venv` já foi criado e as dependências já foram instaladas (veja seção "Instalação Manual" acima).

#### `run_streamlit.bat` - Interface Web

Script simplificado que executa o Streamlit:

```cmd
run_streamlit.bat
```

**Requisitos obrigatórios:**
- O ambiente virtual `.venv` já deve estar criado
- Todas as dependências de `requirements.txt` já devem estar instaladas
- O Streamlit deve estar instalado no ambiente virtual

Este script:
- Ativa o ambiente virtual `.venv`
- Configura o `PYTHONPATH` corretamente
- Executa o Streamlit na porta 8501

**Se você ainda não configurou o ambiente:**
Siga os passos da seção "Instalação Manual" acima antes de usar este script.

#### `run_cli.bat` - Interface de Linha de Comando Interativa

Script interativo para executar o CLI:

```cmd
run_cli.bat
```

**Requisitos obrigatórios:**
- O ambiente virtual `.venv` já deve estar criado
- Todas as dependências de `requirements.txt` já devem estar instaladas

Este script:
- Ativa o ambiente virtual `.venv`
- Configura o `PYTHONPATH` corretamente
- Solicita o caminho do diretório com arquivos `.ufdr`
- Executa a varredura automaticamente

**Se você ainda não configurou o ambiente:**
Siga os passos da seção "Instalação Manual" acima antes de usar este script.

## Uso

### Interface Web (Streamlit)

**Opção 1 - Usando o Script:**
```cmd
run_streamlit.bat
```

**Requisitos:** O ambiente virtual `.venv` e as dependências devem estar instalados (veja seção "Instalação Manual" acima).

**Opção 2 - Comando Manual:**
Se preferir executar manualmente:
```cmd
.venv\Scripts\activate
python -m streamlit run src\streamlit_app.py --server.port 8501
```

**Após iniciar:**
1. Acesse http://localhost:8501 no navegador
2. Selecione o diretório com arquivos `.ufdr`
3. Escolha as extensões de arquivo a processar
4. Clique em "Iniciar varredura"
5. Aguarde o processamento e visualize os resultados

### Interface de Linha de Comando (CLI)

**Opção 1 - Script Interativo:**
```cmd
run_cli.bat
```
O script solicitará o caminho do diretório com arquivos `.ufdr` e executará a varredura.

**Opção 2 - Comando Manual:**
```cmd
.venv\Scripts\activate
python -m src.cli scan -i "caminho\para\evidencias"
```

**Com modo verboso (mostra detalhes de cada arquivo):**
```cmd
python -m src.cli --verbose scan -i "caminho\para\evidencias"
```

**Com opções personalizadas:**
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
├── outputs/               # Resultados gerados (com timestamp)
├── requirements.txt       # Dependências Python
├── run_streamlit.bat      # Script completo Streamlit (Windows)
├── run_streamlit.sh       # Script completo Streamlit (Linux/macOS)
├── run_cli.bat            # Script interativo CLI (Windows)
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

A ferramenta gera dois arquivos de saída com timestamp:

1. **JSON** (`prometheus_results_YYYYMMDD_HHMMSS.json`): Estruturado, completo
2. **CSV** (`prometheus_results_YYYYMMDD_HHMMSS.csv`): Planilha, fácil de analisar

Ambos contêm as mesmas informações sobre ocorrências encontradas. O timestamp garante que cada execução gere arquivos únicos, evitando sobrescrever resultados anteriores.

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

### Erro: "C extension: pandas.compat._constants not built"

Este erro ocorre quando o pandas não foi compilado corretamente. Para resolver:

```cmd
.venv\Scripts\activate
pip uninstall pandas
pip install --no-cache-dir pandas
```

Ou usando `uv`:
```cmd
uv pip uninstall --python .venv\Scripts\python.exe pandas
uv pip install --python .venv\Scripts\python.exe pandas
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

