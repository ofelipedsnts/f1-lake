# Design: Módulo de Coleta de Voltas (Laps Collection)

**Data:** 2026-03-12  
**Contexto:** Pipeline f1-lake - Expansão da coleta de dados da Fórmula 1

---

## Objetivo

Implementar um módulo de coleta de dados de voltas (laps) das sessões de Fórmula 1, seguindo o padrão estabelecido pelo módulo `collect.py` (coleta de resultados). O módulo será executável via CLI de forma independente e permitirá futura integração com `main.py`.

---

## Escopo

**Incluído:**
- Classe `CollectLaps` espelhando estrutura de `Collect`
- Coleta de dados de voltas via `session.laps` da biblioteca `fastf1`
- Enriquecimento com 4 colunas de metadados do evento
- Persistência em Parquet na subpasta `data/laps/`
- Interface CLI com argumentos `--years`, `--start`, `--stop`, `--modes`
- Logging centralizado seguindo padrão do projeto
- Arquivo `__init__.py` para tornar `src/laps/` um pacote Python

**Excluído (explicitamente):**
- Integração imediata com `main.py` (será implementada futuramente)
- Upload para AWS S3 (será reutilizada a classe `Load` existente)
- Testes automatizados (projeto não possui framework de testes)

---

## Arquitetura

### Estrutura de Arquivos

```
src/laps/
├── __init__.py                  # Marca laps/ como pacote Python
└── extract_session_laps.py      # Classe CollectLaps + CLI

data/
└── laps/                        # Subpasta para arquivos de voltas
    └── {year}_{gp:02}_{mode}.parquet
```

### Componentes

**Classe `CollectLaps`**
- Responsabilidade: Orquestrar coleta, enriquecimento e persistência de dados de voltas
- Padrão: Espelha `Collect` com métodos paralelos mas lógica específica para voltas

**CLI (argparse)**
- Responsabilidade: Interface de linha de comando para execução standalone
- Padrão: Idêntico ao `collect.py`

---

## Design Detalhado

### Classe CollectLaps

#### `__init__(self, years=[2021, 2022, 2023, 2024, 2025], modes=["R", "S"])`

**Responsabilidade:** Inicializar configuração de anos e modos a processar.

**Parâmetros:**
- `years` (list[int]): Anos da F1 a processar (default: 2021-2025)
- `modes` (list[str]): Modos de sessão ("R" = Race, "S" = Sprint)

**Comportamento:**
- Armazena configuração em atributos de instância
- Não valida entradas (confia nos defaults ou valores do usuário)

---

#### `get_data(self, year, gp, mode) -> pd.DataFrame`

**Responsabilidade:** Obter dados de voltas de uma sessão específica e enriquecer com metadados do evento.

**Parâmetros:**
- `year` (int): Ano da temporada
- `gp` (int): Número do GP (1-30)
- `mode` (str): Modo da sessão ("R" ou "S")

**Comportamento:**
1. Obtém sessão via `fastf1.get_session(year, gp, mode)`
2. **Diferença crítica vs `collect.py`:** Chama `session.load()` (completo) ao invés de `session._load_drivers_results()`
3. Extrai DataFrame de voltas: `df = session.laps`
4. Enriquece com 4 colunas do evento:
   - `df["event_date"] = session.event["EventDate"]`
   - `df["event_name"] = session.event["EventName"]`
   - `df["event_location"] = session.event["Location"]`
   - `df["event_country"] = session.event["Country"]`
5. Retorna DataFrame enriquecido

**Tratamento de erros:**
- Captura `ValueError` (sessão não existe)
- Retorna `pd.DataFrame()` vazio
- Não faz logging de erro (comportamento silencioso = esperado)

**Observações:**
- Mantém **todos os dados brutos** de `session.laps` (não remove colunas)
- Adiciona **apenas** as 4 colunas especificadas (não inclui Year, Mode, RoundNumber, etc.)

---

#### `save_data(self, df, year, gp, mode)`

**Responsabilidade:** Persistir DataFrame em arquivo Parquet.

**Parâmetros:**
- `df` (pd.DataFrame): DataFrame de voltas enriquecido
- `year` (int): Ano da temporada
- `gp` (int): Número do GP
- `mode` (str): Modo da sessão

**Comportamento:**
1. Constrói nome do arquivo: `f"data/laps/{year}_{gp:02}_{mode}.parquet"`
   - Usa formatação `{gp:02}` para zero-padding (ex: `01`, `02`, ..., `24`)
