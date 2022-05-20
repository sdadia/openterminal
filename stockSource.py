import datetime
import os
from typing import Union, Dict, Literal

import pandas as pd
import requests
import rich_dataframe
from loguru import logger
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter

from sources import DataSourceBase


class AlphaVantageStockDataSourceBase(DataSourceBase):
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


# ss = AlphaVantageStockSource(stockName='aram')
# print(AlphaVantageStockSource.find('SAR'))
# df = ss.loadDaily(startDate=ciso8601.parse_datetime('2020-01-01'))
# ss.plotLine(df)
# plt.show()
