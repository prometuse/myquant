import pandas as pd
import MySQLdb
import talib as ta

def load_stock_code_name_mapping():
	""" """
	stocks = dict()
	with open('data/sh_stock_code_full.txt', 'r') as f:
		for line in f.readlines():
			name, code = line.strip().split('\t')
			code_str = "sh." + code
			if not code.startswith( '6' ):
				code_str = "sz." + code
			stocks[code_str] = name
	return stocks

def if_zhangtings(preclose, close, pctChg):
	if pctChg < 9.0:
		return False
	if (preclose * 1.1 - close) < 0.01:
		return True
	return False

def if_continue_rise():
	return 0

def if_junxian_good(dat_df):
	#10
	#5
	types=['SMA','EMA','WMA','DEMA','TEMA',
	'TRIMA','KAMA','MAMA','T3']
	df_ma=pd.DataFrame(df.close)
	for i in range(len(types)):
	    df_ma[types[i]]=ta.MA(df.close,timeperiod=5,matype=i)
	df_ma.tail()

	return 0

def test():
	if_zhangtings()

if __name__ == '__main__':
    test()