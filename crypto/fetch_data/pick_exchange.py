

def test():
    binance_dict = set()
    with open('../data/exchange_binance_volumn.txt', 'r') as f:
        for line in f.readlines():
            binance_dict.add(line.strip())

    with open('../data/exchange.txt', 'r') as f:
        idx = 0
        for line in f.readlines():
            coin = line.strip()
            idx += 1
            if idx <= 100 and coin in binance_dict:
                print(coin)

if __name__ == '__main__':
    test()