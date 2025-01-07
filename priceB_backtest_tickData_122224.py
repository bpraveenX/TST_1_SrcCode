LIVETRADE = 0 ## 1 is live trade enabled.
# import packages
import warnings
warnings.filterwarnings('ignore')

import streamlit as st 
import pandas as pd
import datetime 

import numpy as np

import plotly.graph_objects as go
totalSumm = pd.DataFrame() 

from kite_trade import *
from kiteconnect import KiteTicker
import csv 
import os 
import time 

import requests

import requests
import zipfile
import io
import pandas as pd

trialcode = 0 


SYMBOLDICT = {}
live_data = {}
Token_yet_to_subscribe = []

spacing_cl = st.sidebar.input_number('Spacing_CL', 20)
breakevenprice_cl = st.sidebar.input_number('Break Even Price_CL', 10)
entryDelta_cl = st.sidebar.input_number('Entry Delta_CL', 3)

spacing_bn = st.sidebar.input_number('Spacing_BN', 10)
breakevenprice_bn = st.sidebar.input_number('Break Even Price_BN', 10)
entryDelta_bn = st.sidebar.input_number('Entry Delta_BN', 2)

spacing_nft = st.sidebar.input_number('Spacing_NFT', 10)
breakevenprice_nft = st.sidebar.input_number('Break Even Price_NFT', 10) 
entryDelta_nft = st.sidebar.input_number('Entry Delta_NFT', 2)

submit = st.sidebar.button('Submit')
# File path for saving the tick data
csv_files = ['tick_data_cl.csv','tick_data_bn.csv', 'tick_data_nft.csv']

outdf = pd.DataFrame() 

