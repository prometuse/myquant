#年线策略: 但次年线

import MySQLdb
from stock.utils import *
import numpy as np
import pandas as pd
import sys

IF_DEBUG=False
DEBUG_INFO = {'s1':0, 's2':0, 's3':0, 's4':0, 'c1':0, 'c2':0, 'c3':0, 'c4':0, 'c5':0, 'sc1':0, 'f':0}

YEAR_LINE_STAT_RANGE = 100
TUPO_PRE_STAT_MIN = 30
TUPO_STAT_RANGE = 2
TUPO_STAT_MAX_RANGE = 20
TUPO_HUITIAO_MIN_GAP = 8
HUITIAO_STAT_RANGE = 2
HUITIAO_STAT_MAX_RANGE = 20

TUPO_THLD_PERCENT = 0.06
HUITIAO_THLD_PERCENT = 0.03
FANGLIANG_COE = 5.0
SUOLIANG_COE = 0.6
MIN_VOL_COE = 1.5

MAX_ZHANGFU = 0.1
MAX_DIEFU_UNDER_YEAR_LINE = 0.05
MIN_pctChg = 3.0
MAX_pctChg_MINUS = -15.0
CURRENT_PRICE_THLD = 0.1
MAX_LIANXU_MINUS = 4

LABLE_STAT_DAYS = 60
YIYI = 100000000
SHANGZHENG_CODE='sh.000001'
ZHONGXIAO_CODE='sz.399106'
CHUANGYE_CODE='sz.399006'

def reset_gloabl_var():
	for k, v in DEBUG_INFO.items():
		DEBUG_INFO[k] = 0

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

	if_nianxian_tiaozheng = False
	if_fangliangtupo = False
	if_suolianghuitiao = False
	if_final_ok = False

	pre_vol = 0.0
	tupo_vol = 0.0
	huitiao_vol = 0.0

	i = max(date_idx - YEAR_LINE_STAT_RANGE, 0)
	end = date_idx - TUPO_STAT_RANGE - TUPO_HUITIAO_MIN_GAP - HUITIAO_STAT_RANGE + 2
	while i <= end:
		if_nianxian_tiaozheng = False
		if_fangliangtupo = False
		if_suolianghuitiao = False
		
		pre_vol = 0.0
		tupo_vol = 0.0
		huitiao_vol = 0.0

		#s1:年线以下调整
		s1_end = i
		s2_begin = i
		for s1_i in range(i, end):
			# if date_list[s1_i] == '2020-07-24':
			# 	print("{}\t{}\t".format(close[s1_i], ma[s1_i]))
			if close[s1_i] >= ma[s1_i]:
				s1_end = s1_i
				break
		if (s1_end - i) >= TUPO_PRE_STAT_MIN:
			if IF_DEBUG:
				print("年线调整" + date_list[s1_end])
			if_nianxian_tiaozheng = True
			DEBUG_INFO['s1'] = DEBUG_INFO['s1'] + 1

		if if_nianxian_tiaozheng:
			#s2:放量突破
			for s2_i in range(s1_end, min(s1_end + TUPO_STAT_MAX_RANGE, date_idx)):
				#if date_list[s2_i] == '2020-08-03':
					#print((close[s2_i] - ma[s2_i]) / ma[s2_i])
				if (close[s2_i] - ma[s2_i]) / ma[s2_i] >= TUPO_THLD_PERCENT:
					if IF_DEBUG:
						print("突破" + date_list[s2_i])
					#放量
					pre_vol = np.mean([volume[j] for j in range(i, s1_end)])
					#print("{}\t{}\t{}".format(date_list[i], date_list[s1_end], pre_vol))

					tupo_vol = np.mean([volume[j] for j in range(s2_i, s2_i + TUPO_STAT_RANGE)])	
					#print("{}\t{}\t{}".format(date_list[s2_i], date_list[s2_i + TUPO_STAT_RANGE], tupo_vol))

					if pre_vol > 0.0 and tupo_vol / pre_vol > FANGLIANG_COE:
						if IF_DEBUG:
							print("放量" + date_list[s2_i])
						if_fangliangtupo = True
						DEBUG_INFO['s2'] = DEBUG_INFO['s2'] + 1
						s2_begin = s2_i
						s2_end = s2_i + TUPO_STAT_RANGE
						break

			#s3:缩量回调
			if if_fangliangtupo:
				#不能提前回调
				if_tiqianhuitiao = False
				for s3_i in range(s2_end, min(s2_end + TUPO_HUITIAO_MIN_GAP, date_idx)):
					if (close[s3_i] - ma[s3_i]) / ma[s3_i] <= HUITIAO_THLD_PERCENT:
						if_tiqianhuitiao = True
						DEBUG_INFO['sc1'] = DEBUG_INFO['sc1'] + 1
						break
				if not if_tiqianhuitiao:
					for s3_i in range(s2_end + TUPO_HUITIAO_MIN_GAP, min(s2_end + TUPO_HUITIAO_MIN_GAP + HUITIAO_STAT_MAX_RANGE, date_idx)):
					#DEBUG if date_list[i] == '2020-07-06':
						if (close[s3_i] - ma[s3_i]) / ma[s3_i] <= HUITIAO_THLD_PERCENT:
							if IF_DEBUG:
								print("回调" + date_list[s3_i])
							DEBUG_INFO['s3'] = DEBUG_INFO['s3'] + 1

							#放量
							huitiao_vol = np.mean([volume[j] for j in range(s3_i, min(date_idx, s3_i + HUITIAO_STAT_RANGE)) ])	
							#print(close[s3_i])
							#print(ma[s3_i])
							#print("回调{}\t{}\t{}".format(date_list[s3_i], date_list[date_idx], huitiao_vol))

							if huitiao_vol / tupo_vol <= SUOLIANG_COE and (date_idx - s3_i) <= 5:
								if IF_DEBUG:
									print("缩量" + date_list[s3_i])
								if_suolianghuitiao = True
								DEBUG_INFO['s4'] = DEBUG_INFO['s4'] + 1

						if if_suolianghuitiao:
							#附加条件限制:
							#c1:没有过大涨幅
							#c2:回调不太大
							#c3:震幅
							#c4:涨幅
							max_price = -1.0
							min_price = 1000000.0
							max_huitiao_percent = 0.0
							max_pctChg = -1.0
							max_pctChg_minus = 100000.0
							for c_i in range(s2_begin, date_idx + 1):
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

							if mkt_value < 500:
								if_c1_ok = False
								if_c2_ok = False
								if_c3_ok = False
								if_c4_ok = False
								if_c5_ok = False
								if_c6_ok = False
								#if (max_price - cur_price) / cur_price < MAX_ZHANGFU:
								if cur_vol / pre_vol > MIN_VOL_COE:
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
									print(if_nianxian_tiaozheng)
									print(if_fangliangtupo)
									print(if_suolianghuitiao)
									print(if_c1_ok)
									print(if_c2_ok)
									print(if_c3_ok)
									print(if_c4_ok)
									print(if_c5_ok)	
									print(if_c6_ok)	

								if_final_ok = if_nianxian_tiaozheng and if_fangliangtupo and if_suolianghuitiao \
									and if_c1_ok and if_c2_ok and if_c3_ok and if_c4_ok and if_c5_ok and if_c6_ok
								if if_final_ok:
									DEBUG_INFO['f'] = DEBUG_INFO['f'] + 1
									break		 

			if if_final_ok:
				break				
			#if if_fangliangtupo and if_suolianghuitiao:
				#break
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
		" WHERE date between '" + date_begin + "' and '" + date_end + "' and (amount<=0.0  or  amount/turn/100000000 <= 1200 or  code in ('sh.000001', 'sz.399106', 'sz.399006') ) " + \
		" order by code, date"
		#" and code in ('sh.601918','sh.603330','sh.600399','sh.600135','sh.603567','sh.600833','sh.600420','sh.600618','sh.600056','sh.600220','sz.002246','sz.002486','sz.002527','sh.600500','sz.002252','sz.002097','sz.300284','sh.601126','sh.600300','sz.000639','sh.600726','sz.000848', 'sh.000001', 'sz.399106', 'sz.399006') " + \

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

