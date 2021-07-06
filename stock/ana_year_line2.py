#年线策略:连续年线

import MySQLdb
from stock.utils import *
import numpy as np
import pandas as pd
import sys

IF_DEBUG=False
MODE = 'predict'
DEBUG_INFO = {'s1':0, 's2':0, 's3':0, 's4':0, 'c1':0, 'c2':0, 'c3':0, 'c4':0, 'c5':0, 'sc1':0, 'f':0}

YEAR_LINE_STAT_RANGE = 100
TUPO_PRE_STAT_MIN = 30
TUPO_STAT_RANGE = 2
TUPO_STAT_MAX_RANGE = 20
TUPO_HUITIAO_MIN_GAP = 4
HUITIAO_STAT_RANGE = 2
HUITIAO_STAT_MAX_RANGE = 20

TUPO_THLD_PERCENT = 0.06
HUITIAO_THLD_PERCENT = 0.03
FANGLIANG_COE = 4.0
SUOLIANG_COE = 0.6
MIN_VOL_COE = 1.5

MAX_ZHANGFU = 0.1
MAX_DIEFU_UNDER_YEAR_LINE = 0.05
MIN_pctChg = 3.0
MAX_pctChg_MINUS = -8.0 
CURRENT_PRICE_THLD = 0.1
MAX_LIANXU_MINUS = 4
MAX_MKT_VALUE = 1000

LABLE_STAT_DAYS = 30
YIYI = 100000000
SHANGZHENG_CODE='sh.000001'
ZHONGXIAO_CODE='sz.399106'
CHUANGYE_CODE='sz.399006'

def reset_gloabl_var():
	for k, v in DEBUG_INFO.items():
		DEBUG_INFO[k] = 0

def match_pre_adjust_under_year_line(dat, ma, date_list, begin_idx, end_idx, feas, adjust_least_days=TUPO_PRE_STAT_MIN):
	close = dat.close
	pctChg =dat.pctChg
	turn = dat.turn
	volume = dat.volume
	if_nianxian_tiaozheng = False
	s1_end = begin_idx
	for s1_i in range(begin_idx, end_idx):
		if close[s1_i] >= ma[s1_i]:
			s1_end = s1_i
			break
	if (s1_end - begin_idx) >= adjust_least_days:
		if IF_DEBUG:
			print("年线调整" + date_list[s1_end])
		if_nianxian_tiaozheng = True
		DEBUG_INFO['s1'] = DEBUG_INFO['s1'] + 1
		pre_vol = np.mean([volume[j] for j in range(begin_idx, s1_end)])
		feas['pre_vol'] = pre_vol

	return if_nianxian_tiaozheng, s1_end

def match_fangliang_tupo(dat, ma, date_list, begin_idx, end_idx, feas, fangliang_coe=FANGLIANG_COE):
	close = dat.close
	pctChg =dat.pctChg
	volume = dat.volume
	if_fangliangtupo = False
	s2_begin = 0
	s2_end = 0
	tupo_vol = 0.0
	for s2_i in range(begin_idx, end_idx):
		if (close[s2_i] - ma[s2_i]) / ma[s2_i] >= TUPO_THLD_PERCENT:
			if IF_DEBUG:
				print("突破" + date_list[s2_i])

			tupo_vol = np.mean([volume[j] for j in range(s2_i, s2_i + TUPO_STAT_RANGE)])
			feas['tupo_vol'] = tupo_vol
			#print("{}\t{}\t{}".format(date_list[s2_i], date_list[s2_i + TUPO_STAT_RANGE], tupo_vol))

			if 'pre_vol' in feas and feas['pre_vol'] > 0.0 and tupo_vol / feas['pre_vol'] > fangliang_coe:
				if IF_DEBUG:
					print("放量" + date_list[s2_i])
				if_fangliangtupo = True
				DEBUG_INFO['s2'] = DEBUG_INFO['s2'] + 1
				s2_begin = s2_i
				s2_end = s2_i + TUPO_STAT_RANGE
				break

	return if_fangliangtupo, s2_begin, s2_end

