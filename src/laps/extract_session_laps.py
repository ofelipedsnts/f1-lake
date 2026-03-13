# %%
import sys
from pathlib import Path

# Adiciona src/ ao path ANTES de importar módulos locais
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import argparse

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

    def get_data(self, year: int, gp: int, mode: str) -> pd.DataFrame:
        try:
            session = fastf1.get_session(year, gp, mode)
        except ValueError:
            return pd.DataFrame()

        try:
            session.load()
        except Exception as e:
            logger.error(f"Erro ao carregar sessão {year} GP{gp} {mode}: {e}")
            return pd.DataFrame()

        df = session.laps

        df["event_date"] = session.event["EventDate"]
        df["event_name"] = session.event["EventName"]
        df["event_location"] = session.event["Location"]
        df["event_country"] = session.event["Country"]

        return df

    def save_data(self, df: pd.DataFrame, year: int, gp: int, mode: str) -> bool:
        try:
            Path("data/laps").mkdir(parents=True, exist_ok=True)
            
            filename = f"data/laps/{year}_{gp:02}_{mode}.parquet"
            df.to_parquet(filename, index=False)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo {year}_{gp:02}_{mode}.parquet: {e}")
            return False

    def process(self, year: int, gp: int, mode: str) -> bool:
        logger.info(f"Processando {year} GP{gp:02} {mode}")
        df = self.get_data(year, gp, mode)

        if df.empty:
            logger.warning(f"Sem dados para {year} GP{gp:02} {mode}")
            return False

        if not self.save_data(df, year, gp, mode):
            return False
        
        logger.info(f"Sucesso ao processar {year} GP{gp:02} {mode}")
        time.sleep(1)
        return True

    def process_year_modes(self, year: int) -> None:
        for i in range(1, 30):
            for mode in self.modes:
                if not self.process(year, i, mode) and mode == "R":
                    return

    def process_years(self) -> None:
        for year in self.years:
            logger.info(f'Coletando voltas do ano {year}')
            self.process_year_modes(year)
            time.sleep(10)


# %%
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int, default=0)
    parser.add_argument("--years", "-y", nargs="+", type=int)
    parser.add_argument("--modes", "-m", nargs="+")
    args = parser.parse_args()

    collect = None
    
    if args.years:
        collect = CollectLaps(args.years, args.modes)

    elif args.start and args.stop:
        years = [i for i in range(args.start, args.stop + 1)]
        collect = CollectLaps(years, args.modes)

    # Guard clause: prevent crash when no args provided
    if not collect:
        logger.error("Nenhum argumento fornecido. Use --years ou --start/--stop")
        parser.print_help()
        exit(1)

    collect.process_years()
