# 簡単な自動売買ロジック

# ライブラリインポート
import os
import oandapyV20
from oandapyV20.endpoints.instruments import InstrumentsCandles
import pandas as pd
import time  # 追加

# アカウント情報
accountID = os.environ.get('OANDA_ID')
access_token = os.environ.get('OANDA_TOKEN')

# ドル円データを取得する関数


def get_price(min):
    api = oandapyV20.API(access_token=access_token, environment="practice")
    r = InstrumentsCandles(instrument="USD_JPY", params={"granularity": min})
    api.request(r)

    data = r.response["candles"][-2]

    return {"close_time": pd.to_datetime(data["time"]),
            "open_price": float(data["mid"]["o"]),
            "high_price": float(data["mid"]["h"]),
            "low_price": float(data["mid"]["l"]),
            "close_price": float(data["mid"]["c"])}

# 取得データをAnaconda Promotに表示する関数


def print_price(data):
    print("時間: " + str(data["close_time"])
          + " 始値: " + str(data["open_price"])
          + " 終値: " + str(data["close_price"]))

# 陽線を判定する関数


def check_ascend(data):
    if data["close_price"] > data["open_price"]:
        return True


# ここからメイン処理
last_data = get_price("M1")
print_price(last_data)
flag = 0

while True:
    data = get_price("M1")

    if data["close_time"] != last_data["close_time"]:
        print_price(data)

        if flag == 0 and check_ascend(data):
            flag = 1

        elif flag == 1 and check_ascend(data):
            flag = 2

        elif flag == 2 and check_ascend(data):
            print("３本連続で陽線なので買い！")
            flag = 3

        elif flag == 3:
            if check_ascend(data):
                pass
            else:
                print("陰線が出たので決済！")
                flag = 0

        else:
            flag = 0

        last_data = data

    time.sleep(10)
