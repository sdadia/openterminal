import argparse
import datetime
import difflib
import os
from typing import Dict, Literal, List, Optional

import ciso8601
import matplotlib.dates as mdates
import pandas as pd
import requests
from loguru import logger
from matplotlib import pyplot as plt
from rich_dataframe import rich_dataframe

from common import session, console
from sources import DataSourceBase


class ForexDataDataSourceBaseBase(DataSourceBase):
    from_symbol: str = None
    to_symbol: str = None

    def plotLine(cls, df: pd.DataFrame, plotGlobalEvents: bool = True, adjust=True):
        # Check if df is not empty
        assert not (df.empty), Exception("No data available for plotting")
        assert "Close" in df.columns, Exception("'Close' column not found in df")

        fig, ax = plt.subplots()
        # Plot the price
        df.plot(ax=ax, kind="line", y="Close", color="#003366")

        # Plot the global events
        if plotGlobalEvents:
            fig, ax = cls.plotGlobalEvents(df, fig, ax, adjust=adjust)

        # set title
        ax.set_title(
            f"\nFOREX : {cls.from_symbol} to {cls.to_symbol}"
            f"\n{df.index[0]} to {df.index[-1]}"
            f"\nMin: {df['Close'].min()}, Max: {df['Close'].max()}, Last: {df['Close'].tolist()[-1]}",
            loc="left",
            fontsize="medium",
        )
        ax.set_ylabel("Closing Price")
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()

        if df.shape[0] > 200:
            # set date format
            locator = mdates.AutoDateLocator()
            formatter = mdates.ConciseDateFormatter(locator)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)

        # show legend
        ax.legend(bbox_to_anchor=(1.04, 1), borderaxespad=1)
        ax.grid()
        # plt.tight_layout()

        return fig, ax


class AlphaVantageForexSource(ForexDataDataSourceBaseBase):
    physical_currency_df: pd.DataFrame = pd.read_csv("./av_physical_currency_list.csv")
    physical_currency_codes: List[str] = physical_currency_df["currency code"].tolist()
    physical_currency_codes = [x.upper() for x in physical_currency_codes]
    physical_currency_name: List[str] = physical_currency_df["currency name"].tolist()
    physical_currency_name = [x.upper() for x in physical_currency_name]

    apiURL: str = "https://www.alphavantage.co/query?"
    apiKeyName: str = "ALPHA_VANTAGE_API_KEY"
    apiKey: str = None
    outputSize: Literal["full", "compact"] = "full"
    isValidElement: bool = False

    def __init__(self, fromCurrency: str, toCurrency: str):
        # check if API key is present in environment variable or not
        if not os.environ.get(self.apiKeyName):
            raise Exception(
                f"{self.apiKeyName} not found in .env file. Set the ALPHA_VANTAGE_API_KEY in .env file"
            )
        self.apiKey: str = os.environ.get(
            self.apiKeyName, "demo"
        )  # get api key name from environment

        assert self.checkSymbolExists(fromCurrency), Exception(
            f"{fromCurrency} not found in valid currency"
        )
        assert self.checkSymbolExists(toCurrency), Exception(
            f"{toCurrency} not found in valid currency"
        )

        self.from_symbol = fromCurrency.upper()
        self.to_symbol = toCurrency.upper()

        self.element = f"{self.from_symbol} / {self.to_symbol}"

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
        functionName: str = "FX_DAILY"

        url = f"{self.apiURL}function={functionName}&from_symbol={self.from_symbol}&to_symbol={self.to_symbol}&outputsize={self.outputSize}&apikey={self.apiKey}"
        logger.debug(f"URL for daily FX data is : {url}")
        r = requests.get(url)
        data: Dict = r.json()

        if "Error Message" in data:
            logger.exception(
                f"Error getting daily stock prices for : {self.element} from ALPHA_VANTAGE. Error is : {data['Error Message']}"
            )
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        else:
            # load data in dictionary
            df = pd.DataFrame.from_dict(data["Time Series FX (Daily)"], orient="index")
            # rename columns and sort data
            df.columns = ["Open", "High", "Low", "Close"]
            for column in df.columns:
                df[column] = df[column].astype(float)
            df.sort_index(inplace=True)

            # convert index to datetime
            df.index = pd.to_datetime(df.index)

            # filter data
            df = df[(df.index >= str(startDate)) & (df.index <= str(endDate))]
            # Convert to datetime

            self.df = df
            return df

    def checkSymbolExists(self, currencyString: str) -> bool:
        return currencyString.upper() in self.physical_currency_codes

    @classmethod
    def find(cls, currencyToSearch: str) -> pd.DataFrame:
        currencyToSearch = currencyToSearch.upper()
        indexToDisplay: List[Optional[int]] = []
        for index, i in enumerate(cls.physical_currency_codes):
            print(i, currencyToSearch)
            if difflib.SequenceMatcher(None, i, currencyToSearch).ratio() > 0.7:
                indexToDisplay.append(index)

        indexToDisplay = list(set(indexToDisplay))
        if len(indexToDisplay) > 0:
            topMatches: pd.DataFrame = cls.physical_currency_df.iloc[indexToDisplay]
        else:
            topMatches: pd.DataFrame = pd.DataFrame(
                columns=["currency code", "currency name"]
            )

        return topMatches


