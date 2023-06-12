# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 13:24:34 2022

@author: mik13
"""

import pandas as pd
import yfinance as yf
from scipy import stats
from fund_data import FundamentalDataOrganizer
import plotly.graph_objects as go
import plotly.io as pio

# from finpieloc import finpie as fp


# driver = webdriver.Chrome(ChromeDriverManager().install())


class IntrinsicValue:
    def __init__(self):
        pass

    def calculate_intrin(self, path="data/intrin.csv", rate=0.08):
        intrin = pd.read_csv(path)
        finished = 0
        for ticker in intrin["Symbol"]:

            intr_val, notes, data = self._calculate_intr(ticker, rate)[:3]

            if intr_val:

                intrin.loc[intrin["Symbol"] == ticker, "INTR"] = intr_val
                intrin.loc[intrin["Symbol"] == ticker, "notes"] = ", ".join(notes)
                intrin.loc[intrin["Symbol"] == ticker, "Updated"] = (
                    data["date"].iloc[-1].year
                )

            else:
                print(f"Error loading {ticker}")

            finished += 1

            print(f"{round((finished / len(intrin))*100,2)} % Finished")
            # except:
            #     print("Error when trying to fetch price for {}".format(ticker))
            #     notes.append("Error")
            #     intrin.loc[intrin["Symbol"] == ticker, "notes"] = ", ".join(notes)

        intrin.to_csv(path, index=False)

    def intr_report(self, ticker, rate=0.08):

        hist = yf.Ticker(ticker.replace(".", "-"))
        tick_info = hist.fast_info

        # print(hist)
        try:
            price = tick_info["previous_close"]
        except KeyError:
            return None, None, None, None

        intr_val, notes, data, fc_data = self._calculate_intr(ticker, rate)
        fc_data["date"] = data["date"].iloc[-1]
        for i in fc_data["year"]:
            fc_data.loc[fc_data["year"] == i, "date"] = data["date"].iloc[
                -1
            ] + pd.offsets.DateOffset(years=i)

        fc_data.set_index("date", inplace=True)
        data.set_index("date", inplace=True)

        df_comb = pd.concat(
            [
                data,
                fc_data.rename(
                    columns={"book": "book_fw", "eps": "eps_fw", "cf": "cf_fw"}
                ),
            ],
            axis=1,
        )
        df_comb["book_disc"] = df_comb["book_fw"].iloc[-1] / (
            (1 + rate) ** (fc_data["year"].iloc[-1] - fc_data["year"])
        )
        df_comb["eps_disc"] = (df_comb["eps_sum"].iloc[-1] + price) / (
            (1 + rate) ** (fc_data["year"].iloc[-1] - fc_data["year"])
        )
        df_comb["cf_disc"] = (df_comb["cf_sum"].iloc[-1] + price) / (
            (1 + rate) ** (fc_data["year"].iloc[-1] - fc_data["year"])
        )
        df_comb = pd.concat([df_comb,pd.DataFrame.from_dict({
            "date": [df_comb.index[-1] + pd.DateOffset(1, "D")],
            "eps_sum": [df_comb["eps_sum"][df_comb.index[-1]] + price],
            "cf_sum": [df_comb["cf_sum"][df_comb.index[-1]] + price],
        }, orient="columns").set_index("date")])

        
        figure_components = {
            "columns": [
                "book",
                "eps",
                "cfps",
                "book_model",
                "eps_model",
                "cfps_model",
                "book_fw",
                "eps_fw",
                "cf_fw",
                "eps_sum",
                "cf_sum",
                "book_disc",
                "eps_disc",
                "cf_disc",
            ],
            "modes": [
                "markers",
                "markers",
                "markers",
                "lines",
                "lines",
                "lines",
                "lines",
                "lines",
                "lines",
                "lines",
                "lines",
                "lines",
                "lines",
                "lines",
            ],
            "names": [
                "book",
                "eps",
                "cfps",
                "book model",
                "eps model",
                "cfp model",
                "book model",
                "eps model",
                "cf model",
                "eps sum",
                "cf sum",
                "book disc",
                "eps disc",
                "cf disc",
            ],
            "colors": [
                "darkred",
                "darkblue",
                "darkgreen",
                "darkred",
                "darkblue",
                "darkgreen",
                "darkred",
                "darkblue",
                "darkgreen",
                "darkblue",
                "darkgreen",
                "red",
                "blue",
                "green",
            ],
        }

        figure_annotations = {
            "names": ["book", "eps", "cf"],
            "colors": ["red", "blue", "green"],
        }
        fig = go.Figure()

        for i, col in enumerate(figure_components["columns"]):
            fig = self._add_to_figure(
                fig,
                df_comb,
                col,
                figure_components["modes"][i],
                figure_components["names"][i],
                figure_components["colors"][i],
            )

        for i, name in enumerate(figure_annotations["names"]):
            fig = self._add_annotation(
                fig, data, df_comb, name, figure_annotations["colors"][i]
            )

        fig.update_layout(
            title=f"Fundamental analysis of {ticker}. Intrinsic estimate = {intr_val.round(2)} &#36;."
            f" Price = {round(price,2)} &#36;."
            f" Discount to intrinsic = {((price/intr_val)*100).round(2)} %",
            xaxis_title="Date (Year)",
            yaxis_title="USD ($)",
            margin=dict(l=30, r=30, t=30, b=30),
            paper_bgcolor="LightSteelBlue",
        )

        pio.write_image(
            fig, f"reports/plots/{ticker}.png", scale=1, width=1200, height=1000
        )

    def _add_to_figure(
        self, fig, df, column, mode="markers", name="test", color="blue"
    ):
        if mode == "markers":
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode=mode,
                    name=name,
                    marker=dict(color=color, size=15),
                )
            )
        elif mode == "lines":
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode=mode,
                    name=name,
                    line=dict(color=color),
                )
            )
        else:
            raise TypeError("Unknown figure mode")

        return fig

    def _add_annotation(self, fig, data, df_comb, name="book", color="red"):
        fig.add_annotation(
            x=data.index[-1],
            y=df_comb[f"{name}_disc"][data.index[-1]],
            xref="x",
            yref="y",
            text=f"{name} intr: {df_comb[f'{name}_disc'][data.index[-1]].round(2)} $",
            showarrow=True,
            font=dict(family="Courier New, monospace", size=16, color="#ffffff"),
            align="center",
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#636363",
            ax=20,
            ay=-30,
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=4,
            bgcolor=color,
            opacity=0.5,
        )
        return fig

    def _calculate_intr(self, ticker, rate=0.08):

        notes = []
        # try:
        # tick = yf.Ticker(ticker.replace(".","-"))
        hist = yf.Ticker(ticker.replace(".", "-"))
        tick_info = hist.fast_info

        # print(hist)
        try:
            price = tick_info["previous_close"]
        except KeyError:
            return None, None, None, None

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
            data.index, data["book"]
        )
        if slope < 0:
            notes.append("book decreasing")
        if intercept < 0:
            notes.append("book0 negative")
        data["book_model"] = data.index * slope + intercept
        data["book_change"] = (
            (data["book"] - data["book"].shift(1)) / data["book"].shift(1) * 100
        )
        data["book_model_change"] = (
            (data["book_model"] - data["book_model"].shift(1))
            / data["book_model"].shift(1)
            * 100
        )

        book_change = slope
        if book_change / data["book"].iloc[-1] > 0.25:
            notes.append("high book growth")
        if book_change / data["book"].iloc[-1] < 0.05:
            notes.append("low book growth")
        book_start = data["book"].iloc[-1]

        slope, intercept, r_value, p_value, std_err = stats.linregress(
            data.index, data["eps"]
        )
        if slope < 0:
            notes.append("eps decreasing")
        if intercept < 0:
            notes.append("eps0 negative")
        data["eps_model"] = data.index * slope + intercept
        data["eps_change"] = (
            (data["eps"] - data["eps"].shift(1)) / data["eps"].shift(1) * 100
        )
        data["eps_model_change"] = (
            (data["eps_model"] - data["eps_model"].shift(1))
            / data["eps_model"].shift(1)
            * 100
        )

        eps_change = slope
        if eps_change / data["eps"].iloc[-1] > 0.25:
            notes.append("high eps growth")
        if eps_change / data["eps"].iloc[-1] < 0.05:
            notes.append("low eps growth")
        eps_start = data["eps_model"].iloc[-1]

        slope, intercept, r_value, p_value, std_err = stats.linregress(
            data.index, data["cfps"]
        )
        if slope < 0:
            notes.append("fc decreasing")
        if intercept < 0:
            notes.append("fc0 negative")
        data["cfps_model"] = data.index * slope + intercept
        data["cfps_change"] = (
            (data["cfps"] - data["cfps"].shift(1)) / data["cfps"].shift(1) * 100
        )
        data["cfps_model_change"] = (
            (data["cfps_model"] - data["cfps_model"].shift(1))
            / data["cfps_model"].shift(1)
            * 100
        )

        cfps_change = slope
        cfps_start = data["cfps_model"].iloc[-1]

        fc_data = pd.DataFrame({"year": range(11)})
        fc_data["book"] = book_start
        for i in fc_data["year"].iloc[:-1]:
            fc_data.loc[fc_data["year"] == i + 1, "book"] = (
                fc_data.loc[fc_data["year"] == i]["book"] + book_change
            ).iloc[0]
        fc_data["book"] = fc_data["book"] + (dividend * fc_data["year"])

        fc_data["eps"] = eps_start
        fc_data["eps_sum"] = eps_start
        for i in fc_data["year"].iloc[:-1]:
            fc_data.loc[fc_data["year"] == i + 1, "eps"] = (
                fc_data.loc[fc_data["year"] == i]["eps"] + eps_change
            ).iloc[0]
            fc_data.loc[fc_data["year"] == i + 1, "eps_sum"] = fc_data["eps"][
                0 : i + 2
            ].sum()

        fc_data["cf"] = cfps_start
        fc_data["cf_sum"] = cfps_start
        for i in fc_data["year"].iloc[:-1]:
            fc_data.loc[fc_data["year"] == i + 1, "cf"] = (
                fc_data.loc[fc_data["year"] == i]["cf"] + cfps_change
            ).iloc[0]
            fc_data.loc[fc_data["year"] == i + 1, "cf_sum"] = fc_data["cf"][
                0 : i + 2
            ].sum()

        book5 = fc_data["book"][5] / ((1 + rate) ** 5)
        book10 = fc_data["book"][10] / ((1 + rate) ** 10)

        eps5 = (fc_data["eps_sum"][5] + price) / ((1 + rate) ** 5)
        eps10 = (fc_data["eps_sum"][10] + price) / ((1 + rate) ** 10)

        fc5 = (fc_data["cf_sum"][5] + price) / ((1 + rate) ** 5)
        fc10 = (fc_data["cf_sum"][10] + price) / ((1 + rate) ** 10)

        intr_val = sum([book5, book10, eps5, eps10, fc5, fc10]) / 6

        return intr_val, notes, data, fc_data

    def organize_data(self, path):

        intrin = pd.read_csv(path)
        len_start = len(intrin)
        intrin = intrin.loc[intrin["INTR"].notnull()]
        intrin = intrin.loc[intrin["INTR"] > 0]
        tickers = list(intrin["Symbol"])
        for tick in tickers:
            data = self._get_data(tick)
            if len(data) < 5:
                intrin = intrin.loc[intrin["Symbol"] != tick]
        intrin.to_csv(path, index=False)
        len_end = len(intrin)

        print(f"{len_start-len_end} ({round((((len_start-len_end) / len_start) *100),2)} %) bad tickers have been purged...")
        pass

    def _get_data(self, ticker):
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
        except FileNotFoundError:
            inst = FundamentalDataOrganizer(ticker=ticker.replace("-", "."))
            inst.organize_data(ticker=ticker.replace("-", "."))

            inc = pd.read_pickle(
                f"data/income_statements/annual/{ticker.replace('-','.')}.pkl"
            )
            bal = pd.read_pickle(
                f"data/balance_sheets/annual/{ticker.replace('-','.')}.pkl"
            )
            cf = pd.read_pickle(
                f"data/cash_flow_statements/annual/{ticker.replace('-','.')}.pkl"
            )

        data = pd.concat(
            [
                inc["shares_outstanding"],
                inc["net_income"],
                bal["share_holder_equity"],
                cf["free_cf"],
            ],
            axis=1,
        )

        data = data.rename(
            columns={"shares_outstanding": "shares", "share_holder_equity": "equity"}
        )

        return data


if __name__ == "__main__":

    org_ins = IntrinsicValue()
    org_ins.calculate_intrin(path="data/my_stocks.csv")
    # data = org_ins.organize_data(path="data/companies_long.csv")
    # data = org_ins.intr_report("BIG")
