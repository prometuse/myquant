"""
    简单动量 Strategy for CTA.

    挑选当时涨幅最大的5个币,按一定比例进行买卖
    条件限制：
    1.有一定相对成交量
    2.涨幅不能过大


"""
import numpy as np
import pandas as pd
from online.multicoinmm.strategy import BarData
from online.multicoinmm.strategy import BaseStrategy
from online.multicoinmm.array_manager import ArrayManager
from online.multicoinmm.broker import Broker
from online.multicoinmm.PoolManager import PoolManager
from gateway.binance import MIN_TRADE_QUOTE
import talib as ta
from utils.log_utils import print_log
from utils.config import config

class MmStrategy(BaseStrategy):

    def __init__(self, broker:Broker, poolM:PoolManager, sell_pct_rank_min, top_k_mm_buy, zhisun_pct, log_file=None):
        super(BaseStrategy, self).__init__()

        #监控当前所有的交易对的动量
        self.broker = broker
        self.poolM = poolM
        self.log_file = log_file
        self.sell_pct_rank_min = sell_pct_rank_min
        self.top_k_mm_buy = top_k_mm_buy
        self.zhisun_pct = zhisun_pct


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

    def update_bars(self, bars):
        for coin, bar in bars.items():
            # update coin info
            if bar.close_price <= 0.0:
                continue
            self.poolM.update_coin(coin, bar)
            # update hold coin info
            if coin in self.broker.poto_manager.coins:
                self.broker.poto_manager.update_poto(coin, bar.close_price)

    def next_bar(self, bars, datetime):
        """
        这里是核心，整个策略都在这里实现..
        :param bar:
        :return:
        """
        '''
        1. use bar info to update pool and poto info
        '''
        btc_price = bars['btcusdt'].close_price
        btc_score = self.poolM.ams['btcusdt'].cur_score()

        '''
        2:卖出
        '''
        # 1.止盈
        # 止盈, TODO,技术完善
        # zhiying_coins = self.broker.poto_manager.quick_zhiying_coins(config.zhiying_pct)
        # for coin in zhiying_coins:
        #     print_log(f'sell: {coin} 止盈 ', self.log_file)
        #     # self.broker.sell(coin, self.poolM.ams[coin].cur_close(), self.broker.poto_manager.coins[coin].volumn, f'{datetime} 止损')
        #     # 第一时间止盈
        #     self.broker.sell(coin, self.broker.poto_manager.coins[coin].bought_price * (1 + config.zhiying_pct), self.broker.poto_manager.coins[coin].volumn, f'{datetime} 止盈')

        # 2.卖策略：所持币涨幅跌出pool的topN， p2
        top_m_pct_coins = self.poolM.get_ndays_top_m_pct_coins(self.sell_pct_rank_min)
        #top_m_pct_coins = self.poolM.get_ndays_max_kcoins(self.sell_pct_rank_min, set(bars.keys())) 效果不好
        coins = list(self.broker.poto_manager.coins.keys()).copy()
        for coin in coins:
            if coin not in top_m_pct_coins:
                print_log(f'[sell] {datetime} {coin} 跌出动量Top ', self.log_file)
                if config.buy_real == 1:
                    self.broker.sell_online(coin, self.broker.poto_manager.coins[coin].volumn, f'{datetime} 跌出动量Top', self.log_file)
                else:
                    self.broker.sell(coin, self.poolM.ams[coin].cur_close(), self.broker.poto_manager.coins[coin].volumn, f'{datetime} 跌出动量Top')
        # 3.止损
        zhisun_coins = self.broker.poto_manager.zhisun_coins(self.zhisun_pct)
        for coin in zhisun_coins:
            print_log(f'[sell] {datetime} {coin} 止损 ', self.log_file)
            if config.buy_real == 1:
                self.broker.sell_online(coin, self.broker.poto_manager.coins[coin].volumn, f'{datetime} 止损', self.log_file)
            else:
                self.broker.sell(coin, self.poolM.ams[coin].cur_close(), self.broker.poto_manager.coins[coin].volumn, f'{datetime} 止损')
            #假设第一时间止损
            #self.broker.sell(coin, self.broker.poto_manager.coins[coin].bought_price * (1 + self.zhisun_pct), self.broker.poto_manager.coins[coin].volumn, f'{datetime} 止损')

        '''
        3:买入
        '''
        if btc_score >= config.btc_min_score and btc_score <= config.btc_max_score:#大盘太差或太好都不买
            # 买策略：买入N天涨幅最高的N个币, 一直补充满
            max_coins = self.poolM.get_ndays_max_kcoins(self.top_k_mm_buy, set(bars.keys()))

            for (max_coin, score) in max_coins:
                if max_coin and max_coin not in self.broker.poto_manager.coins:
                    # 没有资金的卖策略
                    # 1.挑选涨幅最大的一只卖出, 被其他币替换
                    # if self.broker.cash <= 1.0:
                    #     sell_max_pct_coin = self.broker.poto_manager.pct_max_coin()
                    #     self.broker.sell(sell_max_pct_coin, self.poolM.ams[sell_max_pct_coin].cur_close(), self.broker.poto_manager.coins[sell_max_pct_coin].volumn, f'{datetime} 现金不够')
                    # 2.不卖
                    # 3.挑选动量最低的卖

                    price = self.poolM.ams[max_coin].cur_close()
                    if self.broker.cash >= MIN_TRADE_QUOTE:
                        print_log(f'[buy] {datetime} {max_coin} {score} 动量Top ', self.log_file)
                        if config.buy_real == 1:
                            self.broker.buy_online(max_coin, f'{datetime} 动量Top score {"%.4f" % score}', self.log_file)
                        else:
                            self.broker.buy(max_coin, price, f'{datetime} 动量Top score {"%.4f" % score}')

        '''
        4 update broker infos: net value and history online_data
        '''
        self.broker.update(bars)
        self.broker.hm.update(self.broker.cur_net, datetime, btc_price)
        print(f'{datetime} net value: {self.broker.cur_net}')
