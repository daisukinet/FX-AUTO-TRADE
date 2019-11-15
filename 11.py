# ドル円の１時間足の過去データを取得

import os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles
import pandas as pd
import time   
import json #これだけ先頭に追加で記述

# アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

api = oandapyV20.API(access_token = access_token, environment = "practice")
 
# データを取得する関数
def get_price(chart_sec):
	start = "2019-05-18T00:00:00.000000Z"
	end = "2019-10-18T00:00:00.000000Z"
	price = []
	r = InstrumentsCandles(instrument="USD_JPY",
							params={
								"granularity":chart_sec, 
								"from" : start,
								"to" : end
								})
	api.request(r)
	data = r.response["candles"]
	
	for j in range(len(data)):
		price.append({ "close_time" : data[j]["time"],
					"open_price" : float(data[j]["mid"]["o"]),
					"close_price" : float(data[j]["mid"]["c"]),
					"low_price" : float(data[j]["mid"]["l"]),
					"high_price" : float(data[j]["mid"]["h"])})
					
	print(price[0]["close_time"], price[-1]["close_time"])
	print(len(price))
	#ファイルに書き込む
	file = open("usd_jpy_data.json","w",encoding="utf-8")
	json.dump(price,file,indent=4)
	
	return price

get_price("H1")

#jsonファイルを読み込む関数
def get_price_from_file(path):
	file = open(path,"r",encoding="utf-8")
	price = json.load(file)
	return price
 
# ここからメイン
price = get_price_from_file("usd_jpy_data.json")
print(price)