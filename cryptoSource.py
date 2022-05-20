import datetime
import os
from typing import Union, Dict, Literal

import pandas as pd
import requests
from loguru import logger

from sources import DataSourceBase


class AlphaVantageCrytpoDataSourceBase(DataSourceBase):
    physical_currency_df = pd.read_csv("./av_physical_currency_list.csv")
    digital_currency_df = pd.read_csv("./av_physical_currency_list.csv")

    apiURL: str = "https://www.alphavantage.co/query?"
    apiKeyName: str = "ALPHA_VANTAGE_API_KEY"
    apiKey: str = None
    outputSize: Literal["full", "compact"] = "full"
    isValidElement: bool = False
    element: Union[str, None] = None

    def __init__(self, crytpoName: str):
        # check if API key is present in environment variable or not
        if not os.environ.get(self.apiKeyName):
            raise Exception(
                f"{self.apiKeyName} not found in .env file. Set the ALPHA_VANTAGE_API_KEY in .env file"
            )
        self.apiKey: str = os.environ.get(
            self.apiKeyName, "demo"
        )  # get api key name from environment

        # # Check if given valid stock name
        # assert self.checkSymbolExists(crytpoName), Exception(
        #     f'Invalid stock name provided. Close matches are : {self.find(crytpoName)["Symbol"].tolist()}'
        # )
        self.element = crytpoName

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

            # filter data
            df = df[(df.index >= str(startDate)) & (df.index <= str(endDate))]
            # Convert to datetime

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
    def find(cls, crytpoName: str) -> pd.DataFrame:
        """
        Check if the stock exists exists
        :param crytpoName:
        :return:
        """
        # function name and symbol name
        functionName: str = "SYMBOL_SEARCH"
        symbol: str = crytpoName

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
