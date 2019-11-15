# 自動売買BOTのバックテストを行い勝率・平均リターン・総利益を計算する

import os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles
import pandas as pd
import numpy as np
from datetime import datetime
import json

# アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

 
api = oandapyV20.API(access_token = access_token, environment = "practice")
 

# バックテスト用の初期設定値
chart_sec = "H1"           # 1時間足
lot = 10000                # 1トレードの枚数
slippage = 0.003          # 手数料やスリッページ（0.3%）


#ドル円データを取得する関数
def get_price(chart_sec):
	price = []
	r = InstrumentsCandles(instrument="USD_JPY",
							params={
								"granularity":chart_sec, 
								"count" : 5000
								})
	api.request(r)
	data = r.response["candles"]
	
	for j in range(len(data)):
		price.append({ "close_time" : pd.to_datetime(data[j]["time"]),
					"open_price" : float(data[j]["mid"]["o"]),
					"close_price" : float(data[j]["mid"]["c"]),
					"low_price" : float(data[j]["mid"]["l"]),
					"high_price" : float(data[j]["mid"]["h"])})
					
	print(price[0]["close_time"], price[-1]["close_time"])
	print(len(price))
	
	return price


# json形式のファイルから価格データを読み込む関数
def get_price_from_file(path):
	file = open(path,'r',encoding='utf-8')
	price = json.load(file)
	return price		

 
#取得データをAnaconda Promotに表示する関数		
def print_price( data ):
	print( "時間: " + str(data["close_time"])
				+ " 始値: " + str(data["open_price"])
				+ " 終値: " + str(data["close_price"]) )
				

# 時間と始値・終値をログに記録する関数
def log_price( data,flag ):
	log =  "時間： " + str(data["close_time"]) + " 始値： " + str(data["open_price"]) + " 終値： " + str(data["close_price"]) + "\n"
	flag["records"]["log"].append(log)
	return flag


# 買いシグナルが出たら指値で買い注文を出す関数
def buy_signal( data,last_data,flag ):
	if flag["buy_signal"] == 0 and check_candle( data,"BUY" ) and check_ascend( data ):
		flag["buy_signal"] = 1

	elif flag["buy_signal"] == 1 and check_candle( data,"BUY" ) and check_ascend( data ):
		flag["buy_signal"] = 2

	elif flag["buy_signal"] == 2 and check_candle( data,"BUY" ) and check_ascend( data ):
		log = "３本連続で陽線 なので" + str(data["close_price"]) + "円で買い注文を入れます\n"
		flag["records"]["log"].append(log)
		flag["buy_signal"] = 3
		
		# ここに買い注文コードを入れる

		flag["order"]["exist"] = True
		flag["order"]["side"] = "BUY"
		flag["order"]["price"] = data["close_price"] * lot
	
	else:
		flag["buy_signal"] = 0
	return flag
	

# 売りシグナルが出たら指値で売り注文を出す関数
def sell_signal( data,last_data,flag ):
	if flag["sell_signal"] == 0 and check_candle( data,"SELL" ) and check_descend( data ):
		flag["sell_signal"] = 1

	elif flag["sell_signal"] == 1 and check_candle( data,"SELL" ) and check_descend( data ):
		flag["sell_signal"] = 2

	elif flag["sell_signal"] == 2 and check_candle( data,"SELL" ) and check_descend( data ):
		log = "３本連続で陰線 なので" + str(data["close_price"]) + "円で売り注文を入れます\n"
		flag["records"]["log"].append(log)
		flag["sell_signal"] = 3
		
		# ここに売り注文コードを入れる

		flag["order"]["exist"] = True
		flag["order"]["side"] = "SELL"
		flag["order"]["price"] = data["close_price"] * lot
		
	else:
		flag["sell_signal"] = 0
	return flag
	
 
#フィルター処理する関数
def check_candle( data,side ):
	if side == "BUY":
		if (data["close_price"]/data["open_price"] - 1) * 100 > 0.001:
			return True
		
	if side == "SELL":
		if (data["open_price"]/data["close_price"] - 1) * 100 > 0.001:
			return True
			
			
#陽線を判定する関数			
def check_ascend( data ):
	if data["close_price"] > data["open_price"]:
		return True


#陰線を判定する関数			
def check_descend( data ):
	if data["close_price"] < data["open_price"]:
		return True
		

# 手仕舞いのシグナルが出たら決済の成行注文を出す関数
def close_position( data,last_data,flag ):
	
	if flag["position"]["side"] == "BUY":
		if data["close_price"] < last_data["close_price"]:
			log = "前回の終値を下回ったので" + str(data["close_price"]) + "円あたりで成行で決済します\n"
			flag["records"]["log"].append(log)
			
			# 決済の成行注文コードを入れる

			records( flag,data )
			flag["position"]["exist"] = False
			flag["position"]["count"] = 0
			
	if flag["position"]["side"] == "SELL":
		if data["close_price"] > last_data["close_price"]:
			log = "前回の終値を上回ったので" + str(data["close_price"]) + "円あたりで成行で決済します\n"
			flag["records"]["log"].append(log)
			
			# 決済の成行注文コードを入れる

			records( flag,data )
			flag["position"]["exist"] = False
			flag["position"]["count"] = 0
	return flag
	