def match_suoliang_huitiao(dat, ma, date_list, date_idx, s2_begin_idx, begin_idx, end_idx, feas, if_condition=True, tupo_huitiao_gap=TUPO_HUITIAO_MIN_GAP, suoliang_coe=SUOLIANG_COE):
	close = dat.close
	pctChg =dat.pctChg
	volume = dat.volume
	if_tiqianhuitiao = False
	if_suolianghuitiao = False
	if_condition_ok = False
	huitiao_vol = 0.0
	s3_end = begin_idx

	#不能提前回调
	for s3_i in range(begin_idx, min(begin_idx + tupo_huitiao_gap, date_idx)):
		if (close[s3_i] - ma[s3_i]) / ma[s3_i] <= HUITIAO_THLD_PERCENT:
			if_tiqianhuitiao = True
			DEBUG_INFO['sc1'] = DEBUG_INFO['sc1'] + 1
			break
	if not if_tiqianhuitiao:
		for s3_i in range(begin_idx + tupo_huitiao_gap, end_idx):
		#DEBUG if date_list[i] == '2020-07-06':
			if (close[s3_i] - ma[s3_i]) / ma[s3_i] <= HUITIAO_THLD_PERCENT:
				if IF_DEBUG:
					print("回调" + date_list[s3_i])
				DEBUG_INFO['s3'] = DEBUG_INFO['s3'] + 1

				#放量
				huitiao_vol = np.mean([volume[j] for j in range(s3_i, min(date_idx, s3_i + HUITIAO_STAT_RANGE))])
				feas['huitiao_vol'] = huitiao_vol	
				#print("回调{}\t{}\t{}".format(date_list[s3_i], date_list[date_idx], huitiao_vol))

				if 'tupo_vol' in feas and feas['tupo_vol'] > 0 and huitiao_vol / feas['tupo_vol'] <= suoliang_coe:
					if IF_DEBUG:
						print("缩量" + date_list[s3_i])
					if_suolianghuitiao = True
					DEBUG_INFO['s4'] = DEBUG_INFO['s4'] + 1
					s3_end = s3_i

					if if_condition:
						if_condition_ok = match_condition(dat, ma, date_list, s2_begin_idx, date_idx, feas)
					else:
						if_condition_ok = True

					if if_condition_ok:
						break

	return if_suolianghuitiao, if_condition_ok, s3_end

