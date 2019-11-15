# ブレイクアウト手法を実装してバックテスト検証する

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
chart_sec = "H1"         # 1時間足
lot = 10000              # 1トレードの枚数
slippage = 0.003         # 手数料やスリッページ（0.3%）
term = 20                #過去ｎ日の設定


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


# ブレイクを判定する関数
def breakout( data,last_data):
	highest = max(i["high_price"] for i in last_data[-1 * term:])
	if data["high_price"] > highest:
		return {"side":"BUY","price":highest}
	
	lowest = min(i["low_price"] for i in last_data[-1 * term:])
	if data["low_price"] < lowest:
		return {"side":"SELL","price":lowest}
	
	return {"side" : None , "price":0}

# ブレイクを判定してエントリー注文を出す関数
def entry_signal( data,last_data,flag ):
	signal = breakout( data,last_data )
	if signal["side"] == "BUY":
		flag["records"]["log"].append("過去{0}足の最高値{1}円を、直近の高値が{2}円でブレイクしました\n".format(term,signal["price"],data["high_price"]))
		flag["records"]["log"].append(str(data["close_price"]) + "円で買いの指値注文を出します\n")

		# ここに買い注文のコードを入れる
		
		flag["order"]["exist"] = True
		flag["order"]["side"] = "BUY"
		flag["order"]["price"] = data["close_price"] * lot

	if signal["side"] == "SELL":
		flag["records"]["log"].append("過去{0}足の最安値{1}円を、直近の安値が{2}円でブレイクしました\n".format(term,signal["price"],data["low_price"]))
		flag["records"]["log"].append(str(data["close_price"]) + "円で売りの指値注文を出します\n")

		# ここに売り注文のコードを入れる
		
		flag["order"]["exist"] = True
		flag["order"]["side"] = "SELL"
		flag["order"]["price"] = data["close_price"] * lot

	return flag
		
# 手仕舞いのシグナルが出たら決済の成行注文を出す関数
def close_position( data,last_data,flag ):
	
	flag["position"]["count"] += 1
	signal = breakout( data,last_data )
	
	if flag["position"]["side"] == "BUY":
		if signal["side"] == "SELL":
			flag["records"]["log"].append("過去{0}足の最安値{1}円を、直近の安値が{2}円でブレイクしました\n".format(term,signal["price"],data["low_price"]))
			flag["records"]["log"].append(str(data["close_price"]) + "円あたりで成行注文を出してポジションを決済します\n")
			
			# 決済の成行注文コードを入れる
			
			records( flag,data )
			flag["position"]["exist"] = False
			flag["position"]["count"] = 0
			
	if flag["position"]["side"] == "SELL":
		if signal["side"] == "BUY":
			flag["records"]["log"].append("過去{0}足の最高値{1}円を、直近の高値が{2}円でブレイクしました\n".format(term,signal["price"],data["high_price"]))
			flag["records"]["log"].append(str(data["close_price"]) + "円あたりで成行注文を出してポジションを決済します\n")
			
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
	exit_price = data["close_price"] * lot
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
		flag["records"]["buy-holding-periods"].append( flag["position"]["count"] )
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
		flag["records"]["sell-holding-periods"].append( flag["position"]["count"] )
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
	print("平均保有期間  :  {}足分".format( round(np.average(flag["records"]["buy-holding-periods"]),1) ))
	
	print("--------------------------")
	print("売りエントリの成績")
	print("--------------------------")
	print("トレード回数  :  {}回".format(flag["records"]["sell-count"] ))
	print("勝率          :  {}％".format(round(flag["records"]["sell-winning"] / flag["records"]["sell-count"] * 100,1)))
	print("平均リターン  :  {}％".format(round(np.average(flag["records"]["sell-return"]),4)))
	print("総損益        :  {}円".format( np.sum(flag["records"]["sell-profit"]) ))
	print("平均保有期間  :  {}足分".format( round(np.average(flag["records"]["sell-holding-periods"]),1) ))
	
	print("--------------------------")
	print("総合の成績")
	print("--------------------------")
	print("総損益        :  {}円".format( np.sum(flag["records"]["sell-profit"]) + np.sum(flag["records"]["buy-profit"]) ))
	print("手数料合計    :  {}円".format( np.sum(flag["records"]["slippage"]) ))
	
	# ログファイルの出力
	file =  open("./{0}-log.txt".format(datetime.now().strftime("%Y-%m-%d-%H-%M")),'wt',encoding='utf-8')
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
		"price": 0,
		"count": 0
	},
	"records":{
		"buy-count": 0,
		"buy-winning" : 0,
		"buy-return":[],
		"buy-profit": [],
		"buy-holding-periods":[],
		
		"sell-count": 0,
		"sell-winning" : 0,
		"sell-return":[],
		"sell-profit":[],
		"sell-holding-periods":[],
		
		"slippage":[],
		"log":[]
	}
}

last_data = []
i = 0
while i < len(price):

	#ブレイクアウト判定に使う最低限ｎ期間分のローソク足をセット
	if len(last_data) < term:
		last_data.append(price[i])
		flag = log_price(price[i],flag)
		i += 1
		continue
		
	data = price[i]
	flag = log_price(data,flag)
	
	
	if flag["order"]["exist"]: # 未約定の注文がないかチェック
		flag = check_order( flag )
	elif flag["position"]["exist"]:
		flag = close_position( data,last_data,flag ) #ポジションがあれば決済条件を満たしていないかチェック
	else:
		flag = entry_signal( data,last_data,flag ) #ポジションが無い場合はエントリー条件を満たしているかチェック
	
	last_data.append( data )
	i += 1

backtest(flag)