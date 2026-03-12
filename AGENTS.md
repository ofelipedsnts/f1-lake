# AGENTS.md — f1-lake

> Documentação de contexto para agentes de IA. Mantida atualizada a cada ciclo de desenvolvimento.
> Última atualização: 2026-03-12

---

## Contexto da Aplicação

Pipeline de dados da Fórmula 1 que coleta resultados de corridas e sprints via biblioteca `fastf1`, persiste localmente em Parquet e carrega no AWS S3. Além dos resultados agregados, o pipeline também coleta dados de voltas individuais (laps) para análises detalhadas de desempenho. Uma camada analítica em PySpark/Nekt agrega estatísticas de pilotos e publica na camada silver do data lake. O projeto roda em loop contínuo (120h de sleep entre ciclos) e é executado dentro de um Dev Container com Python 3.9 e JDK para suporte ao Spark.

---

## Estrutura do Projeto

```
f1-lake/
├── src/
│   ├── main.py          # Entry point — orquestra collect + load em loop infinito
│   ├── collect.py       # Coleta dados via fastf1, salva como .parquet em data/
│   ├── load.py          # Upload de .parquet para AWS S3 e remoção local
│   ├── laps/
│   │   ├── __init__.py  # Marca laps/ como pacote Python
│   │   └── extract_session_laps.py  # Coleta voltas individuais (laps) por sessão
│   └── logs/
│       ├── __init__.py  # Marca logs/ como pacote Python
│       └── logger.py    # Fábrica centralizada de loggers
├── notebooks/
│   └── drivers_stats.py # Script analítico PySpark — gera feature store de pilotos
├── data/                # Staging local de arquivos .parquet (não versionado)
│   └── laps/            # Subdiretório para dados de voltas individuais
├── .devcontainer/
│   ├── Dockerfile       # Python 3.9 + JDK (para Spark)
│   └── devcontainer.json
├── requirements.txt
└── .gitignore
```

---

## Como Executar

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar o pipeline completo (coleta + upload S3)
python src/main.py

# Rodar apenas a coleta (CLI)
python src/collect.py --years 2024 2025 --modes R S
python src/collect.py --start 2021 --stop 2025

# Rodar coleta de voltas individuais (laps)
python src/laps/extract_session_laps.py --years 2024 2025 --modes R S
python src/laps/extract_session_laps.py --start 2021 --stop 2025

# Rodar apenas o upload S3
python src/load.py --bucket_name meu-bucket --folder f1

# Rodar o notebook analítico
python notebooks/drivers_stats.py
```

---

## Variáveis de Ambiente

O projeto usa `python-dotenv`. Crie um arquivo `.env` na raiz (nunca commite este arquivo):

| Variável | Obrigatória | Descrição |
|---|---|---|
| `AWS_ACCESS_KEY` | Sim | Access Key ID da AWS |
| `AWS_SECRET_KEY` | Sim | Secret Access Key da AWS |
| `AWS_S3_BUCKET_NAME` | Sim | Nome do bucket S3 de destino |
| `AWS_S3_BUCKET_FOLDER` | Sim | Pasta dentro do bucket |
| `NEKT_TOKEN` | Sim (notebooks) | Token de acesso ao SDK Nekt |

---

## Dependências Principais

| Biblioteca | Uso |
|---|---|
| `fastf1` | Coleta de resultados de sessões F1 via API |
| `pandas` | Manipulação de DataFrames |
| `boto3` | Upload para AWS S3 |
| `python-dotenv` | Leitura de variáveis de ambiente |
| `pyspark` | Processamento analítico em escala |
| `nekt` | Acesso ao data lake (camadas bronze/silver) |
| `tqdm` | Progress bar nos loops de upload |
| `pyarrow` | Engine para leitura/escrita de Parquet |

> **Atenção:** `boto3`, `tqdm`, `nekt` e `pyarrow` são usados no código mas **não estão no `requirements.txt`**. Instale manualmente se necessário.

---

## Fluxo Principal

```
fastf1 API
    → collect.py (process_year_modes)
        → data/{year}_{gp:02}_{mode}.parquet  (staging local)
    → load.py (proccess_data)
        → S3: {bucket}/{folder}/{filename}
        → remove arquivo local após upload

