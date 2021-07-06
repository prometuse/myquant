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

class DataType(Enum):
    SPOT = 'spot' # 现货
    FUTURE = 'future' # 合约
    COINE_FUTURE = 'coin_future' # 币本位合约

BASE_URL_S = 'https://api.binance.com' # 现货
KLINE_URL_S = '/api/v3/klines' # K线数据

BASE_URL_F = 'https://fapi.binance.com' # U本位永续合约
KLINE_URL_F = '/fapi/v1/klines' # U本位永续合约K线
FUNDINGRATE_F ='/fapi/v1/fundingRate' # 资金费率

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


def convert_param_to_url(params:dict):
    return '&'.join([f'{k}={v}' for k, v in params.items() if v])

def get_klines(data_type: DataType, symbol, interval, start_time_str, end_time_str, output_path='day'):
    start_time = int(datetime.strptime(start_time_str, '%Y-%m-%d_%H_%M').timestamp() * 1000)
    end_time = int(datetime.strptime(end_time_str, '%Y-%m-%d_%H_%M').timestamp() * 1000)

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
    while cur_start_time < end_time and cur_end_time <= end_time:
        kline_param['startTime'] = cur_start_time
        kline_param['endTime'] = cur_end_time
        print('getting {} data from {} to {}'.format(symbol, time_utils.timestamp_to_str(cur_start_time/1000), time_utils.timestamp_to_str(cur_end_time/1000)))

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
        print('data shape:{}'.format(data.shape))
        time_col = pd.to_datetime(data['openTime'], unit='ms')
        data = pd.concat([time_col, data.drop(['openTime'], axis=1)], axis=1)

        total_data = total_data.append(data)

        cur_start_time += interval_dict[interval] * BINANCE_SPOT_LIMIT
        cur_end_time = min(end_time, cur_start_time + interval_dict[interval] * (BINANCE_SPOT_LIMIT - 1))

    total_data.set_index('openTime', inplace=True)
    total_data.to_csv('../data/spot_{}/{}_{}_{}_{}.csv'.format(output_path, symbol, interval, start_time_str, end_time_str))


def get_kline_batch():
    with open('../data/exchange.txt') as f:
        for line in f.readlines():
            symbol = line.strip()
            if symbol:
                get_klines(DataType.SPOT, symbol, "1d", "2020-01-01_06_55", "2020-12-31_06_55", 'day')

def main():
    get_kline_batch()

if __name__ == '__main__':
    main()


#获取天级别线

#获取小时级别

#获取分钟级别
