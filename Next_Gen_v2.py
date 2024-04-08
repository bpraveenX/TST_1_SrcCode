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

# ... (the rest of the code remains the same)

def main():
    # ... (the rest of the code remains the same)

    while datetime.now() < exitTime:
        if breakcode == 1:
            break
        timeInNewYork = datetime.now(newYorkTz)
        try:
            msg = retrieve_messages()
            crntmsg = msg.iloc[0][0]
            crntmtime = msg.iloc[0][1]
            prevhour = crnthour
            crnthour = timeInNewYork.hour

            prevmin = crntmin
            crntmin = timeInNewYork.minute

            crntmtime = pd.to_datetime(crntmtime) - timedelta(hours=deltaHours)

            if str(crntmtime) > str(datetime.now() - timedelta(seconds=155)):
                if crntmsg != prevmsg:
                    print(crntmsg)
                    if 'Enter Long' in crntmsg:
                        # Enter long trade
                        x22 = crntmsg.split("@")
                        lmt_price = round_nearest_qtr(float(x22[1]))
                        sl_price = round_nearest_qtr(float(x22[-1].split("SL")[-1]))
                        order_id = app.nextValidOrderId
                        app.placeOrder(order_id, contract, limitOrder("BUY", qty, lmt_price))
                        app.placeOrder(order_id + 1, contract, stopOrder("SELL", qty, sl_price, transmit=True))

                    elif 'Enter Short' in crntmsg:
                        # Enter short trade
                        x22 = crntmsg.split("@")
                        lmt_price = round_nearest_qtr(float(x22[1]))
                        sl_price = round_nearest_qtr(float(x22[-1].split("SL")[-1]))
                        order_id = app.nextValidOrderId
                        app.placeOrder(order_id, contract, limitOrder("SELL", qty, lmt_price))
                        app.placeOrder(order_id + 1, contract, stopOrder("BUY", qty, sl_price, transmit=True))

                    elif 'Exit Long TP' in crntmsg or 'Exit Long MA/SD SL' in crntmsg:
                        # Exit long trade (take profit or stop loss)
                        app.reqGlobalCancel()

                    elif 'Exit Short TP' in crntmsg or 'Exit Short MA/SD SL' in crntmsg:
                        # Exit short trade (take profit or stop loss)
                        app.reqGlobalCancel()

                prevmsg = crntmsg
            print('read @', datetime.now())
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
