"""
    对整个候选池的信息管理
"""
import os
import pandas as pd
from crypto.backtest.multicoinbacktester.array_manager import ArrayManager

MAX_LEGAL_RISE_RATIO = 0.5
MIN_LEGAL_RISE_RATIO = -100

class PoolManager(object):
    def __init__(self, coins):
        self.ams = {}
        for coin in coins:
            self.ams[coin] = ArrayManager(name=coin, size=1000)  # 计算产生的信号..
        pass

    def update_coin(self, coin, bar):
        self.ams[coin].update_bar(bar)

    def get_ndays_max_coin(self, cur_cycle_coins):
        max_coin = ""
        max_pct = -1.0
        for coin, am in self.ams.items():
            if am.count <= 0 or coin not in cur_cycle_coins:
                continue
            if max_pct < am.cur_pct_n() and am.cur_pct_n() <= MAX_LEGAL_RISE_RATIO:
                max_pct = am.cur_pct_n()
                max_coin = coin
        return max_coin

    def get_ndays_max_kcoins(self, k, cur_cycle_coins):
        legal_ams = [am for am in self.ams.values() if am.name in cur_cycle_coins and am.cur_pct_n() <= MAX_LEGAL_RISE_RATIO and am.cur_pct_n() >= MIN_LEGAL_RISE_RATIO]
        sorted_ams = sorted(legal_ams, key=lambda v: v.cur_score(), reverse=True)
        return [am.name for am in sorted_ams[:k]]

    def get_ndays_top_m_pct_coins(self, m):
        all_coins = list(self.ams.values())
        all_coins.sort(key=lambda x: x.cur_score(), reverse=True)
        top_coins = all_coins[:m]
        top_coins = [coin.name for coin in top_coins]
        return top_coins

    def caculate(self):
        pass


