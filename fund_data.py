# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 13:24:50 2022

@author: mik13
"""

import pandas as pd
#from finpieloc import finpie as fp
from macrotrends import MacrotrendsData

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

#driver = webdriver.Chrome(ChromeDriverManager().install())


class FundamentalDataOrganizer:

    def __init__(self, ticker="AAPL", freq="A"):
        self.ticker = ticker
        self.freq = freq

    def save_bulk(self, path):
        intrin = pd.read_csv(path).dropna()

        for i in intrin["Symbol"]:
            try:
                pd.read_pickle(f"data/income_statements/annual/{i}.pkl")
            except:
                i = i.replace("-",".")
                try:
                    self.organize_data(i)
                except:
                    i = i.replace(".","-")
                    intrin = intrin.drop(intrin.loc[intrin["Symbol"] == i].index)
                    intrin.to_csv(path)

        pass

    def organize_data(self, ticker, freq="A"):
        income, balance, cf = self._get_data(ticker, freq=freq)
        cf["free_cf"] = cf["cash_flow_from_operating_activities"] + \
            cf["net_change_in_property,_plant,_and_equipment"]
        income.to_pickle(f"data/income_statements/annual/{ticker}.pkl")
        balance.to_pickle(f"data/balance_sheets/annual/{ticker}.pkl")
        cf.to_pickle(f"data/cash_flow_statements/annual/{ticker}.pkl")

    def _get_data(self, ticker, freq="A"):
        #data = fp.Fundamentals(ticker, source=source, freq=freq)
        income = MacrotrendsData(ticker, freq=freq).income_statement()
        balance = MacrotrendsData(ticker, freq=freq).balance_sheet()
        cf = MacrotrendsData(ticker, freq=freq).cashflow_statement()

        return income, balance, cf


if __name__ == "__main__":

    org_ins = FundamentalDataOrganizer()
    data = org_ins.save_bulk(path="data/companies_long.csv")
