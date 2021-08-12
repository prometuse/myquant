"""

"""
import sys
import os

src_dir= os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, src_dir)
base_dat_dir=f'{src_dir}/online_data/'

from online.multicoinmm import Broker
from online.multicoinmm.PotoManager import PotoManager
from online.multicoinmm.PoolManager import PoolManager
from online.multicoinmm.HistDataManager import HistDataManager
from online.multicoinmm.strategy import BaseStrategy
from online.multicoinmm import MmStrategy
from online.multicoinmm import Evaluator
from online.multicoinmm.data import BarData
from utils.time_utils import *
from online.fetch_kline_inc import  *
from utils.log_utils import  *
from utils.file_utils import *
from datetime import datetime,timedelta
import pandas as pd
import glob
import pickle
from os import path
from types import SimpleNamespace


pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数


index_format = "%Y-%m-%d %H:%M:%S"

def load_data(topn, start_time, end_time, hour_cycle, trade_time, log_file):
    target_coins = read_file(f'{base_dat_dir}/exchange.txt')
    target_coins = [coin.lower() for coin in target_coins]
    target_coins = set(target_coins[:topn])

    from datetime import datetime
    start_day = datetime.strptime(start_time, index_format)
    end_day = datetime.strptime(end_time, index_format)
    days = (end_day - start_day).days
    hours = days * 24 + int((end_day - start_day).seconds / 3600)
    index = []
    for i in range(0, hours + 1):
        index.append((start_day + timedelta(hours=i)).strftime(index_format))
    date_index = pd.DataFrame(index, columns=['date_time'])

    coin_dfs = dict()
    for name in glob.glob(f'{base_dat_dir}/hour/*'):
        coin = name.split('/')[-1].split('.')[0].split('_')[0].lower()
        if coin not in target_coins:
            continue
        df = pd.read_csv(name) \
            .rename(columns={"openTime": "open_time"})

        #df = df[df['open_time'] >= start_time]
        #df = df[df['open_time'] <= end_time]

        if len(df) == 0:
            continue
        if coin not in coin_dfs:
            coin_dfs[coin] = df
        else:
            coin_dfs[coin] = coin_dfs[coin].append(df)

    legal_hours = len(index)
    remain_coins = {}
    for coin, df in coin_dfs.items():
        #try:
        if True:
            if len(df) < legal_hours:
                 continue
            df['open_time'] = pd.to_datetime(df['open_time']) - timedelta(hours=trade_time) #**表示N点开始交易！！！
            df['open_time'] = df['open_time'].apply(lambda x: x.strftime(index_format))
            df.set_index('open_time', inplace=True)
            df.sort_index(inplace=True)
            df = df[~df.index.duplicated(keep='first')]

            #补全数据
            total_df = pd.merge(date_index, df, how='left', left_on='date_time', right_on='open_time')
            total_df['date_time'] = pd.to_datetime(total_df['date_time'])
            total_df.set_index('date_time', inplace=True)
            total_df.sort_index(inplace=True)
            total_df = total_df.dropna(subset=['open']).ffill()
            #聚合
            period_type = f'{hour_cycle}H'
            cycle_df = total_df.resample(period_type).last()
            cycle_df['open'] = total_df['open'].resample(period_type).first()
            cycle_df['high'] = total_df['high'].resample(period_type).max()
            cycle_df['low'] = total_df['low'].resample(period_type).min()
            cycle_df['close'] = total_df['close'].resample(period_type).last()
            cycle_df['volumn'] = total_df['volumn'].resample(period_type).sum()

            remain_coins[coin] = cycle_df
            # if coin == 'btcusdt':
            #     print(cycle_df)
            #     exit()
        # except:
        #     print_log(f'[load online_data][error] {end_time} resample {coin} failed', log_file)
        #     continue
    print_log(f'[load data] {end_time} legal coin num: {len(remain_coins)}', log_file)
    print(f'[load data] {end_time} legal coin num: {len(remain_coins)}')
    return remain_coins

