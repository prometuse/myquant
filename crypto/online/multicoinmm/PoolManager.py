"""
    对整个候选池的信息管理
"""
import os
import pandas as pd
from online.multicoinmm.array_manager import ArrayManager

MAX_LEGAL_RISE_RATIO = 0.5
MAX_LEGAL_HIGH_RATIO = 100
MIN_LEGAL_RISE_RATIO = -100

class PoolManager(object):
    def __init__(self, coins, pct_days):
        self.ams = {}
        for coin in coins:
            self.ams[coin] = ArrayManager(name=coin, pct_days=pct_days, size=1000)  # 计算产生的信号..

    def update_coin(self, coin, bar):
        self.ams[coin].update_bar(bar)

    def if_legal_coin(self, am):
        ret = am.cur_pct_n() <= MAX_LEGAL_RISE_RATIO and am.cur_pct_1day() >= MIN_LEGAL_RISE_RATIO \
                and am.cur_pct_n() != 0.0 \
              and am.count >= am.pct_days \
              and (am.cur_high() - am.cur_close()) / am.cur_close() <= MAX_LEGAL_HIGH_RATIO
        return ret
        #and am.count >= am.pct_days

    def get_ndays_max_kcoins(self, k, cur_cycle_coins):
        legal_ams = [am for am in self.ams.values() if am.name in cur_cycle_coins and self.if_legal_coin(am)]
        sorted_ams = sorted(legal_ams, key=lambda v: v.cur_score(), reverse=True)
        # for am in sorted_ams:
        #     print(f'{am.name} {am.cur_score()}')
        return [(am.name, am.cur_score()) for am in sorted_ams[:k]]

    def get_ndays_top_m_pct_coins(self, m):
        all_coins = list(self.ams.values())
        all_coins.sort(key=lambda x: x.cur_score(), reverse=True)
        top_coins = all_coins[:m]
        top_coins = [coin.name for coin in top_coins]
        return top_coins

    def caculate(self):
        pass


