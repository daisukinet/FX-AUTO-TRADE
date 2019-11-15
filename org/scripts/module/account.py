"""
Get account info from environment variable.
"""

import os


def get_id():
    return os.environ.get('OANDA_ID')


def get_token():
    return os.environ.get('OANDA_TOKEN')
