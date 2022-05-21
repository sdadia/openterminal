import argparse
import datetime
import os
from typing import Union, Dict, Literal, List

import ciso8601
import pandas as pd
import requests
import rich_dataframe
from loguru import logger
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter

from sources import DataSourceBase
from common import console, session
from prompt_toolkit.completion import WordCompleter


class AlphaVantageStockDataSource(DataSourceBase):
    apiURL: str = "https://www.alphavantage.co/query?"
    apiKeyName: str = "ALPHA_VANTAGE_API_KEY"
    apiKey: str = None
    outputSize: Literal["full", "compact"] = "full"
    isValidElement: bool = False
    element: Union[str, None] = None

    def __init__(self, stockName: str):
        # check if API key is present in environment variable or not
        if not os.environ.get(self.apiKeyName):
            raise Exception(
                f"{self.apiKeyName} not found in .env file. Set the ALPHA_VANTAGE_API_KEY in .env file and reset the terminal"
            )
        self.apiKey: str = os.environ.get(
            self.apiKeyName, "demo"
        )  # get api key name from environment

        # # Check if given valid stock name
        assert self.checkSymbolExists(stockName), Exception(
            f'Invalid stock name provided. Close matches are : {self.find(stockName)["Symbol"].tolist()}'
        )
        self.element = stockName.upper()

        self.isValidElement = True

    def loadDaily(
        self,
        startDate: datetime.date = datetime.datetime.today()
        - datetime.timedelta(days=366),
        endDate: datetime.date = datetime.datetime.today(),
    ) -> pd.DataFrame:
        """
        Function returns the daily OHLC data
        :param startDate:
        :param endDate:
        :return:
        """
        assert self.isValidElement, Exception("Select valid symbol")
        assert startDate < endDate, Exception("Start date should be less than end date")

        # function name and symbol name
        functionName: str = "TIME_SERIES_DAILY"
        symbol: str = self.element

        url = f"{self.apiURL}function={functionName}&symbol={symbol}&outputsize={self.outputSize}&apikey={self.apiKey}&datatype=json"
        logger.debug(f"URL for daily time series is : {url}")
        r = requests.get(url)
        data: Dict = r.json()

        if "Error Message" in data:
            logger.exception(
                f"Error getting daily stock prices for : {self.element} from ALPHA_VANTAGE. Error is : {data['Error Message']}"
            )
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        else:
            # load data in dictionary
            df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
            # rename columns and sort data
            df.columns = ["Open", "High", "Low", "Close", "Volume"]
            for column in df.columns:
                df[column] = df[column].astype(float)
            df.sort_index(inplace=True)

            # convert index to datetime
            df.index = pd.to_datetime(df.index)
            logger.critical(f"Min and max : {df.index.min()} and {df.index.max()}")
            # filter data
            df = df[(df.index >= str(startDate)) & (df.index <= str(endDate))]
            # Convert to datetime
            logger.critical(f"Min and max : {df.index.min()} and {df.index.max()}")

            self.df = df
            return df

    def checkSymbolExists(self, symbolName: str) -> bool:
        # To check if symbol exists, then it
        functionName: str = "GLOBAL_QUOTE"
        symbol: str = symbolName

        url = (
            f"{self.apiURL}function={functionName}&symbol={symbol}&apikey={self.apiKey}"
        )
        logger.debug(f"URL for checking if symbol exists is : {url}")
        r = requests.get(url)
        data: Dict = r.json()

        return bool(data["Global Quote"])  # check if

    @classmethod
    def find(cls, stockName: str) -> pd.DataFrame:
        """
        Check if the stock exists exists
        :param stockName:
        :return:
        """
        # function name and symbol name
        functionName: str = "SYMBOL_SEARCH"
        symbol: str = stockName

        url = (
            f"{cls.apiURL}function={functionName}&keywords={symbol}&apikey={cls.apiKey}"
        )
        logger.debug(f"URL for finding stocks is : {url}")
        r = requests.get(url)
        data: Dict = r.json()

        df = pd.DataFrame(data["bestMatches"])
        df.columns = [
            "Symbol",
            "Name",
            "Type",
            "Region",
            "MarketOpen",
            "MarketClose",
            "Timezone",
            "Currency",
            "MatchScore",
        ]
        return df

    def getFundamentalData(self) -> (pd.DataFrame, pd.DataFrame):
        """
        This function returns the fundamental data for the quarterly and annual data
        :return:
        """
        functionName: str = "BALANCE_SHEET"
        symbol: str = self.element

        url = (
            f"{self.apiURL}function={functionName}&symbol={symbol}&apikey={self.apiKey}"
        )
        logger.debug(f"URL for gettign fundamental data is : {url}")
        r = requests.get(url)
        data = r.json()

        quaterlyFundamentaData: pd.DataFrame = pd.DataFrame(data["quarterlyReports"])
        annualFundamentaData: pd.DataFrame = pd.DataFrame(data["annualReports"])
        for col in ["totalAssets", "totalLiabilities", "totalShareholderEquity"]:
            quaterlyFundamentaData[col] = quaterlyFundamentaData[col].astype(float)
            annualFundamentaData[col] = annualFundamentaData[col].astype(float)
        quaterlyFundamentaData["fiscalDateEnding"] = pd.to_datetime(
            quaterlyFundamentaData["fiscalDateEnding"]
        )
        annualFundamentaData["fiscalDateEnding"] = pd.to_datetime(
            annualFundamentaData["fiscalDateEnding"]
        )
        quaterlyFundamentaData["fiscalDateEnding"] = pd.PeriodIndex(
            quaterlyFundamentaData["fiscalDateEnding"], freq="Q"
        )
        annualFundamentaData["fiscalDateEnding"] = pd.PeriodIndex(
            annualFundamentaData["fiscalDateEnding"], freq="A"
        )
        # print(df.)

        quaterlyFundamentaData["ticker"] = symbol
        annualFundamentaData["ticker"] = symbol

        quaterlyFundamentaData.set_index("fiscalDateEnding", inplace=True)
        quaterlyFundamentaData.sort_index(ascending=True, inplace=True)
        annualFundamentaData.set_index("fiscalDateEnding", inplace=True)
        annualFundamentaData.sort_index(ascending=True, inplace=True)
        rich_dataframe.prettify(quaterlyFundamentaData)

        return quaterlyFundamentaData, annualFundamentaData

    def format_number(data_value, indx):
        if data_value >= 1_000_000:
            formatter = "{:1.1f}M".format(data_value * 0.000_001)
        else:
            formatter = "{:1.0f}K".format(data_value * 0.001)
        return formatter

    def plotFundamentalData(self, df):
        fig, ax = plt.subplots(nrows=1)

        ###################################
        # Plot liabilities / assets ratio #
        ###################################
        df["Liabilities/Assets"] = df["totalLiabilities"] / df["totalShareholderEquity"]
        df.plot(y="Liabilities/Assets", kind="line", color="#003366", marker="o", ax=ax)
        ax.set_ylabel("Liabilities/Assets ratio", fontweight="bold")
        ax.legend(loc=2)

        #####################
        # Plot total assets #
        #####################
        def human_format(num, pos):
            magnitude = 0
            while abs(num) >= 1000:
                magnitude += 1
                num /= 1000.0
            # add more suffixes if you need them
            return "%.2f %s" % (
                num,
                ["", "K", "Million", "Billion", "Trillion", "P"][magnitude],
            )

        # formatter =
        ax2 = ax.twinx()
        ax2.yaxis.set_major_formatter(FuncFormatter(human_format))
        df.plot(y="totalAssets", kind="line", color="red", marker="o", ax=ax2)
        ax2.set_ylabel("totalAssets", fontweight="bold")
        ax2.legend(loc=1)

        ax.grid()

        ax.set_title(
            f"\nTICKER : {self.element}" f"\n{df.index[0]} to {df.index[-1]}",
            loc="left",
            fontsize="medium",
        )

        return fig, ax



