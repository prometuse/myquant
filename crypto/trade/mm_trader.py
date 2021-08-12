'''
动量策略trader
'''

import sys
import os
src_dir= os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, src_dir)

from gateway.binance import BinanceSpotHttp, OrderStatus, OrderType, OrderSide
from utils.config import config

class MMTrader(object):

    def __init__(self):
        """
        :param api_key:
        :param secret:
        :param trade_type: 交易的类型， only support future and spot.
        """
        self.http_client = BinanceSpotHttp(api_key=config.api_key, secret=config.api_secret, proxy_host=config.proxy_host, proxy_port=config.proxy_port)


    '''
    :param symbol
    :param money
    :return volumn
    
    order info examples:
    {'symbol': 'ADAUSDT', 'orderId': 2026696943, 'orderListId': -1, 'clientOrderId': 'x-A6SIDXVS16282641458061000001', 'price': '0.00000000', 'origQty': '8.00000000', 
    'executedQty': '8.00000000', 'cummulativeQuoteQty': '11.08320000', 'status': 'FILLED', 'timeInForce': 'GTC', 
    'type': 'MARKET', 'side': 'BUY', 'stopPrice': '0.00000000', 'icebergQty': '0.00000000', 'time': 1628264146417, 
    'updateTime': 1628264146417, 'isWorking': True, 'origQuoteOrderQty': '0.00000000'}
    '''
    def buy(self, symbol, money):
        order = self.http_client.place_order(symbol=symbol.upper(), order_side=OrderSide.BUY,
                                                order_type=OrderType.MARKET, quantity=0.1, price=0.1, quoteOrderQty=money)
        volumn = 0.0
        cost = 0.0
        if order:
            try:
                print('[buy order info]')
                print(order)
                volumn = float(order.get('executedQty'))
                cost = float(order.get('cummulativeQuoteQty'))
            except:
                return 0.0
        return volumn,cost

    '''
    {'symbol': 'ADAUSDT', 'orderId': 2029640096, 'orderListId': -1, 'clientOrderId': 'x-A6SIDXVS16283107334751000001', 
    'transactTime': 1628310733984, 'price': '0.00000000', 'origQty': '10.02000000', 'executedQty': '10.02000000',
     'cummulativeQuoteQty': '14.45485200', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'SELL',
      'fills': [{'price': '1.44260000', 'qty': '10.02000000', 'commission': '0.00003086', 'commissionAsset': 'BNB', 'tradeId': 231296778}]}
    '''
    def sell(self, symbol, volumn):
        order = self.http_client.place_order(symbol=symbol.upper(), order_side=OrderSide.SELL,
                                             order_type=OrderType.MARKET, quantity=volumn, price=0.1)
        money = 0.0
        if order:
            try:
                print('[sell order info]')
                print(order)
                money = float(order.get('cummulativeQuoteQty'))
            except:
                return 0.0
        return money

def ret_test():
    a=1
    b=2
    return a,b

def test():
    a,b = ret_test()
    print(a)
    print(b)


    #mmt = MMTrader()
    #print(mmt.buy('slpusdt', 10.0))


if __name__ == '__main__':
    test()