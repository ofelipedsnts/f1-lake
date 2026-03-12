# Laps Collection Module Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a standalone CLI module to collect F1 session laps data via fastf1 and persist to Parquet files.

**Architecture:** Mirror `src/collect.py` structure with `CollectLaps` class containing methods for data acquisition, enrichment, persistence, and orchestration. CLI uses argparse for year/mode selection.

**Tech Stack:** Python 3.9, fastf1, pandas, argparse, logging (centralized via `logs.logger`)

**Spec Reference:** `docs/superpowers/specs/2026-03-12-laps-collection-design.md`

---

## Chunk 1: Foundation

### Task 1: Create Package Structure

**Files:**
- Create: `src/laps/__init__.py`
- Create: `data/laps/.gitkeep`

- [ ] **Step 1: Create laps package marker**

Create empty `src/laps/__init__.py` to mark directory as Python package.

```python
# src/laps/__init__.py
# Empty file - marks laps/ as a Python package
```

- [ ] **Step 2: Create data/laps directory with .gitkeep**

Ensure `data/laps/` exists and is tracked by git (empty directories need .gitkeep).

```bash
mkdir -p data/laps
touch data/laps/.gitkeep
```

- [ ] **Step 3: Verify .gitignore covers data/*.parquet**

Run: `grep -r "data/" .gitignore`
Expected: `.gitignore` contains pattern that excludes `data/` contents (but not the directory itself)

- [ ] **Step 4: Commit package structure**

```bash
git add src/laps/__init__.py data/laps/.gitkeep
git commit -m "feat(laps): create package structure and data directory"
```

---

### Task 2: Implement CollectLaps.__init__

**Files:**
- Modify: `src/laps/extract_session_laps.py`

- [ ] **Step 1: Add imports and logger setup**

Create file with content:

```python
# %%
import time
import argparse
from pathlib import Path

import fastf1
import pandas as pd

from logs.logger import get_logger

pd.set_option('display.max_columns', None)

logger = get_logger(__name__)

# %%


class CollectLaps:
    def __init__(self, years=[2021, 2022, 2023, 2024, 2025], modes=["R", "S"]):
        self.years = years
        self.modes = modes
```

- [ ] **Step 2: Verify imports resolve**

Run from project root:
```bash
python -c "import sys; sys.path.insert(0, 'src'); from laps.extract_session_laps import CollectLaps; print('Imports OK')"
```

Expected: `Imports OK` (no import errors)

- [ ] **Step 3: Commit initialization**

```bash
git add src/laps/extract_session_laps.py
git commit -m "feat(laps): add CollectLaps class with __init__"
```

---

### Task 3: Implement CollectLaps.get_data

**Files:**
- Modify: `src/laps/extract_session_laps.py`

- [ ] **Step 1: Add get_data method**

Add method to `CollectLaps` class:

```python
    def get_data(self, year: int, gp: int, mode: str) -> pd.DataFrame:
        try:
            session = fastf1.get_session(year, gp, mode)
        except ValueError:
            return pd.DataFrame()

        session.load()

        df = session.laps

        df["event_date"] = session.event["EventDate"]
        df["event_name"] = session.event["EventName"]
        df["event_location"] = session.event["Location"]
        df["event_country"] = session.event["Country"]

        return df
```

- [ ] **Step 2: Manual test - valid session**

Test with known valid session (2025 Australian GP):

```python
# Test script: test_get_data_valid.py
import sys
sys.path.insert(0, 'src')
from laps.extract_session_laps import CollectLaps

collector = CollectLaps()
df = collector.get_data(2025, 1, 'R')

print(f"Shape: {df.shape}")
print(f"Columns include event_date: {'event_date' in df.columns}")
print(f"Columns include event_name: {'event_name' in df.columns}")
print(f"Columns include event_location: {'event_location' in df.columns}")
print(f"Columns include event_country: {'event_country' in df.columns}")
```

Run: `python test_get_data_valid.py`

Expected:
- Shape: `(XXX, YYY)` (non-empty DataFrame)
- All 4 event columns present: `True`

- [ ] **Step 3: Manual test - invalid session**

Test with non-existent session:

```python
# Test script: test_get_data_invalid.py
import sys
sys.path.insert(0, 'src')
from laps.extract_session_laps import CollectLaps

collector = CollectLaps()
df = collector.get_data(2025, 99, 'R')

print(f"Is empty: {df.empty}")
print(f"Shape: {df.shape}")
```

Run: `python test_get_data_invalid.py`

Expected:
- `Is empty: True`
- `Shape: (0, 0)`

- [ ] **Step 4: Clean up test scripts**

```bash
rm test_get_data_valid.py test_get_data_invalid.py
```

- [ ] **Step 5: Commit get_data method**

```bash
git add src/laps/extract_session_laps.py
git commit -m "feat(laps): add get_data method with event enrichment"
```

---

### Task 4: Implement CollectLaps.save_data

**Files:**
- Modify: `src/laps/extract_session_laps.py`

- [ ] **Step 1: Add save_data method**

Add method to `CollectLaps` class:

```python
    def save_data(self, df: pd.DataFrame, year: int, gp: int, mode: str):
        # Ensure data/laps directory exists
        Path("data/laps").mkdir(parents=True, exist_ok=True)
        
        filename = f"data/laps/{year}_{gp:02}_{mode}.parquet"
        df.to_parquet(filename, index=False)
```

- [ ] **Step 2: Manual test - save valid DataFrame**

```python
# Test script: test_save_data.py
import sys
sys.path.insert(0, 'src')
from laps.extract_session_laps import CollectLaps
from pathlib import Path

collector = CollectLaps()
df = collector.get_data(2025, 1, 'R')

if not df.empty:
    collector.save_data(df, 2025, 1, 'R')
    
    # Verify file exists
    filepath = Path("data/laps/2025_01_R.parquet")
    print(f"File exists: {filepath.exists()}")
    
    # Verify file is readable
    import pandas as pd
    df_read = pd.read_parquet(filepath)
    print(f"Read shape: {df_read.shape}")
    print(f"Event columns present: {all(col in df_read.columns for col in ['event_date', 'event_name', 'event_location', 'event_country'])}")
else:
    print("ERROR: get_data returned empty DataFrame")
```

Run: `python test_save_data.py`

Expected:
- `File exists: True`
- `Read shape: (XXX, YYY)` (matches original DataFrame)
- `Event columns present: True`

- [ ] **Step 3: Verify filename formatting (zero-padding)**

Check that file uses `01` not `1`:

```bash
ls -la data/laps/
```

Expected: `2025_01_R.parquet` (with zero-padding)

- [ ] **Step 4: Clean up test files**

```bash
rm test_save_data.py
rm data/laps/2025_01_R.parquet
```

- [ ] **Step 5: Commit save_data method**

```bash
git add src/laps/extract_session_laps.py
git commit -m "feat(laps): add save_data method with directory creation"
```

---

## Chunk 2: Orchestration & CLI

### Task 5: Implement CollectLaps.process

**Files:**
- Modify: `src/laps/extract_session_laps.py`

- [ ] **Step 1: Add process method**

Add method to `CollectLaps` class:

```python
    def process(self, year: int, gp: int, mode: str) -> bool:
        df = self.get_data(year, gp, mode)

        if df.empty:
            return False

        self.save_data(df, year, gp, mode)
        time.sleep(1)
        return True
```

- [ ] **Step 2: Manual test - successful process**

```python
# Test script: test_process_success.py
import sys
sys.path.insert(0, 'src')
from laps.extract_session_laps import CollectLaps
from pathlib import Path

collector = CollectLaps()
result = collector.process(2025, 1, 'R')

print(f"Process returned: {result}")
print(f"File created: {Path('data/laps/2025_01_R.parquet').exists()}")
```

Run: `python test_process_success.py`

Expected:
- `Process returned: True`
- `File created: True`

- [ ] **Step 3: Manual test - failed process (invalid session)**

```python
# Test script: test_process_fail.py
import sys
sys.path.insert(0, 'src')
from laps.extract_session_laps import CollectLaps
from pathlib import Path

collector = CollectLaps()
result = collector.process(2025, 99, 'R')

print(f"Process returned: {result}")
print(f"File created: {Path('data/laps/2025_99_R.parquet').exists()}")
```

Run: `python test_process_fail.py`

Expected:
- `Process returned: False`
- `File created: False`

- [ ] **Step 4: Clean up test files**

```bash
rm test_process_success.py test_process_fail.py
rm -f data/laps/2025_01_R.parquet
```

- [ ] **Step 5: Commit process method**

```bash
git add src/laps/extract_session_laps.py
git commit -m "feat(laps): add process method with boolean return"
```

---

### Task 6: Implement CollectLaps.process_year_modes

**Files:**
- Modify: `src/laps/extract_session_laps.py`

- [ ] **Step 1: Add process_year_modes method**

Add method to `CollectLaps` class:

```python
    def process_year_modes(self, year: int):
        for i in range(1, 30):
            for mode in self.modes:
                if not self.process(year, i, mode) and mode == "R":
                    return
```

- [ ] **Step 2: Manual test - early stopping**

Test that method stops when Race mode returns False:

```python
# Test script: test_process_year_modes.py
import sys
sys.path.insert(0, 'src')
from laps.extract_session_laps import CollectLaps
from pathlib import Path

# Use a past year with known GPs (e.g., 2023 had 22 races)
collector = CollectLaps(years=[2023], modes=["R"])
collector.process_year_modes(2023)

# Count created files
files = list(Path('data/laps').glob('2023_*_R.parquet'))
print(f"Files created: {len(files)}")
print(f"Expected: ~22 (2023 season had 22 races)")
print(f"Not 30: {len(files) < 30}")
```

Run: `python test_process_year_modes.py` (WARNING: This will take several minutes due to fastf1 API calls)

Expected:
- `Files created: 22` (or close to it)
- `Not 30: True` (early stopping worked)

**Note:** This test is time-consuming. Consider skipping if confident in logic, or test with single GP range:

```python
# Faster alternative test
collector = CollectLaps(years=[2025], modes=["R"])
# Manually test just GP 1-3
for i in range(1, 4):
    result = collector.process(2025, i, "R")
    print(f"GP {i}: {result}")
```

- [ ] **Step 3: Clean up test files**

```bash
rm test_process_year_modes.py
rm -f data/laps/2023_*.parquet
rm -f data/laps/2025_*.parquet
```

- [ ] **Step 4: Commit process_year_modes method**

```bash
git add src/laps/extract_session_laps.py
git commit -m "feat(laps): add process_year_modes with early stopping"
```

---

### Task 7: Implement CollectLaps.process_years

**Files:**
- Modify: `src/laps/extract_session_laps.py`

- [ ] **Step 1: Add process_years method**

Add method to `CollectLaps` class:

```python
    def process_years(self):
        for year in self.years:
            logger.info(f'Coletando voltas do ano {year}')
            self.process_year_modes(year)
            time.sleep(10)
```

- [ ] **Step 2: Manual test - logging verification**

```python
# Test script: test_process_years_logging.py
import sys
sys.path.insert(0, 'src')
from laps.extract_session_laps import CollectLaps

# Test with single recent year and only first GP
collector = CollectLaps(years=[2025], modes=["R"])

# Manually override to process only GP 1
original_method = collector.process_year_modes
def limited_process(year):
    collector.process(year, 1, "R")

collector.process_year_modes = limited_process
collector.process_years()
```

Run: `python test_process_years_logging.py`

Expected output includes:
```
INFO:laps.extract_session_laps:Coletando voltas do ano 2025
```

- [ ] **Step 3: Clean up test files**

```bash
rm test_process_years_logging.py
rm -f data/laps/2025_01_R.parquet
```

- [ ] **Step 4: Commit process_years method**

```bash
git add src/laps/extract_session_laps.py
git commit -m "feat(laps): add process_years with logging"
```

---

### Task 8: Implement CLI Interface

**Files:**
- Modify: `src/laps/extract_session_laps.py`

- [ ] **Step 1: Add CLI block**

Add at end of file (after class definition):

```python
# %%
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int, default=0)
    parser.add_argument("--years", "-y", nargs="+", type=int)
    parser.add_argument("--modes", "-m", nargs="+")
    args = parser.parse_args()

    if args.years:
        collect = CollectLaps(args.years, args.modes)

    elif args.start and args.stop:
        years = [i for i in range(args.start, args.stop + 1)]
        collect = CollectLaps(years, args.modes)

    collect.process_years()
```

- [ ] **Step 2: Test CLI - help message**

```bash
python src/laps/extract_session_laps.py --help
```

Expected: Displays help with `--start`, `--stop`, `--years`, `--modes` options

- [ ] **Step 3: Test CLI - years argument (dry run)**

Add temporary print before `process_years()`:

```python
    # Temporary debug
    print(f"Years: {collect.years}")
    print(f"Modes: {collect.modes}")
    # collect.process_years()
```

Run:
```bash
python src/laps/extract_session_laps.py --years 2024 2025 --modes R S
```

Expected:
```
Years: [2024, 2025]
Modes: ['R', 'S']
```

- [ ] **Step 4: Test CLI - start/stop argument (dry run)**

Run:
```bash
python src/laps/extract_session_laps.py --start 2021 --stop 2023 --modes R
```

Expected:
```
Years: [2021, 2022, 2023]
Modes: ['R']
```

- [ ] **Step 5: Remove debug print, uncomment process_years()**

Remove temporary debug lines, restore:

```python
    collect.process_years()
```

- [ ] **Step 6: Commit CLI interface**

```bash
git add src/laps/extract_session_laps.py
git commit -m "feat(laps): add CLI interface with argparse"
```

---

## Chunk 3: Integration Testing & Documentation

### Task 9: End-to-End Integration Test

**Files:**
- No file changes (manual testing)

- [ ] **Step 1: Full CLI test - single year, single mode**

Run actual collection for a small scope:

```bash
python src/laps/extract_session_laps.py --years 2025 --modes R
```

Expected:
- Log message: `INFO:laps.extract_session_laps:Coletando voltas do ano 2025`
- Files created in `data/laps/` with pattern `2025_XX_R.parquet`
- Process stops when no more races found (no error messages)

- [ ] **Step 2: Verify file content**

```python
# Verification script: verify_output.py
import pandas as pd
from pathlib import Path

files = sorted(Path('data/laps').glob('2025_*_R.parquet'))

if not files:
    print("ERROR: No files found")
else:
    print(f"Files created: {len(files)}")
    
    # Check first file
    df = pd.read_parquet(files[0])
    print(f"\nFirst file: {files[0].name}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {len(df.columns)}")
    
    required_cols = ['event_date', 'event_name', 'event_location', 'event_country']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        print(f"ERROR: Missing columns: {missing}")
    else:
        print("✓ All required event columns present")
        print(f"\nSample data:")
        print(df[required_cols].head(1))
```

Run: `python verify_output.py`

Expected:
- Multiple files created
- All required columns present
- Sample data shows valid event information

- [ ] **Step 3: Clean up verification script**

```bash
rm verify_output.py
```

- [ ] **Step 4: Clean up test data**

```bash
rm -f data/laps/2025_*.parquet
```

- [ ] **Step 5: Document successful integration test**

No commit needed - testing phase complete.

---

### Task 10: Update AGENTS.md Documentation

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Add laps module to project structure**

Locate the "Estrutura do Projeto" section and update it:

Replace the existing structure with:

```
f1-lake/
├── src/
│   ├── main.py          # Entry point — orquestra collect + load em loop infinito
│   ├── collect.py       # Coleta dados via fastf1, salva como .parquet em data/
│   ├── load.py          # Upload de .parquet para AWS S3 e remoção local
│   ├── laps/
│   │   ├── __init__.py
│   │   └── extract_session_laps.py  # Coleta dados de voltas (laps) via fastf1
│   └── logs/
│       ├── __init__.py  # Marca logs/ como pacote Python
│       └── logger.py    # Fábrica centralizada de loggers
├── notebooks/
│   └── drivers_stats.py # Script analítico PySpark — gera feature store de pilotos
├── data/                # Staging local de arquivos .parquet (não versionado)
│   └── laps/            # Subpasta para dados de voltas
├── .devcontainer/
│   ├── Dockerfile       # Python 3.9 + JDK (para Spark)
│   └── devcontainer.json
├── requirements.txt
└── .gitignore
```

- [ ] **Step 2: Add execution instructions**

Locate "Como Executar" section and add:

```markdown
# Rodar coleta de voltas (CLI)
python src/laps/extract_session_laps.py --years 2024 2025 --modes R S
python src/laps/extract_session_laps.py --start 2021 --stop 2025
```

- [ ] **Step 3: Add to Histórico de Alterações**

Add entry at the top of the changelog:

```markdown
| Data | Alteração |
|---|---|
| 2026-03-12 | Implementação do módulo de coleta de voltas (laps) em `src/laps/extract_session_laps.py` |
```

- [ ] **Step 4: Verify markdown formatting**

```bash
# Check if AGENTS.md is valid markdown
python -m markdown AGENTS.md > /dev/null && echo "✓ Valid markdown" || echo "✗ Invalid markdown"
```

Expected: `✓ Valid markdown`

- [ ] **Step 5: Commit AGENTS.md update**

```bash
git add AGENTS.md
git commit -m "docs: update AGENTS.md with laps collection module"
```

---

### Task 11: Create README Section (Optional)

**Files:**
- Modify: `README.md` (if exists and needs update)

- [ ] **Step 1: Check if README mentions data collection**

```bash
grep -i "collect" README.md
```

If README has a section about data collection, update it to mention laps collection.

- [ ] **Step 2: Add laps collection example (if applicable)**

Add to relevant section:

```markdown
### Coleta de Dados de Voltas

O módulo `extract_session_laps.py` coleta dados detalhados de voltas de cada sessão:

```bash
# Coletar voltas de anos específicos
python src/laps/extract_session_laps.py --years 2024 2025 --modes R S

# Coletar range de anos
python src/laps/extract_session_laps.py --start 2021 --stop 2025 --modes R
```
```

- [ ] **Step 3: Commit README update (if modified)**

```bash
git add README.md
git commit -m "docs: add laps collection to README"
```

**Note:** Skip this task if README doesn't need updating or doesn't exist.

---

## Chunk 4: Final Validation

### Task 12: Final Code Review Checklist

**Files:**
- Review: `src/laps/extract_session_laps.py`

- [ ] **Step 1: Verify code follows project patterns**

Review checklist:
- [ ] Uses `from logs.logger import get_logger` (not direct logging config)
- [ ] Type hints on public methods (`-> pd.DataFrame`, `-> bool`)
- [ ] Uses `snake_case` for methods and variables
- [ ] Uses `PascalCase` for class name
- [ ] Has `# %%` cell markers for Jupyter compatibility
- [ ] Logging in Portuguese
- [ ] No `print()` statements (uses logger)

- [ ] **Step 2: Compare structure with collect.py**

```bash
# Compare method names
grep "def " src/collect.py
grep "def " src/laps/extract_session_laps.py
```

Expected: Both files have parallel structure:
- `__init__`
- `get_data`
- `save_data`
- `process`
- `process_year_modes`
- `process_years`
- CLI block (`if __name__ == "__main__"`)

- [ ] **Step 3: Verify imports order (PEP 8)**

Check that imports follow order:
1. Stdlib (`time`, `argparse`, `pathlib`)
2. Third-party (`fastf1`, `pandas`)
3. Local (`from logs.logger import get_logger`)

- [ ] **Step 4: Check for code smells**

Review for:
- [ ] No hardcoded paths (uses `Path` or relative paths)
- [ ] No magic numbers (except range(1, 30) which is documented)
- [ ] No commented-out code
- [ ] Consistent spacing and formatting

- [ ] **Step 5: Document review completion**

No commit needed - checklist verification only.

---

### Task 13: Smoke Test - Full Execution

**Files:**
- No file changes (final testing)

- [ ] **Step 1: Clean data/laps directory**

```bash
rm -f data/laps/*.parquet
ls data/laps/
```

Expected: Only `.gitkeep` present (or directory empty)

- [ ] **Step 2: Run full collection for single year**

```bash
python src/laps/extract_session_laps.py --years 2024 --modes R
```

Expected:
- Process runs to completion
- Log messages in Portuguese
- Multiple `.parquet` files created
- No errors or exceptions

- [ ] **Step 3: Verify output files**

```bash
ls -lh data/laps/*.parquet | head -5
```

Expected:
- Files named `2024_01_R.parquet`, `2024_02_R.parquet`, etc.
- Non-zero file sizes

- [ ] **Step 4: Verify data integrity**

```python
# Quick integrity check
import pandas as pd
from pathlib import Path

files = list(Path('data/laps').glob('2024_*_R.parquet'))
print(f"Total files: {len(files)}")

# Check first and last file
for f in [files[0], files[-1]]:
    df = pd.read_parquet(f)
    required = ['event_date', 'event_name', 'event_location', 'event_country']
    print(f"{f.name}: {df.shape}, has all columns: {all(c in df.columns for c in required)}")
```

Expected:
- Multiple files found
- All files have required columns
- Non-empty DataFrames

- [ ] **Step 5: Clean up smoke test data**

```bash
rm -f data/laps/2024_*.parquet
```

- [ ] **Step 6: Final success confirmation**

All tests passed - implementation complete!

---

## Implementation Complete

**Deliverables:**
- ✅ `src/laps/__init__.py` - Package marker
- ✅ `src/laps/extract_session_laps.py` - Full implementation
- ✅ `data/laps/` - Output directory structure
- ✅ `AGENTS.md` - Updated documentation
- ✅ CLI interface with `--years`, `--start/stop`, `--modes`
- ✅ Logging in Portuguese via centralized logger
- ✅ Pattern consistency with `collect.py`

**Testing:**
- ✅ Unit-level manual tests for each method
- ✅ Integration test of full CLI workflow
- ✅ Smoke test with real data collection

**Next Steps:**
- Future: Integrate with `main.py` for automated collection
- Future: Create upload workflow to S3 using `Load` class
- Future: Add to scheduled pipeline execution

**Verification Command:**
```bash
python src/laps/extract_session_laps.py --years 2025 --modes R
```
