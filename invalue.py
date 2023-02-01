# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 13:24:34 2022

@author: mik13
"""

import pandas as pd
import yfinance as yf
from scipy import stats
from fund_data import FundamentalDataOrganizer
#from finpieloc import finpie as fp


#driver = webdriver.Chrome(ChromeDriverManager().install())

class IntrinsicValue:

    def __init__(self):
        pass

    def calculate_intrin(self, path = "data/intrin.csv", rate=0.08):
        intrin = pd.read_csv(path)
        finished = 0
        for ticker in intrin["Symbol"]:
            notes = []
            # try:
            # tick = yf.Ticker(ticker.replace(".","-"))
            hist = yf.Ticker(ticker.replace(".","-"))
            tick_info = hist.fast_info

            # print(hist)
            price = tick_info["previous_close"]
            try:
                dividend = hist.dividends.iloc[0]
            except IndexError:
                dividend = 0

            data = self._get_data(ticker)

            data = data.iloc[-10:]
            data = data.reset_index()

            data["book"] = data["equity"] / data["shares"]
            data["eps"] = data["net_income"] / data["shares"]
            data["cfps"] = data["free_cf"] / data["shares"]

            slope, intercept, r_value, p_value, std_err = stats.linregress(
                data.index, data["book"])
            if slope < 0:
                notes.append("book decreasing")
            if intercept < 0:
                notes.append("book0 negative")
            data["book_model"] = data.index*slope+intercept
            data["book_change"] = (
                data["book"] - data["book"].shift(1)) / data["book"].shift(1) * 100
            data["book_model_change"] = (
                data["book_model"] - data["book_model"].shift(1)) / data["book_model"].shift(1) * 100

            book_change = slope
            if book_change > 25:
                notes.append("high book growth")
            if book_change < 5:
                notes.append("low book growth")
            book_start = data["book"].iloc[-1]

            slope, intercept, r_value, p_value, std_err = stats.linregress(
                data.index, data["eps"])
            if slope < 0:
                notes.append("eps decreasing")
            if intercept < 0:
                notes.append("eps0 negative")
            data["eps_model"] = data.index*slope+intercept
            data["eps_change"] = (
                data["eps"] - data["eps"].shift(1)) / data["eps"].shift(1) * 100
            data["eps_model_change"] = (
                data["eps_model"] - data["eps_model"].shift(1)) / data["eps_model"].shift(1) * 100

            eps_change = slope
            if eps_change > 25:
                notes.append("high eps growth")
            if eps_change < 5:
                notes.append("low eps growth")
            eps_start = data["eps_model"].iloc[-1]

            slope, intercept, r_value, p_value, std_err = stats.linregress(
                data.index, data["cfps"])
            if slope < 0:
                notes.append("fc decreasing")
            if intercept < 0:
                notes.append("fc0 negative")
            data["cfps_model"] = data.index*slope+intercept
            data["cfps_change"] = (
                data["cfps"] - data["cfps"].shift(1)) / data["cfps"].shift(1) * 100
            data["cfps_model_change"] = (
                data["cfps_model"] - data["cfps_model"].shift(1)) / data["cfps_model"].shift(1) * 100

            cfps_change = slope
            cfps_start = data["cfps_model"].iloc[-1]

            fc_data = pd.DataFrame({"year": range(11)})
            fc_data["book"] = book_start
            for i in fc_data["year"].iloc[:-1]:
                fc_data.loc[fc_data["year"] == i+1, "book"] = (fc_data.loc[fc_data["year"]== i]["book"] + cfps_change).iloc[0]
                fc_data["book"] = fc_data["book"] + dividend*fc_data["year"]

            fc_data["eps"] = eps_start
            fc_data["eps_sum"] = eps_start
            for i in fc_data["year"].iloc[:-1]:
                fc_data.loc[fc_data["year"] == i+1, "eps"] = (fc_data.loc[fc_data["year"]== i]["eps"] + cfps_change).iloc[0]
                fc_data.loc[fc_data["year"] == i+1, "eps_sum"] = fc_data["eps"][0:i+2].sum()

            fc_data["cf"] = cfps_start
            fc_data["cf_sum"] = cfps_start
            for i in fc_data["year"].iloc[:-1]:
                fc_data.loc[fc_data["year"] == i+1, "cf"] = (fc_data.loc[fc_data["year"]== i]["cf"] + cfps_change).iloc[0]
                fc_data.loc[fc_data["year"] == i+1, "cf_sum"] = fc_data["cf"][0:i+2].sum()

            book5 = fc_data["book"][5] / ((1+rate)**5)
            book10 = fc_data["book"][10] / ((1+rate)**10)

            eps5 = (fc_data["eps_sum"][5] + price) / ((1+rate)**5)
            eps10 = (fc_data["eps_sum"][10] + price) / ((1+rate)**10)

            fc5 = (fc_data["cf_sum"][5] + price) / ((1+rate)**5)
            fc10 = (fc_data["cf_sum"][10] + price) / ((1+rate)**10)

            intr_val = sum([book5, book10, eps5, eps10, fc5, fc10]) / 6
            
            intrin.loc[intrin["Symbol"] == ticker, "INTR"] = intr_val
            intrin.loc[intrin["Symbol"] == ticker, "notes"] = ", ".join(notes)
            intrin.loc[intrin["Symbol"] == ticker, "Updated"] = data["date"].iloc[-1].year

            finished += 1

            print(f"{round((finished / len(intrin))*100,2)} % Finished")
            # except:
            #     print("Error when trying to fetch price for {}".format(ticker))
            #     notes.append("Error")
            #     intrin.loc[intrin["Symbol"] == ticker, "notes"] = ", ".join(notes)


        pass
        intrin.to_csv(path, index=False)

    def organize_data(self):
        pass

    def _get_data(self, ticker):
        try:
            inc = pd.read_pickle(f"data/income_statements/annual/{ticker.replace('-','.')}.pkl")
            bal = pd.read_pickle(f"data/balance_sheets/annual/{ticker.replace('-','.')}.pkl")
            cf = pd.read_pickle(f"data/cash_flow_statements/annual/{ticker.replace('-','.')}.pkl")
        except FileNotFoundError:
            inst = FundamentalDataOrganizer(ticker=ticker.replace('-','.'))
            inst.organize_data(ticker=ticker.replace('-','.'))

            inc = pd.read_pickle(f"data/income_statements/annual/{ticker.replace('-','.')}.pkl")
            bal = pd.read_pickle(f"data/balance_sheets/annual/{ticker.replace('-','.')}.pkl")
            cf = pd.read_pickle(f"data/cash_flow_statements/annual/{ticker.replace('-','.')}.pkl")


        data = pd.concat([inc["shares_outstanding"], inc["net_income"],
                         bal["share_holder_equity"], cf["free_cf"]], axis=1)

        data = data.rename(
            columns={"shares_outstanding": "shares", "share_holder_equity": "equity"})

        return data


if __name__ == "__main__":

    org_ins = IntrinsicValue()
    data = org_ins.calculate_intrin(path="data/companies_long.csv")
