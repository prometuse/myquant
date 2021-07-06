#均线策略

import MySQLdb
from stock.ana_year_line import *

IF_DEBUG=False

ZHANGTING_DAY_NUM = 2
ZHANGTING_PREVIOUS_ANA_DAY_NUM = 10
ZHANGTING_LABEL_STAT_DAY_NUM = 1

LABLE_STAT_DAYS = 3
JUNXIAN_STAT_DAYS = [3,7]
TIAOZHENG_STAT_DAYS = [10,30]


def ana_junxian(dat, date_list, date_idx):
	"""站稳均线"""

	if dat.empty or len(dat) < len(date_list):
		return False, 0, {}
	feas = {}

	low = dat.low
	high = dat.high
	open = dat.open
	close = dat.close
	pctChg =dat.pctChg
	turn = dat.turn
	amt = dat.amount
	df_ma = pd.DataFrame(close)
	ma_5 = ta.MA(close,timeperiod=5,matype=0)

	if_junxian_ok = False
	junxian_min_stat_day = JUNXIAN_STAT_DAYS[0]
	junxian_max_stat_day = JUNXIAN_STAT_DAYS[1]
	junxian_stat_days = 0

	for j in range(date_idx - junxian_max_stat_day + 1, date_idx - junxian_min_stat_day + 2):
		sub_if_junxian_ok = True
		pctChg_buf = []
		low_ma_buf = []
		turn_buff = []
		close_low_diff_buf = []
		pre_turn = np.mean([turn[k] for k in range(j-5, j)])

		for i in range(j, date_idx + 1):
			junxian_stat_days = date_idx - j + 1
			low_diff = (low[i] - ma_5[i]) / low[i] * 100
			close_low_diff = (open[i] - low[i]) / low[i] * 100
			pctChg_buf.append(pctChg[i])
			low_ma_buf.append(abs(low_diff))
			turn_buff.append(turn[i])
			close_low_diff_buf.append(close_low_diff)

			if low_diff <= -2.0 or low_diff >= 3.0:
				sub_if_junxian_ok = False
				break
			if pctChg[i] >= 7.0:
				sub_if_junxian_ok = False
				break

		avg_pctChg = np.mean(pctChg_buf)
		avg_close_low_diff = np.mean(close_low_diff_buf)
		avg_turn =  np.mean(turn_buff)
		# if avg_pctChg <= 1.5 or avg_pctChg >= 4.0:
		# 	sub_if_junxian_ok = False
		avg_low_ma_diff = np.mean(low_ma_buf)
		# if avg_low_diff >= 2.0:
		# 	sub_if_junxian_ok = False
		if (close[date_idx] -  close[j] ) / close[j] < 0.05:
			sub_if_junxian_ok = False

		#放量
		if avg_turn < 1.0 or avg_turn / pre_turn < 1.5:
			sub_if_junxian_ok = False
		#下影线
		if avg_close_low_diff <= 1.5:
			sub_if_junxian_ok = False


		#feas
		feas['junxian_turn'] = avg_turn
		feas['junxian_low'] = avg_close_low_diff
		feas['junxian_pctChg'] = avg_pctChg
		feas['price'] = close[date_idx - junxian_min_stat_day + 1]
		feas['market_value'] = amt[date_idx - junxian_min_stat_day + 1] / turn[i] * 100 / 100000000

		if sub_if_junxian_ok:
			if_junxian_ok = True
			break

	return if_junxian_ok,junxian_stat_days,feas

def ana_adjust(dat, date_list, date_idx):

	if dat.empty or len(dat) < len(date_list):
		return False, {}

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
			if turn[i] > avg_turn:
				sub_if_adjust_ok = False
				break

			#跌幅
			if (close[i] - close[date_idx]) /  close[date_idx] < -0.05:
				sub_if_adjust_ok = False
				break

		feas['adjust_turn'] = np.mean(turn_buf)
		feas['adjust_bodong'] = np.mean(bodong_buf)

		# print(date_list[j])
		# print(date_list[date_idx])
		# print(sub_if_adjust_ok)

		if sub_if_adjust_ok:
			if_adjust_ok = True
			break

	return if_adjust_ok, feas

