# -*- coding: utf-8 -*-
"""
Created on Thu May 27 09:54:22 2021

@author: msb
"""

import yfinance as yf
import pandas as pd

import warnings

warnings.filterwarnings("ignore")


def update_intr(path="intrin.csv", save=False):
    data = pd.read_csv(f"data/{path}")
    # print(data)

    disc_bot = 0
    disc_top = 0

    length = len(data["Symbol"])

    length_bot = int(length / 2)
    # print("lengthbot = {}".format(length_bot))
    length_top = length - length_bot
    # print("lengthtop = {}".format(length_top))

    print("Updating discount calculations...\n")
    for i in range(len(data["Symbol"])):
        name = data["Symbol"][i]
        try:
            price_data = data["Current"][i]
        except KeyError:
            price_data = 1
        try:
            tick = yf.Ticker(name)
            hist = tick.fast_info
            # print(hist)
            price = hist["day_low"]

            data["NewPrice"][i] = price
            discount = (price / data["INTR"][i]) * 100
            data["Discount"][i] = discount

            move = ((price - price_data) / price_data) * 100

            if i + 1 > length_bot:
                disc_top += move
                # print("i: {} and in top".format(i))
            else:
                disc_bot += move
                # print("i: {} and in bot".format(i))

            print(
                "{} moved: {}%, Discount: {}%".format(
                    name, round(move, 2), round(discount, 2)
                )
            )
        except Exception as e:
            print(f"{e} error when trying to fetch price for {name}")

    avg_bot = disc_bot / length_bot
    avg_top = disc_top / length_top

    print(
        "\nAverage movement in bot: {}% \nAverage movement in top: {}%\n".format(
            round(avg_bot, 4), round(avg_top, 4)
        )
    )

    data = data.sort_values(by=["Discount"])

    print("Top 10 most discounted companies:\n")
    print(data[0:10])

    if save:
        print("\nSaving the new prices to csv...\n")
        data["Current"] = data["NewPrice"]
        data.to_csv(f"data/{path}", index=False)
    else:
        print("\nNew prices were not saved to csv...\n")


if __name__ == "__main__":
    # update_intr()
    update_intr("my_stocks.csv", save=True)
