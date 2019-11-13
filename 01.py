#ライブラリインポート
import os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles

#アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

#APIに接続
api = oandapyV20.API(access_token = access_token, environment = "practice")

#取得したいデータ情報
r = InstrumentsCandles(instrument="USD_JPY",params={"granularity":"H1"})

#APIへデータ要求
api.request(r)

#「data」変数に取得データを格納
data = r.response

#データ出力
print(data)
