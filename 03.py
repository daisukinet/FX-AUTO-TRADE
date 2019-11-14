# OandaAPIによる注文＆全決済 

# ライブラリインポート
import os
import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.positions as positions

# アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

#APIに接続
api = oandapyV20.API(access_token = access_token, environment = "practice")
 
#注文情報
#order_data = {"order":{
#				"instrument": "USD_JPY",
#				"units": "-10000",
#				"type": "MARKET"
#				}
#			}
 
#APIに対する注文書を作成
#o = orders.OrderCreate(accountID, data=order_data)
 
#注文要求
#api.request(o)

#決済したいポジションの情報
position_data = {"shortUnits": "ALL"}

#APIに対する注文書を作成
p = positions.PositionClose(accountID=accountID, data=position_data, instrument="USD_JPY")

#注文要求
api.request(p)