2. Salva usando `df.to_parquet(filename, index=False)`

**Observações:**
- Assume que o diretório `data/laps/` já existe (será criado na implementação)
- Caminho relativo à raiz do projeto (script deve ser executado da raiz)

---

#### `process(self, year, gp, mode) -> bool`

**Responsabilidade:** Processar uma única sessão (obter + salvar).

**Parâmetros:**
- `year` (int): Ano da temporada
- `gp` (int): Número do GP
- `mode` (str): Modo da sessão

**Comportamento:**
1. Chama `get_data(year, gp, mode)`
2. Se DataFrame vazio → retorna `False`
3. Se DataFrame válido:
   - Chama `save_data(df, year, gp, mode)`
   - Sleep de 1 segundo (`time.sleep(1)`)
   - Retorna `True`

**Retorno:**
- `True`: Sessão processada com sucesso
- `False`: Sessão não encontrada (fim dos GPs do ano)

---

#### `process_year_modes(self, year)`

**Responsabilidade:** Processar todos os GPs e modos de um ano específico.

**Parâmetros:**
- `year` (int): Ano da temporada

**Comportamento:**
1. Loop de `i` de 1 a 30 (máximo de GPs possíveis)
2. Loop interno nos `self.modes` (ex: ["R", "S"])
3. Para cada combinação (year, gp, mode):
   - Chama `process(year, i, mode)`
   - Se modo == "R" e retornou `False` → `return` (encerra o ano)

**Lógica de parada antecipada:**
- Apenas o modo "R" (Race) é usado como critério de parada
- Assume que se a corrida não existe, o sprint também não existirá
- Evita tentativas desnecessárias de GPs futuros

---

#### `process_years(self)`

**Responsabilidade:** Processar todos os anos configurados.

**Comportamento:**
1. Loop em `self.years`
2. Para cada ano:
   - Faz log: `logger.info(f'Coletando voltas do ano {year}')`
   - Chama `process_year_modes(year)`
   - Sleep de 10 segundos (`time.sleep(10)`)

**Observações:**
- Sem log por GP individual (mantém simplicidade)
- Sleep entre anos para evitar sobrecarga da API fastf1

---

### Interface CLI

#### Bloco `if __name__ == "__main__"`

**Responsabilidade:** Permitir execução standalone via linha de comando.

**Argumentos (argparse):**
- `--start` (int): Ano inicial do range (default: 0)
- `--stop` (int): Ano final do range (default: 0)
- `--years` / `-y` (nargs="+"): Lista de anos específicos
- `--modes` / `-m` (nargs="+"): Modos a coletar (ex: R, S)

**Lógica:**
1. Se `--years` fornecido:
   - Usa `args.years` diretamente
2. Else se `--start` e `--stop` fornecidos:
   - Gera range: `[i for i in range(args.start, args.stop + 1)]`
3. Instancia `CollectLaps(years, args.modes)`
4. Chama `collect.process_years()`

**Exemplos de uso:**
```bash
# Coletar voltas de 2024 e 2025, apenas corridas
python src/laps/extract_session_laps.py --years 2024 2025 --modes R

# Coletar range de anos com corridas e sprints
python src/laps/extract_session_laps.py --start 2021 --stop 2025 --modes R S

# Coletar apenas sprints de 2023
python src/laps/extract_session_laps.py --years 2023 --modes S
```

---

## Fluxo de Dados

```
fastf1.get_session(year, gp, mode)
    ↓
session.load()  (carga completa - diferente de collect.py)
    ↓
session.laps  (DataFrame de voltas - diferente de session.results)
    ↓
Enriquecimento:
  + event_date    (session.event["EventDate"])
  + event_name    (session.event["EventName"])
  + event_location (session.event["Location"])
  + event_country  (session.event["Country"])
    ↓
data/laps/{year}_{gp:02}_{mode}.parquet
```

---

## Logging

**Padrão:**
- Importação: `from logs.logger import get_logger`
- Inicialização: `logger = get_logger(__name__)`
- Idioma: Português (seguindo padrão do projeto)

**Mensagens:**
- `logger.info(f'Coletando voltas do ano {year}')` → Início de processamento de cada ano
- Sem log de erro em `get_data()` (comportamento silencioso quando sessão não existe)
- Sem log por GP (mantém simplicidade)

---

## Tratamento de Erros

