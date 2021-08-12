import MySQLdb
from stock.utils import *
import numpy as np
import pandas as pd
import sys

LABLE_STAT_DAYS = 5
JUNXIAN_STAT_DAYS = [3,6]
TIAOZHENG_STAT_DAYS = [3,10]

def load_stock_code_name_mapping():
	stocks = dict()
	with open('data/sh_stock_code_full.txt', 'r') as f:
		for line in f.readlines():
			name, code = line.strip().split('\t')
			code_str = "sh." + code
			if not code.startswith( '6' ):
				code_str = "sz." + code
			stocks[code_str] = name
	return stocks

def ana_junxian(dat, date_list, date_idx):

	if dat.empty or len(dat) < len(date_list):
			return False
	feas = {}

	low = dat.low
	high = dat.high
	close = dat.close
	pctChg =dat.pctChg
	turn = dat.turn
	amt = dat.amount
	df_ma = pd.DataFrame(close)
	ma_5 = ta.MA(close,timeperiod=5,matype=0)

	if_junxian_ok = False
	junxian_min_stat_day = JUNXIAN_STAT_DAYS[0]
	junxian_max_stat_day = JUNXIAN_STAT_DAYS[1]
	junxian_stat_days = junxian_min_stat_day - 1

	for j in range(date_idx - junxian_max_stat_day + 1, date_idx - junxian_min_stat_day + 2):
		junxian_stat_days += 1
		sub_if_junxian_ok = True
		pctChg_buf = []
		low_diff_buf = []
		turn_buff = []

		for i in range(j, date_idx + 1):
			low_diff = (low[i] - ma_5[i]) / low[i] * 100
			pctChg_buf.append(pctChg[i])
			low_diff_buf.append(abs(low_diff))
			turn_buff.append(turn[i])

			if low_diff <= -1.0 or low_diff >= 3.0:
				sub_if_junxian_ok = False
				break
			if pctChg[i] >= 5.0:
				sub_if_junxian_ok = False
				break

		avg_pctChg = np.mean(pctChg_buf)
		if avg_pctChg <= 1.5 or avg_pctChg >= 4.0:
			sub_if_junxian_ok = False
		avg_low_diff = np.mean(low_diff_buf)	
		if avg_low_diff >= 2.0:
			sub_if_junxian_ok = False

		#feas
		feas['junxian_turn'] = np.mean(turn_buff)
		feas['junxian_low'] = avg_low_diff
		feas['junxian_pctChg'] = avg_pctChg
		feas['price'] = close[date_idx - junxian_min_stat_day + 1]
		feas['market_value'] = amt[date_idx - junxian_min_stat_day + 1] / turn[i] * 100 / 100000000

		if sub_if_junxian_ok:
			if_junxian_ok = True
			break

	return if_junxian_ok,junxian_stat_days,feas

def ana_adjust(dat, date_list, date_idx):

	if dat.empty or len(dat) < len(date_list):
		return 0

	feas = {}

	open = dat.open
	low = dat.low
	high = dat.high
	close = dat.close
	pctChg = dat.pctChg
	turn = dat.turn
	avg_turn = np.mean(turn.tolist())

	if_adjust_ok = False
	adjust_min_stat_day = TIAOZHENG_STAT_DAYS[0]
	adjust_max_stat_day = TIAOZHENG_STAT_DAYS[1]

	for j in range(date_idx - adjust_max_stat_day + 1, date_idx - adjust_min_stat_day + 2):
		sub_if_adjust_ok = True
		turn_buf = []
		bodong_buf = []

		for i in range(j, date_idx + 1):
			#波动
			bodong = abs((high[i] - low[i]) / open[i])
			bodong_buf.append(bodong)
			if bodong > 0.04:
				sub_if_adjust_ok = False
				break

			#涨幅大小
			#print(abs(pctChg[i]))
			if abs(pctChg[i]) > 2:
 				sub_if_adjust_ok = False
 				break

			#换手
			turn_buf.append(turn[i])
			# if turn[i] > avg_turn:
			# 	sub_if_adjust_ok = False
			# 	break
		feas['adjust_turn'] = np.mean(turn_buf)
		feas['adjust_bodong'] = np.mean(bodong_buf)

		if sub_if_adjust_ok:
			if_adjust_ok = True
			break

	return if_adjust_ok, feas

