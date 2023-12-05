# -*- coding: utf-8 -*-
"""
Created on Wed Nov 15 21:19:12 2023

@author: prave
"""

# # integration with IB API

# # Created on Mon Nov 14, 2023 21:00 EST

# # @author: nlove


######## IMPORT PACKAGES ##############
import numpy as np
import pandas as pd
import os
import operator
import math
import datetime
from datetime import timedelta

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



authorizationCode = ''
discordChannel = ""


                                                      
######### discord piece of code ##############
# this is to retrieve messages from channel

def retrieve_messages():
    headers = {
        'authorization':authorizationCode
        }
    
    r = requests.get(discordChannel,headers = headers)
    
    jobj = json.loads(r.text)
    i = 0
    df = pd.DataFrame()
    for value in jobj:
        i += 1
        if i > 2:
            break
        # print('value is ',value)
        # print(value['content'],"\n")
        df = pd.concat([df,pd.DataFrame([value['content'],value['timestamp']]).transpose()])
        
    # https://discord.com/api/v9/channels/1127012008601075736/messages?limit=50
    return df
        
        
        
# define inputs
timeinterval = '5 mins'
interval_mins = 5

# ####### INPUTS FROM TRADINGVIEW SETTINGS #######
consec_runs = 5 #"Consecutive Runs"
fib_buy = 40 #"Fib Level to Buy (%)"
fib_SL = 0 #"Fib Level to Place Stop Loss (%)"
fib_TP = 100 #"Fib Level to Place Take Profit (%)"

class TradeApp(EWrapper, EClient):  # creating the tradeapp class with historicalData to be printed in dataframe
    def __init__(self): 
        EClient.__init__(self, self) 
        self.data = {}
        
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)
        
    ######### uncomment code below if you want to see the data downloaded (historic)
    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = pd.DataFrame([{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}])
        else:
            self.data[reqId] = pd.concat((self.data[reqId],pd.DataFrame([{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}])))
            #self.data[reqId].append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})
        # print("reqID:{}, date:{}, open:{}, high:{}, low:{}, close:{}, volume:{}".format(reqId,bar.date,bar.open,bar.high,bar.low,bar.close,bar.volume))

def usTechStk(symbol,expiry,sec_type="FUT",currency="USD",exchange="CME"):
    # ES is pulled from the CME exchange, not GLOBEX
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    contract.lastTradeDateOrContractMonth = expiry
    return contract 

def histData(req_num,contract,duration,candle_size):
    """extracts historical data"""
    app.reqHistoricalData(reqId=req_num, 
                          contract=contract,
                          endDateTime='',
                          durationStr=duration,
                          barSizeSetting=candle_size,
                          whatToShow='ADJUSTED_LAST',
                          useRTH=0,
                          formatDate=1,
                          keepUpToDate=0,
                          chartOptions=[]) # EClient function to request contract details
    
#creating object of the limit order class - will be used as a parameter for other function calls
def limitOrder(direction,quantity,lmt_price):
    order = Order()
    order.action = direction
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = lmt_price
    return order

def websocket_con():
    app.run()
    
#creating object of the Contract class - will be used as a parameter for other function calls
def placeTradeContract(symbol,sec_type="FUT",currency="USD",exchange="CME"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

###################storing trade app object in dataframe#######################
def dataDataframe(symbols,TradeApp_obj):
    "returns extracted historical data in dataframe format"
    df_data = {}
    for symbol in symbols:
        df_data[symbol] = pd.DataFrame(TradeApp_obj.data[symbols.index(symbol)])        
        df_data[symbol].set_index("Date",inplace=True)
        #if you need to change the timezone of the candles, uncomment below line and change the time zones accordingly
        #df_data[symbol].index = pd.to_datetime(df_data[symbol].index, format='%Y%m%d %H:%M:%S %Z')
        #df_data[symbol].index= pd.DatetimeIndex(df_data[symbol].index).tz_convert("America/Indiana/Petersburg")
    return df_data

#creating object of the bracket order class - will be used as a parameter for other function calls
def bktOrder(order_id,direction,quantity,lmt_price, sl_price, tp_price):
    """
    Parameters
    ----------
    order_id : Order ID value
    direction : Buy or Sell
    quantity : qty
    lmt_price : limit price
    sl_price : stop loss price
    tp_price : take profit price

    Returns
    -------
    bracket_order : bracket order

    """
    parent = Order()
    parent.orderId = order_id
    parent.action = direction
    parent.orderType = "LMT"
    parent.totalQuantity = quantity
    parent.lmtPrice = lmt_price
    parent.transmit = False
    parent.eTradeOnly = ''
    parent.firmQuoteOnly = ''
    parent.tif = "GTC"
    
    slOrder = Order()
    slOrder.orderId = parent.orderId + 1
    slOrder.action =  "SELL" if direction == "BUY" else "BUY"
    slOrder.orderType = "STP" 
    slOrder.totalQuantity = quantity
    slOrder.auxPrice = sl_price
    slOrder.parentId = order_id
    slOrder.transmit = False
    slOrder.eTradeOnly = ''
    slOrder.firmQuoteOnly = ''
    slOrder.tif = "GTC"
    
    tpOrder = Order()
    tpOrder.orderId = parent.orderId + 2
    tpOrder.action = "SELL" if direction == "BUY" else "BUY"
    tpOrder.orderType = "LMT"
    tpOrder.totalQuantity = quantity
    tpOrder.lmtPrice = tp_price
    tpOrder.parentId = order_id
    tpOrder.transmit = True
    tpOrder.eTradeOnly = ''
    tpOrder.firmQuoteOnly = ''
    tpOrder.tif = "GTC"
    
    bracket_order = [parent, slOrder, tpOrder]
    # sample code : bracket = bktOrder(app.nextValidOrderId,"BUY",10,85,75,95)
    return bracket_order

app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=4) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1) # some latency added to ensure that the connection is established

