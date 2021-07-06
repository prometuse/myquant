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

def convert_param_to_url(params:dict):
    return '&'.join([f'{k}={v}' for k, v in params.items() if v])

def get_all_exchange():
    params = {
        'symbol': symbol,  # must
        'interval': interval,  # must   ENUM    YES
    }

    param_url = convert_param_to_url(kline_param)

    if data_type == DataType.SPOT:
        kline_param['limit'] = BINANCE_SPOT_LIMIT
        url = f'{BASE_URL_S}{KLINE_URL_S}?{param_url}'

    data = requests.get(url).json()

    data = pd.DataFrame(data, columns=BINANCE_SPOT_DAT_COL)
    SPOT, "BTCUSDT", "1h", "2021-01-01_00_00", "2021-06-30_23_00")

def main():
    get_kline_batch()

if __name__ == '__main__':
    main()


#获取天级别线

#获取小时级别

#获取分钟级别
