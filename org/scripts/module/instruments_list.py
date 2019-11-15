"""
Get instruments list
"""

import oandapyV20
import oandapyV20.endpoints.accounts as accounts
from module import account


def get():
    api = oandapyV20.API(access_token=account.get_token())
    ai = accounts.AccountInstruments(accountID=account.get_id())
    return api.request(ai)
