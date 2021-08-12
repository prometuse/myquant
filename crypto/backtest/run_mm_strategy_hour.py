"""

"""
from backtest.multicoinbacktester import Broker
from backtest.multicoinbacktester import PotoManager
from backtest.multicoinbacktester.PoolManager import PoolManager
from backtest.multicoinbacktester import HistDataManager
from backtest.multicoinbacktester import MmStrategy
from backtest.multicoinbacktester import Evaluator
from utils.file_utils import *
from utils.config import config
from datetime import datetime,timedelta
import pandas as pd
import glob

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数

base_dir='..'

def load_data(topn, start_time, end_time, hour_cycle, trade_time):
    target_coins = read_file(f'{base_dir}/data/exchange_binance_volumn.txt')
    target_coins = [coin.lower() for coin in target_coins]
    target_coins = set(target_coins[:topn])
    print(len(target_coins))

    from datetime import datetime
    date_format = "%Y-%m-%d %H:%M:%S"
    start_day = datetime.strptime(start_time, date_format)
    end_day = datetime.strptime(end_time, date_format)
    days = (end_day - start_day).days
    hours = days * 24 + int((end_day - start_day).seconds / 3600)
    index = []
    for i in range(0, hours + 1):
        index.append((start_day + timedelta(hours=i)).strftime(date_format))
    date_index = pd.DataFrame(index, columns=['date_time'])
    #date_index.set_index('date_time', inplace=True)
    #date_index.sort_index(inplace=True)

    coin_dfs = dict()
    for name in glob.glob(f'{base_dir}/data/spot_hour_binance/*'):
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

    legal_hours = len(coin_dfs['btcusdt'])
    remain_coins = {}
    for coin, df in coin_dfs.items():
        #try:
        if True:
            if len(df) < legal_hours:
                 continue
            df['open_time'] = pd.to_datetime(df['open_time']) - timedelta(hours=trade_time) #**表示N点开始交易！！！
            df['open_time'] = df['open_time'].apply(lambda x: x.strftime(date_format))
            df.set_index('open_time', inplace=True)
            df.sort_index(inplace=True)
            df = df[~df.index.duplicated(keep='first')]

            #if coin == 'scusdt':
            #     print(df)
            #补全数据
            #total_df['date_time'] = pd.to_datetime(total_df['date_time']) - timedelta(hours=trade_time) #**表示N点开始交易！！！
            total_df = pd.merge(date_index, df, how='left', left_on='date_time', right_on='open_time')
            total_df['date_time'] = pd.to_datetime(total_df['date_time'])
            total_df.set_index('date_time', inplace=True)
            total_df.sort_index(inplace=True)
            total_df = total_df.ffill()
            #total_df.to_csv("/Users/daonyu/Documents/workdesk/crypt_quant/test1.csv")

            #聚合
            period_type = f'{hour_cycle}H'
            cycle_df = total_df.resample(period_type).last()
            cycle_df['open'] = total_df['open'].resample(period_type).first()
            cycle_df['high'] = total_df['high'].resample(period_type).max()
            cycle_df['low'] = total_df['low'].resample(period_type).min()
            cycle_df['close'] = total_df['close'].resample(period_type).last()
            cycle_df['volumn'] = total_df['volumn'].resample(period_type).sum()
            #cycle_df.to_csv("/Users/daonyu/Documents/workdesk/crypt_quant/test2.csv")
            #exit()

            # if coin == 'btcusdt':
            #     print(cycle_df)
            #     exit()
            remain_coins[coin] = cycle_df
        # except:
        #     print(coin)
        #     continue
    print(len(remain_coins))
    return remain_coins


if __name__ == '__main__':

    BINANCE_SPOT_DAT_COL = ['open_time', 'open', 'high', 'low', 'close', 'volumn', 'close_time', 'quote_volumn', 'trades',
                            'taker_base_volumn', 'taker_quote_volumn', 'ignore']

    #config:
    config.loads('../data/config/config.json')
    start_day = '2021-07-01'
    end_day = '2021-08-05'
    load_start_day = (datetime.strptime(start_day, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")

    #log_base_dir= '/Users/daonyu/Documents/workdesk/crypt_quant/log/'
    log_base_dir= '/Users/daonyu/Documents/dev/crypto/myquant/crypto/data/debug'
    log_file = open(f'{log_base_dir}/operate.log', 'w')

    # load online_data
    dfs = load_data(config.top_n_coins, load_start_day + ' 00:00:00', end_day + ' 08:00:00', config.hours_cycle, config.trade_time)

    broker = Broker(start_day, config.init_cash, one_buy_ratio=config.one_buy_ratio)
    poolM = PoolManager(dfs.keys(), pct_days=config.pct_days)

    broker.set_strategy(MmStrategy.MmStrategy)
    broker.set_backtest_data(dfs)  # 数据.

    broker.run(poolM, config.sell_pct_rank_min, config.top_k_mm_buy, config.zhisun_pct, log_file)

    log_file.close()

    Evaluator.Evaluator.stat_info(broker.hm.end_times, broker.hm.net_array, broker.hm.pct_array, broker.hm.btc_pct_array)
