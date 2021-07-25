"""
    单个币的行情序列
"""

import numpy as np
import talib
from .data import BarData
import math

class ArrayManager(object):
    """
    For:
    1. time series container of bar data
    2. calculating technical indicator value
    """

    def __init__(self, name, size=500):
        """Constructor"""
        self.count = 0
        self.name = name
        self.size = size
        self.inited = False
        self.pct_days = 3

        self.open_array = np.zeros(size)
        self.high_array = np.zeros(size)
        self.low_array = np.zeros(size)
        self.close_array = np.zeros(size)
        self.volume_array = np.zeros(size)
        self.pct_ndays_array = np.zeros(size) #n日内的平均日收益率
        self.pct_log_ndays_array = np.zeros(size) #n日内的平均日收益率的对数
        self.pctbodong_ndays_array = np.zeros(size) #n日内的日收益率的波动率
        self.pctbodong_log_ndays_array = np.zeros(size) #n日内的日收益率的波动率

    def cur_open(self):
        return self.open_array[self.count]

    def cur_high(self):
        return self.high_array[self.count]

    def cur_low(self):
        return self.low_array[self.count]

    def cur_close(self):
        return self.close_array[self.count]

    def cur_volumn(self):
        return self.volume_array[self.count]

    def cur_pct_n(self):
        return self.pct_ndays_array[self.count]

    def cur_score(self):
        return self.pct_ndays_array[self.count]
        #return self.pct_ndays_array[self.count] / self.pctbodong_ndays_array[self.count]

    def update_bar(self, bar: BarData):
        """
        Update new bar data into array manager.
        """
        #**从1开始
        self.count += 1
        if not self.inited and self.count > self.size:
            self.inited = True

        self.open_array[self.count] = bar.open_price
        self.high_array[self.count] = bar.high_price
        self.low_array[self.count] = bar.low_price
        self.close_array[self.count] = bar.close_price
        self.volume_array[self.count] = bar.volume
        if self.count == 1:
            self.open_array[0] = bar.open_price
            self.high_array[0] = bar.high_price
            self.low_array[0] = bar.low_price
            self.close_array[0] = bar.close_price
            self.volume_array[0] = bar.volume

        #日收益率
        self.pct_ndays_array[self.count] = (bar.close_price - self.close_array[max(1, self.count - self.pct_days)]) / self.close_array[max(1, self.count - self.pct_days)]

        #日对数收益率

        #日收益率波动
        self.pctbodong_ndays_array[self.count] = np.std(self.pct_ndays_array[max(1, self.count - self.pct_days) :self.count])

        stat_days = min(self.pct_days, self.count)
        self.pct_ndays_array[self.count] = (bar.close_price - self.close_array[self.count - stat_days]) / self.close_array[self.count - stat_days]
        # self.pct_ndays_array[self.count] /= stat_days TODO:check
        # #日收益率波动
        # self.pctbodong_ndays_array[self.count] = np.std(self.pct_ndays_array[self.count - stat_days + 1:])

        # 日对数收益率
        # self.pct_log_ndays_array[self.count] = math.log(self.pct_ndays_array[self.count])
        # self.pctbodong_log_ndays_array[self.count] = np.std(self.pct_log_ndays_array[self.count - stat_days + 1:])

        # cum_pct = 1.0
        # for i in range(1, min(self.count, self.pct_days)):
        #     self.pct_ndays_array[self.count - i]
        # self.pct_ndays_array[self.count]
        return 0


    @property
    def open(self):
        """
        Get open price time series.
        """
        return self.open_array

    @property
    def high(self):
        """
        Get high price time series.
        """
        return self.high_array

    @property
    def low(self):
        """
        Get low price time series.
        """
        return self.low_array

    @property
    def close(self):
        """
        Get close price time series.
        """
        return self.close_array

    @property
    def volume(self):
        """
        Get trading volume time series.
        """
        return self.volume_array

    def sma(self, n, array=False):
        """
        Simple moving average.
        """
        result = talib.SMA(self.close, n)
        if array:
            return result
        return result[-1]

    def std(self, n, array=False):
        """
        Standard deviation
        """
        result = talib.STDDEV(self.close, n)
        if array:
            return result
        return result[-1]

    def cci(self, n, array=False):
        """
        Commodity Channel Index (CCI).
        """
        result = talib.CCI(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def atr(self, n, array=False):
        """
        Average True Range (ATR).
        """
        result = talib.ATR(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def rsi(self, n, array=False):
        """
        Relative Strenght Index (RSI).
        """
        result = talib.RSI(self.close, n)
        if array:
            return result
        return result[-1]

    def macd(self, fast_period, slow_period, signal_period, array=False):
        """
        MACD.
        """
        macd, signal, hist = talib.MACD(
            self.close, fast_period, slow_period, signal_period
        )
        if array:
            return macd, signal, hist
        return macd[-1], signal[-1], hist[-1]

    def adx(self, n, array=False):
        """
        ADX.
        """
        result = talib.ADX(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def boll(self, n, dev, array=False):
        """
        Bollinger Channel.
        """
        mid = self.sma(n, array)
        std = self.std(n, array)

        up = mid + std * dev
        down = mid - std * dev

        return up, down

    def keltner(self, n, dev, array=False):
        """
        Keltner Channel.
        """
        mid = self.sma(n, array)
        atr = self.atr(n, array)

        up = mid + atr * dev
        down = mid - atr * dev

        return up, down

    def donchian(self, n, array=False):
        """
        Donchian Channel.
        """
        up = talib.MAX(self.high, n)
        down = talib.MIN(self.low, n)

        if array:
            return up, down
        return up[-1], down[-1]