def round_nearest_qtr(number):
    base = 0.25
    return round(base * round(number/base),2)

tickers = ["ES"]
contract = Contract()
contract.symbol = "ES"
contract.secType = "FUT"
contract.exchange = "CME"
contract.currency = "USD"
contract.lastTradeDateOrContractMonth = "202312"  # Replace with your desired expiration date

app.reqIds(-1)
ordernum  = app.nextValidOrderId
prevmsg = ''
error_inc = 0
folder_time = datetime.now().strftime("%Y-%m-%d")


# timezone identification
newYorkTz = pytz.timezone("US/Eastern") #New_York
timeInNewYork = datetime.now(newYorkTz)
currentTimeInNewYork = timeInNewYork.strftime("%H:%M:%S")
systemTime = datetime.now()
systemTime - pd.to_datetime(currentTimeInNewYork)
UtcTz= pytz.timezone("UTC")
timeInUTC = datetime.now(UtcTz)
currentTimeinUTC = timeInUTC.strftime("%H:%M:%S")
deltaHours = 0
if (systemTime - pd.to_datetime(currentTimeinUTC)) < timedelta(minutes = 1):
    deltaHours = 0
elif (systemTime - pd.to_datetime(currentTimeInNewYork)) < timedelta(minutes = 1):
    deltaHours = 4 
elif (systemTime - pd.to_datetime(currentTimeInNewYork)) > timedelta(hours = 2, minutes = 59):
    deltaHours = 7
elif (systemTime - pd.to_datetime(currentTimeInNewYork)) > timedelta(hours = 1, minutes = 59):
    deltaHours = 6
elif (systemTime - pd.to_datetime(currentTimeInNewYork)) > timedelta(minutes = 59):
    deltaHours = 5 

while True:
    try:
        msg = retrieve_messages()
        crntmsg = msg.iloc[0][0] #initialzing previous message
        prevmsg = crntmsg
        print('initialMessage: \n')
        print(prevmsg)
        if len(prevmsg) > 1:
            break
        
    except:
        print('msg not found')
        time.sleep(1)
        pass

while True:
    # print(i)
    try: # running the whole code in try except loop to check for errors
        msg = retrieve_messages()
        print('current time: ',datetime.now())
        crntmsg = msg.iloc[0][0]
        crntmtime = msg.iloc[0][1]
        # print([crntmtime,datetime.now()])
        
        # print('message time: ',crntmtime)
        crntmtime = pd.to_datetime(crntmtime) - timedelta(hours = deltaHours)
        print(crntmsg)
        if str(crntmtime) > str(datetime.now() - timedelta(seconds = 5)):
            # it is a recent message
            
                
            if crntmsg!=prevmsg: 
                if 'Enter Long' in crntmsg:
                    # enter long trade - bracket order
                    # in current message: entry level, tp level, sl level
                    x22 = crntmsg.split("@")
                    buyval = float(x22[1])
                    buyval = round_nearest_qtr(buyval)
                    tplvl = float(x22[2])
                    tplvl = round_nearest_qtr(tplvl)
                    sllvl = float(x22[3])
                    sllvl = round_nearest_qtr(sllvl)
                    print([buyval,tplvl,sllvl])
                    # order_id = app.nextValidOrderId
                    order_id = ordernum
                    print('in enter long')
                    # bktOrder(order_id,direction,quantity,lmt_price, sl_price, tp_price)
                    bracket = bktOrder(order_id,"BUY",1,buyval,sllvl,tplvl)
                    for ordr in bracket:
                        app.placeOrder(ordr.orderId, contract, ordr)
                    
                    ordernum = ordernum+3
                    
                elif 'Exit Long' in crntmsg:
                    # exit : in bracket order have to cancel open limit orders
                    # order_id = app.nextValidOrderId - 1 ## check if this logic works
                    order_id = ordernum - 3
                    app.cancelOrder(order_id)
                    
                elif 'Enter Short' in crntmsg:
                    # enter short trade - bracket order
                    # in current message: entry level, tp level, sl level
                    x22 = crntmsg.split("@")
                    buyval = float(x22[1])
                    buyval = round_nearest_qtr(buyval)
                    tplvl = float(x22[2])
                    tplvl = round_nearest_qtr(tplvl)
                    sllvl = float(x22[3])
                    sllvl = round_nearest_qtr(sllvl)
                    print([buyval,tplvl,sllvl])
                    order_id = ordernum
                    # order_id = app.nextValidOrderId
                    print('in enter short')
                    
                    # bktOrder(order_id,direction,quantity,lmt_price, sl_price, tp_price)
                    bracket = bktOrder(order_id,"SELL",1,buyval,sllvl,tplvl)
                    for ordr in bracket:
                        app.placeOrder(ordr.orderId, contract, ordr)
                    ordernum = ordernum+3
                    
                elif 'Exit Short' in crntmsg:
                    # exit : in bracket order have to cancel open limit orders
                    # order_id = app.nextValidOrderId - 1 ## check if this logic works
                    order_id = ordernum - 3
                    app.cancelOrder(order_id)
                    
                
                    
            prevmsg = crntmsg
            
    except Exception as e:
         if error_inc < 3:
             errorFile = r"errorLog_" + folder_time+".txt"
             print(e)
             # error_message = traceback.format_exc()
             # error_payload = {'content': f"Error in script: {error_message}"}
             df3 = pd.DataFrame([e])
             if e != "string indices must be integers, not 'str'":
                 df3.to_csv(errorFile, header=None, index=None, sep=' ', mode='a')
             time.sleep(.25) # to give it a min and see if we can re run code.
         else:
             break
    
    
    time.sleep(1)