class ForexLoop:
    sourceClassMapping: Dict[str, object] = {"av": AlphaVantageForexSource}
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
    classToUse = AlphaVantageForexSource
    classInstance = None

    def runLoop(self):

        # Print help message
        helpMessage = (
            "[red]Welcome to stock bot. Choose from the following choices."
            f"\n Choose from the following : [yellow]{self.commands}"
        )
        console.print(helpMessage)

        # Parser for parsing the command
        forexParser = argparse.ArgumentParser(prog="forex", add_help=True)
        forexParser.add_argument("cmd", choices=self.commands)

        continueForexLoop: bool = True
        while continueForexLoop:
            userInput = session.prompt("Forex>> ")

            # Parse main command of the list of possible self.commands
            try:
                (forexParserArgs, l_args) = forexParser.parse_known_args(
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
            if forexParserArgs.cmd in ("help", "h"):
                console.print(helpMessage)

            ################
            # Quit program #
            ################
            elif forexParserArgs.cmd in ("quit", "q"):
                console.print("[red]Exiting Forex section")
                continueForexLoop = False

            ################
            # Clear screen #
            ################
            elif forexParserArgs.cmd == "cls":
                os.system("cls||clear")

            ################
            # Load program #
            ################
            elif forexParserArgs.cmd in ("load"):
                ##########################
                # Create load parameters #
                ##########################
                loadParser = argparse.ArgumentParser(prog="load")
                loadParser.add_argument("--fromCurrency", type=str, required=True)
                loadParser.add_argument("--toCurrency", type=str, required=True)
                loadParser.add_argument(
                    "--source", choices=[list(self.sourceClassMapping.keys())], default="av"
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
                    self.classInstance = self.sourceClassMapping[loadParserArgs.source](
                        fromCurrency=loadParserArgs.fromCurrency,
                        toCurrency=loadParserArgs.toCurrency,
                    )
                except Exception as error:
                    console.print(f'[red]{error}')

            ################
            # Plot Program #
            ################
            elif forexParserArgs.cmd in ("plotLine", "pl"):
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
                        "--adjust", type=int, help="", default=1,
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
            elif forexParserArgs.cmd in ("find", "fi"):
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
                searchResultsDF: pd.DataFrame = self.classToUse.find(
                    findParserArgs.keyword
                )
                # searchResultsDF: pd.DataFrame = AlphaVantageForexSource.find(
                #     findParserArgs.keyword
                # )
                # searchResultsDF: pd.DataFrame = searchStock(findParserArgs.keyword)
                rich_dataframe.prettify(searchResultsDF)

            else:
                console.print("Here")
                console.print(
                    f"[red]The command selected doesn't exist. Available commands are : {self.commands}"
                )
                continue
