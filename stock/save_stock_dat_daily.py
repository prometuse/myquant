import baostock as bs
import pandas as pd
import MySQLdb

def load_stock_index():
	stocks = dict()
	#with open('fetch_data/sh_stock_code_full.txt', 'r') as f:
	with open('../data/index_code.txt', 'r') as f:
		for line in f.readlines():
			name, code = line.strip().split('\t')
			stocks[code] = name
	return stocks

def pull_one_day(lg, code, begin_date, end_date, fields, stock_dict):
	'''
	params:lg, 拉数据api初始化
	'''
	code_str = code
	if not code.startswith('s'):
		code_str = "sh." + code
		if not code.startswith( '6' ):
			code_str = "sz." + code

	print(code_str)
	rs = bs.query_history_k_data_plus(code_str,
	    ','.join(fields),
	    start_date=begin_date, end_date=end_date,
	    frequency='d', adjustflag='2')
	print('query_history_k_data_plus respond error_code:'+rs.error_code)
	print('query_history_k_data_plus respond  error_msg:'+rs.error_msg)

	#### 打印结果集 ####
	data_list = []
	while (rs.error_code == '0') & rs.next():
	    dat = rs.get_row_data()
	    dat.append(stock_dict[code])
	    data_list.append(dat)

	return data_list

def save_dat_to_db(db, cursor, fields, dats):

	sql = "REPLACE INTO a_stock_market_price_day ( " + ','.join(fields) + ") VALUES ("
	for i in range(0, len(fields)):
		sql += "%s,"
	sql = sql[:-1] + ")"	

	values=[]
	for dat in dats:
		value = []
		for i in range(0, len(dat)):
			if dat[i] != '':
				value.append(dat[i])
			else:
				value.append('0')
		values.append(value)

	cursor.executemany(sql, values)
	db.commit()
	return 0

def pull_dats():
	stock_dict = load_stock_index()
	#mysql init
	db = MySQLdb.connect("localhost", "root", "fwfw1231231", "astock", charset='utf8' )
	cursor = db.cursor()
	# 显示登陆返回信息
	lg = bs.login()
	print('login respond error_code:'+lg.error_code)
	print('login respond  error_msg:'+lg.error_msg)

	fetch_fields = 'date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,psTTM,pcfNcfTTM,pbMRQ,isST'.split(',')
	mysql_fields = fetch_fields.copy()
	mysql_fields.append('name')

	for code, name in stock_dict.items():
		print('pull ' + name + ' dat begin')
		dat = pull_one_day(lg, code, '2020-12-26', '2021-01-05', fetch_fields, stock_dict)
		save_dat_to_db(db, cursor, mysql_fields, dat)
		print('pull ' + name + ' dat end')

	#### 登出系统 ####
	db.close()
	bs.logout()


def main():
	pull_dats()

if __name__ == '__main__':
    main()