def test():
    # aa = BrokerTest("2021-08-04", 0.8)
    # with open(f'{base_dat_dir}/online_data/person.pkl', 'wb') as inp:
    #     pickle.dump(aa, inp)
    # exit()
    poto_manager = PotoManager(1.0)
    with open(f'{base_dat_dir}/potoManager.pkl', 'wb') as inp:
        pickle.dump(poto_manager, inp)

    with open(f'{base_dat_dir}/potoManager.pkl', 'rb') as inp:
        potoManager = pickle.load(inp)

if __name__ == '__main__':

    log_file = open(f'{base_dat_dir}/log/operate.log', 'a')

    BINANCE_SPOT_DAT_COL = ['open_time', 'open', 'high', 'low', 'close', 'volumn', 'close_time', 'quote_volumn', 'trades',
                            'taker_base_volumn', 'taker_quote_volumn', 'ignore']
    #params:
    import json
    config_str = open(f'{base_dat_dir}/config/config.json', mode='r').read()
    config = json.loads(config_str, object_hook=lambda d: SimpleNamespace(**d))

    '''
    time params: round to hour。 
    1.08-10 7:01 get 08-09 07 ~ 07 08-10 06. 时区不进行时间减少，按照crontab. 比如trade_time 7, crontab 7.01, 执行time=now()
    2.hour平移trade_time=7, 
    3.计算 8-7-8-9号的close数据
    '''
    cur_time = datetime.now()
    if config.start_time:
        cur_time = datetime.strptime(config.start_time, "%Y-%m-%d %H:%M:%S")#e.g 2021-08-10 08:01:00

    begin_datetime = datetime.strptime((cur_time - timedelta(hours=24)).strftime("%Y-%m-%d %H"), "%Y-%m-%d %H")
    #load
    load_begin_str = (begin_datetime - timedelta(days=(config.pct_days))).strftime(index_format)
    load_end_str = (begin_datetime + timedelta(hours=23)).strftime(index_format)
    #fetch
    fetch_begin_str = begin_datetime.strftime(index_format)
    fetch_end_str = load_end_str
    print('Fetch Begin hour:' + fetch_begin_str)
    print('Fetch End hour:' + fetch_end_str)
    #run
    run_begin_day = fetch_begin_str[0:10]
    run_end_day = fetch_begin_str[0:10]

    # fetch online_data inc
    if config.fetch_data_hours > 0:
        fetch_hours = 24 if config.fetch_data_hours <= 24 else config.fetch_data_hours
        fetch_start = datetime.strptime((cur_time - timedelta(hours=fetch_hours)).strftime("%Y-%m-%d %H"), "%Y-%m-%d %H").strftime(index_format)
        get_dat_signal = get_kline_batch_inc(base_dat_dir, fetch_start, fetch_end_str)
        if get_dat_signal < 0:
            print_log(f'[fetch kline error] {fetch_end_str}', log_file)
            exit()

    # load history online_data
    dfs = load_data(config.top_n_coins, load_begin_str, load_end_str, config.hours_cycle, config.trade_time, log_file)

    # load broker info:poto, cash
    broker = Broker(run_begin_day, run_end_day, config.init_money, one_buy_ratio=config.one_buy_ratio)
    broker.set_strategy(MmStrategy.MmStrategy)
    if path.exists(f"{base_dat_dir}/potoManager.pkl"):
        with open(f'{base_dat_dir}/potoManager.pkl', 'rb') as inp:
            potoManager = pickle.load(inp)
            print_log(f'[info load cash] {potoManager.cash}', log_file)
            print_log(f'[info load coins] {potoManager.coins}', log_file)
            broker.set_cash(potoManager.cash)
            broker.set_potoManager(potoManager)
    poolM = PoolManager(dfs.keys(), pct_days=config.pct_days)

    # run strategy
    broker.set_backtest_data(dfs)
    broker.set_time_range(run_begin_day, run_end_day)
    broker.run(poolM, config.sell_pct_rank_min, config.top_k_mm_buy, config.zhisun_pct, log_file)

    #save trade & net info
    Evaluator.Evaluator.save_net(f'{base_dat_dir}/hist/net_hist.txt', fetch_end_str, broker.hm.net_array)

    #save broker
    with open(f'{base_dat_dir}/potoManager.pkl', 'wb') as inp:
        pickle.dump(broker.poto_manager, inp)
