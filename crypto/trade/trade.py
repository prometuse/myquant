
import sys
import os
src_dir= os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, src_dir)

from gateway.binance import BinanceSpotHttp, OrderStatus, OrderType, OrderSide
from utils.config import config

config.loads('../data/config/config.json')

def test():
    http_client = BinanceSpotHttp(api_key=config.api_key, secret=config.api_secret, proxy_host=config.proxy_host,
                                       proxy_port=config.proxy_port)

    new_sell_order = http_client.place_order(symbol='adausdt'.upper(), order_side=OrderSide.SELL,
                                             order_type=OrderType.STOP, stop_price=)

    print(new_sell_order)
    exit()

    new_buy_order = http_client.place_order(symbol='adausdt'.upper(), order_side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=8, price=1.1, quoteOrderQty=0.1)
    print('order')
    print(new_buy_order)
    if new_buy_order:
        print('in order')
        print(new_buy_order.get('executedQty'))

    # if new_buy_order:
    #     print('check order')
    #     check_order = http_client.get_order('adausdt'.upper(),  client_order_id=new_buy_order.get('clientOrderId'))
    #     print(check_order)
    exit()
    #
    # print(new_buy_order)
    #
    # exit()



if __name__ == '__main__':
    test()