def match_condition(dat, ma, date_list, s2_begin_idx, date_idx, feas):
	close = dat.close
	pctChg =dat.pctChg
	volume = dat.volume
	amt = dat.amount
	turn = dat.turn

	#附加条件限制:
	if_c1_ok = False
	if_c2_ok = False
	if_c3_ok = False
	if_c4_ok = False
	if_c5_ok = False
	if_c6_ok = False

	max_price = -1.0
	min_price = 1000000.0
	max_huitiao_percent = 0.0
	max_pctChg = -1.0
	max_pctChg_minus = 100000.0
	for c_i in range(s2_begin_idx, date_idx + 1):
		if close[c_i] > max_price:
			max_price = close[c_i]
		if close[c_i] < min_price:
			min_price = close[c_i]
		huitiao_percent = (close[c_i] - ma[c_i]) / ma[c_i]
		if  huitiao_percent < 0.0 and huitiao_percent < max_huitiao_percent:
			max_huitiao_percent = huitiao_percent
		if pctChg[c_i] > max_pctChg:
			max_pctChg = pctChg[c_i]
		if pctChg[c_i] < 0.0 and pctChg[c_i] < max_pctChg_minus:
			max_pctChg_minus = pctChg[c_i] 

	cur_price = close[date_idx]
	cur_vol = volume[date_idx]
	cur_year_line_price = ma[date_idx]
	mkt_value = amt[date_idx] / turn[date_idx] * 100 / YIYI
	# print((max_price - cur_price) / cur_price)
	# print((max_price - min_price) / min_price)
	# print(abs(max_huitiao_percent))
	# print(max_pctChg)
	# print(max_pctChg_minus)

	if mkt_value <= MAX_MKT_VALUE:
		if_c1_ok = False
		if_c2_ok = False
		if_c3_ok = False
		if_c4_ok = False
		if_c5_ok = False
		if_c6_ok = False
		#if (max_price - cur_price) / cur_price < MAX_ZHANGFU:
		if 'pre_vol' in feas and cur_vol / feas['pre_vol'] > MIN_VOL_COE:
			if_c1_ok = True
			DEBUG_INFO['c1'] = DEBUG_INFO['c1'] + 1
		if abs(max_huitiao_percent) < MAX_DIEFU_UNDER_YEAR_LINE:
			if_c2_ok = True	
			DEBUG_INFO['c2'] = DEBUG_INFO['c2'] + 1
		if max_pctChg > MIN_pctChg:
			if_c3_ok = True
			DEBUG_INFO['c3'] = DEBUG_INFO['c3'] + 1
		if max_pctChg_minus > MAX_pctChg_MINUS:
			if_c4_ok = True
			DEBUG_INFO['c4'] = DEBUG_INFO['c4'] + 1
		cur_price_year_line_gap = ( cur_price - cur_year_line_price ) / cur_price
		if cur_price_year_line_gap >= -0.03:
		# and cur_price_year_line_gap <= 0.1
			if_c5_ok = True
			DEBUG_INFO['c5'] = DEBUG_INFO['c5'] + 1

		#往前回溯，连续N天下跌
		for k in range(date_idx - MAX_LIANXU_MINUS + 1, date_idx + 1):
			if pctChg[k] > -1.0:
				if_c6_ok = True
				break

		if IF_DEBUG:
			print(if_c1_ok)
			print(if_c2_ok)
			print(if_c3_ok)
			print(if_c4_ok)
			print(if_c5_ok)	
			print(if_c6_ok)

	return if_c1_ok and if_c2_ok and if_c3_ok and if_c4_ok and if_c5_ok and if_c6_ok

