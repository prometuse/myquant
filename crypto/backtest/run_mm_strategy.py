"""

"""
from crypto.backtest.multicoinbacktester import Broker
from crypto.backtest.multicoinbacktester import PotoManager
from crypto.backtest.multicoinbacktester.PoolManager import PoolManager
from crypto.backtest.multicoinbacktester import HistDataManager
from crypto.backtest.multicoinbacktester import MmStrategy
from crypto.backtest.multicoinbacktester import Evaluator
from crypto.utils.file_utils import read_file

import pandas as pd
import glob

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数

base_dir='/Users/daonyu/Documents/dev/my_quant/crypto/'

def load_data(topn, start_time, end_time):
    target_coins = read_file(f'{base_dir}/data/exchange.txt')
    target_coins = [coin.lower() for coin in target_coins]
    target_coins = set(target_coins[:topn])
    print(len(target_coins))

    from datetime import datetime
    date_format = "%Y-%m-%d"
    start_day = datetime.strptime(start_time, date_format)
    end_day = datetime.strptime(end_time, date_format)
    days = (end_day - start_day).days

    coin_dfs = dict()
    for name in glob.glob(f'{base_dir}/data/spot_day/*'):
        coin = name.split('/')[-1].split('_')[0].lower()
        if coin not in target_coins:
            continue
        df = pd.read_csv(name) \
            .rename(columns={"openTime": "open_time"})

        df = df[df['open_time'] >= start_time]
        df = df[df['open_time'] <= end_time]

        if len(df) == 0:
            continue
        if coin not in coin_dfs:
            coin_dfs[coin] = df
        else:
            coin_dfs[coin] = coin_dfs[coin].append(df)

    remain_coins = {}
    for coin, df in coin_dfs.items():
        try:
            if len(df) < (days - 1):
                continue
            df.set_index('open_time', inplace=True)
            df.sort_index(inplace=True)
            df = df[~df.index.duplicated(keep='first')]
            remain_coins[coin] = df
        except:
            print(coin)
            continue
    print(len(remain_coins))
    return remain_coins


if __name__ == '__main__':

    BINANCE_SPOT_DAT_COL = ['open_time', 'open', 'high', 'low', 'close', 'volumn', 'close_time', 'quote_volumn', 'trades',
                            'taker_base_volumn', 'taker_quote_volumn', 'ignore']
    data_dir = '/Users/daonyu/Documents/dev/crypto/myquant/crypto/data/spot_day'

    dfs = load_data(100, '2021-01-01', '2021-07-23')

    broker = Broker(dfs['btcusdt'].index.values[0])
    poolM = PoolManager(dfs.keys())

    broker.set_strategy(MmStrategy.MmStrategy)
    broker.set_leverage(1.0)
    broker.set_cash(1_000_000)  # 100万初始资金.
    broker.set_backtest_data(dfs)  # 数据.

    broker.run(poolM)

    Evaluator.Evaluator.stat_info(broker.hm.end_times, broker.hm.net_array, broker.hm.pct_array, broker.hm.btc_pct_array)

    # 参数优化， 穷举法， 遗传算法。
    # broker.optimize_strategy(long_period=[i for i in range(100, 300, 10)], short_period=[i for i in range(50, 100, 5)])






