
######## IMPORT PACKAGES ##############
import numpy as np
import pandas as pd
import os
import operator
import math
import datetime
from datetime import timedelta
 
exitTime = datetime.datetime.now() + timedelta(minutes=29, seconds=45)
import warnings
warnings.filterwarnings("ignore")

# import yfinance as yf
from datetime import datetime, timedelta
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.tag_value import TagValue
from ibapi.common import *
import pandas as pd
import threading
import time

import requests
import json

import pytz

import sys

# print(authCode)
expiryValue = '202406'

######### discord piece of code ##############
# this is to retrieve messages from channel
from discord import SyncWebhook

def send_discord_message(message):
    webhook.send(message)

cred_file = pd.read_csv('C:\Users\Administrator\Downloads\next_gen_v2_cred_text.txt', header=None)
webhook_link = cred_file.iloc[0][0].split('=')[1].strip()
discordChLink = cred_file.iloc[1][0].split('=')[1].strip()
authCode = cred_file.iloc[2][0].split('=')[1].strip()
portNum = cred_file.iloc[3][0].split('=')[1].strip()
qty = cred_file.iloc[4][0].split('=')[1].strip()
contractName = cred_file.iloc[5][0].split('=')[1].strip()

# TTB channel
webhook = SyncWebhook.from_url(webhook_link)
discordChannel = discordChLink
authorizationCode = authCode

def retrieve_messages():
    headers = {
        'authorization': authorizationCode
    }

    r = requests.get(discordChannel, headers=headers)

    jobj = json.loads(r.text)
    i = 0
    df = pd.DataFrame()
    for value in jobj:
        i += 1
        if i > 2:
            break
        df = pd.concat([df, pd.DataFrame([value['content'], value['timestamp']]).transpose()])

    return df

def main():
    class TradeApp(EWrapper, EClient):
        def __init__(self):
            EClient.__init__(self, self)
            self.nextValidOrderId = None  
            self.acc_summary = pd.DataFrame(columns=['ReqId', 'Account', 'Tag', 'Value', 'Currency'])
            self.pnl_summary = pd.DataFrame(columns=['ReqId', 'DailyPnL', 'UnrealizedPnL', 'RealizedPnL'])
            self.order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId',
                                                  'Account', 'Symbol', 'SecType',
                                                  'Exchange', 'Action', 'OrderType',
                                                  'TotalQty', 'CashQty', 'LmtPrice',
                                                  'AuxPrice', 'Status'])
            self.pos_df = pd.DataFrame(columns=['Account', 'Symbol', 'SecType',
                                                'Currency', 'Position', 'Avg cost'])

        # Implementing additional methods for TradeApp...
        
        # Overriding the position method to handle the specific command changes

    def websocket_con():
        app.run()

    app = TradeApp()
    app.connect(host='127.0.0.1', port=int(portNum), clientId=1)
    con_thread = threading.Thread(target=websocket_con, daemon=True)
    con_thread.start()
    time.sleep(1)

    while datetime.now() < exitTime:
        msg = retrieve_messages()
        crntmsg = msg.iloc[0][0]
        if 'Enter Long' in crntmsg or 'Close entry(s) order Short' in crntmsg or 'vi enter long' in crntmsg:
            handle_entry_command(crntmsg)
        elif 'Exit Long' in crntmsg:
            handle_exit_command(crntmsg)
        elif 'Enter Short' in crntmsg or 'Close entry(s) order Long' in crntmsg or 'vi enter short' in crntmsg:
            handle_entry_command(crntmsg)
        elif 'Exit Short' in crntmsg:
            handle_exit_command(crntmsg)
        # Further command handling...

if __name__ == '__main__':
    main()