def ana_year_line(dat, date_list, date_idx, code=''):
	"""突破年线"""
	"""rule:  s1->s2->s3-> c1...."""
	if dat.empty or len(dat) < len(date_list):
		# print(code)
		# print(len(dat))
		# print(len(date_list))
		# print('not ok')
		return False, {}
	feas = {}

	low = dat.low
	high = dat.high
	close = dat.close
	pctChg =dat.pctChg
	turn = dat.turn
	amt = dat.amount
	volume = dat.volume
	df_ma = pd.DataFrame(close)
	ma = ta.MA(close, timeperiod=250)#year line

	if_final_ok = False

	tupo_vol = 0.0
	huitiao_vol = 0.0

	i = max(date_idx - YEAR_LINE_STAT_RANGE, 0)
	outer_end = date_idx - TUPO_STAT_RANGE - TUPO_HUITIAO_MIN_GAP - HUITIAO_STAT_RANGE + 2
	while i <= outer_end:
		feas = {}
		#s1:年线以下调整
		if_nianxian_tiaozheng, s1_end = match_pre_adjust_under_year_line(dat, ma, date_list, i, outer_end, feas)

		if if_nianxian_tiaozheng:
			#s2:放量突破
			s2_max_end = min(s1_end + TUPO_STAT_MAX_RANGE, date_idx)
			if_fangliangtupo, s2_begin, s2_end = match_fangliang_tupo(dat, ma, date_list, s1_end, s2_max_end, feas, fangliang_coe=3.0)

			#s3:缩量回调
			if if_fangliangtupo:
				if_suolianghuitiao, if_condition_ok, s3_end = match_suoliang_huitiao(dat, ma, date_list, date_idx, s2_begin, s2_end, \
					min(s2_end + TUPO_HUITIAO_MIN_GAP + HUITIAO_STAT_MAX_RANGE, date_idx), feas, if_condition=False)

				#二次
				if if_suolianghuitiao:
					sec_feas = {}

					#if_sec_tiaozheng, s1_end2 = match_pre_adjust_under_year_line(dat, ma, date_list, s3_end+1, outer_end, sec_feas, adjust_least_days=3)
					# print(code)
					# print(date_list[s3_end+1])
					# print(if_sec_tiaozheng)

					#if if_sec_tiaozheng:
					s1_end2 = s3_end
					sec_feas['pre_vol'] = feas['huitiao_vol']
					s2_max_end = min(s1_end2 + TUPO_STAT_MAX_RANGE, date_idx)
					if_sec_tupo, s2_begin2, s2_end2 = match_fangliang_tupo(dat, ma, date_list, s1_end2, s2_max_end, sec_feas, fangliang_coe=2.0)
					#print(if_sec_tupo)
					
					if if_sec_tupo:
						if_suoliang2, if_condition2, s3_end2 = match_suoliang_huitiao(dat, ma, date_list, date_idx, s2_begin2, s2_end2, \
							min(int(s2_end2 + TUPO_HUITIAO_MIN_GAP + HUITIAO_STAT_MAX_RANGE), date_idx), sec_feas, if_condition=False, tupo_huitiao_gap=int(TUPO_HUITIAO_MIN_GAP), suoliang_coe=0.8 )

						if_final_ok = if_suoliang2 and if_condition2
		if if_final_ok:
			break

		i = s1_end + 1

	return if_final_ok, feas

def recall_stocks(dats, date_list, date_idx):
	"""年线召回"""
	stock_list = []
	types=['SMA','EMA','WMA','DEMA','TEMA','TRIMA','KAMA','MAMA','T3']
	feas = {}
	for code, dat in dats.items():
		#年线策略
		if code in [SHANGZHENG_CODE, ZHONGXIAO_CODE, CHUANGYE_CODE]:
			continue
		if_year_ok, feas = ana_year_line(dat, date_list, date_idx, code)

		if if_year_ok:
			stock_list.append(code)
			#feas[code] = extract_feas(adjust_feas, junxian_feas)

	return stock_list, feas

def rank_stocks():
	return 0

def extract_feas(*raw_feas):
	# 个股
	# 大盘 
	# 板块
	feas = {}
	for raw_fea in raw_feas:
		feas.update(raw_fea)
	return sorted(feas.items(), key=lambda d:d[0], reverse = True)

def extract_label(stocks, dats, date_list, date_idx, stat_days):
	labels = {}

	for stock in stocks:
		cur_df = dats[stock]

		pctChg = cur_df.pctChg

		profit = 1.0
		max_profit = 1.0

		for i in range(date_idx + 1, min(date_idx + stat_days + 1, len(date_list)) ):
			profit *= (100.0 + pctChg[i]) / 100.0

			#融入买卖点策略
			#stra1:利益回撤
			if profit > max_profit:
				max_profit = profit
			if max_profit > 1.0:
				delta_profit = (max_profit - 1.0 - (profit - 1.0))
				delta_profit_percent = (profit - 1.0) / (max_profit - 1.0) 
				if max_profit >= 1.3 and delta_profit_percent <= 0.6:
					if IF_DEBUG:
						print('sell 1 :' + date_list[i])
					break
				# if max_profit >= 1.2 and delta_profit_percent <= 0.5:
				# 	if IF_DEBUG:
				# 		print('sell 2 :' + date_list[i])
				# 	break
				# if delta_profit >= 0.1:
				# 	if IF_DEBUG:
				# 		print('sell 3 : {} {} {}'.format(date_list[i], max_profit, delta_profit))
				# 	break

			#stra2:止损
			if profit <= 0.9:
				if IF_DEBUG:
					print('sell 3 :' + date_list[i])
				break

		if stock not in labels:
			labels[stock] = {}
		labels[stock]['profit'] = profit

	return labels