def ana_oneday(mode, *args):

	db = MySQLdb.connect("localhost", "root", "fwfw1231231", "astock", charset='utf8' )
	cursor = db.cursor()

	fetch_fields = 'date,name,code,open,high,low,close,preclose,volume,amount,turn,pctChg'.split(',')
	#
	code_name_dict = load_stock_code_name_mapping()

	date_begin = '2019-01-01'
	date_end = '2020-08-14'

	#basci dat
	stock_infos = select_dat(db, cursor, fetch_fields, date_begin, date_end)
	date_list = stock_infos[SHANGZHENG_CODE].date.tolist()

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

	db.close()

def ana_days(mode, *args):

	db = MySQLdb.connect("localhost", "root", "fwfw1231231", "astock", charset='utf8' )
	cursor = db.cursor()

	fetch_fields = 'date,name,code,open,high,low,close,preclose,volume,amount,turn,pctChg'.split(',')
	#
	code_name_dict = load_stock_code_name_mapping()

	date_begin = '2019-01-01'
	date_end = '2020-11-05'

	#basci dat
	stock_infos = select_dat(db, cursor, fetch_fields, date_begin, date_end)
	date_list = stock_infos[SHANGZHENG_CODE].date.tolist()


	#stat target
	stock_set = set()

	target_begin_date = '2020-09-08'
	target_begin_idx = date_list.index(target_begin_date)

	target_end_date = '2020-09-08'
	target_end_idx = date_list.index(target_end_date)

	for target_idx in range(target_begin_idx, target_end_idx + 1):
		stock_candidates, feas = recall_stocks(stock_infos, date_list, target_idx)
		cur_date = date_list[target_idx]
		#print(date_list[target_idx])
		#print(DEBUG_INFO)
		reset_gloabl_var()

		#generate sample
		if mode == 'train':
			labels = extract_label(stock_candidates, stock_infos, date_list, target_idx, LABLE_STAT_DAYS)
			for code in stock_candidates:
				if code not in stock_set:
					code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
					fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
					profit = str(labels[code]['profit'])
					print(cur_date + '\t' + code + '\t' + code_name + '\t' + profit + '\t' + fea_str)
				stock_set.add(code)

		#predict
		if mode == 'predict':	
			for code in stock_candidates:
				if code not in stock_set:
					code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
					#fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
					print(cur_date + '\t' + code + '\t' + code_name)
				stock_set.add(code)

		sys.stdout.flush()

	db.close()


def main():
	mode = sys.argv[1]
	ana_days(mode)

if __name__ == '__main__':
    main()
