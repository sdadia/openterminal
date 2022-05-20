import argparse
import datetime
import os
import subprocess
import sys

import ciso8601
import dotenv
import matplotlib.pyplot as plt
import pandas as pd
import rich_dataframe
from alpha_vantage.cryptocurrencies import CryptoCurrencies
from alpha_vantage.timeseries import TimeSeries

from common import session, console
from forexDataSourceBase import ForexLoop
from stockSource import AlphaVantageStockDataSourceBase

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
main_parser.add_argument(
    "cmd",
    choices=[
        "quit",
        "q",
        "plotLine",
        "plotFund",
        "find",
        "load",
        "reset",
        "r",
        "cls",
        "forex",
    ],
)

console.print(
    "Welcome to stock bot. Choose from the following choices.\n"
    "plotLine\n"
    "quit\n"
    "find\n"
)

continueLoop: bool = True

while continueLoop:
    userInput = session.prompt("Main>> ")

    # Parse main command of the list of possible commands
    try:
        (mainParserArgs, l_args) = main_parser.parse_known_args(userInput.split())
    except SystemExit:
        console.print(f"The command selected doesn't exist\n")
        continue

    # Quit program
    if mainParserArgs.cmd in ("quit", "q"):
        console.print("[red]Quitting. Good bye.")
        continueLoop = False

    if mainParserArgs.cmd == "reset" or mainParserArgs.cmd == "r":
        console.print("[red]Resetting...")
        continueLoop = False
        os.system('cls||clear')
        subprocess.run(  # nosec
            f"{sys.executable} terminal.py", shell=True, check=False
        )
        console.print("Done")

    if mainParserArgs.cmd == "cls":
        os.system("cls||clear")


    # Load program
    if mainParserArgs.cmd == "load":

        ##############################
        # Create load parameters #
        ##############################
        loadParser = argparse.ArgumentParser(prog="load")
        loadParser.add_argument("--ticker", type=str, required=False)
        # loadParser.add_argument(
        #     "--startDate",
        #     type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
        #     help="The starting date (format YYYY-MM-DD) of the stock",
        #     default=datetime.datetime.today() - datetime.timedelta(days=365),
        # )
        # loadParser.add_argument(
        #     "--endDate",
        #     type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
        #     help="The starting date (format YYYY-MM-DD) of the stock",
        #     default=datetime.datetime.today(),
        # )
        try:
            (loadParserArgs, largs) = loadParser.parse_known_args(userInput.split())
        except SystemExit:
            console.print("[red]Invalid arguemnts")
            continue

        ###########################
        # Load data for the stock #
        ###########################

        try:
            ss: AlphaVantageStockDataSourceBase = AlphaVantageStockDataSourceBase(
                stockName=loadParserArgs.ticker
            )
        except Exception as error:
            console.log(error)

    # Load program
    if mainParserArgs.cmd == "plotLine":

        ##############################
        # Create plotLine parameters #
        ##############################
        viewParser = argparse.ArgumentParser(prog="plotLine")
        viewParser.add_argument(
            "--type", type=str, required=False, default="line", choices=["line", "ohlc"]
        )
        viewParser.add_argument(
            "--startDate",
            type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
            help="The starting date (format YYYY-MM-DD)",
            default=datetime.datetime.today() - datetime.timedelta(days=365),
        )
        viewParser.add_argument(
            "--endDate",
            type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
            help="The starting date (format YYYY-MM-DD)",
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
        try:
            df = ss.loadDaily(
                startDate=ciso8601.parse_datetime(str(viewParserArgs.startDate)),
                endDate=ciso8601.parse_datetime(str(viewParserArgs.endDate)),
            )
            ss.plotLine(df, plotGlobalEvents=True)
            plt.show()
        except Exception as err:
            console.print(f"[red]{err}")

    # Load program
    if mainParserArgs.cmd == "plotFund":

        ##############################
        # Create plotLine parameters #
        ##############################
        viewParser = argparse.ArgumentParser(prog="plotFund")
        # # viewParser.add_argument(
        # #     "--type", type=str, required=False, default="line", choices=["line", "ohlc"]
        # # )
        # # viewParser.add_argument(
        # #     "--startDate",
        # #     type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
        # #     help="The starting date (format YYYY-MM-DD) of the stock",
        # #     default=datetime.datetime.today() - datetime.timedelta(days=365),
        # # )
        # # viewParser.add_argument(
        # #     "--endDate",
        # #     type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
        # #     help="The starting date (format YYYY-MM-DD) of the stock",
        # #     default=datetime.datetime.today(),
        # # )
        # try:
        #     (viewParserArgs, largs) = viewParser.parse_known_args(userInput.split())
        # except SystemExit:
        #     console.print("[red]Invalid arguemnts")
        #     continue

        ###########################
        # Load data for the stock #
        ###########################
        try:
            quaterlyFundamentaData, annualFundamentaData = ss.getFundamentalData()
            ss.plotFundamentalData(quaterlyFundamentaData)
            plt.show()
        except Exception as err:
            console.print(f"[red]{err}")

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
        searchResultsDF: pd.DataFrame = AlphaVantageStockDataSourceBase.find(
            findParserArgs.keyword
        )
        # searchResultsDF: pd.DataFrame = searchStock(findParserArgs.keyword)
        rich_dataframe.prettify(searchResultsDF)
        # console.print(searchResultsDF.to_string())

    if mainParserArgs.cmd == "forex":
        ##############
        # Get source #
        ##############
        forexParser = argparse.ArgumentParser(prog="forex")
        ForexLoop().runLoop()

    # # TODO : Add Stock loop
    if continueLoop is False:
        sys.exit(-1)
