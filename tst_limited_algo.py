
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

import sys

# print(authCode)
expiryValue = '202403'
# quantity value taken from the discord_cred_text file in line49

######### discord piece of code ##############
# this is to retrieve messages from channel
from discord import SyncWebhook

def send_discord_message(message):
    webhook.send(message)

cred_file = pd.read_csv('C:\\Users\\Administrator\\Downloads\\discord_cred_text.txt', header = None)
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
        'authorization':authorizationCode
        }
    
    r = requests.get(discordChannel,headers = headers)
    
    jobj = json.loads(r.text)
    i = 0
    df = pd.DataFrame()
    for value in jobj:
        # print(value) 
        i += 1
        if i > 2:
            break
        # print(value['content'],"\n")
        df = pd.concat([df,pd.DataFrame([value['content'],value['timestamp']]).transpose()])
        
    return df
        
        

def main():
        
    
    
    class TradeApp(EWrapper, EClient):  # creating the tradeapp class with historicalData to be printed in dataframe
        def __init__(self): 
            EClient.__init__(self, self) 
            self.acc_summary = pd.DataFrame(columns=['ReqId', 'Account', 'Tag', 'Value', 'Currency'])
            self.pnl_summary = pd.DataFrame(columns=['ReqId', 'DailyPnL', 'UnrealizedPnL', 'RealizedPnL'])
            self.order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId',
                                                  'Account', 'Symbol', 'SecType',
                                                  'Exchange', 'Action', 'OrderType',
                                                  'TotalQty', 'CashQty', 'LmtPrice',
                                                  'AuxPrice', 'Status'])
            self.pos_df = pd.DataFrame(columns=['Account', 'Symbol', 'SecType',
                                                'Currency', 'Position', 'Avg cost'])
    
        def accountSummary(self, reqId, account, tag, value, currency):
            super().accountSummary(reqId, account, tag, value, currency)
            dictionary = {"ReqId":reqId, "Account": account, "Tag": tag, "Value": value, "Currency": currency}
            # self.acc_summary = self.acc_summary.append(dictionary, ignore_index=True)
            d1 = pd.DataFrame([dictionary])
            d2 = pd.concat([self.acc_summary,d1])
            self.acc_summary = d2
            
        def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
            super().pnl(reqId, dailyPnL, unrealizedPnL, realizedPnL)
            dictionary = {"ReqId":reqId, "DailyPnL": dailyPnL, "UnrealizedPnL": unrealizedPnL, "RealizedPnL": realizedPnL}
            # self.pnl_summary = self.pnl_summary.append(dictionary, ignore_index=True)
            d1 = pd.DataFrame([dictionary])
            d2 = pd.concat([self.pnl_summary,d1])
            self.pnl_summary = d2
            
        def nextValidId(self, orderId):
            super().nextValidId(orderId)
            self.nextValidOrderId = orderId
            print("NextValidId:", orderId)
            
        def openOrder(self, orderId, contract, order, orderState):
            super().openOrder(orderId, contract, order, orderState)
            dictionary = {"PermId":order.permId, "ClientId": order.clientId, "OrderId": orderId, 
                          "Account": order.account, "Symbol": contract.symbol, "SecType": contract.secType,
                          "Exchange": contract.exchange, "Action": order.action, "OrderType": order.orderType,
                          "TotalQty": order.totalQuantity, "CashQty": order.cashQty, 
                          "LmtPrice": order.lmtPrice, "AuxPrice": order.auxPrice, "Status": orderState.status}
            # self.order_df = self.order_df.append(dictionary, ignore_index=True)
            d1 = pd.DataFrame([dictionary])
            d2 = pd.concat([self.order_df,d1])
            self.order_df = d2
            
        ######### uncomment code below if you want to see the data downloaded (historic)
        def historicalData(self, reqId, bar):
            if reqId not in self.data:
                self.data[reqId] = pd.DataFrame([{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}])
            else:
                self.data[reqId] = pd.concat((self.data[reqId],pd.DataFrame([{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}])))
                #self.data[reqId].append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})
            # print("reqID:{}, date:{}, open:{}, high:{}, low:{}, close:{}, volume:{}".format(reqId,bar.date,bar.open,bar.high,bar.low,bar.close,bar.volume))
            
        def position(self, account, contract, position, avgCost):
            super().position(account, contract, position, avgCost)
            dictionary = {"Account":account, "Symbol": contract.symbol, "SecType": contract.secType,
                          "Currency": contract.currency, "Position": position, "Avg cost": avgCost}
            # self.pos_df = self.pos_df.append(dictionary, ignore_index=True)
            d1 = pd.DataFrame([dictionary])
            d2 = pd.concat([self.pos_df,d1])
            self.pos_df = d2
    
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
                              chartOptions=[])	 # EClient function to request contract details
        
    #creating object of the limit order class - will be used as a parameter for other function calls
    def limitOrder(direction,quantity,lmt_price):
        order = Order()
        order.action = direction
        order.orderType = "LMT"
        order.totalQuantity = quantity
        order.lmtPrice = lmt_price
        order.tif = "GTC" 
        order.eTradeOnly = False 
        order.firmQuoteOnly = False 
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
    
    def marketOrder(direction,quantity):
        order = Order()
        order.action = direction
        order.orderType = "MKT"
        order.totalQuantity = quantity
        order.eTradeOnly = ''
        order.firmQuoteOnly = ''
        order.tif = 'GTC'
        order.outsideRth = True
        return order
    
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
        
        ordersummary = pd.DataFrame()
        
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
        parent.outsideRth = True
        tdf = pd.DataFrame([order_id,direction])
        ordersummary = pd.concat([ordersummary,tdf.transpose()])
        
        
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
        slOrder.outsideRth = True
        tdf = pd.DataFrame([parent.orderId + 1,slOrder.action])
        ordersummary = pd.concat([ordersummary,tdf.transpose()])
        
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
        tpOrder.outsideRth = True
        tdf = pd.DataFrame([parent.orderId + 2,tpOrder.action])
        ordersummary = pd.concat([ordersummary,tdf.transpose()])
        ordersummary.to_excel('ordersummary.xlsx')
        bracket_order = [parent, slOrder, tpOrder]
        # sample code : bracket = bktOrder(app.nextValidOrderId,"BUY",10,85,75,95)
        return bracket_order
    
    # app.placeOrder(order_id,usTechStk("FB"),marketOrder("BUY",1))
    
    clientId = 1
    
    app = TradeApp()
    app.connect(host='127.0.0.1', port=int(portNum), clientId=clientId) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
    con_thread = threading.Thread(target=websocket_con, daemon=True)
    con_thread.start()
    time.sleep(1) # some latency added to ensure that the connection is established
    
    def round_nearest_qtr(number):
        base = 0.25
        return round(base * round(number/base),2)
    
    tickers = ["ES"]
    contract = Contract()
    contract.symbol = contractName
    contract.secType = "FUT"
    contract.exchange = "CME"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = expiryValue  # Replace with your desired expiration date
    
    retryConnection = 0
    breakcode = 0 # to exit code if any issues are found and send discord message
    
    while True:
        if breakcode ==1 :
            send_discord_message('Please resolve issues and re run code, or it will next start automatically in an hour.')
            time.sleep(.5)
            break
        try:
            ordernum  = app.nextValidOrderId
            print('established connection..')
            send_discord_message("Connection established")
            break
        except Exception as e:
            print(e)
            retryConnection += 1
            clientId += 1
            del app
            del con_thread
            time.sleep(1)
            print('restarting TWS connection')
            app = TradeApp()
            app.connect(host='127.0.0.1', port=int(portNum), clientId=clientId) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
            con_thread = threading.Thread(target=websocket_con, daemon=True)
            con_thread.start()
            time.sleep(1) # some latency added to ensure that the connection is established
            app.reqIds(-1)
            try:
                ordernum  = app.nextValidOrderId
                print(ordernum)
                print('established connection..')
                send_discord_message("Connection established")
                time.sleep(.2)
                break
            except:
                print('retrial: ',retryConnection)
                if retryConnection > 10:
                    breakcode = 1
                    send_discord_message("Error with TWS Connection. Please check if account is logged in, or connect with our representatives.")
                    time.sleep(.5)
                    break
                pass
            # if retryConnection > 5:
            #     print('couldnt establish connection, please check manually')
            #     cstr = 'couldnt establish connection, please check manually'
            #     send_discord_message(cstr)
            #     time.sleep(.4)
            #     break
            
            
    prevmsg = ''
    error_inc = 0
    folder_time = datetime.now().strftime("%Y-%m-%d")
    
    
    # timezone identification
    newYorkTz = pytz.timezone("US/Eastern") #New_York
    UtcTz = pytz.timezone("UTC") #New_York
    timeInNewYork = datetime.now(newYorkTz)
    timeInUTC = datetime.now(UtcTz)
    utcHour = timeInUTC.hour
    currentTimeInNewYork = timeInNewYork.strftime("%H:%M:%S")
    currentTimeInUTC = timeInUTC.strftime("%H:%M:%S")
    systemTime = datetime.now()
    systemTime - pd.to_datetime(currentTimeInUTC)
    pd.to_datetime(currentTimeInUTC) - systemTime
    
    deltaHours = 0
    
    # order_id = app.nextValidOrderId
    # app.placeOrder(order_id, contract, marketOrder("BUY",1))
    
    if (systemTime - pd.to_datetime(currentTimeInUTC)) < timedelta(minutes = 1):
        deltaHours = 0 
    elif (systemTime - pd.to_datetime(currentTimeInNewYork)) < timedelta(minutes = 1):
        deltaHours = 4 
    elif (systemTime - pd.to_datetime(currentTimeInNewYork)) > timedelta(hours = 2, minutes = 59):
        deltaHours = 7
    elif (systemTime - pd.to_datetime(currentTimeInNewYork)) > timedelta(hours = 1, minutes = 59):
        deltaHours = 6
    elif (systemTime - pd.to_datetime(currentTimeInNewYork)) > timedelta(minutes = 59):
        deltaHours = 5 
    
        
    crntmsg = '1'
    prevmsg = '2'
    
    while crntmsg != prevmsg:
        try:
            msg = retrieve_messages()
            crntmsg = msg.iloc[0][0]
            prevmsg = crntmsg
            print(crntmsg)
            crnthour = timeInNewYork.hour
            prevhour = crnthour
            crntmin = timeInNewYork.minute
            prevmin = crntmin
            dttemp = datetime.now()
            if dttemp.minute < 29:
                exitTime = dttemp.replace(minute = 29, second = 58)
            else:
                exitTime = dttemp.replace(minute = 59, second = 58)#pd.to_datetime(currentTimeInNewYork) + timedelta(minutes = 59, seconds = 50)
            print('exitTime is ',exitTime)
        except:
            time.sleep(.5)
        
    print('exitTime is ',exitTime)
    # code to handle trades that are placed exactly during the code refresh time
    # check for edge of hourly messages missing trades
    headers = {
        'authorization':authorizationCode
        }

    df = pd.DataFrame()
    while len(df) == 0:
        try:
            r = requests.get(discordChannel,headers = headers)
            
            jobj = json.loads(r.text)
            i = 0
            
            # code for the edge case of hourly messages
            
            # first reading when previous code shutdown
            
            for value in jobj:
                i += 1
                print(value['content'],"\n")
                df = pd.concat([df,pd.DataFrame([value['content'],value['timestamp']]).transpose()]) # contains discord messages
                if i > 4:
                    break
        except:
            time.sleep(.5)
            
    df[1] = pd.to_datetime(df[1])
    # df[1] = df[1].apply(lambda x:str(x)[:19])
    customUTC = timeInUTC.replace(minute = 0,second = 0)
    dffilt = df[df[1]>=customUTC]
    
    print('dffilt is :')
    print(dffilt)
    if len(dffilt)>0:
        
        for i in range(0,len(dffilt)):
            # print(dffilt.iloc[i][0])
            if 'ES1' in dffilt.iloc[i][0]:
                print('in loop:',i)
                crntmsg = dffilt.iloc[i][0]
                print('ES1! trade found during transition!!')
                # place order
                print(crntmsg)
                
                
    ####################
    
    while datetime.now() < exitTime:
        # print(i)
        if breakcode == 1:
            break
        timeInNewYork = datetime.now(newYorkTz)
        try: # running the whole code in try except loop to check for errors
            msg = retrieve_messages()
            # print(datetime.now())
            crntmsg = msg.iloc[0][0]
            crntmtime = msg.iloc[0][1]
            # print([crntmtime,datetime.now()])
            prevhour = crnthour
            crnthour = timeInNewYork.hour
            
                
            prevmin = crntmin
            crntmin = timeInNewYork.minute
            
            crntmtime = pd.to_datetime(crntmtime) - timedelta(hours = deltaHours)
            # 
            if str(crntmtime) > str(datetime.now() - timedelta(seconds = 155)):
                # it is a recent message
                
                if crntmsg!=prevmsg: 
                    print(crntmsg)
                    if 'Enter Long' in crntmsg or 'Close entry(s) order Short' in crntmsg or 'vi enter long' in crntmsg:
                        # enter long trade - bracket order
                        # in current message: entry level, tp level, sl level
                        app.reqPositions()
                        time.sleep(.5)
                        pos_df = app.pos_df
                        pos_df.drop_duplicates(inplace=True,ignore_index=True)
                        crntLen = len(pos_df)
                        x22 = crntmsg.split("@")
                        lmt_price = round_nearest_qtr(float(x22[1]))
                        # order_id = app.nextValidOrderId
                        print('in enter long')
                        app.reqIds(-1)
                        time.sleep(1.5)
                        order_id = app.nextValidOrderId
                        print('in enter long')
                        # bktOrder(order_id,direction,quantity,lmt_price, sl_price, tp_price)
                        # placing market order instead of brackt order
                        
                        # enter long order
                        # app.placeOrder(order_id,contract,marketOrder("BUY",qty))
                        app.placeOrder(order_id,contract,limitOrder("BUY",qty,lmt_price))
                        time.sleep(2)
                        app.reqPositions()
                        time.sleep(1)
                        pos_df = app.pos_df
                        # pos_df.drop_duplicates(inplace=True,ignore_index=True)
                        postLen = len(pos_df)
                        
                        if postLen > crntLen:
                            send_discord_message("Order placed in TWS")
                        else:
                            send_discord_message('Order didnt go through!')
                        
                    elif 'Exit Long' in crntmsg:
                        # exit : in bracket order have to cancel open limit orders
                        # order_id = app.nextValidOrderId - 1 ## check if this logic works
                        order_id = ordernum - 3
                        app.cancelOrder(order_id)
                        
                    elif 'Enter Short' in crntmsg or 'Close entry(s) order Long' in crntmsg or 'vi enter short' in crntmsg:
                        # enter short trade - bracket order
                        # in current message: entry level, tp level, sl level
                        app.reqPositions()
                        time.sleep(.5)
                        pos_df = app.pos_df
                        pos_df.drop_duplicates(inplace=True,ignore_index=True)
                        crntLen = len(pos_df)
                        
                        x22 = crntmsg.split("@")
                        lmt_price = round_nearest_qtr(float(x22[1]))
                        app.reqIds(-1)
                        time.sleep(1.5)
                        order_id = app.nextValidOrderId
                        # order_id = app.nextValidOrderId
                        print('in enter short')
                        
                        # enter short order
                        # app.placeOrder(order_id,contract,marketOrder("SELL",qty))
                        app.placeOrder(order_id,contract,limitOrder("SELL",qty,lmt_price))
                        
                        time.sleep(2)
                        
                        app.reqPositions()
                        time.sleep(1)
                        pos_df = app.pos_df
                        # pos_df.drop_duplicates(inplace=True,ignore_index=True)
                        postLen = len(pos_df)
                        
                        if postLen > crntLen:
                            send_discord_message("Order placed in TWS")
                        else:
                            send_discord_message('Order didnt go through!')
                        
                    elif 'Exit Short' in crntmsg:
                        # exit : in bracket order have to cancel open limit orders
                        # order_id = app.nextValidOrderId - 1 ## check if this logic works
                        order_id = ordernum - 3
                        app.cancelOrder(order_id)
                        
                    elif 'report status' in crntmsg:
                        # this is to send details of how the bot is working
                        cstr = 'last TWS connection was at:'+str(app.twsConnectionTime())
                        send_discord_message(cstr)
                        
                        
                        
                    elif 'time left' in crntmsg:
                        timeleft = exitTime - datetime.now()
                        cstr = "code will end in "+str(timeleft.seconds)+ " seconds."
                        send_discord_message(cstr)
                        time.sleep(.1)
                        
                    elif 'close all orders' in crntmsg:
                        app.reqPositions()
                        time.sleep(1)
                        pos_df = app.pos_df
                        pos_df.drop_duplicates(inplace=True,ignore_index=True)
                        crntLen = len(pos_df)
                        time.sleep(1)
                        # got the current position above
                        # startIdx = len(pos_df) - 5 
                        # if startIdx < 0:
                        startIdx = 0
                        for pos in range(startIdx,len(pos_df)):
                            po = pos_df['Position'].iloc[pos]
                            ordType = ''
                            ordernum = app.nextValidOrderId
                            order_id = ordernum
                            posQty = 0
                            if po < 0:
                                ordType = 'BUY'
                                posQty = int(po * -1)
                            elif po > 0:
                                ordType = 'SELL'
                                posQty = int(po)
                                
                            if len(ordType)>1:
                                app.placeOrder(order_id, contract, marketOrder(ordType,posQty))
                                app.reqIds(-1)
                                time.sleep(1)
                        
                        app.reqPositions()
                        time.sleep(1)
                        pos_df = app.pos_df
                        # pos_df.drop_duplicates(inplace=True,ignore_index=True)
                        postLen = len(pos_df)
                        if postLen > crntLen:
                            
                            send_discord_message('closed all contracts..')
                        else:
                            send_discord_message('couldnt close the contracts! please check again!')
                            
                        time.sleep(.1)
                    elif 'cancel all open order' in crntmsg:
                        
                        # command to cancel all open orders
                        app.reqGlobalCancel()
                        
                        
                        # break
                    elif 'refresh connection' in crntmsg:
                        # providing code to refresh connection to TWS through Nic's discord bots
                        
                        try:
                            retryConnection += 1
                            clientId += 1
                            del app
                            del con_thread
                            time.sleep(.5)
                            print('restarting TWS connection')
                            app = TradeApp()
                            app.connect(host='127.0.0.1', port=int(portNum), clientId=clientId) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
                            con_thread = threading.Thread(target=websocket_con, daemon=True)
                            con_thread.start()
                            time.sleep(1) # some latency added to ensure that the connection is established
                            try:
                                ordernum  = app.nextValidOrderId
                                print(ordernum)
                                cstr = "TWS connection re established with Client ID: "+str(clientId)
                                send_discord_message(cstr)
                                # break
                                retryConnection= 0
                            except Exception as e:
                                print(e)
                                if retryConnection > 10:
                                    send_discord_message("TWS connection FAILED..")
                                    time.sleep(.5)
                                    break
                                pass
                        except Exception as e:
                            print(e)
                            
                            retryConnection += 1
                            if retryConnection > 12:
                                print('couldnt establish connection, please check manually')
                                time.sleep(.6)
                                print('message 2')
                                send_discord_message("ERROR in re establishing connection! Please check immediately!!!!!!!")
                                time.sleep(1)
                                breakcode = 1
                                break
                        
                    
                        
                prevmsg = crntmsg
            print('read @',datetime.now())
        except Exception as e:
             #print('type of error is ', type(e))
             df3 = pd.DataFrame([e])
             #print(df3)
             if 'positional indexer' in str(df3[0].iloc[0]):
                 print('in except refresh connection loop')
                 #refresh connection
                 while True:
                     try:
                         retryConnection += 1
                         clientId += 1
                         del app
                         del con_thread
                         time.sleep(.5)
                         print('restarting TWS connection')
                         app = TradeApp()
                         app.connect(host='127.0.0.1', port=int(portNum), clientId=clientId) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
                         con_thread = threading.Thread(target=websocket_con, daemon=True)
                         con_thread.start()
                         time.sleep(1) # some latency added to ensure that the connection is established
                         try:
                             ordernum  = app.nextValidOrderId
                             print(ordernum)
                             cstr = "TWS connection re established with Client ID: "+str(clientId)
                             send_discord_message(cstr)
                             # break
                             retryConnection= 0
                         except Exception as e:
                             print(df3)
                             if retryConnection > 10:
                                 send_discord_message("TWS connection FAILED..")
                                 breakcode = 1
                                 time.sleep(.5)
                                 break
                             pass
                     except Exception as e:
                         print(e)
                         
                         retryConnection += 1
                         if retryConnection > 12:
                             print('couldnt establish connection, please check manually')
                             time.sleep(.6)
                             print('message 2')
                             send_discord_message("ERROR in re establishing connection! Please check immediately!!!!!!!")
                             time.sleep(1)
                             breakcode = 1
                             break
                         
             elif "find order with id" in str(df3[0].iloc[0]):
                 print('in loop..')
                 ordernum  = app.nextValidOrderId
                 order_id = ordernum
                 app.placeOrder(order_id, contract, marketOrder(ordType,posQty))
                 send_discord_message('placed order after revising order number..')
                 time.sleep(.4)
                 
             elif "Order rejected - reason:Parent order is being cancelled." in str(df3[0].iloc[0]):
                 ordernum  = app.nextValidOrderId
                 order_id = ordernum
                 app.placeOrder(order_id, contract, marketOrder(ordType,posQty))
                 send_discord_message('placed order after revising order number..')
                 time.sleep(.4)
                 
             if error_inc < 3:
                 #errorFile = r"errorLog_" + folder_time+".txt"
                 #print(df3)
                 # error_message = traceback.format_exc()
                 # error_payload = {'content': f"Error in script: {error_message}"}
                 #df3 = pd.DataFrame([e])
                 #df3.to_csv(errorFile, header=None, index=None, sep=' ', mode='a')
                 time.sleep(1) # to give it a min and see if we can re run code.
             else:
                 break
        
        
    # time.sleep(1)
    print([crnthour,prevhour])
    print(exitTime)
    send_discord_message("Hourly program terminanted..")

if __name__ == '__main__':
    # send_discord_message('v5_4')
    main()
    newYorkTz = pytz.timezone("US/Eastern") #New_York
    UtcTz = pytz.timezone("UTC") #New_York
    timeInNewYork = datetime.now(newYorkTz)
    timeInUTC = datetime.now(UtcTz)
    currentTimeInNewYork = timeInNewYork.strftime("%H:%M:%S")
    currentTimeInUTC = timeInUTC.strftime("%H:%M:%S")
    
    
