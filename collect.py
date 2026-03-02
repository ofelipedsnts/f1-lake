#%%
import fastf1
import pandas as pd
import time
import argparse

pd.set_option('display.max_columns', None)
# %%

class Collect:
    def __init__(self, years=[2021, 2022, 2023, 2024, 2025], modes=["R", "S"]):
        self.years = years
        self.modes = modes

    
    def get_data(self, year, gp, mode) -> pd.DataFrame():
        try:
            session = fastf1.get_session(year, gp, mode)
        
        except ValueError as err:
            return pd.DataFrame()

        session._load_drivers_results()

        df = session.results

        df["Mode"] = mode
        return df


    def save_data(self, df, year, gp, mode):
        df.to_parquet(f"data/{year}-{gp:02}-{mode}.parquet")


    def process(self, year):
        for i in range(1,50):
            print(f"processando GP {i}")

            for m in self.modes: 
                print(f"processando mode {m}")
                df = self.get_data(year, i, m)

                if df.empty:
                    continue

                self.save_data(df, year, i, m)

    
    def extract_data(self):
        for year in self.years:
            print(f"coletando dados do ano {year}")
            self.process(year)
            time.sleep(10)

# %%
parser = argparse.ArgumentParser()

parser.add_argument("--years", "-y", nargs="+", type=int)
parser.add_argument("--modes", "-m", nargs="+")
args = parser.parse_args()

collect = Collect(args.years, args.modes)
collect.extract_data()