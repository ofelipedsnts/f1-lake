# F1 Lake

> Pipeline de dados de Formula 1 para coletar resultados de sessões, persistir em Parquet e publicar no data lake.

---

## 📋 Visao Geral

O F1 Lake e um projeto de engenharia de dados focado na coleta e publicaçãoo de dados históricos da Formula 1. A ingestao usa a biblioteca `fastf1` para obter resultados de corridas e sprints por temporada, salvando arquivos Parquet localmente como staging.

Na etapa seguinte, os arquivos sao enviados para AWS S3, compondo a camada bruta (raw/bronze). Em paralelo, o projeto possui um fluxo analítico em PySpark com Nekt SDK para consolidar metricas de pilotos e publicar uma tabela de feature store na camada silver.

O projeto foi estruturado para execução recorrente, com um loop de coleta + carga no `src/main.py`, e tambem suporta execução modular via CLI.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso no projeto |
|---|---|
| Python 3.9 | Linguagem principal do pipeline |
| fastf1 | Coleta de resultados de sessoes de F1 |
| pandas | Manipulação de DataFrames e escrita Parquet |
| pyarrow | Engine para leitura/escrita Parquet |
| boto3 | Upload de arquivos para AWS S3 |
| python-dotenv | Carregamento de variaveis de ambiente |
| pyspark | Processamento analítico distribuido |
| nekt | Leitura/escrita de tabelas no data lake |
| tqdm | Barra de progresso em loops de processamento |
| Dev Container | Ambiente de desenvolvimento padronizado |

---

## 🏗️ Arquitetura

O projeto segue um fluxo de pipeline em camadas:

```text
fastf1 API
  -> src/collect.py (coleta por ano/GP/modo)
  -> data/*.parquet (staging local)
  -> src/load.py (upload para S3)
  -> S3 bucket/folder (camada bronze/raw)

notebooks/drivers_stats.py (fluxo separado)
  -> le driver_results da bronze
  -> agrega metricas de pilotos com Spark SQL
  -> salva fs_driver_results_life na silver
```

A orquestração contínua é feita em `src/main.py`, que executa coleta e carga em loop com intervalo de 120 horas.

---

## 🎯 Iniciativa

Este projeto nasce como um estudo prático de engenharia de dados aplicado ao domínio esportivo, com objetivo de montar uma base confiavel para analises historicas e modelos preditivos de Formula 1.

---

## 📊 Resultados Obtidos

- Pipeline funcional de coleta histórica de corridas e sprints com parada antecipada por ano.
- Publicação automatizada de arquivos Parquet para S3.
- Estrutura de logs centralizada com modulo `logging`.
- Script analitico para gerar feature store de pilotos na camada silver.

> ⚠️ A preencher: metricas quantitativas de volume processado (arquivos por ciclo, tempo medio de execucao, custo de armazenamento e taxa de falhas).

---

## 🚀 Como Executar

### Pre-requisitos

- Python 3.9+
- Java/JDK (necessario para PySpark)
- Credenciais AWS com permissao de escrita no bucket
- Token Nekt (para o fluxo analitico)

### 1) Instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Dependencias usadas no codigo e que podem precisar de instalacao manual:

```bash
pip install boto3 tqdm pyarrow
```

Se for executar a parte do Nekt:

```bash
pip install git+https://<seu-token>@github.com/nektcom/nekt-sdk-py.git#egg=nekt-sdk
```

### 2) Configurar ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
AWS_ACCESS_KEY=...
AWS_SECRET_KEY=...
AWS_S3_BUCKET_NAME=...
AWS_S3_BUCKET_FOLDER=...
NEKT_TOKEN=...
```

### 3) Executar pipeline completo

```bash
python src/main.py
```

### 4) Executar modulos separadamente

```bash
# Coleta
python src/collect.py --years 2024 2025 --modes R S
python src/collect.py --start 2021 --stop 2025

# Upload S3
python src/load.py --bucket_name meu-bucket --folder f1

# Analitico
python notebooks/drivers_stats.py
```

---

## 📁 Estrutura do Projeto

```text
f1-lake/
├── src/
│   ├── main.py             # Entry point: loop de coletar e carregar
│   ├── collect.py          # Ingestao FastF1 e persistencia parquet local
│   ├── load.py             # Upload S3 e limpeza de staging local
│   └── logs/
│       ├── __init__.py
│       └── logger.py       # Fabrica centralizada de loggers
├── notebooks/
│   └── drivers_stats.py    # Agregacoes Spark + publicacao silver
├── data/                   # Staging local dos arquivos parquet
├── .devcontainer/
│   ├── Dockerfile
│   └── devcontainer.json
├── requirements.txt
└── README.md
```

---
