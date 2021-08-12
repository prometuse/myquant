#均线策略

import ccxt
import requests
import pytz
import time
from enum import Enum
from datetime import datetime
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import time_utils
from datetime import timedelta
import glob

class DataType(Enum):
    SPOT = 'spot' # 现货
    FUTURE = 'future' # 合约
    COINE_FUTURE = 'coin_future' # 币本位合约

BASE_URL_S = 'https://api.binance.com' # 现货
KLINE_URL_S = '/api/v3/klines' # K线数据

BASE_URL_F = 'https://fapi.binance.com' # U本位永续合约
KLINE_URL_F = '/fapi/v1/klines' # U本位永续合约K线
FUNDINGRATE_F ='/fapi/v1/fundipwdngRate' # 资金费率

MAX_FAIL_COIN_NUM = 30
BINANCE_SPOT_LIMIT = 500
BINANCE_FUTURE_LIMIT = 1500
FUNDINGRATE_LIMIT = 1000

# 单位 ms
MIN_INTERVAL = 60 * 1000
HOUR_INTERVAL = MIN_INTERVAL * 60
DAY_INTERVAL = HOUR_INTERVAL * 24
interval_dict = {
    "1m": MIN_INTERVAL,
    "1h": HOUR_INTERVAL,
    "1d": DAY_INTERVAL,
}
BINANCE_SPOT_DAT_COL=['openTime', 'open', 'high', 'low', 'close', 'volumn', 'closeTime', 'quote_volumn', 'trades', 'taker_base_volumn', 'taker_quote_volumn', 'ignore']
proxies = None

CHINA_TZ = pytz.timezone("Asia/Shanghai")
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数


SOURCE_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def convert_param_to_url(params:dict):
    return '&'.join([f'{k}={v}' for k, v in params.items() if v])

def fetch_new_data_multitimes(data_type: DataType, symbol, interval, start_time_str, end_time_str, max_try=3):

    cnt = 0
    while cnt < max_try:
        df = fetch_new_data(data_type, symbol, interval, start_time_str, end_time_str)
        if len(df) > 0:
            return df
        time.sleep(1)
        cnt += 1

    return pd.DataFrame(columns=BINANCE_SPOT_DAT_COL)

def fetch_new_data(data_type: DataType, symbol, interval, start_time_str, end_time_str):
    start_time = int(datetime.strptime(start_time_str, SOURCE_DATE_FORMAT).timestamp() * 1000)
    end_time = int(datetime.strptime(end_time_str, SOURCE_DATE_FORMAT).timestamp() * 1000)

    # 10050个， 需要调用 11次
    fetch_instance_num = (start_time - end_time) / interval_dict[interval]
    fetch_cnt = round(fetch_instance_num / BINANCE_SPOT_LIMIT)

    kline_param = {
        'symbol': symbol,  # must
        'interval': interval,  # must   ENUM    YES
    }

    cur_start_time = start_time
    cur_end_time = min(end_time, start_time + interval_dict[interval] * (BINANCE_SPOT_LIMIT - 1) )

    total_data = pd.DataFrame(columns=BINANCE_SPOT_DAT_COL)
    try:
        while cur_start_time < end_time and cur_end_time <= end_time:
            kline_param['startTime'] = cur_start_time
            kline_param['endTime'] = cur_end_time
            print('[fetch online_data] {} from {} to {}'.format(symbol, time_utils.timestamp_to_str(cur_start_time/1000), time_utils.timestamp_to_str(cur_end_time/1000)))

            param_url = convert_param_to_url(kline_param)

            if data_type == DataType.SPOT:
                kline_param['limit'] = BINANCE_SPOT_LIMIT
                url = f'{BASE_URL_S}{KLINE_URL_S}?{param_url}'

            elif data_type == DataType.FUTURE:
                kline_param['limit'] = BINANCE_FUTURE_LIMIT
                url = f'{BASE_URL_F}{KLINE_URL_F}?{param_url}'

            elif data_type == DataType.COINE_FUTURE:
                pass

            data = requests.get(url).json()

            data = pd.DataFrame(data, columns=BINANCE_SPOT_DAT_COL)
            print('online_data shape:{}'.format(data.shape))
            time_col = pd.to_datetime(data['openTime'], unit='ms') + timedelta(hours=8)
            data = pd.concat([time_col, data.drop(['openTime'], axis=1)], axis=1)

            total_data = total_data.append(data)

            cur_start_time = min(end_time, cur_start_time + interval_dict[interval] * BINANCE_SPOT_LIMIT)
            cur_end_time = min(end_time, cur_end_time + interval_dict[interval] * (BINANCE_SPOT_LIMIT))
    except:
        print(f'[fetch online_data] {start_time_str} failed')
        return total_data

    total_data.set_index('openTime', inplace=True)
    return total_data

def load_old_data(coin, dat_dir):
    total_df = pd.DataFrame(columns=BINANCE_SPOT_DAT_COL)
    for name in glob.glob(f'{dat_dir}/hour/*'):
        cur_coin = name.split('/')[-1].split('.')[0].split('_')[0].lower()
        if cur_coin != coin.lower():
            continue
        df = pd.read_csv(name)
        if len(df) == 0:
            continue
        total_df = total_df.append(df)
    total_df.set_index('openTime', inplace=True)
    return total_df
'''
    @return: -1不成功
'''
def get_kline_batch_inc(dat_dir, begin, end):
    fail_num = 0
    with open(f'{dat_dir}/fetch_data_exchange.txt') as f:
        for line in f.readlines():
            symbol = line.strip()
            if symbol:
                #7:01执行， 8-2 7:01 fetch 8-1 8:00 ~ 8-2 7:55
                #TODO, 失败重试
                new_df = fetch_new_data_multitimes(DataType.SPOT, symbol, "1h", begin, end)
                old_df = load_old_data(symbol, dat_dir)
                if len(new_df) == 0:
                    fail_num += 1
                else:
                    total_data = old_df.append(new_df)
                    total_data.to_csv(f'{dat_dir}/hour/{symbol}.csv')
    if fail_num > MAX_FAIL_COIN_NUM:
        return -1
    return 0

def main():
    get_kline_batch_inc()

if __name__ == '__main__':
    main()


#获取天级别线

#获取小时级别

#获取分钟级别