# サーバーに出した注文が約定したかどうかチェックする関数
def check_order( flag ):
	
	# 注文状況を確認して通っていたら以下を実行
	# 一定時間で注文が通っていなければキャンセルする
	
	flag["order"]["exist"] = False
	flag["order"]["count"] = 0
	flag["position"]["exist"] = True
	flag["position"]["side"] = flag["order"]["side"]
	flag["position"]["price"] = flag["order"]["price"]
	
	return flag
	

# 各トレードのパフォーマンスを記録する関数
def records(flag,data):
	
	# 取引手数料等の計算
	entry_price = flag["position"]["price"]
	exit_price = round(data["close_price"] * lot)
	trade_cost = round( lot * slippage )
	
	log = "スリッページ・手数料として " + str(trade_cost) + "円を考慮します\n"
	flag["records"]["log"].append(log)
	flag["records"]["slippage"].append(trade_cost)
	
	# 値幅の計算
	buy_profit = exit_price - entry_price - trade_cost
	sell_profit = entry_price - exit_price - trade_cost
	
	# 利益が出てるかの計算
	if flag["position"]["side"] == "BUY":
		flag["records"]["buy-count"] += 1
		flag["records"]["buy-profit"].append( buy_profit )
		flag["records"]["buy-return"].append( round( buy_profit / entry_price * 100, 4 ))
		if buy_profit  > 0:
			flag["records"]["buy-winning"] += 1
			log = str(buy_profit) + "円の利益です\n"
			flag["records"]["log"].append(log)
		else:
			log = str(buy_profit) + "円の損失です\n"
			flag["records"]["log"].append(log)
	
	if flag["position"]["side"] == "SELL":
		flag["records"]["sell-count"] += 1
		flag["records"]["sell-profit"].append( sell_profit )
		flag["records"]["sell-return"].append( round( sell_profit / entry_price * 100, 4 ))
		if sell_profit > 0:
			flag["records"]["sell-winning"] += 1
			log = str(sell_profit) + "円の利益です\n"
			flag["records"]["log"].append(log)
		else:
			log = str(sell_profit) + "円の損失です\n"
			flag["records"]["log"].append(log)
	
	return flag
	

# バックテストの集計用の関数
def backtest(flag):
	
	buy_gross_profit = np.sum(flag["records"]["buy-profit"])
	sell_gross_profit = np.sum(flag["records"]["sell-profit"])
	
	print("バックテストの結果")
	print("--------------------------")
	print("買いエントリの成績")
	print("--------------------------")
	print("トレード回数  :  {}回".format(flag["records"]["buy-count"] ))
	print("勝率          :  {}％".format(round(flag["records"]["buy-winning"] / flag["records"]["buy-count"] * 100,1)))
	print("平均リターン  :  {}％".format(round(np.average(flag["records"]["buy-return"]),4)))
	print("総損益        :  {}円".format( np.sum(flag["records"]["buy-profit"]) ))
	
	print("--------------------------")
	print("売りエントリの成績")
	print("--------------------------")
	print("トレード回数  :  {}回".format(flag["records"]["sell-count"] ))
	print("勝率          :  {}％".format(round(flag["records"]["sell-winning"] / flag["records"]["sell-count"] * 100,1)))
	print("平均リターン  :  {}％".format(round(np.average(flag["records"]["sell-return"]),4)))
	print("総損益        :  {}円".format( np.sum(flag["records"]["sell-profit"]) ))
	
	print("--------------------------")
	print("総合の成績")
	print("--------------------------")
	print("総損益        :  {}円".format( np.sum(flag["records"]["sell-profit"]) + np.sum(flag["records"]["buy-profit"]) ))
	print("手数料合計    :  {}円".format( np.sum(flag["records"]["slippage"]) ))
	
	# ログファイルの出力
	file =  open("./{0}-log.txt".format(datetime.now().strftime("%Y-%m-%d-%H-%M")),'w',encoding='utf-8')
	file.writelines(flag["records"]["log"])


#ここからメイン処理

# 価格チャートを取得
price = get_price("H1")

print("--------------------------")
print("テスト期間：")
print("開始時点 : " + str(price[0]["close_time"]))
print("終了時点 : " + str(price[-1]["close_time"]))
print(str(len(price)) + "件のローソク足データで検証")
print("--------------------------")


last_data = price[0] # 初期値となる価格データをセット

 
flag = {
	"buy_signal":0,
	"sell_signal":0,
	"order":{
		"exist" : False,
		"side" : "",
		"price" : 0,
		"count" : 0
	},
	"position":{
		"exist" : False,
		"side" : "",
		"price": 0
	},
	"records":{
		"buy-count": 0,
		"buy-winning" : 0,
		"buy-return":[],
		"buy-profit": [],
		
		"sell-count": 0,
		"sell-winning" : 0,
		"sell-return":[],
		"sell-profit":[],
		
		"slippage":[],
		"log":[]
	}
}


i = 1
while i < len(price):
	if flag["order"]["exist"]: #　未約定の注文がないかチェック
		flag = check_order( flag )

	data = price[i]
	flag = log_price(data,flag) # 新しいローソク足の日時と始値・終値を記録
	
	if flag["position"]["exist"]: # ポジションがあれば、手仕舞い条件をチェック
		flag = close_position( data,last_data,flag )

	else:
		flag = buy_signal( data,last_data,flag ) # 買いエントリの条件をチェック
		flag = sell_signal( data,last_data,flag ) # 売りエントリの条件をチェック

	last_data = data
	i += 1

backtest(flag)