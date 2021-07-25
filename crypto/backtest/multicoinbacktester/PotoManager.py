"""
    对目前持有币的管理.
    包括涨幅
"""
import os
import pandas as pd

#持有的币种信息
class CoinPosInfo(object):
    def __init__(self, price, volumn):
        self.cur_net = 0.0
        self.bought_price = price
        self.cur_price = price
        self.cur_pct = 0.0
        self.volumn = volumn
        self.bought_date = ""
        self.sold_date = ""

    def change_volumn(self, volumn):
        self.volumn += volumn

    def update(self, cur_price):
        self.cur_price = cur_price
        self.cur_net = self.volumn * cur_price
        self.cur_pct = (cur_price - self.bought_price) / self.bought_price


class PotoManager(object):

    def __init__(self):
        self.coins = {}
        self.net = 0.0

    def update_poto(self, symbol, price):
        if symbol not in self.coins:
            return
        self.coins[symbol].update(price)

    def buy_coin(self, symbol, price, volumn):
        self.coins[symbol] = CoinPosInfo(price, volumn)

    def sell_coin(self, symbol, volumn):
        if symbol not in self.coins:
            return
        sell_volumn = volumn if volumn < self.coins[symbol].volumn else self.coins[symbol].volumn
        self.coins[symbol].volumn -= sell_volumn
        if self.coins[symbol].volumn <= 0.0:
            del self.coins[symbol]

    def pct_max_coin(self):
        max_pct = -1.0
        max_coin = ''
        for coin, info in self.coins.items():
            if info.cur_pct > max_pct:
                max_pct = info.cur_pct
                max_coin = coin
        return max_coin

    def zhisun_coins(self, thld):
        result = []
        for coin, info in self.coins.items():
            if info.cur_pct < thld:
                result.append(coin)
        return result

    def pct_min_coin(self, coins):
        pass