**Em `get_data()`:**
- **Erro esperado:** `ValueError` quando sessão não existe
- **Comportamento:** Retornar `pd.DataFrame()` vazio
- **Sem logging:** Sessão inexistente é comportamento normal (fim dos GPs)

**Em `save_data()`:**
- Não trata erros de I/O (segue padrão de `collect.py`)
- Permite exceções propagarem (falha deve ser visível)

---

## Diferenças vs collect.py

| Aspecto | collect.py | extract_session_laps.py |
|---------|-----------|-------------------------|
| **Método de carga** | `session._load_drivers_results()` | `session.load()` |
| **Fonte de dados** | `session.results` | `session.laps` |
| **Colunas adicionadas** | Mode, Year, Date, RoundNumber, OfficialEventName, EventName, Country, Location | event_date, event_name, event_location, event_country |
| **Diretório de saída** | `data/` | `data/laps/` |
| **Propósito** | Resultados finais de pilotos | Dados detalhados de voltas |

---

## Padrões de Código

**Nomenclatura:**
- Classe: `CollectLaps` (PascalCase)
- Métodos: `get_data`, `save_data`, `process_year_modes` (snake_case)
- Variáveis: `year`, `gp`, `mode` (snake_case)

**Type Hints:**
- Usar em métodos públicos
- Retorno de `get_data`: `-> pd.DataFrame` (não `pd.DataFrame()`)
- Retorno de `process`: `-> bool`

**Imports (ordem PEP 8):**
```python
# 1. Stdlib
import time
import argparse

# 2. Third-party
import fastf1
import pandas as pd

# 3. Local (relativo ao src/)
from logs.logger import get_logger
```

**Marcadores de célula Jupyter:**
- Usar `# %%` para compatibilidade com VS Code/Jupyter

---

## Arquivos a Criar/Modificar

**Criar:**
1. `src/laps/__init__.py` (vazio, marca como pacote)
2. `data/laps/` (diretório, vazio)

**Modificar:**
1. `src/laps/extract_session_laps.py` (substituir esboço pela implementação completa)

**Não modificar:**
- `src/main.py` (integração adiada para o futuro)
- `.gitignore` (já ignora `data/`)

---

## Casos de Uso

**Caso 1: Coletar voltas do ano corrente**
```bash
python src/laps/extract_session_laps.py --years 2025 --modes R S
```

**Caso 2: Coletar histórico completo**
```bash
python src/laps/extract_session_laps.py --start 2021 --stop 2025 --modes R S
```

**Caso 3: Coletar apenas corridas (sem sprints)**
```bash
python src/laps/extract_session_laps.py --start 2023 --stop 2025 --modes R
```

**Caso 4: Futuro - Integração com main.py**
```python
# (Não implementado agora)
from laps.extract_session_laps import CollectLaps

collect_laps = CollectLaps(years=[2025], modes=["R", "S"])
collect_laps.process_years()
```

---

## Validação da Implementação

**Critérios de sucesso:**
1. Classe `CollectLaps` segue estrutura de `Collect`
2. CLI aceita mesmos argumentos de `collect.py`
3. Arquivos Parquet salvos em `data/laps/` com nomenclatura correta
4. DataFrame contém dados brutos de `session.laps` + 4 colunas de evento
5. Logging segue padrão do projeto (português, usando `logger`)
6. Parada antecipada funciona quando modo "R" não encontra sessão

**Teste manual sugerido:**
```bash
# Deve criar data/laps/2025_01_R.parquet
python src/laps/extract_session_laps.py --years 2025 --modes R

# Verificar conteúdo
python -c "import pandas as pd; df = pd.read_parquet('data/laps/2025_01_R.parquet'); print(df.columns); print(df.shape)"
```

---

## Notas de Implementação

**Criação do diretório `data/laps/`:**
- Adicionar checagem/criação automática no método `save_data()` ou no `__init__`
- Usar `Path` da stdlib para portabilidade

**Caminho relativo vs absoluto:**
- Código atual usa caminho relativo `"data/laps/..."`
- Considerar usar `Path(__file__).parent.parent / "data" / "laps"` para robustez
- Por consistência com `collect.py`, manter caminho relativo (usuário deve executar da raiz)

**Futuras integrações:**
- Quando integrar com `main.py`, parametrizar diretório de saída
- Reutilizar classe `Load` para upload S3 (parametrizar `data_dir="data/laps"`)

---

## Questões em Aberto

**Nenhuma** — Design aprovado e completo.
