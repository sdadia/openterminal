from abc import ABC, abstractmethod
from typing import Union, List

import dotenv
import matplotlib.dates as mdates
import mplfinance as mpl
import pandas as pd
from adjustText import adjust_text
from loguru import logger
from matplotlib import pyplot as plt
from common import console

##############################
# Load environment variables #
##############################
console.log("Loading environment")
dotenv.load_dotenv()


###################################
# Base class for each data source #
###################################
class DataSourceBase(ABC):
    element: str = str
    apiKeyName: Union[str, None] = None
    apiKey: Union[str, None] = None
    apiURL: Union[str, None] = None

    @abstractmethod
    def loadDaily(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def find(cls) -> pd.DataFrame:
        pass

    @abstractmethod
    def checkSymbolExists(self, element: str) -> bool:
        pass

    def plotLine(cls, df: pd.DataFrame, plotGlobalEvents: bool = True, adjust=True):
        # Check if df is not empty
        assert not (df.empty), Exception("No data available for plotting")
        assert "Close" in df.columns, Exception("'Close' column not found in df")

        fig, ax = plt.subplots()
        df.plot(ax=ax, kind="line", y="Close", color="#003366")
        # Plot the global events
        if plotGlobalEvents:
            fig, ax = cls.plotGlobalEvents(df, fig, ax)

        ax.set_title(
            f"\nTICKER : {cls.element}"
            f"\n{df.index[0]} to {df.index[-1]}"
            f"\nMin: {df['Close'].min()}, Max: {df['Close'].max()}, Last: {df['Close'].tolist()[-1]}",
            loc="left",
            fontsize="medium",
        )
        ax.set_ylabel("Closing Price", fontweight="bold")
        ax.yaxis.set_label_position("right")
        # ax.yaxis.set_label_loc('top')
        ax.yaxis.tick_right()

        # If more than 200 rows in the dataframe use concise datetime format
        if df.shape[0] > 200 and df.shape[0] < 900:
            # set date format
            locator = mdates.MonthLocator()  # every month
        else:
            locator = mdates.AutoDateLocator()

        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.grid(True, which="minor")

        plt.legend()
        ax.grid()
        # plt.tight_layout()

        return fig, ax

    def plotCandle(cls, df: pd.DataFrame, volume=True):
        # Check if df is not empty
        assert not (df.empty), Exception("No data available for plotting")

        df.index = pd.to_datetime(df.index)

        fig, ax = plt.subplots()
        mpl.plot(df, type="candle", style="sas", ax=ax)

        ax.set_title(
            f"\nTICKER : {cls.element}"
            f"\n{df.index[0]} to {df.index[-1]}"
            f"\nMin: {df['Close'].min()}, Max: {df['Close'].max()}, Last: {df['Close'].tolist()[-1]}",
            loc="left",
            fontsize="medium",
        )
        ax.grid()

        plt.tight_layout()

        return fig, ax

    def plotGlobalEvents(self, df, fig, ax, adjust=True):

        globalEvents = [
            {"eventName": "Ukraine war", "eventDate": "2022-02-24"},
            {"eventName": "US sanctions", "eventDate": "2022-03-15"},
            {"eventName": "Russian gas in Rubles", "eventDate": "2022-03-22"},
            {"eventName": "India ban wheat export", "eventDate": "2022-05-14"},
            {"eventName": "Covid started", "eventDate": "2019-12-31"},
            {"eventName": "Coinbase IPO", "eventDate": "2021-04-14"},
            {"eventName": "USDC Feb GT report", "eventDate": "2021-04-27"},
            {"eventName": "Coinbase convertible bond", "eventDate": "2021-05-17"},
            {"eventName": "Crypto Crash", "eventDate": "2021-05-19"},
            {"eventName": "UST Terra crash", "eventDate": "2022-05-13"},
            {"eventName": "NFLX price inc", "eventDate": "2022-04-19"},
            {"eventName": "Russia stop gas to Finland", "eventDate": "2022-05-20"},
        ]
        globalEventsDF = pd.DataFrame(globalEvents)
        globalEventsDF.eventDate = pd.to_datetime(globalEventsDF.eventDate)
        globalEventsDF.set_index("eventDate", inplace=True)
        globalEventsDF.sort_index(inplace=True)

        mergedEventsDF = pd.merge(
            left=globalEventsDF,
            right=df,
            left_index=True,
            right_index=True,
            how="outer",
        )
        mergedEventsDF = mergedEventsDF[
            (mergedEventsDF.index >= df.index.min())
            & (mergedEventsDF.index <= df.index.max())
        ]
        if mergedEventsDF.empty:
            return fig, ax
        mergedEventsDF.interpolate(
            method="linear", inplace=True, limit_direction="both"
        )
        # Filter rows where we have events
        mergedEventsDF = mergedEventsDF[mergedEventsDF.eventName.notnull()]

        if mergedEventsDF.shape[0] == 1:
            ax.scatter(
                x=mergedEventsDF.index.tolist(),
                y=mergedEventsDF.Close.tolist(),
                marker="o",
                color="r",
            )
        else:
            ax.scatter(
                x=mergedEventsDF.index,
                y=mergedEventsDF.Close.tolist(),
                marker="o",
                color="r",
            )

        texts = []
        for index, row in mergedEventsDF.iterrows():
            texts.append(ax.text(index, row["Close"], row["eventName"], fontsize=12))
        if False:
            adjust_text(
                texts,
                arrowprops=dict(arrowstyle="->", color="blue"),
                ax=ax,
                expand_points=(1.2, 1.2),
                # expand_text=(3,3),
                # expand_objects=(1.5, 1.5),
                # expand_align=(1.1, 1.2),
            )

        return fig, ax


class TerminalLoop:
    commands: List[str] = [
        "forex",
        "fo" "reset",
        "r" "quit",
        "q",
        "help",
        "h",
    ]

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

        continueTerminalLoop: bool = True
        while continueTerminalLoop:
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
                continueTerminalLoop = False

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
                    self.classInstance = self.sourceClassMapping[loadParserArgs.source](
                        fromCurrency=loadParserArgs.fromCurrency,
                        toCurrency=loadParserArgs.toCurrency,
                    )
                except Exception as error:
                    console.print(f"[red]{error}")

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
