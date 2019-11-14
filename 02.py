# OandaAPIによるドル円取得からのデータ構造の扱い

# ライブラリインポート
import os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles
from pprint import pprint   # 追加

# アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

# APIに接続
api = oandapyV20.API(access_token=access_token, environment="practice")

# 取得したいデータ情報
r = InstrumentsCandles(instrument="USD_JPY", params={"granularity": "H1",
                                                     "count": 3  # 追加
                                                     })

# APIへデータ要求
api.request(r)

# 「data」変数に取得データを格納
data = r.response

high_price = data["candles"][0]["mid"]["h"] #追加
# データ出力
# print(data)
#pprint(data)  # 追加
print(high_price) #変更
