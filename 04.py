# OandaAPIによる無限ループによるドル円取得

# ライブラリインポート
import os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles
import pandas as pd
import time   #追加

# アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

#APIに接続
api = oandapyV20.API(access_token = access_token, environment = "practice")
 
#取得したいデータ情報
r = InstrumentsCandles(instrument="USD_JPY",params={"granularity":"M1"})

last_time = 0 

while True:   #追加
    #APIへデータ要求
    api.request(r)
     
    #最後から2番目のローソク足を取り出す
    data = r.response["candles"][-2]
     
    #ローソク足から日時・始値・終値を取り出す
    close_time = pd.to_datetime(data["time"])       #日時
    open_price = data["mid"]["o"]                   #始値
    close_price = data["mid"]["c"]                  #終値
    
    if last_time != close_time:
        #データ出力
        print( "時間: " + str(close_time)
        		+ " 始値: " + (open_price)
        		+ " 終値: " + (close_price) )
        last_time = close_time
    time.sleep(10)   #追加
