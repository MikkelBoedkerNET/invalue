import pandas as pd
from invalue import IntrinsicValue


def make_reports(list_of_tickers):
    for ind in range(len(list_of_tickers)):
        IntrinsicValue().intr_report(list_of_tickers[ind])
        print(
            f"Finished generating report for {list_of_tickers[ind]}... {round(((ind+1)/len(list_of_tickers)*100),2)} % Finished..."
        )


def run_reports(path, disc=60):
    data = pd.read_csv(f"data/{path}")

    data_report = data.loc[data["Discount"] <= disc]

    tickers = data_report["Symbol"]

    make_reports(tickers)


if __name__ == "__main__":
    run_reports("my_stocks.csv", disc=2005)
