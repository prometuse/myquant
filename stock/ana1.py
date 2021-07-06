import MySQLdb
from stock.utils import *
import numpy as np

LABLE_STAT_DAYS = 2

def choose_stocks(dats, pre_date, date):
	stock_list = []
	if pre_date not in dats or date not in dats:
		return 0

	#TODO:剔除N连板	
	for code in dats[pre_date].keys():
		if code not in dats[date]:
			continue
		if if_zhangtings(dats[pre_date][code]['preclose'], dats[pre_date][code]['close'], dats[pre_date][code]['pctChg']):
			stock_list.append(code)

	return stock_list

def extract_feas(cur_date_idx, date_list, target_stock_codes, dats):
	
	# 大盘
	# 板块
	
	feas = {}
	fea_names = ['turn', '']
	for target_stock in target_stock_codes:
		today = date_list[cur_date_idx]
		# 个股
		# 换手率， 波动
		yesDay = date_list[cur_date_idx - 1]
		turn = (dats[today][target_stock]['turn'] + dats[yesDay][target_stock]['turn']) / 2
		if target_stock not in feas:
			feas[target_stock] = {}
		feas[target_stock]['turn'] = turn	
		# 前N天数据
		# 涨跌幅， 换手， 形态（是否均线上）
		for i in range(2, 2 + back_ward_days):
			tmp_date = date_list[cur_date_idx - i]


	return feas

def extract_label(cur_date_idx, date_list, target_stock_codes, dats):
	labels = {}

	for target_stock in target_stock_codes:
		tmp_list = []
		for i in range(cur_date_idx + 1, cur_date_idx + LABLE_STAT_DAYS + 1):
			tmp_list.append(dats[date_list[i]][target_stock]['pctChg'])

		#tmp_list = [dats[date_list[i]][target_stock]['pctChg'] for i in range(cur_date_idx + 1, cur_date_idx + label_stat_days) ]
		tmp_avg_profit = np.mean(tmp_list) 

		if target_stock not in labels:
			labels[target_stock] = {}
		labels[target_stock]['profit'] = tmp_avg_profit

		labels[target_stock]['open_profit'] = (dats[date_list[cur_date_idx + 1]][target_stock]['open'] - dats[date_list[cur_date_idx + 1]][target_stock]['preclose']) / dats[date_list[cur_date_idx + 1]][target_stock]['preclose'] * 100

	return labels


def eva_dats(labels, dats):
	#how to buy

	#profit by buy_time, sell_time

	return 0

def select_zhangting_dats(db, cursor, fields, date_begin, date_end):

	code_dict = {} #date -> code -> {code info}

	sql = "SELECT  " + ','.join(fields) + " FROM a_stock_market_price_day " \
		" WHERE pctChg>9.0 and (preclose * 1.1 - close ) < 0.01 and " + \
		" date between '" + date_begin + "' and '" + date_end + "'"

	try:
		cursor.execute(sql)
		results = cursor.fetchall()
		for row in results:
			date = row[0]
			if date not in code_dict:
				code_dict[date] = {}
			code = row[2]
			if code not in code_dict[date]:
				code_dict[date][code] = {}

			for i in range(0, len(fields)):
				code_dict[date][code][fields[i]] = row[i]
	except:
		print("Error: unable to fecth fetch_data")
	return code_dict

def select_dat_by_codes(db, cursor, codes, fields, date_begin, date_end):

	code_dict = {} #date -> code -> {code info}

	code_info = "','".join(codes)
	sql = "SELECT  " + ','.join(fields) + " FROM a_stock_market_price_day " \
		" WHERE code in ('" + code_info + "') and " \
		" date between '" + date_begin + "' and '" + date_end + "'"

	try:
		cursor.execute(sql)
		results = cursor.fetchall()
		for row in results:
			date = row[0]
			if date not in code_dict:
				code_dict[date] = {}
			code = row[2]
			if code not in code_dict[date]:
				code_dict[date][code] = {}

			for i in range(0, len(fields)):
				code_dict[date][code][fields[i]] = row[i]
	except:
		print("Error: unable to fecth fetch_data")
	return code_dict

def ana_zhangting():

	db = MySQLdb.connect("localhost", "root", "fwfw1231231", "astock", charset='utf8' )
	cursor = db.cursor()

	fetch_fields = 'date,name,code,open,high,low,close,preclose,volume,amount,turn,pctChg'.split(',')

	date_begin = '2020-06-01'
	date_end = '2020-06-19'

	#
	code_name_dict = load_stock_code_name_mapping()

	#index
	zhangting_stocks = select_zhangting_dats(db, cursor, fetch_fields, date_begin, date_end)
	
	date_list = list(zhangting_stocks.keys())
	date_list = sorted(date_list, key=str.lower)
	for i in range(1, len(date_list) - 3):
		#recall
		zhangting_stocks_2ds = choose_stocks(zhangting_stocks, date_list[i - 1], date_list[i])

		#feas
		feas = extract_feas(i, date_list, zhangting_stocks_2ds, zhangting_stocks)

		#label
		target_stock_infos = select_dat_by_codes(db, cursor, zhangting_stocks_2ds, fetch_fields, date_list[i + 1], date_list[i + LABLE_STAT_DAYS])
		labels = extract_label(i, date_list, zhangting_stocks_2ds, target_stock_infos)

		#assemble samples
		for code, code_info in labels.items():
			print("%s,%s,%s,%f,%f,%f" % (date_list[i], code, code_name_dict[code], feas[code]['turn'], code_info['profit'], code_info['open_profit']))

		#print(np.mean([code_info['profit'] for code, code_info in labels.items()]))

	db.close()

def main():
	ana_zhangting()

if __name__ == '__main__':
    main()