def sell_func():
	return 0

def buy_func():
	return 0

def eva_dats(labels, dats):
	#how to buy

	#profit by buy_time, sell_time

	return 0

def select_dat(db, cursor, fields, date_begin, date_end):

	code_dict = {} #code -> dataframe(date, feas)
	code_dict_df = {} #code -> dataframe(date, feas)

	sql = "SELECT  " + ','.join(fields) + " FROM a_stock_market_price_day " \
		" WHERE date between '" + date_begin + "' and '" + date_end + "' and (amount<=0.0  or  amount/turn/100000000 <= 2000 or  code in ('sh.000001', 'sz.399106', 'sz.399006') ) " + \
		" order by code, date"
		#" and code in ('sz.000923', 'sh.000001', 'sz.399106', 'sz.399006') " + \

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

	return code_dict_df

def init(begin_date, end_date):
	db = MySQLdb.connect("localhost", "root", "fwfw1231231", "astock", charset='utf8' )
	cursor = db.cursor()

	fetch_fields = 'date,name,code,open,high,low,close,preclose,volume,amount,turn,pctChg'.split(',')


	stock_infos = select_dat(db, cursor, fetch_fields, begin_date, end_date)
	
	date_list = stock_infos[SHANGZHENG_CODE].date.tolist()

	code_name_dict = load_stock_code_name_mapping()

	db.close()

	return stock_infos, date_list, code_name_dict

def ana_oneday(*args):

	#init
	date_begin = '2018-01-01'
	date_end = '2020-08-01'
	stock_infos, date_list, code_name_dict = init(date_begin, date_end)

	#recall
	target_date = '2020-06-19'
	target_idx = date_list.index(target_date)
	stock_candidates, feas = recall_stocks(stock_infos, date_list, target_idx)

	#generate sample
	if mode == 'train':
		labels = extract_label(stock_candidates, stock_infos, date_list, target_idx, LABLE_STAT_DAYS)
		for code in stock_candidates:
			code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
			fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
			profit = str(labels[code]['profit'])
			print(code + '\t' + code_name + '\t' + profit + '\t' + fea_str)

	#predict
	if mode == 'predict':	
		for code in stock_candidates:
			code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
			#fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
			print(code + '\t' + code_name)

def ana_days(*args):

	#init
	date_begin = '2018-01-01'
	date_end = '2020-09-22'
	stock_infos, date_list, code_name_dict = init(date_begin, date_end)

	#recall
	stock_set = set()
	target_begin_date = '2020-09-22'
	target_begin_idx = date_list.index(target_begin_date)

	target_end_date = '2020-09-22'
	target_end_idx = date_list.index(target_end_date)

	for target_idx in range(target_begin_idx, target_end_idx + 1):
		stock_candidates, feas = recall_stocks(stock_infos, date_list, target_idx)
		cur_date = date_list[target_idx]
		#print(date_list[target_idx])
		#print(DEBUG_INFO)
		reset_gloabl_var()

		#generate sample
		if MODE == 'train':
			labels = extract_label(stock_candidates, stock_infos, date_list, target_idx, LABLE_STAT_DAYS)
			for code in stock_candidates:
				if code not in stock_set:
					code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
					fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
					profit = str(labels[code]['profit'])
					print(cur_date + '\t' + code + '\t' + code_name + '\t' + profit + '\t' + fea_str)
				stock_set.add(code)

		#predict
		if MODE == 'predict':	
			for code in stock_candidates:
				if code not in stock_set:
					code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
					#fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
					print(cur_date + '\t' + code + '\t' + code_name)
				stock_set.add(code)

		sys.stdout.flush()



def main():
	ana_days()

if __name__ == '__main__':
    main()
