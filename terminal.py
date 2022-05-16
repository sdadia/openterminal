import argparse
import datetime
import os

import dotenv
import matplotlib.pyplot as plt
import pandas as pd
from alpha_vantage.cryptocurrencies import CryptoCurrencies
from alpha_vantage.timeseries import TimeSeries
import rich_dataframe


from common import session, console, searchStock

########################
# Load env config file #
########################
dotenv.load_dotenv()

# Alpha Vantage Client
avStockClient = TimeSeries(
    key=os.getenv("ALPHA_VANTAGE_API_KEY", "demo"), output_format="pandas"
)
avCryptoClient = CryptoCurrencies(
    key=os.getenv("ALPHA_VANTAGE_API_KEY", "demo"), output_format="pandas"
)

main_parser = argparse.ArgumentParser(prog="terminal", add_help=True)
main_parser.add_argument("cmd", choices=["quit", "plot", "find"])

console.print(
    "Welcome to stock bot. Choose from the following choices.\n" "plot\n" "quit\n" "find\n"
)

continueLoop: bool = True

while continueLoop:
    userInput = session.prompt()

    # Parse main command of the list of possible commands
    try:
        (mainParserArgs, l_args) = main_parser.parse_known_args(userInput.split())
    except SystemExit:
        console.print(f"The command selected doesn't exist\n")
        continue

    # Quit program
    if mainParserArgs.cmd == "quit":
        console.print("[red]Quitting. Good bye.")
        continueLoop = False

    # Load program
    if mainParserArgs.cmd == "plot":

        ##########################
        # Create plot parameters #
        ##########################
        viewParser = argparse.ArgumentParser(prog="plot")
        viewParser.add_argument("--ticker", type=str, required=True)
        viewParser.add_argument(
            "--type", type=str, required=False, default="line", choices=["line", "ohlc"]
        )
        viewParser.add_argument(
            "--startDate",
            type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
            help="The starting date (format YYYY-MM-DD) of the stock",
            default=datetime.datetime.today() - datetime.timedelta(days=365),
        )
        viewParser.add_argument(
            "--endDate",
            type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
            help="The starting date (format YYYY-MM-DD) of the stock",
            default=datetime.datetime.today(),
        )
        try:
            (viewParserArgs, largs) = viewParser.parse_known_args(userInput.split())
        except SystemExit:
            console.print("[red]Invalid arguemnts")
            continue

        ###########################
        # Load data for the stock #
        ###########################
        data, meta_data = avStockClient.get_daily(
            viewParserArgs.ticker, outputsize="full"
        )
        # Rename correct column
        data.columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]
        data.sort_index(inplace=True)
        # Subset data based on start and end time
        data = data[
            (data.index >= viewParserArgs.startDate)
            & (data.index <= viewParserArgs.endDate)
        ]

        ##########################
        # Create different plots #
        ##########################
        if viewParserArgs.type == "line":
            fig, ax = plt.subplots()
            data.plot(ax=ax, kind="line", y="Close")

            Name = "AssetType"
            ax.set_title(
                f""
                f"\nTICKER : {viewParserArgs.ticker}"
                f"\n{data.index[0].strftime('%Y-%b-%d')} to {data.index[-1].strftime('%Y-%b-%d')}",
                loc="left",
                fontsize="medium",
            )
            ax.set_ylabel("Closing Price")
            ax.grid()

        plt.show(block=False)
        plt.pause(1)

    # Find program
    if mainParserArgs.cmd == "find":

        #########################
        # Create cmd parameters #
        #########################
        findParser = argparse.ArgumentParser(prog="find")
        findParser.add_argument("--keyword", type=str, required=True)

        try:
            (findParserArgs, largs) = findParser.parse_known_args(userInput.split())
        except SystemExit:
            console.print("[red]Invalid arguemnts")
            continue

        ###########################
        # Load data for the stock #
        ###########################
        console.print(f"Results for : {findParserArgs.keyword}")
        searchResultsDF: pd.DataFrame = searchStock(findParserArgs.keyword)
        rich_dataframe.prettify(searchResultsDF)
        # console.print(searchResultsDF.to_string())
