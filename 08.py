# 決済条件を改良して自動売買の精度を高める

# ライブラリインポート
import os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles
import pandas as pd
import time

# アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

api = oandapyV20.API(access_token = access_token, environment = "practice")
r = InstrumentsCandles(instrument="USD_JPY",params={"granularity":"M1"})
api.request(r)
 
#ドル円データを取得する関数
def get_price(min,i):
	data = r.response["candles"][i]
	
	return { "close_time" : pd.to_datetime(data["time"]),
			"open_price" : float(data["mid"]["o"]),
			"high_price" : float(data["mid"]["h"]),
			"low_price" : float(data["mid"]["l"]),
			"close_price" : float(data["mid"]["c"]) }
			
#取得データをAnaconda Promotに表示する関数		
def print_price( data ):
	print( "時間: " + str(data["close_time"])
				+ " 始値: " + str(data["open_price"])
				+ " 終値: " + str(data["close_price"]) )
				
#陽線かどうかとローソク足の上昇率を判定する関数			
def check_ascend( data ):
	if data["close_price"] > data["open_price"]:
		return True

#フィルター処理する関数
def check_candle( data ):
	if (data["close_price"]/data["open_price"] - 1) * 100 > 0.005:
		return True

# 買いシグナルが出たら買い注文を出す関数			
def buy_signal( data,flag ):
	if flag["buy_signal"] == 0 and check_ascend(data) and check_candle(data):
		flag["buy_signal"] = 1
			
	elif flag["buy_signal"] == 1 and check_ascend(data) and check_candle(data):
		print("２本連続で陽線")
		flag["buy_signal"] = 2
		
	elif flag["buy_signal"] == 2 and check_ascend(data) and check_candle(data):
		print("３本連続で陽線なので買い！")
		#ここに買い注文コードを入れる
		
		flag["buy_signal"] = 3
		flag["order"] = True

	else:
		flag["buy_signal"] = 0
	return flag



# 手仕舞いのシグナルが出たら決済注文を出す関数
def close_position( data,last_data,flag ):
	if data["close_price"] < last_data["close_price"]:
		print("前回の終値を下回ったので" + str(data["close_price"]) + "で決済")
		flag["position"] = False
	return flag
		

#出した注文が約定しているか確認する関数
def check_order( flag ):

	#一定時間で注文が通っていなければキャンセルする
	
	flag["order"] = False
	flag["position"] = True
	return flag


#ここからメイン処理
last_data = get_price("M1",0)
print_price( last_data )
 
flag = {
	"buy_signal":0,
	"position":False,
	"order":False
	}
i = 1

#全体のループ処理
while i < 500:
	if flag["order"]:
		flag = check_order( flag )
	
	data = get_price("M1",i)
	if data["close_time"] != last_data["close_time"]:
		print_price( data )
		
		if flag["position"]:
			flag = close_position( data,last_data,flag )
		else:
			flag = buy_signal( data,flag )

		
		last_data = data
		
		i += 1
		
	time.sleep(0.01)