class StockLoop:
    sectionName: str = 'stock'

    sourceClassMapping: Dict[str, object] = {"av": AlphaVantageStockDataSource}
    commands: List[str] = [
        "load",
        "find",
        "fi",
        "plotLine",
        "pl",
        "quit",
        "q",
        "help",
        "h",
    ]
    classToUse = AlphaVantageStockDataSource
    classInstance = None

    def runLoop(self):

        # Print help message
        helpMessage = (
            f"[red]Welcome to {self.sectionName} section. Choose from the following choices."
            f"\n Choose from the following : [yellow]{self.commands}"
        )
        console.print(helpMessage)

        # Parser for parsing the command
        stockParser = argparse.ArgumentParser(prog="stock", add_help=True)
        stockParser.add_argument("cmd", choices=self.commands)

        continueStockLoop: bool = True
        while continueStockLoop:
            userInput = session.prompt(f"{self.sectionName}>> ", completer=WordCompleter(self.commands))

            # Parse main command of the list of possible self.commands
            try:
                (stockParserArgs, l_args) = stockParser.parse_known_args(
                    userInput.lower().split()
                )
            except SystemExit:
                console.print(
                    f"[red]The command selected doesn't exist. Available commands are : {self.commands}"
                )
                continue

            ################
            # Quit program #
            ################
            if stockParserArgs.cmd in ("help", "h"):
                console.print(helpMessage)

            ################
            # Quit program #
            ################
            elif stockParserArgs.cmd in ("quit", "q"):
                console.print(f"[red]Exiting {self.sectionName} section")
                continueStockLoop = False

            ################
            # Clear screen #
            ################
            elif stockParserArgs.cmd == "cls":
                os.system("cls||clear")

            ################
            # Load program #
            ################
            elif stockParserArgs.cmd in ("load"):
                ##########################
                # Create load parameters #
                ##########################
                loadParser = argparse.ArgumentParser(prog="load")
                loadParser.add_argument("--ticker", "-t", type=str, required=True)
                loadParser.add_argument(
                    "--source",
                    choices=[list(self.sourceClassMapping.keys())],
                    default="av",
                )

                try:
                    (loadParserArgs, largs) = loadParser.parse_known_args(
                        userInput.split()
                    )
                except SystemExit:
                    console.print("[red]Invalid arguments")
                    continue

                ###########################
                # Load data for the stock #
                ###########################

                try:
                    # Check if the source they have chosen is correct
                    assert (
                        loadParserArgs.source in self.sourceClassMapping.keys()
                    ), Exception(
                        f"Source {loadParserArgs.source} not defined. Valid values are: {list(self.sourceClassMapping.keys())}"
                    )

                    # Check if we have the correct class
                    self.classToUse = self.sourceClassMapping[loadParserArgs.source]
                    self.classInstance = self.sourceClassMapping[loadParserArgs.source](stockName=loadParserArgs.ticker)
                except Exception as error:
                    console.print(f"[red]{error}")

            ################
            # Plot Program #
            ################
            elif stockParserArgs.cmd in ("plotLine", "pl"):
                if self.classInstance is not None:
                    ##############################
                    # Create plotLine parameters #
                    ##############################
                    viewParser = argparse.ArgumentParser(prog="plotLine")
                    viewParser.add_argument(
                        "--type",
                        type=str,
                        required=False,
                        default="line",
                        choices=["line", "ohlc"],
                    )
                    viewParser.add_argument(
                        "--startDate",
                        type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
                        help="The starting date (format YYYY-MM-DD)",
                        default=datetime.datetime.today()
                        - datetime.timedelta(days=365),
                    )
                    viewParser.add_argument(
                        "--endDate",
                        type=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d"),
                        help="The ending date (format YYYY-MM-DD)",
                        default=datetime.datetime.today(),
                    )
                    viewParser.add_argument(
                        "--adjust",
                        type=int,
                        help="",
                        default=1,
                    )
                    try:
                        (viewParserArgs, largs) = viewParser.parse_known_args(
                            userInput.split()
                        )
                    except SystemExit:
                        console.print("[red]Invalid arguemnts")
                        continue

                    ###########################
                    # Load data for the stock #
                    ###########################
                    try:
                        df = self.classInstance.loadDaily(
                            startDate=ciso8601.parse_datetime(
                                str(viewParserArgs.startDate)
                            ),
                            endDate=ciso8601.parse_datetime(
                                str(viewParserArgs.endDate)
                            ),
                        )
                        self.classInstance.plotLine(
                            df, plotGlobalEvents=True, adjust=viewParserArgs.adjust
                        )
                        plt.show()
                    except Exception as err:
                        console.print(f"[red]{err}")
                else:
                    console.print("[red]currency not loaded. Use load command")

            ################
            # Find program #
            ################
            elif stockParserArgs.cmd in ("find", "fi"):
                #########################
                # Create cmd parameters #
                #########################
                findParser = argparse.ArgumentParser(prog="find")
                findParser.add_argument("--keyword", type=str, required=True)

                try:
                    (findParserArgs, largs) = findParser.parse_known_args(
                        userInput.split()
                    )
                except SystemExit:
                    console.print("[red]Invalid arguemnts")
                    continue

                ###########################
                # Load data for the stock #
                ###########################
                console.print(f"Results for : {findParserArgs.keyword}")
                searchResultsDF: pd.DataFrame = self.classToUse.find(findParserArgs.keyword)
                rich_dataframe.prettify(searchResultsDF) # print the results

            else:
                console.print(f"[red]The command selected doesn't exist. Available commands are : {self.commands}")
                continue
