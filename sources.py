from abc import ABC, abstractmethod
from abc import ABC, abstractmethod
from typing import Union

import dotenv
import mplfinance as mpl
import pandas as pd
from loguru import logger
from matplotlib import pyplot as plt

##############################
# Load environment variables #
##############################
logger.info("Loading environment")
dotenv.load_dotenv()


###################################
# Base class for each data source #
###################################
class Source(ABC):
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

    def plotLine(cls, df: pd.DataFrame):
        # Check if df is not empty
        assert not (df.empty), Exception("No data available for plotting")
        assert "Close" in df.columns, Exception("'Close' column not found in df")

        # df.index = pd.to_datetime(df.index)

        fig, ax = plt.subplots()
        # df.plot(ax=ax, kind="line", y="Close", color='#003366')
        mpl.plot(df, type="line", style="sas", ax=ax, linecolor="#203d74")

        ax.set_title(
            f"\nTICKER : {cls.element}"
            f"\n{df.index[0]} to {df.index[-1]}"
            f"\nMin: {df['Close'].min()}, Max: {df['Close'].max()}, Last: {df['Close'].tolist()[-1]}",
            loc="left",
            fontsize="medium",
        )
        ax.set_ylabel("Closing Price")
        ax.grid()
        plt.tight_layout()

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


