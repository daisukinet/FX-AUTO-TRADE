# 自動売買BOTに例外処理を追加

import os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.orders as orders
import pandas as pd
import time   
 
# アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

 
api = oandapyV20.API(access_token = access_token, environment = "practice")
 
 
#ドル円データを取得する関数
def get_price(min):
	r = InstrumentsCandles(instrument="USD_JPY",params={"granularity":min})
	while True:
		try:
			api.request(r)
	
			data = r.response["candles"][-2]
	
			return { "close_time" : pd.to_datetime(data["time"]),
					"open_price" : float(data["mid"]["o"]),
					"high_price" : float(data["mid"]["h"]),
					"low_price" : float(data["mid"]["l"]),
					"close_price" : float(data["mid"]["c"]) }
		except:
			print("価格取得に失敗しました。１０秒後にリトライします")
			time.sleep(10)
 
# 価格データをAnaconda Promptに表示する関数
def print_price( data ):
	print( "時間: " + str(data["close_time"])
				+ " 始値: " + str(data["open_price"])
				+ " 終値: " + str(data["close_price"]) )
 
 
# 買いシグナル関数
def buy_signal( data,flag ):
	if flag["buy_signal"] == 0 and check_ascend(data) and check_candle(data,"BUY"):
		flag["buy_signal"] = 1
					
	elif flag["buy_signal"] == 1 and check_ascend(data) and check_candle(data,"BUY"):
		print("２本連続で陽線")
		flag["buy_signal"] = 2
		
	elif flag["buy_signal"] == 2 and check_ascend(data) and check_candle(data,"BUY"):
		print("３本連続陽線なので"+str(data["close_price"])+"で買い！")
		flag["buy_signal"] = 3
		
		order_data = {
 					 "order": {
 					   "instrument": "USD_JPY",
  					   "units": "+10000",
  					   "type": "MARKET",
  						}
					}
		o = orders.OrderCreate(accountID, data=order_data)
		
		try:
			api.request(o)
		
			flag["order"]["exist"] = True
			flag["order"]["side"] = "BUY"
				
		except:
			print("注文が失敗しました。")
			time.sleep(10)
 
	else:
		flag["buy_signal"] = 0
	return flag
	
 
# 売りシグナル関数
def sell_signal( data,flag ):
	if flag["sell_signal"] == 0 and check_descend(data) and check_candle(data,"SELL"):
		flag["sell_signal"] = 1
					
	elif flag["sell_signal"] == 1 and check_descend(data) and check_candle(data,"SELL"):
		print("２本連続で陰線")
		flag["sell_signal"] = 2
		
	elif flag["sell_signal"] == 2 and check_descend(data) and check_candle(data,"SELL"):
		print("３本連続陰線なので"+str(data["close_price"])+"で売り！")
		flag["sell_signal"] = 3
		
		order_data = {
 					 "order": {
 					   "instrument": "USD_JPY",
  					   "units": "-10000",
  					   "type": "MARKET",
  						}
					}
		
		o = orders.OrderCreate(accountID, data=order_data)
		
		try:
			api.request(o)
		
			flag["order"]["exist"] = True
			flag["order"]["side"] = "SELL"
			
		except:
			print("注文が失敗しました。")
			time.sleep(10)
 
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
			
			
# 陽線を判定する関数
def check_ascend( data ):
	if data["close_price"] > data["open_price"]:
		return True
		
		
# 陰線を判定する関数			
def check_descend( data ):
	if data["close_price"] < data["open_price"]:
		return True
		
		
# 手仕舞いのシグナルが出たら決済注文を出す関数
def close_position( data,last_data,flag ):
	if flag["position"]["side"] =="BUY":
		if data["close_price"] < last_data["close_price"]:
			print("前回終値を下回ったので" + str(data["close_price"]) + "で決済")
			
			position_data = {"longUnits": "ALL"}
			p = positions.PositionClose(accountID=accountID, data=position_data, instrument="USD_JPY")
			
			while True:
				try:
					api.request(p)
					flag["position"]["exist"] = False
					break
					
				except:
					print("注文が失敗しました。10秒後にリトライします")
					time.sleep(10)
		
	if flag["position"]["side"] =="SELL":
		if data["close_price"] > last_data["close_price"]:
			print("前回終値を上回ったので" + str(data["close_price"]) + "で決済")
			
			position_data = {"shortUnits": "ALL"}
			p = positions.PositionClose(accountID=accountID, data=position_data, instrument="USD_JPY")
			
			while True:
				try:
					api.request(p)
					flag["position"]["exist"] = False
					break
					
				except:
					print("注文が失敗しました。10秒後にリトライします")
					time.sleep(10)
	return flag
	
		
# 出した注文が約定しているか確認する関数
def check_order( flag ):
 
	p = positions.PositionDetails(accountID=accountID, instrument="USD_JPY")
	position_buy = api.request(p)["position"]["long"]["units"]
	position_sell = api.request(p)["position"]["short"]["units"]
		
	if  int(position_buy) > 0 or int(position_sell) < 0:
		print("注文が約定しました！")
		flag["order"]["exist"] = False
		flag["order"]["count"] = 0
		flag["position"]["exist"] = True
		flag["position"]["side"] = flag["order"]["side"]
	
	elif int(position_buy) == 0 and int(position_sell) == 0:
		print("まだ未約定の注文があります")
		flag["order"]["count"] += 1			
		if flag["order"]["count"] > 6:
			flag = cancel_order( orders,flag )
	return flag
 
 
# 注文をキャンセルする関数
def cancel_order( orders,flag ):
	c = orders.OrdersPending(accountID)
	
	while True:
		try:
			orderID = api.request(c)["orders"][0]["id"]
			break
		except:
			print("注文番号の取得に失敗しました。10秒後にリトライします")
			time.sleep(10)
			
	
	c = orders.OrderCancel(accountID=accountID, orderID=orderID)
	
	while True:
		try:
			api.request(c)
	
			print("約定していない注文をキャンセルしました")
			flag["order"]["count"] = 0
			flag["order"]["exist"] = False
			break
		
		except:
			print("注文に失敗しました。10秒後にリトライします")
			time.sleep(10)
	
	return flag
 
# ここからメイン処理
last_data = get_price("M1")
print_price( last_data )
 
 
flag = {
	"buy_signal":0,
	"sell_signal":0,
	"order":{
		"exist" : False,
		"side" : "",
		"count" : 0
	},
	"position":{
		"exist" : False,
		"side" : ""
	}
}
 
while True:
	if flag["order"]["exist"]:
		flag = check_order( flag )
		
	data = get_price("M1")
	if data["close_time"] != last_data["close_time"]:
		print_price( data )
		if flag["position"]["exist"]:
			flag = close_position( data,last_data,flag )
			
		else:
			flag = buy_signal( data,flag )
			flag = sell_signal( data,flag )
		
		last_data = data
			
	time.sleep(10)   
		