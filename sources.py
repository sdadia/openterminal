from abc import ABC, abstractmethod
from abc import ABC, abstractmethod
from typing import Union, Dict

import ciso8601
import dotenv
import mplfinance as mpl
import pandas as pd
from adjustText import adjust_text
from loguru import logger
from matplotlib import pyplot as plt
import matplotlib.dates as mdates

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
        df.plot(ax=ax, kind="line", y="Close", color='#003366')
        # mpl.plot(df, type="line", style="sas", ax=ax, linecolor="#003366")

        ax.set_title(
            f"\nTICKER : {cls.element}"
            f"\n{df.index[0]} to {df.index[-1]}"
            f"\nMin: {df['Close'].min()}, Max: {df['Close'].max()}, Last: {df['Close'].tolist()[-1]}",
            loc="left",
            fontsize="medium",
        )
        ax.set_ylabel("Closing Price")
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()

        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)

        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

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

    def plotGlobalEvents(self, df, fig, ax):

        globalEvents = [
            {'eventName': 'Ukraine war',
             'eventDate': '2022-02-24'},
            {'eventName': 'US sanctions',
             'eventDate': '2022-03-15'},
            {'eventName': 'Russian gas in Rubles',
             'eventDate': '2022-03-22'},
        ]
        globalEventsDF = pd.DataFrame(globalEvents)
        globalEventsDF.eventDate = pd.to_datetime(globalEventsDF.eventDate)
        globalEventsDF.set_index('eventDate', inplace=True)

        mergedEventsDF = pd.merge(left=globalEventsDF, right=df, left_index=True, right_index=True, how='outer')
        mergedEventsDF = mergedEventsDF[(mergedEventsDF.index >= df.index.min()) & (mergedEventsDF.index <= df.index.max())]
        if mergedEventsDF.empty:
            return fig, ax
        mergedEventsDF.interpolate(method='linear', inplace=True, limit_direction='both')
        # Filter rows where we have events
        mergedEventsDF = mergedEventsDF[mergedEventsDF.eventName.notnull()]

        print(mergedEventsDF.info())
        print(mergedEventsDF.head(10))

        ax.scatter(x=mergedEventsDF.index, y=mergedEventsDF.Close, marker='o')

        texts = []
        for index, row in mergedEventsDF.iterrows():
            texts.append(ax.text(index, row['Close'], row['eventName'])
                         )
        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='blue'), ax=ax,
                    expand_points=(2,2),
                    # expand_text=(3,3),
                    expand_objects=(3,6),
                    expand_align=(5,5)
                    )

        return fig, ax