def recall():


	return 0

def choose_good_stocks(dats, date_list, date_idx):
	stock_list = []
	types=['SMA','EMA','WMA','DEMA','TEMA','TRIMA','KAMA','MAMA','T3']
	feas = {}
	for code, dat in dats.items():
		if dat.empty or len(dat) < len(date_list):
			continue
		if_junxian_ok, junxian_stat_days, junxian_feas = ana_junxian(dat, date_list, date_idx)

		#前期调整是否到位
		#if_adjust_ok, adjust_feas = ana_adjust(dat, date_list, date_idx - junxian_stat_days)

        #大盘背离

		#if if_junxian_ok and if_adjust_ok:
		if if_junxian_ok:
			stock_list.append(code)
			#feas[code] = extract_feas(adjust_feas, junxian_feas)

	return stock_list, feas

def extract_feas(*raw_feas):
	# 个股
	# 大盘 
	# 板块
	feas = {}
	for raw_fea in raw_feas:
		feas.update(raw_fea)
	return sorted(feas.items(), key=lambda d:d[0], reverse = True)

def extract_label(stocks, dats, date_list, date_idx):
	labels = {}

	for stock in stocks:
		cur_df = dats[stock]

		pctChg = cur_df.pctChg

		profit = 1.0
		for i in range(date_idx + 1, date_idx + LABLE_STAT_DAYS + 1):
			profit *= (100.0 + pctChg[i]) / 100.0

		if stock not in labels:
			labels[stock] = {}
		labels[stock]['profit'] = profit

	return labels


def eva_dats(labels, dats):
	#how to buy

	#profit by buy_time, sell_time

	return 0

def select_dat(db, cursor, fields, date_begin, date_end):

	code_dict = {} #code -> dataframe(date, feas)
	code_dict_df = {} #code -> dataframe(date, feas)

	sql = "SELECT  " + ','.join(fields) + " FROM a_stock_market_price_day " \
		" WHERE date between '" + date_begin + "' and '" + date_end + "' and amount > 0.0 and isST = 0" + \
		" order by code, date"
		#" and code in ('sz.000524', 'sh.000001') " + \

	try:
		cursor.execute(sql)
		results = cursor.fetchall()
		for row in results:
			code = row[2]
			if code not in code_dict:
				code_dict[code] = []
			code_dict[code].append([row[i] for i in range(0, len(fields))])

		for code, infos in code_dict.items():
			if infos != None:
				code_dict_df[code] = pd.DataFrame(infos, columns=fields)

	except:
		print("Error: unable to fecth fetch_data")
	return code_dict_df

def ana_juxian(mode, *args):

	db = MySQLdb.connect("localhost", "root", "fwfw1231231", "astock", charset='utf8' )
	cursor = db.cursor()

	fetch_fields = 'date,name,code,open,high,low,close,preclose,volume,amount,turn,pctChg'.split(',')
	#
	code_name_dict = load_stock_code_name_mapping()

	date_begin = '2020-07-01'
	date_end = '2020-07-28'

	#basci dat
	stock_infos = select_dat(db, cursor, fetch_fields, date_begin, date_end)
	date_list = stock_infos['sh.000001'].date.tolist()

	target_date = '2020-07-27'
	target_idx = date_list.index(target_date)
	good_stocks, feas = choose_good_stocks(stock_infos, date_list, target_idx)

	#generate sample
	if mode == 'train':
		labels = extract_label(good_stocks, stock_infos, date_list, target_idx)
		for code in good_stocks:
			code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
			fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
			profit = str(labels[code]['profit'])
			print(code + '\t' + code_name + '\t' + profit + '\t' + fea_str)

	#predict
	if mode == 'predict':	
		for code in good_stocks:
			code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
			#fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
			print(code + '\t' + code_name)

	db.close()

def main():
	mode = sys.argv[1]
	ana_juxian(mode)

if __name__ == '__main__':
    main()