def ana_zhangting(dat, date_list, date_idx):
	"""连续涨停"""
	low = dat.low
	high = dat.high
	close = dat.close
	preclose = dat.preclose
	pctChg =dat.pctChg
	turn = dat.turn
	amt = dat.amount
	df_ma = pd.DataFrame(close)
	ma_5 = ta.MA(close,timeperiod=5,matype=0)


	if_zhangting_fit = True
	if_previous_fit = True

	#feas
	feas = {}
	turn_buff = []

	#召回条件
	#1.m-n个涨停板
	#2.n天内有m个，并且最后一天是涨停的
	for i in range(date_idx - ZHANGTING_DAY_NUM + 1, date_idx + 1):
		if not if_zhangtings(preclose[i], close[i], pctChg[i]):
			if_zhangting_fit = False
			break
		turn_buff.append(turn[i])
	if if_zhangting_fit:
		#前面x天内没有涨停。先不召回反包/双头龙
		for i in range(date_idx - ZHANGTING_DAY_NUM - ZHANGTING_PREVIOUS_ANA_DAY_NUM + 1, date_idx - ZHANGTING_DAY_NUM + 1):
			if if_zhangtings(preclose[i], close[i], pctChg[i]):
				if_previous_fit = False
				break		
		
		if if_previous_fit:
			#feas
			feas['junxian_turn'] = np.mean(turn_buff)
			feas['price'] = close[date_idx]
			feas['market_value'] = amt[date_idx] / turn[date_idx] * 100 / 100000000
			#大盘
			#行业

	if_final_fit = if_zhangting_fit and if_previous_fit

	return if_final_fit,feas

def box_zhendang():
	'''
	小范围内箱体震动
	'''
	return 0

def recall_stocks(dats, date_list, date_idx):
	stock_list = []
	types=['SMA','EMA','WMA','DEMA','TEMA','TRIMA','KAMA','MAMA','T3']
	feas = {}
	for code, dat in dats.items():
		if code in [SHANGZHENG_CODE, ZHONGXIAO_CODE, CHUANGYE_CODE]:
			continue

		if_junxian_ok = False
		if_adjust_ok = False
		if_zhangting = False

		#涨停
		#if_zhangting, zhangting_feas = ana_zhangting(dat, date_list, date_idx)

		#是否站稳均线
		if_junxian_ok, junxian_stat_days, junxian_feas = ana_junxian(dat, date_list, date_idx)

		#前期调整是否到位
		#if if_junxian_ok:
			#if_adjust_ok, adjust_feas = ana_adjust(dat, date_list, date_idx - junxian_stat_days)

        #大盘背离

		if if_junxian_ok:
		#if if_zhangting:
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
		for i in range(date_idx + 1, date_idx + stat_days + 1):
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
		" WHERE date between '" + date_begin + "' and '" + date_end + "'  and (amount/turn/100000000 <= 3000 or  code in ('sh.000001', 'sz.399106', 'sz.399006') ) and isST=0" + \
		" order by code, date"
		#" and code in ('sz.adjust_min_stat_day', 'sh.000001') " + \

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

def ana_oneday(mode, *args):

	db = MySQLdb.connect("localhost", "root", "fwfw1231231", "astock", charset='utf8' )
	cursor = db.cursor()

	fetch_fields = 'date,name,code,open,high,low,close,preclose,volume,amount,turn,pctChg'.split(',')
	#
	code_name_dict = load_stock_code_name_mapping()

	date_begin = '2020-08-01'
	date_end = '2020-09-30'

	#basci dat
	stock_infos = select_dat(db, cursor, fetch_fields, date_begin, date_end)
	date_list = stock_infos[SHANGZHENG_CODE].date.tolist()

	target_date = '2020-09-30'
	target_idx = date_list.index(target_date)
	stock_candidates, feas = recall_stocks(stock_infos, date_list, target_idx)

	#generate sample
	if mode == 'train':
		labels = extract_label(stock_candidates, stock_infos, date_list, target_idx, ZHANGTING_LABEL_STAT_DAY_NUM)
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

	date_begin = '2020-09-07'
	date_end = '2020-09-11'

	#basci dat
	stock_infos = select_dat(db, cursor, fetch_fields, date_begin, date_end)
	date_list = stock_infos['sh.000001'].date.tolist()


	for i in range(ZHANGTING_PREVIOUS_ANA_DAY_NUM + 1, len(date_list) - ZHANGTING_LABEL_STAT_DAY_NUM - 1):
		target_date = date_list[i]
		target_idx = i
		stock_candidates, feas = recall_stocks(stock_infos, date_list, target_idx)

		#generate sample
		#print('sample date: ' + target_date)
		if mode == 'train':
			labels = extract_label(stock_candidates, stock_infos, date_list, target_idx, ZHANGTING_LABEL_STAT_DAY_NUM)
			profit_buf = []
			for code in stock_candidates:
				code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
				fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
				profit_buf.append(labels[code]['profit'])
				profit = str(labels[code]['profit'])
			print(np.mean(profit_buf))

		#predict
		if mode == 'predict':	
			for code in stock_candidates:
				code_name = code_name_dict[code] if code in code_name_dict else 'no_name'
				#fea_str = '\t'.join([str(v[1]) for v in feas[code]]) if code in feas else ''
				print(target_date + '\t' + code + '\t' + code_name)

	db.close()


def main():
	mode = sys.argv[1]
	ana_oneday(mode)

if __name__ == '__main__':
    main()
