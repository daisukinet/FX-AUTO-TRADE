# ドル円取得と表示の関数化

# ライブラリインポート
import os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles
import pandas as pd
import time   #追加

# アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

#APIから〇分足のデータを取得する関数
def get_price(min):
    api = oandapyV20.API(access_token = access_token, environment = "practice")
    r = InstrumentsCandles(instrument="USD_JPY",params={"granularity":min})
    api.request(r)
                    
    data = r.response["candles"][-2]
                            
    close_time = pd.to_datetime(data["time"])
    open_price = data["mid"]["o"]
    close_price = data["mid"]["c"]
                                            
    return close_time, open_price, close_price
                                             
#日時・始値・終値を表示する関数
def print_price( close_time, open_price, close_price ):
    print( "時間: " + str(close_time) + " 始値: " + open_price + " 終値: " + close_price )
                                                     
                                                    #ここからメイン処理
last_time = 0
while True:
    #get_price()関数を使い最新のドル円データから日時・始値・終値を取得する
    close_time, open_price, close_price = get_price("M1")
                                        
    if last_time != close_time:
        #print_price()関数を使い価格データを表示する
        print_price( close_time, open_price, close_price )
                                                                                                    
        last_time = close_time
                                                                                                                        
    time.sleep(10)  
