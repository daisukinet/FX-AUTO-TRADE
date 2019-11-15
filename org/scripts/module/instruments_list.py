"""
Get instruments list
"""

import oandapyV20
import oandapyV20.endpoints.accounts as accounts
from module import account


def get():
    client = oandapyV20.API(access_token=account.get_token())
    r = accounts.AccountInstruments(accountID=account.get_id())
    return client.request(r)
