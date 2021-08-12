"""
"""
from online.multicoinmm.PotoManager import *
from online.multicoinmm.HistDataManager import *
from utils.time_utils import *
from trade.mm_trader import *
from .strategy import BaseStrategy, BarData
from utils.config import config
from utils.log_utils import print_log

class Broker(object):

    def __init__(self, start_day, end_day, init_cash, one_buy_ratio):
        self.start_day = start_day
        self.end_day = end_day
        # 策略实例.
        self.strategy_instance = None

        # 手续费
        self.commission = 2/1000

        # 杠杆的比例, 默认使用杠杆.
        self.leverage = 1.0

        # 滑点率，设置为万5
        self.slipper_rate = 5/10000

        # 购买的资产的估值，作为计算爆仓的时候使用.
        self.asset_value = 0

        # 最低保证金比例, 使用bitfinex 的为例子.
        self.min_margin_rate = 0.15

        # 初始本金.
        self.cash = init_cash

        self.strategy_class = None

        # 交易的数据.
        self.trades = []

        # 当前提交的订单.
        self.active_orders = []

        # 回测的数据 dataframe数据, 多个coin, <coin_name,  coin_df>
        self.backtest_data = {}

        self.pos = 0  # 当前的持仓量..

        # 是否是运行策略优化的方法。
        self.is_optimizing_strategy = False

        #position管理
        #简单的最多5份，每份当前市值的20%
        self.default_pos = one_buy_ratio

        self.cur_net = self.cash
        # 每天的净值变化，用于画图和最后统计
        self.net_change_log = []

        #当前购买的交易对
        self.poto_manager = PotoManager(self.cash)

        #
        self.mmt = MMTrader()

        self.hm = HistDataManager(self.cur_net, start_day)

    def set_potoManager(self, poto_manager):
        self.poto_manager = poto_manager

    def set_strategy(self, strategy_class:BaseStrategy):
        """
        设置要跑的策略类.
        :param strategy_class:
        :return:
        """
        self.strategy_class = strategy_class

    def set_leverage(self, leverage: float):
        """
        设置杠杆率.
        :param leverage:
        :return:
        """
        self.leverage = leverage

    def set_commission(self, commission: float):
        """
        设置手续费.
        :param commission:
        :return:
        """
        self.commission = commission

    def set_backtest_data(self, data: pd.DataFrame):
        self.backtest_data = data

    def set_cash(self, cash):
        self.cash = cash

    def update(self, bars):
        self.set_net(bars)

    def set_net(self, bars):
        # cash  + coin net
        self.cur_net = self.cash
        for coin, info in self.poto_manager.coins.items():
            price = bars[coin].close_price
            self.cur_net += price * info.volumn
        self.net_change_log.append(self.cur_net)

    def set_time_range(self, start_day, end_day):
        self.start_day = start_day
        self.end_day = end_day

    def buy_online(self, symbol, msg='', log_file=None):
        """
        这里生成订单.
        order需要包含的信息， order_id, order_price, volume, order_time.
        :param price:
        :param volume:
        :return:
        """
        money = min(self.cur_net * self.default_pos, self.cash)
        money = round(money, 1)
        if money >= 10.0:
            volumn, cost = self.mmt.buy(symbol, money)
            if volumn > 0.0:
                #TODO:成交价和显示价格的差别
                buy_price = cost / volumn
                if log_file:
                    print_log(f"{msg} 买入下单: {symbol} {volumn} {buy_price} {cost}", log_file)
                print(f"{msg} 买入下单: {symbol} {volumn} {buy_price} {cost}")
                self.poto_manager.buy_coin(symbol, buy_price, volumn)
                print(f"买入: {self.poto_manager.coins.keys()} {[v.volumn * v.cur_price for v in self.poto_manager.coins.values()]}")
                self.cash = self.cash - cost
                self.poto_manager.cash = self.poto_manager.cash - cost
                return 1
        return 0

    def sell_online(self, symbol, volumn, msg='', log_file=None):
        volumn = round(volumn, 5)
        if symbol in self.poto_manager.coins and volumn > 0.0:
            money = self.mmt.sell(symbol, volumn)
            if money > 0.0:
                sell_price = float(money) / volumn
                if log_file:
                    print_log(f"{msg} 卖出下单: {symbol} {volumn} {sell_price} {money}", log_file)
                print(f"{msg} 卖出下单: {symbol} {volumn} {sell_price} {money}")
                self.cash = self.cash + money
                self.poto_manager.cash = self.poto_manager.cash + money
                self.poto_manager.sell_coin(symbol, volumn)
                return 1
        return 0

    def buy(self, symbol, price, msg=''):
        """
        这里生成订单.
        order需要包含的信息， order_id, order_price, volume, order_time.
        :param price:
        :param volume:
        :return:
        """
        money = min(self.cur_net * self.default_pos, self.cash)
        volumn = money / price / (1 + self.slipper_rate) / (1 + self.commission)
        if money > 0.0:
            print(f"{msg} 买入下单: {symbol} {volumn} {price} {money}")
            self.poto_manager.buy_coin(symbol, price, volumn)
            print(
                f"买入: {self.poto_manager.coins.keys()} {[v.volumn * v.cur_price for v in self.poto_manager.coins.values()]}")
            self.cash = self.cash - money
            self.poto_manager.cash = self.poto_manager.cash - money

    def sell(self, symbol, price, volumn, msg=''):
        if symbol in self.poto_manager.coins:
            money = price * volumn * (1 - self.slipper_rate) * (1 - self.commission)
            print(f"{msg} 卖出下单: {symbol} {volumn} {price} {money}")
            self.cash = self.cash + money
            self.poto_manager.cash = self.poto_manager.cash + money
            self.poto_manager.sell_coin(symbol, volumn)

    def short(self, price, volume):
        print(f"做空下单: {volume}@{price}")
        """
        在这里生成订单， 等待价格到达后成交.
        """

    def cover(self, symbol, price, volume):
        print(f"做空平仓下单: {volume}@{price}")
        """
        在这里生成订单， 等待价格到达后成交.
        """

    def run(self, poolM, sell_pct_rank_min, top_k_mm_buy, zhisun_pct, log_file=None):

        self.trades = []  # 开始策略前，把trades设置为空列表，表示没有任何交易记录.
        self.active_orders = []  #
        self.strategy_instance = self.strategy_class(self, poolM, sell_pct_rank_min, top_k_mm_buy, zhisun_pct, log_file)
        self.strategy_instance.broker = self
        self.strategy_instance.on_start()

        dates = self.backtest_data['btcusdt'].index.values

        for date in dates:
            print(f'[processing {date}]')
            cur_day = numpy64_to_str(date)[0:10]
            bars = dict()
            #update bars
            for coin, df in self.backtest_data.items():
                if date in dates:
                    candle = df.loc[date]
                    #TODO:因为关注的是某一点的成交价格下的动量，所以用 open初始化了close
                    bars[coin] = BarData(date, candle['open'], candle['high'], candle['low'], candle['close'], candle['volumn'])
            self.strategy_instance.update_bars(bars)

            #strategy
            # NOTICE:preload的排除
            if cur_day < self.start_day or cur_day > self.end_day:
                print(f'[skip preload {cur_day}]')
                continue
            self.check_order(bars)  # 检查订单是否成交..
            self.strategy_instance.next_bar(bars, cur_day)  # 处理数据..

        self.strategy_instance.on_stop()

        # 统计成交的信息.. 夏普率、 盈亏比、胜率、 最大回撤 年化率/最大回撤
        self.calculate()  # usdt.

    def calculate(self):
        # 拿到成交的信息，把成交的记录统计出来.
        sharp_ratio = 0.0
        for trade in self.trades:
            """
             order_id 
             trade_id
             price,
             volume 
             
             10000 --> 1BTC
             12000 --> 1BTC  -- >  2000
            """
            pass

    def check_order(self, bar):
        """
        根据订单信息， 检查是否满足成交的价格， 然后生成交易的记录.
        :param bar:
        :return:
        """
        """
        在这里比较比较订单的价格与当前价格是否满足成交，如果满足，在这里撮合订单。
        """