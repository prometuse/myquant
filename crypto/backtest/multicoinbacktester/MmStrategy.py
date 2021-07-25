"""
    简单动量 Strategy for CTA.

    挑选当时涨幅最大的5个币,按一定比例进行买卖
    条件限制：
    1.有一定相对成交量
    2.涨幅不能过大


"""
import numpy as np
import pandas as pd
from crypto.backtest.multicoinbacktester.strategy import BarData
from crypto.backtest.multicoinbacktester.strategy import BaseStrategy
from crypto.backtest.multicoinbacktester.array_manager import ArrayManager
from crypto.backtest.multicoinbacktester.broker import Broker
from crypto.backtest.multicoinbacktester.PoolManager import PoolManager
import talib as ta

class MmStrategy(BaseStrategy):

    def __init__(self, broker:Broker, poolM:PoolManager):
        super(BaseStrategy, self).__init__()

        #监控当前所有的交易对的动量
        self.broker = broker
        self.poolM = poolM

        self.sell_pct_rank_min = 10
        self.top_k_mm_buy = 3
        self.zhisun_pct = -0.1


    def on_start(self):
        """
        策略开始运行.
        :return:
        """

    def on_stop(self):
        """
        策略运行结束.
        :return:
        """

    def next_bar(self, bar: BarData):


        raise NotImplementedError("请在子类中实现该方法..")


    def buy(self, symbol, price, volume):
        """
        期货中做多，或者现货买
        :param price: 价格
        :param volume: 数量
        :return:
        """
        self.broker.buy(symbol, price, volume)

    def sell(self, price, volume):
        """
        期货合约平多，现货中的卖
        :param price: 价格
        :param volume: 数量
        :return:
        """
        self.broker.sell(price, volume)

    def short(self, price, volume):
        """
        期货做空，
        :param price: 价格
        :param volume: 数量
        :return:
        """
        self.broker.short(price, volume)

    def cover(self, price, volume):
        """
        做空平仓,
        :param price: 价格
        :param volume: 数量
        :return:
        """
        self.cover(price, volume)

    def on_start(self):
        print("策略开始运行..")

    def on_stop(self):
        print("策略停止运行..")

    def next_bar(self, bars):
        """
        这里是核心，整个策略都在这里实现..
        :param bar:
        :return:
        """
        # 1. use bar info to update pool and poto info
        datetime = ''
        for coin, bar in bars.items():
            datetime = bar.datetime
            # update coin info
            if bar.close_price <= 0.0:
                continue
            self.poolM.update_coin(coin, bar)
            # update hold coin info
            if coin in self.broker.poto_manager.coins:
                self.broker.poto_manager.update_poto(coin, bar.close_price)
        btc_price = bars['btcusdt'].close_price

        # 2:卖出
        # 1.卖策略：所持币涨幅跌出pool的topN， p2
        top_m_pct_coins = self.poolM.get_ndays_top_m_pct_coins(self.sell_pct_rank_min)
        #top_m_pct_coins = self.poolM.get_ndays_max_kcoins(self.sell_pct_rank_min, set(bars.keys()))
        coins = list(self.broker.poto_manager.coins.keys()).copy()
        for coin in coins:
            if coin not in top_m_pct_coins:
                self.broker.sell(coin, self.poolM.ams[coin].cur_close(), self.broker.poto_manager.coins[coin].volumn, f'{datetime} 跌出动量Top')
        # 2.止损
        zhisun_coins = self.broker.poto_manager.zhisun_coins(self.zhisun_pct)
        for coin in zhisun_coins:
            self.broker.sell(coin, self.poolM.ams[coin].cur_close(), self.broker.poto_manager.coins[coin].volumn, f'{datetime} 止损')

        # 3:买入
        # 买策略：买入N天涨幅最高的N个币, 一直补充满
        max_coins = self.poolM.get_ndays_max_kcoins(self.top_k_mm_buy, set(bars.keys()))
        #max_coins = [self.poolM.get_ndays_max_coin(set(bars.keys()))]

        #print(f"max coin:{max_coin}")

        for max_coin in max_coins:
            if max_coin and max_coin not in self.broker.poto_manager.coins:
                # 没有资金的卖策略
                # 1.挑选涨幅最大的一只卖出, 被其他币替换
                # if self.broker.cash <= 1.0:
                #     sell_max_pct_coin = self.broker.poto_manager.pct_max_coin()
                #     self.broker.sell(sell_max_pct_coin, self.poolM.ams[sell_max_pct_coin].cur_close(), self.broker.poto_manager.coins[sell_max_pct_coin].volumn, f'{datetime} 现金不够')
                # 2.不卖


                price = self.poolM.ams[max_coin].cur_close()
                volumn = min(self.broker.cur_net * self.broker.default_pos, self.broker.cash) / price
                if volumn > 0.0:
                    self.broker.buy(max_coin, price, volumn, f'{datetime} 动量Top')

        #update broker infos: net value and history data
        self.broker.update(bars)
        self.broker.hm.update(self.broker.cur_net, datetime, btc_price)
        print(f'{datetime} {self.broker.cur_net}')