if submit: 
    for csv_file in csv_files:
        # Create the CSV file and write the header if it doesn't exist
        if not os.path.exists(csv_file):
            with open(csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['instrument_token', 'last_price', 'high', 'low', 'open', 'close', 'change', 'exchange_timestamp'])


        ## read the csv file 
        df1 = pd.read_csv(csv_file)
        df1['exchange_timestamp'] = pd.to_datetime(df1['exchange_timestamp'])
        df1['date'] = df1['exchange_timestamp'].dt.date

        if csv_file == 'tick_data_cl.csv':
            spacing = 20
            breakEvenPrice = 10
            entryDelta = 3
        elif csv_file == 'tick_data_bn.csv':
            spacing = 10
            breakEvenPrice = 5
            entryDelta = 2
        elif csv_file == 'tick_data_nft.csv':
            spacing = 10
            breakEvenPrice = 5
            entryDelta = 2
        breakEvenDone = 0 #used to check if the break even adjustment is done
        openCalculated = 0 
        openValue = 0 

        enterLongLevel = 0 
        enterShortLevel = 0 
        currentTrade = '' # either Long or Short 
        takeProfitLevel = 0 
        stopLossLevel = 0 
        reEnterLevel = 0 

        enterLongPrice = 0 
        enterShortPrice = 0 

        dailyStopLoss = -530

        currentZone = 0 

        codeEnded = 0 

        summdf = pd.DataFrame()

        tick_data = {}
        tick_df = pd.DataFrame() 

        totalProfit = 0 

        indiatime = 0 

        qty = 0 
        incZone = 0 


        ####### backtest engine ###################
        for dt in df1['date'].unique():
            df = df1[df1['date'] == dt]
            x = 0 
            if dt > pd.to_datetime('2024-01-01').date():
                while x in range(-1,len(df)-1):
                    x = x + 1
                    tick = df.iloc[x].to_dict()
                    tick_data = tick
                    # print(tick)
                    # Extract values from the tick dictionary
                    instrument_token = tick['instrument_token']
                    last_price = tick['last_price']
                    high = tick['high']
                    low = tick['low']
                    open_price = tick['open']
                    close_price = tick['close']
                    change = tick.get('change', 0)  # Handle 'change' if missing
                    exchange_timestamp = tick['exchange_timestamp']

                    endday = False
                    # if indiatime == 0:
                    #     endday = exchange_timestamp.hour == 5 and exchange_timestamp.minute >= 50 
                    # else:
                    #     endday = exchange_timestamp.hour == 15 and exchange_timestamp.minute >= 20
                    if endday:
                        print('code ended')
                        codeEnded = 1
                        ## close existing positions 
                        if currentTrade == 'Long':
                            print('squaring off the long position')
                            currentTrade = ''
                            currentZone = 1
                            enterLongLevel = stopLossLevel + entryDelta
                            enterShortLevel = stopLossLevel - entryDelta
                            stopLossLevel = 0
                            if LIVETRADE == 1:
                                sellcode()
                            print('exit long Squared',last_price,'@ ',exchange_timestamp)
                            tdf = pd.DataFrame(['exitLongSquared',last_price,exchange_timestamp]).transpose()
                            summdf = pd.concat([summdf,tdf])
                            qty = 0 
                            incZone = 0
                            totalProfit = totalProfit + (last_price - enterLongPrice)

                            # summdf.to_excel('trades_092324_v2.xlsx')
                            
                        elif currentTrade == 'Short':
                            print('squaring off the short position')
                            currentTrade = ''
                            currentZone = 1
                            enterLongLevel = stopLossLevel + entryDelta
                            enterShortLevel = stopLossLevel - entryDelta
                            stopLossLevel = 0
                            if LIVETRADE == 1:
                                buycode()
                            print('exit short squared',last_price,'@ ',exchange_timestamp)
                            tdf = pd.DataFrame(['exitShortSquared',last_price,exchange_timestamp]).transpose()
                            summdf = pd.concat([summdf,tdf])
                            qty = 0
                            incZone = 0
                            totalProfit = totalProfit + (enterShortPrice - last_price)
                            # summdf.to_excel('trades_092324_v2.xlsx')

                    # with open(csv_file, mode='a', newline='') as file:
                    #     writer = csv.writer(file)
                    #     writer.writerow([instrument_token, last_price, high, low, open_price, close_price, change, exchange_timestamp])
                    # print([last_price,pd.to_datetime(tick['exchange_timestamp']).time()])
                    if openCalculated == 0:
                        # if pd.to_datetime(tick['exchange_timestamp']).time() >= pd.to_datetime('23:45:00').time():
                        openCalculated = 1
                        print('openCalculated',openCalculated)
                        if openValue == 0:
                            openValue = last_price
                            enterLongLevel = openValue + entryDelta + spacing 
                            enterShortLevel = openValue - entryDelta - spacing

                            tdf = pd.DataFrame(['openCalculated',openValue,exchange_timestamp]).transpose()
                            summdf = pd.concat([summdf,tdf])

                            # summdf.to_excel('trades_092324_v2.xlsx')

                    else: 
                        if currentTrade == '' and totalProfit > dailyStopLoss:
                            if last_price > enterLongLevel and codeEnded == 0:
                                # price condition met to go long 
                                currentTrade = "Long"
                                qty = 2
                                incZone = 0
                                stopLossLevel = enterLongLevel - spacing - entryDelta 
                                takeProfitLevel = enterLongLevel + spacing - entryDelta
                                enterLongPrice = last_price
                                if LIVETRADE == 1:
                                    buycode()
                                # print('enter long',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['enterLong',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])

                                # account_balance = float(breeze.get_funds()['Success']['unallocated_balance'])
                                # import math 
                                # qty = math.floor(account_balance/106000)
                                # msg = "Qty is "+str(qty)
                                # send_discord_message(msg)

                                summdf.to_excel('trades_092324_v2.xlsx')

                            elif last_price < enterShortLevel and codeEnded == 0:
                                # price condition met to go short
                                currentTrade = "Short"
                                qty = 2 
                                incZone = 0
                                stopLossLevel = enterShortLevel + spacing + entryDelta
                                takeProfitLevel = enterShortLevel - spacing + entryDelta
                                if LIVETRADE == 1:
                                    sellcode()
                                print('enter short',last_price,'@ ',exchange_timestamp)
                                
                                tdf = pd.DataFrame(['enterShort',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])
                                enterShortPrice = last_price

                                # account_balance = float(breeze.get_funds()['Success']['unallocated_balance'])
                                # import math 
                                # qty = math.floor(account_balance/106000)
                                # msg = "Qty is "+str(qty)
                                # send_discord_message(msg)
                                
                                # summdf.to_excel('trades_092324_v2.xlsx')

                        if currentTrade == 'Long' and totalProfit > dailyStopLoss:
                            if last_price < stopLossLevel:
                                currentTrade = ''
                                currentZone = 1
                                enterLongLevel = stopLossLevel + entryDelta
                                enterShortLevel = stopLossLevel - entryDelta
                                stopLossLevel = 0
                                if LIVETRADE == 1:
                                    sellcode()
                                print('exit long',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['exitLong',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])

                                qty = 0 
                                incZone = 0
                                totalProfit = totalProfit + (last_price - enterLongPrice)

                                # summdf.to_excel('trades_092324_v2.xlsx')
                                

                            elif last_price > takeProfitLevel:
                                # readjust stop loss 
                                stopLossLevel = stopLossLevel + spacing 
                                takeProfitLevel = takeProfitLevel + spacing 
                                incZone += 1
                                print('re adj long @',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['reAdjLong',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])

                                # summdf.to_excel('trades_092324_v2.xlsx')

                        if currentTrade == 'Short' and totalProfit > dailyStopLoss:
                            if last_price > stopLossLevel:
                                currentTrade = ''
                                currentZone = 1
                                enterLongLevel = stopLossLevel + entryDelta
                                enterShortLevel = stopLossLevel - entryDelta
                                stopLossLevel = 0
                                if LIVETRADE == 1:
                                    buycode()
                                print('exit short',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['exitShort',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])
                                qty = 0
                                incZone = 0
                                totalProfit = totalProfit + (enterShortPrice - last_price)
                                # summdf.to_excel('trades_092324_v2.xlsx')

                            elif last_price < takeProfitLevel:
                                # readjust stop loss
                                stopLossLevel = stopLossLevel - spacing
                                takeProfitLevel = takeProfitLevel - spacing
                                print('re adj short',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['reAdjShort',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])
                                incZone += 1
                                # summdf.to_excel('trades_092324_v2.xlsx')
            if currentTrade == 'Long':
                currentTrade = ''
                tdf = pd.DataFrame(['exitEnd',tick['close'],tick['exchange_timestamp']]).transpose()
                summdf = pd.concat([summdf,tdf])
            if currentTrade == 'Short':
                currentTrade = ''
                tdf = pd.DataFrame(['exitEnd',tick['close'],tick['exchange_timestamp']]).transpose()
                summdf = pd.concat([summdf,tdf])
                
        priceb_summ = summdf
        ######### end of backtest engine ################
        ## STRAEGY C ###############
        # breakeven logic
        ####### backtest engine ###################
        summdf = pd.DataFrame()
        for dt in df1['date'].unique():
            df = df1[df1['date'] == dt]
            x = 0 
            if dt > pd.to_datetime('2024-01-01').date():
                while x in range(-1,len(df)-1):
                    x = x + 1
                    tick = df.iloc[x].to_dict()
                    tick_data = tick
                    # print(tick)
                    # Extract values from the tick dictionary
                    instrument_token = tick['instrument_token']
                    last_price = tick['last_price']
                    high = tick['high']
                    low = tick['low']
                    open_price = tick['open']
                    close_price = tick['close']
                    change = tick.get('change', 0)  # Handle 'change' if missing
                    exchange_timestamp = tick['exchange_timestamp']

                    endday = False
                    # if indiatime == 0:
                    #     endday = exchange_timestamp.hour == 5 and exchange_timestamp.minute >= 50 
                    # else:
                    #     endday = exchange_timestamp.hour == 15 and exchange_timestamp.minute >= 20
                    if endday:
                        print('code ended')
                        codeEnded = 1
                        ## close existing positions 
                        if currentTrade == 'Long':
                            print('squaring off the long position')
                            currentTrade = ''
                            breakEvenDone = 0 
                            currentZone = 1
                            enterLongLevel = stopLossLevel + entryDelta
                            enterShortLevel = stopLossLevel - entryDelta

                            stopLossLevel = 0
                            if LIVETRADE == 1:
                                sellcode()
                            print('exit long Squared',last_price,'@ ',exchange_timestamp)
                            tdf = pd.DataFrame(['exitLongSquared',last_price,exchange_timestamp]).transpose()
                            summdf = pd.concat([summdf,tdf])
                            qty = 0 
                            incZone = 0
                            totalProfit = totalProfit + (last_price - enterLongPrice)

                            # summdf.to_excel('trades_092324_v2.xlsx')
                            
                        elif currentTrade == 'Short':
                            print('squaring off the short position')
                            currentTrade = ''
                            breakEvenDone = 0 
                            currentZone = 1
                            enterLongLevel = stopLossLevel + entryDelta
                            enterShortLevel = stopLossLevel - entryDelta
                            stopLossLevel = 0
                            if LIVETRADE == 1:
                                buycode()
                            print('exit short squared',last_price,'@ ',exchange_timestamp)
                            tdf = pd.DataFrame(['exitShortSquared',last_price,exchange_timestamp]).transpose()
                            summdf = pd.concat([summdf,tdf])
                            qty = 0
                            incZone = 0
                            totalProfit = totalProfit + (enterShortPrice - last_price)
                            # summdf.to_excel('trades_092324_v2.xlsx')

                    # with open(csv_file, mode='a', newline='') as file:
                    #     writer = csv.writer(file)
                    #     writer.writerow([instrument_token, last_price, high, low, open_price, close_price, change, exchange_timestamp])
                    # print([last_price,pd.to_datetime(tick['exchange_timestamp']).time()])
                    if openCalculated == 0:
                        # if pd.to_datetime(tick['exchange_timestamp']).time() >= pd.to_datetime('23:45:00').time():
                        openCalculated = 1
                        print('openCalculated',openCalculated)
                        if openValue == 0:
                            openValue = last_price
                            enterLongLevel = openValue + entryDelta + spacing 
                            enterShortLevel = openValue - entryDelta - spacing

                            tdf = pd.DataFrame(['openCalculated',openValue,exchange_timestamp]).transpose()
                            summdf = pd.concat([summdf,tdf])

                            # summdf.to_excel('trades_092324_v2.xlsx')

                    else: 
                        if currentTrade == 'Long' and breakEvenDone == 0:
                            if last_price > price_breakEven:
                                stopLossLevel = enterLongLevel
                                breakEvenDone = 1 
                        if currentTrade == 'Short' and breakEvenDone == 0:
                            if last_price < price_breakEven:
                                stopLossLevel = enterShortLevel
                                breakEvenDone = 1 
                        if currentTrade == '' and totalProfit > dailyStopLoss:
                            if last_price > enterLongLevel and codeEnded == 0:
                                # price condition met to go long 
                                currentTrade = "Long"
                                qty = 2
                                incZone = 0
                                stopLossLevel = enterLongLevel - spacing - entryDelta 
                                takeProfitLevel = enterLongLevel + spacing - entryDelta
                                breakEvenDone = 0 
                                price_breakEven = last_price + breakEvenPrice
                                enterLongPrice = last_price
                                if LIVETRADE == 1:
                                    buycode()
                                # print('enter long',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['enterLong',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])


                            elif last_price < enterShortLevel and codeEnded == 0:
                                # price condition met to go short
                                currentTrade = "Short"
                                qty = 2 
                                incZone = 0
                                stopLossLevel = enterShortLevel + spacing + entryDelta
                                takeProfitLevel = enterShortLevel - spacing + entryDelta
                                breakEvenDone = 0 
                                price_breakEven = last_price + breakEvenPrice
                                if LIVETRADE == 1:
                                    sellcode()
                                print('enter short',last_price,'@ ',exchange_timestamp)
                                
                                tdf = pd.DataFrame(['enterShort',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])
                                enterShortPrice = last_price

                                
                        if currentTrade == 'Long' and totalProfit > dailyStopLoss:
                            if last_price < stopLossLevel:
                                currentTrade = ''
                                currentZone = 1
                                breakEvenDone = 0 
                                enterLongLevel = stopLossLevel + entryDelta
                                enterShortLevel = stopLossLevel - entryDelta
                                stopLossLevel = 0
                                if LIVETRADE == 1:
                                    sellcode()
                                print('exit long',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['exitLong',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])

                                qty = 0 
                                incZone = 0
                                totalProfit = totalProfit + (last_price - enterLongPrice)

                                # summdf.to_excel('trades_092324_v2.xlsx')
                                

                            elif last_price > takeProfitLevel:
                                # readjust stop loss 
                                stopLossLevel = stopLossLevel + spacing 
                                takeProfitLevel = takeProfitLevel + spacing 
                                incZone += 1
                                print('re adj long @',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['reAdjLong',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])

                                # summdf.to_excel('trades_092324_v2.xlsx')

                        if currentTrade == 'Short' and totalProfit > dailyStopLoss:
                            if last_price > stopLossLevel:
                                currentTrade = ''
                                breakEvenDone = 0 
                                currentZone = 1
                                enterLongLevel = stopLossLevel + entryDelta
                                enterShortLevel = stopLossLevel - entryDelta
                                stopLossLevel = 0
                                if LIVETRADE == 1:
                                    buycode()
                                print('exit short',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['exitShort',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])
                                qty = 0
                                incZone = 0
                                totalProfit = totalProfit + (enterShortPrice - last_price)
                                # summdf.to_excel('trades_092324_v2.xlsx')

                            elif last_price < takeProfitLevel:
                                # readjust stop loss
                                stopLossLevel = stopLossLevel - spacing
                                takeProfitLevel = takeProfitLevel - spacing
                                print('re adj short',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['reAdjShort',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])
                                incZone += 1
                                # summdf.to_excel('trades_092324_v2.xlsx')
            if currentTrade == 'Long':
                currentTrade = ''
                tdf = pd.DataFrame(['exitEnd',tick['close'],tick['exchange_timestamp']]).transpose()
                summdf = pd.concat([summdf,tdf])
            if currentTrade == 'Short':
                currentTrade = ''
                tdf = pd.DataFrame(['exitEnd',tick['close'],tick['exchange_timestamp']]).transpose()
                summdf = pd.concat([summdf,tdf])
                
        price_c_df = summdf

        ## STRAEGY D ###############
        ####### backtest engine ###################
        summdf = pd.DataFrame()
        for dt in df1['date'].unique():
            df = df1[df1['date'] == dt]
            x = 0 
            if dt > pd.to_datetime('2024-01-01').date():
                while x in range(-1,len(df)-1):
                    x = x + 1
                    tick = df.iloc[x].to_dict()
                    tick_data = tick
                    # print(tick)
                    # Extract values from the tick dictionary
                    instrument_token = tick['instrument_token']
                    last_price = tick['last_price']
                    high = tick['high']
                    low = tick['low']
                    open_price = tick['open']
                    close_price = tick['close']
                    change = tick.get('change', 0)  # Handle 'change' if missing
                    exchange_timestamp = tick['exchange_timestamp']

                    endday = False
                    # if indiatime == 0:
                    #     endday = exchange_timestamp.hour == 5 and exchange_timestamp.minute >= 50 
                    # else:
                    #     endday = exchange_timestamp.hour == 15 and exchange_timestamp.minute >= 20
                    if endday:
                        print('code ended')
                        codeEnded = 1
                        ## close existing positions 
                        if currentTrade == 'Long':
                            print('squaring off the long position')
                            currentTrade = ''
                            breakEvenDone = 0 
                            currentZone = 1
                            enterLongLevel = stopLossLevel + entryDelta
                            enterShortLevel = stopLossLevel - entryDelta

                            stopLossLevel = 0
                            if LIVETRADE == 1:
                                sellcode()
                            print('exit long Squared',last_price,'@ ',exchange_timestamp)
                            tdf = pd.DataFrame(['exitLongSquared',last_price,exchange_timestamp]).transpose()
                            summdf = pd.concat([summdf,tdf])
                            qty = 0 
                            incZone = 0
                            totalProfit = totalProfit + (last_price - enterLongPrice)

                            # summdf.to_excel('trades_092324_v2.xlsx')
                            
                        elif currentTrade == 'Short':
                            print('squaring off the short position')
                            currentTrade = ''
                            breakEvenDone = 0 
                            currentZone = 1
                            enterLongLevel = stopLossLevel + entryDelta
                            enterShortLevel = stopLossLevel - entryDelta
                            stopLossLevel = 0
                            if LIVETRADE == 1:
                                buycode()
                            print('exit short squared',last_price,'@ ',exchange_timestamp)
                            tdf = pd.DataFrame(['exitShortSquared',last_price,exchange_timestamp]).transpose()
                            summdf = pd.concat([summdf,tdf])
                            qty = 0
                            incZone = 0
                            totalProfit = totalProfit + (enterShortPrice - last_price)
                            # summdf.to_excel('trades_092324_v2.xlsx')

                    # with open(csv_file, mode='a', newline='') as file:
                    #     writer = csv.writer(file)
                    #     writer.writerow([instrument_token, last_price, high, low, open_price, close_price, change, exchange_timestamp])
                    # print([last_price,pd.to_datetime(tick['exchange_timestamp']).time()])
                    if openCalculated == 0:
                        # if pd.to_datetime(tick['exchange_timestamp']).time() >= pd.to_datetime('23:45:00').time():
                        openCalculated = 1
                        print('openCalculated',openCalculated)
                        if openValue == 0:
                            openValue = last_price
                            enterLongLevel = openValue + entryDelta + spacing 
                            enterShortLevel = openValue - entryDelta - spacing

                            tdf = pd.DataFrame(['openCalculated',openValue,exchange_timestamp]).transpose()
                            summdf = pd.concat([summdf,tdf])

                            # summdf.to_excel('trades_092324_v2.xlsx')

                    else: 
                        if currentTrade == '' and totalProfit > dailyStopLoss:
                            if last_price > enterLongLevel and codeEnded == 0:
                                # price condition met to go long 
                                currentTrade = "Long"
                                qty = 2
                                incZone = 0
                                stopLossLevel = enterLongLevel - spacing - entryDelta 
                                takeProfitLevel = enterLongLevel + spacing - entryDelta
                                breakEvenDone = 0 
                                price_breakEven = last_price + breakEvenPrice
                                enterLongPrice = last_price
                                if LIVETRADE == 1:
                                    buycode()
                                # print('enter long',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['enterLong',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])


                            elif last_price < enterShortLevel and codeEnded == 0:
                                # price condition met to go short
                                currentTrade = "Short"
                                qty = 2 
                                incZone = 0
                                stopLossLevel = enterShortLevel + spacing + entryDelta
                                takeProfitLevel = enterShortLevel - spacing + entryDelta
                                breakEvenDone = 0 
                                price_breakEven = last_price + breakEvenPrice
                                if LIVETRADE == 1:
                                    sellcode()
                                print('enter short',last_price,'@ ',exchange_timestamp)
                                
                                tdf = pd.DataFrame(['enterShort',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])
                                enterShortPrice = last_price

                                
                        if currentTrade == 'Long' and totalProfit > dailyStopLoss:
                            if last_price < stopLossLevel:
                                currentTrade = ''
                                currentZone = 1
                                breakEvenDone = 0 
                                enterLongLevel = stopLossLevel + entryDelta
                                enterShortLevel = stopLossLevel - entryDelta
                                stopLossLevel = 0
                                if LIVETRADE == 1:
                                    sellcode()
                                print('exit long',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['exitLong',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])

                                qty = 0 
                                incZone = 0
                                totalProfit = totalProfit + (last_price - enterLongPrice)

                                # summdf.to_excel('trades_092324_v2.xlsx')
                                

                            elif last_price > takeProfitLevel:
                                # readjust stop loss 
                                stopLossLevel = stopLossLevel + spacing * 3 # to exit the trade
                                takeProfitLevel = takeProfitLevel + spacing 
                                incZone += 1
                                print('re adj long @',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['reAdjLong',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])

                                # summdf.to_excel('trades_092324_v2.xlsx')

                        if currentTrade == 'Short' and totalProfit > dailyStopLoss:
                            if last_price > stopLossLevel:
                                currentTrade = ''
                                breakEvenDone = 0 
                                currentZone = 1
                                enterLongLevel = stopLossLevel + entryDelta
                                enterShortLevel = stopLossLevel - entryDelta
                                stopLossLevel = 0
                                if LIVETRADE == 1:
                                    buycode()
                                print('exit short',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['exitShort',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])
                                qty = 0
                                incZone = 0
                                totalProfit = totalProfit + (enterShortPrice - last_price)
                                # summdf.to_excel('trades_092324_v2.xlsx')

                            elif last_price < takeProfitLevel:
                                # readjust stop loss
                                stopLossLevel = stopLossLevel - spacing * 3
                                takeProfitLevel = takeProfitLevel - spacing
                                print('re adj short',last_price,'@ ',exchange_timestamp)
                                tdf = pd.DataFrame(['reAdjShort',last_price,exchange_timestamp]).transpose()
                                summdf = pd.concat([summdf,tdf])
                                incZone += 1
                                # summdf.to_excel('trades_092324_v2.xlsx')
            if currentTrade == 'Long':
                currentTrade = ''
                tdf = pd.DataFrame(['exitEnd',tick['close'],tick['exchange_timestamp']]).transpose()
                summdf = pd.concat([summdf,tdf])
            if currentTrade == 'Short':
                currentTrade = ''
                tdf = pd.DataFrame(['exitEnd',tick['close'],tick['exchange_timestamp']]).transpose()
                summdf = pd.concat([summdf,tdf])
                
        price_d_df = summdf


        pbdf = pd.DataFrame()
        for i in range(0,len(priceb_summ)):
            if 'enter' in priceb_summ.iloc[i][0]:
                if 'Long' in priceb_summ.iloc[i][0]:
                    currentTrade = 'Long'
                if 'Short' in priceb_summ.iloc[i][0]:
                    currentTrade = 'Short'
                enterPrice = priceb_summ.iloc[i][1]
                enterTime = priceb_summ.iloc[i][2]
            if 'exit' in priceb_summ.iloc[i][0]:
                exitPrice = priceb_summ.iloc[i][1]
                exitTime = priceb_summ.iloc[i][2]
                tdf = pd.DataFrame([currentTrade,enterPrice,enterTime,exitPrice,exitTime]).transpose()
                tdf.columns = ['currentTrade','enterPrice','enterTime','exitPrice','exitTime']
                pbdf = pd.concat([pbdf,tdf])
        pbdf['Profit'] = 0 
        pbdf['Profit'][pbdf['currentTrade'] == 'Long'] = pbdf['exitPrice'][pbdf['currentTrade'] == 'Long'] - pbdf['enterPrice'][pbdf['currentTrade'] == 'Long']
        pbdf['Profit'][pbdf['currentTrade'] == 'Short'] = pbdf['enterPrice'][pbdf['currentTrade'] == 'Short'] - pbdf['exitPrice'][pbdf['currentTrade'] == 'Short']

        pcdf = pd.DataFrame()
        for i in range(0,len(price_c_df)):
            if 'enter' in price_c_df.iloc[i][0]:
                if 'Long' in price_c_df.iloc[i][0]:
                    currentTrade = 'Long'
                if 'Short' in price_c_df.iloc[i][0]:
                    currentTrade = 'Short'
                enterPrice = price_c_df.iloc[i][1]
                enterTime = price_c_df.iloc[i][2]
            if 'exit' in price_c_df.iloc[i][0]:
                exitPrice = price_c_df.iloc[i][1]
                exitTime = price_c_df.iloc[i][2]
                tdf = pd.DataFrame([currentTrade,enterPrice,enterTime,exitPrice,exitTime]).transpose()
                tdf.columns = ['currentTrade','enterPrice','enterTime','exitPrice','exitTime']
                pcdf = pd.concat([pcdf,tdf])
        pcdf['Profit'] = 0 
        pcdf['Profit'][pcdf['currentTrade'] == 'Long'] = pcdf['exitPrice'][pcdf['currentTrade'] == 'Long'] - pcdf['enterPrice'][pcdf['currentTrade'] == 'Long']
        pcdf['Profit'][pcdf['currentTrade'] == 'Short'] = pcdf['enterPrice'][pcdf['currentTrade'] == 'Short'] - pcdf['exitPrice'][pcdf['currentTrade'] == 'Short']


        pddf = pd.DataFrame()
        for i in range(0,len(price_d_df)):
            if 'enter' in price_d_df.iloc[i][0]:
                if 'Long' in price_d_df.iloc[i][0]:
                    currentTrade = 'Long'
                if 'Short' in price_d_df.iloc[i][0]:
                    currentTrade = 'Short'
                enterPrice = price_d_df.iloc[i][1]
                enterTime = price_d_df.iloc[i][2]
            if 'exit' in price_d_df.iloc[i][0]:
                exitPrice = price_d_df.iloc[i][1]
                exitTime = price_d_df.iloc[i][2]
                tdf = pd.DataFrame([currentTrade,enterPrice,enterTime,exitPrice,exitTime]).transpose()
                tdf.columns = ['currentTrade','enterPrice','enterTime','exitPrice','exitTime']
                pddf = pd.concat([pddf,tdf])
        pddf['Profit'] = 0 
        pddf['Profit'][pddf['currentTrade'] == 'Long'] = pddf['exitPrice'][pddf['currentTrade'] == 'Long'] - pddf['enterPrice'][pddf['currentTrade'] == 'Long']
        pddf['Profit'][pddf['currentTrade'] == 'Short'] = pddf['enterPrice'][pddf['currentTrade'] == 'Short'] - pddf['exitPrice'][pddf['currentTrade'] == 'Short']

        print('summary for ',csv_file)

        tdf = pd.DataFrame([pbdf['Profit'].sum(),pcdf['Profit'].sum(),pddf['Profit'].sum()]).T
        tdf.columns = ['priceB','priceC','priceD']

        tdf['Ticker'] = csv_file

        outdf = pd.concat([outdf,tdf])


    st.dataframe(outdf)
    