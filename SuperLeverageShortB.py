# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
from pickle import LONG
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib


class SuperLeverageShortB(IStrategy):
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy.
    timeframe = '30m'

    # Can this strategy go short?
    can_short: bool = False

    # Buy hyperspace params:
    buy_params = {
        "buy_rsi": 19,
        "liquidation_buffer": 0.1,  # value loaded from strategy
    }

    # Sell hyperspace params:
    sell_params = {
        "sell_rsi": 74,
    }

    # ROI table:
    minimal_roi = {
        "0": 0.328,
        "108": 0.077,
        "138": 0.037,
        "254": 0
    }

    # Stoploss:
    stoploss = -0.035

    # Trailing stop:    
    trailing_stop: bool = False
    trailing_stop_positive: float = 0.05
    trailing_stop_positive_offset: float = 0.06
    trailing_only_offset_is_reached = False  # value loaded from strategy


    # Liquidation buffer percentage for the exchange.
    # This attribute will be overridden if the config file contains "liquidation_buffer".
    liquidation_buffer = DecimalParameter(0.03, 0.2, default=0.1, decimals=3, space="buy", optimize=False)


    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = True
    ignore_roi_if_entry_signal = True

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 12

    # Strategy parameters
    buy_rsi = IntParameter(10, 42, default=28, space="buy")
    sell_rsi = IntParameter(60, 94, default=79, space="sell")

    # Optional order type mapping.
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }
    
    @property
    def plotly_config(self):
        return {
            # Main plot indicators (Moving averages, ...)
            'main_plot': {
                'ST_long': {'color':'green'},
                'ST_short': {'color': 'red'}
              },
        }


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        
        # Momentum Indicators
        # ------------------------------------
        periodo = 7
        atr_multiplicador = 3.0

        dataframe['ST_long'] = pta.supertrend(dataframe['high'], dataframe['low'], dataframe['close'], length=periodo,
                                            multiplier=atr_multiplicador)[f'SUPERTl_{periodo}_{atr_multiplicador}']
        
        dataframe['ST_short'] = pta.supertrend(dataframe['high'], dataframe['low'], dataframe['close'], length=periodo,
                                            multiplier=atr_multiplicador)[f'SUPERTs_{periodo}_{atr_multiplicador}']
        
        # Exit short when indicator crosses back above 25
        dataframe.loc[(dataframe['ST_short'].shift(1) < 25) & (dataframe['ST_short'] >= 25), 'signal'] = 'exit'
        
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str], side: str,
                 **kwargs) -> float:

        proposed_leverage: 3.0
        max_leverage: 3.5
        side: LONG
        return 3.0

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Enter long position
        dataframe.loc[
            (
                (dataframe['ST_long'] < dataframe['close']) &
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'enter_long'] = 1

        # Enter short position
        dataframe.loc[
            (
                (dataframe['ST_short'] > dataframe['close']) &
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[
            (
                (dataframe['ST_short'] > dataframe['close']) &
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'exit_long'] = 1
        
        dataframe.loc[
            (
                (dataframe['ST_long'] < dataframe['close']) &
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'exit_short'] = 1
        
            
        return dataframe