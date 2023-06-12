# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 13:24:50 2022

@author: mik13
"""

import pandas as pd

# from finpieloc import finpie as fp
from macrotrends import MacrotrendsData

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

import warnings

warnings.filterwarnings("ignore")
import gc

# driver = webdriver.Chrome(ChromeDriverManager().install())


class FundamentalDataOrganizer:
    def __init__(self, ticker="AAPL", freq="A"):
        self.ticker = ticker
        self.freq = freq

    def save_bulk(self, path, freq="A", update=False, update_date="2022"):
        intrin = pd.read_csv(path).dropna()
        finished = 0
        if update:
            for i in intrin["Symbol"]:
                try:
                    self.update_data(i, freq=freq, last_date=update_date)
                except:
                    intrin = intrin.drop(intrin.loc[intrin["Symbol"] == i].index)
                    intrin.to_csv(path)
                finished += 1
                print(
                    f"Finised updating {(finished / len(intrin)) * 100} % of the tickers..."
                )

        else:
            for i in intrin["Symbol"]:
                try:
                    pd.read_pickle(f"data/income_statements/annual/{i}.pkl")
                except:
                    i = i.replace("-", ".")
                    try:
                        self.organize_data(i, freq=freq)
                    except:
                        i = i.replace(".", "-")
                        intrin = intrin.drop(intrin.loc[intrin["Symbol"] == i].index)
                        intrin.to_csv(path)

    def organize_data(self, ticker, freq="A"):
        income, balance, cf = self._get_data(ticker, freq=freq)
        cf["free_cf"] = (
            cf["cash_flow_from_operating_activities"]
            + cf["net_change_in_property,_plant,_and_equipment"]
        )
        income.to_pickle(f"data/income_statements/annual/{ticker}.pkl")
        balance.to_pickle(f"data/balance_sheets/annual/{ticker}.pkl")
        cf.to_pickle(f"data/cash_flow_statements/annual/{ticker}.pkl")

        del income, balance, cf
        gc.collect()

    def update_data(self, ticker, freq="A", last_date="2022"):
        try:
            inc = pd.read_pickle(
                f"data/income_statements/annual/{ticker.replace('-','.')}.pkl"
            )
            bal = pd.read_pickle(
                f"data/balance_sheets/annual/{ticker.replace('-','.')}.pkl"
            )
            cf = pd.read_pickle(
                f"data/cash_flow_statements/annual/{ticker.replace('-','.')}.pkl"
            )
            if inc.index[-1] < pd.Timestamp(last_date):
                inc_new, bal_new, cf_new = self._get_data(ticker, freq=freq)
                cf_new["free_cf"] = (
                    cf_new["cash_flow_from_operating_activities"]
                    + cf_new["net_change_in_property,_plant,_and_equipment"]
                )

                income = inc.combine_first(inc_new)
                balance = bal.combine_first(bal_new)
                cashflow = cf.combine_first(cf_new)

                income.to_pickle(f"data/income_statements/annual/{ticker}.pkl")
                balance.to_pickle(f"data/balance_sheets/annual/{ticker}.pkl")
                cashflow.to_pickle(f"data/cash_flow_statements/annual/{ticker}.pkl")
                print(f"Updated {ticker} data to {last_date}!")
                del inc, bal, cf, inc_new, bal_new, cf_new, income, balance, cashflow
            else:
                print(f"{ticker} already updated to {last_date}, skipping...")
                del inc, bal, cf

        except FileNotFoundError:
            income, balance, cf = self._get_data(ticker, freq=freq)
            cf["free_cf"] = (
                cf["cash_flow_from_operating_activities"]
                + cf["net_change_in_property,_plant,_and_equipment"]
            )
            income.to_pickle(f"data/income_statements/annual/{ticker}.pkl")
            balance.to_pickle(f"data/balance_sheets/annual/{ticker}.pkl")
            cf.to_pickle(f"data/cash_flow_statements/annual/{ticker}.pkl")

            del income, balance, cf

        gc.collect()

    def _get_data(self, ticker, freq="A"):
        # data = fp.Fundamentals(ticker, source=source, freq=freq)
        income = MacrotrendsData(ticker, freq=freq).income_statement()
        balance = MacrotrendsData(ticker, freq=freq).balance_sheet()
        cf = MacrotrendsData(ticker, freq=freq).cashflow_statement()

        return income, balance, cf


if __name__ == "__main__":
    org_ins = FundamentalDataOrganizer()
    # org_ins.update_data("DISH", freq="A")
    data = org_ins.save_bulk(
        path="data/companies_long.csv", update=True, update_date="2022"
    )
