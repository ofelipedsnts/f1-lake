# %%
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

        df["Mode"] = session.name
        df["Year"] = session.date.year
        df["Date"] = session.date
        df["RoundNumber"] = session.event["RoundNumber"]
        df["OfficialEventName"] = session.event["OfficialEventName"]
        df["EventName"] = session.event["EventName"]
        df["Country"] = session.event["Country"]
        df["Location"] = session.event["Location"]

        return df

    def save_data(self, df, year, gp, mode):
        filename = f"data/{year}_{gp:02}_{mode}.parquet"
        df.to_parquet(filename, index=False)

    def process(self, year, gp, mode):
        df = self.get_data(year, gp, mode)

        if df.empty:
            return False

        self.save_data(df, year, gp, mode)
        time.sleep(1)
        return True

    def process_year_modes(self, year):
        for i in range(1, 30):
            for mode in self.modes:
                if not self.process(year, i, mode) and mode == "R":
                    return

    def process_years(self):
        for year in self.years:
            print(f"coletando dados do ano {year}")
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

    if args.years:
        collect = Collect(args.years, args.modes)

    elif args.start and args.stop:
        years = []

        years = [i for i in range(args.start, args.stop + 1)]
        collect = Collect(years, args.modes)

    collect.process_years()
