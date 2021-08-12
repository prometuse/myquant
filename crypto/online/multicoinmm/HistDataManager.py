"""
    对历史的净值、年化、回撤信息进行快照记录
    每个周期都有个instance
"""

class HistDataManager(object):
    def __init__(self, init_cash, start_time):
        self.net_array = [init_cash]
        self.end_times = [start_time]
        self.btc_pct_array = [1.0]
        self.btc_price_array = []
        self.pct_array = [1.0]
        self.cnt = 0

    def update(self, net, datetime, btc_price):
        self.cnt += 1
        pct = self.pct_array[-1] * (1.0 + ((net - self.net_array[-1]) / self.net_array[-1]))
        self.pct_array.append(pct)
        self.net_array.append(net)
        self.end_times.append(datetime)

        if len(self.btc_price_array) == 0:
            self.btc_price_array.append(btc_price)
        btc_pct = self.btc_pct_array[-1] * (1.0 + (btc_price - self.btc_price_array[-1]) / self.btc_price_array[-1])
        self.btc_pct_array.append(btc_pct)
        self.btc_price_array.append(btc_price)