notebooks/drivers_stats.py (execução separada):
    Nekt bronze (driver_results)
        → PySpark SQL (agregações por piloto/data)
        → Nekt silver (fs_driver_results_life)
```

---

## Padrão de Logging

Todos os módulos usam a fábrica centralizada em `src/logs/logger.py`:

```python
from logs.logger import get_logger
logger = get_logger(__name__)
```

| Nível | Quando usar |
|---|---|
| `logger.debug()` | Dados brutos, variáveis internas (só em desenvolvimento) |
| `logger.info()` | Progresso normal do pipeline |
| `logger.warning()` | Situação inesperada mas não fatal (ex: ano sem dados) |
| `logger.error()` | Falha em operação específica (ex: erro de upload) |
| `logger.critical()` | Falha que impede o sistema de continuar |

Mensagens de log devem ser escritas em **português**.
Não use `print()` — use sempre o `logger`.

---

## Estilo de Código

### Nomenclatura
- **Classes:** `PascalCase` — ex: `Collect`, `Load`
- **Métodos e funções:** `snake_case` — ex: `get_data`, `upload_file`, `process_year_modes`
- **Variáveis:** `snake_case` — ex: `bucket_name`, `data_dir`
- **Constantes de módulo:** `UPPER_SNAKE_CASE` — ex: `DATA_DIR`, `AWS_ACCESS_KEY`

### Imports
Siga a ordem PEP 8, separados por linha em branco:
```python
# 1. Stdlib
import os
import datetime

# 2. Third-party
import pandas as pd
import boto3

# 3. Local
from logs.logger import get_logger
```

### Type Hints
- Use type hints em funções públicas
- Use `pd.DataFrame` como tipo (sem parênteses — `pd.DataFrame()` é instanciação, não tipo)
- Retornos booleanos explícitos: `-> bool`

```python
# Correto
def get_data(self, year: int, gp: int, mode: str) -> pd.DataFrame:

# Errado (padrão legado presente no código — evitar)
def get_data(self, year, gp, mode) -> pd.DataFrame():
```

### Tratamento de Erros
- Em coleta de dados: capture `ValueError` especificamente, retorne `pd.DataFrame()` vazio
- Em I/O (upload, disco): capture `Exception` amplo, faça log do erro, retorne `False`
- Use retorno booleano (`True`/`False`) para sinalizar sucesso/falha em métodos de processo

### Células Jupyter
Todos os scripts usam marcadores `# %%` para compatibilidade com Jupyter/VS Code:
```python
# %%
# Seção de configuração

# %%
# Seção de execução
```

---

## Pontos de Atenção para Agentes

- **Path relativo em `collect.py`:** `save_data` usa `"data/{year}_..."` como caminho relativo. O script deve ser executado a partir da raiz do projeto. Prefira `Path(__file__).parent.parent / "data"` para caminhos absolutos.
- **Typo consistente:** O método `proccess_data` (duplo `c`) existe em `load.py` e é referenciado em `main.py`. Não corrija sem atualizar ambos os arquivos.
- **`boto3` região hardcoded:** A região AWS `us-east-2` está fixada em `load.py:27`. Externalize para variável de ambiente se necessário mudar.
- **`.env` não deve ser commitado:** Está no `.gitignore`. Nunca adicione credenciais ao repositório.
- **`__pycache__/` e `*.pyc`** estão no `.gitignore` — nunca commite arquivos compilados.
- **Sem testes:** O projeto não possui testes automatizados nem framework de testes configurado.
- **Logger não idempotente:** `basicConfig` é chamado dentro de `get_logger()` a cada invocação. Em processos de longa duração isso pode gerar handlers duplicados.

---

## Histórico de Alterações Relevantes

| Data | Alteração |
|---|---|
| 2026-03-12 | Adicionado módulo `src/laps/` para coleta de dados de voltas individuais (laps) |
| 2026-03-11 | Refatoração de `process` em `process`, `process_year_modes`, `process_years` com parada antecipada |
| 2026-03-11 | Substituição de `print()` por módulo `logging` centralizado em `src/logs/logger.py` |
| 2026-03-11 | Adicionado `pyarrow` como dependência para suporte a Parquet |
| 2026-03-11 | Melhoria de logging em `load.py` com mensagens de progresso e erro detalhadas |
| 2026-03-11 | Adicionado `__pycache__/` e `*.pyc` ao `.gitignore` |
