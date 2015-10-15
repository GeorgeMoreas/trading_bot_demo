import httplib
import urllib
import json
import datetime
import time

from pylab import *
from datetime import datetime
from matplotlib.dates import  DateFormatter, WeekdayLocator, HourLocator, \
     DayLocator, MONDAY
from matplotlib.finance import candlestick,\
     plot_day_summary, candlestick2

import matplotlib.pyplot as plt
from matplotlib.finance import candlestick_ohlc

rest_sandbox = "api-sandbox.oanda.com"
rest_practice = "api-fxpractice.oanda.com"
rest_trade = "api-fxtrade.oanda.com"

stream_sandbox = "stream-sandbox.oanda.com"
stream_practice = "stream-fxpractice.oanda.com"
stream_trade = "stream-fxtrade.oanda.com"

access_token = 'a0fce8d9a47637254bdef08a4e059641-b03e0bd3095df91751f3fbb7592f2579'
account_id = '270129'
headers = {'Content-Type' : 'application/x-www-form-urlencoded', 'Authorization' : 'Bearer ' + access_token}
lastTrade = "buy"
shape = 'cD'
tradeSize = "30000"


## Parses a granularity like S10 or M15 into the corresponding number of seconds
## Does not take into account anything weird, leap years, DST, etc.
is_dst = time.daylight and time.localtime().tm_isdst > 0
utc_offset = (time.altzone if is_dst else time.timezone)
def getGranularitySeconds(granularity):
    if granularity[0] == 'S':
        return int(granularity[1:])
    elif granularity[0] == 'M' and len(granularity) > 1:
        return 60 * int(granularity[1:])
    elif granularity[0] == 'H':
        return 60 * 60 * int(granularity[1:])
    elif granularity[0] == 'D':
        return 60 * 60 * 24
    elif granularity[0] == 'W':
        return 60 * 60 * 24 * 7
    #Does not take into account actual month length
    elif granularity[0] == 'M':
        return 60 * 60 * 24 * 30


def account():
    conn = httplib.HTTPSConnection(rest_practice)
    conn.request("GET", "/v1/accounts/" + account_id, "", headers)
    conn_json = conn.getresponse().read()
    print conn_json
    return conn_json


def order(pair, units, buysell):
    now = datetime.datetime.now()
    expire = now + datetime.timedelta(days=1)
    expire = expire.isoformat('T') + "Z"
    conn = httplib.HTTPSConnection(rest_practice)
    params = urllib.urlencode({"instrument": pair,
                               "units" : units,
                               "type" : "market",
                               "side" : buysell
							   })
    url = ''.join(["/v1/accounts/", account_id, "/orders"])
    conn.request("POST", url, params, headers)
    conn_json = conn.getresponse().read()
    print conn_json
    return conn_json


def close():
    conn = httplib.HTTPSConnection(rest_practice)
    url = ''.join(["/v1/accounts/", account_id, "/positions"])
    conn.request("DELETE", url, "", headers)
    conn_json = conn.getresponse().read()
    print conn_json
    return conn_json


def price(pair='USD_JPY'):
    conn = httplib.HTTPSConnection(rest_practice)
    params = urllib.urlencode({"instrument": pair})
    url = ''.join(["/v1/prices"])
    conn.request("GET", url, params, headers)
    conn_json = conn.getresponse().read()
    print conn_json
    return conn_json


def positions():
    conn = httplib.HTTPSConnection(rest_practice)
    url = ''.join(["/v1/accounts/", account_id, "/positions"])
    conn.request("GET", url, "", headers)
    conn_json = conn.getresponse().read()
    print conn_json
    return conn_json

	
def get_candles(period, granularity, pair):
    conn = httplib.HTTPSConnection(rest_practice)
    params = urllib.urlencode({"instrument": pair,
                               "count": str(period + 1),
                               "granularity": str(granularity),
                               "candleFormat": "midpoint"})
    print params
    url = ''.join(["/v1/candles"])
    conn.request("GET", url, params, headers)
    conn_json = conn.getresponse().read()	
    print conn_json
    return conn_json

## Calculates the WMA over 'period' candles of size 'granularity' for pair 'pair'
def WMA(period=100, granularity='S5', pair='USD_JPY'):
    wma_total = []
    wma_period = []
    wma_denom = []
    wma = []
    candle_prices = []
    date_values = []
    date_labels = []
    candle_width = getGranularitySeconds(granularity)
    graph_padding = 0.1 #so the graph is not touching top and bottom of the plot area
    min_candle = 10000 #set extreme opposite min and max to establish true min and max
    max_candle = 0 

    print pair

    conn_json = get_candles(period, granularity, pair)
    resp = json.loads(conn_json)
    candles = resp['candles']
    candles_data = []
	
    for i in range(period):
        for j in range(i):
            wma_total[i] += candles[i - j]['highMid'] * (wma_period[i] - j)
        wma_denom[i] = (i * (i + 1)) / 2
        wma[i] = wma_total[i] / wma_denom[i]
        candles_data[i]['wma_' + str(i)] = wma[i]
		
    i = 0
    for candle in candles:
        candleTimeLabels = time.strptime(str(candle['time']),  '%Y-%m-%dT%H:%M:%S.%fZ')
        candleTimeValues = date2num(datetime.strptime(candle['time'], '%Y-%m-%dT%H:%M:%S.%fZ'))
        date_labels.append(str(candleTimeLabels[1]) + '-' +
                           str(candleTimeLabels[2]) + '-' +
                           str(candleTimeLabels[0]) + ' ' +
                           str(candleTimeLabels[3]) + ':' +
                           str(candleTimeLabels[4]) + ':' +
                           str(candleTimeLabels[5])
						   )
        date_values.append(candleTimeValues)
        candle_prices.append([candleTimeValues, candle['openMid'], candle['highMid'], candle['lowMid'], candle['closeMid']])
		
        candles_data[i]['date_label'] = date_labels[i]
        candles_data[i]['date_value'] = date_values[i]
        candles_data[i]['price'] = candles_prices[i]
		
    compare_wma(candles_data)
		
#        if candle['closeMid'] < min_candle:
#            min_candle = candle['lowMid']
#        if candle['closeMid'] > max_candle:
#            max_candle = candle['highMid']
		
#		i += 1
			
#    min_candle -= graph_padding
#    max_candle += graph_padding
	
#	wma_graph(date_values, date_labels, candle_prices, min_candle, max_candle, pair, candle_width)
	

		
def compare_wma(candles_data):
    pass

#add functionality to take in an array of wma periods, and compare them all
#against each other, with the following variables for AB testing:
# 1. distance between the direction changes (int, int) --> (int)
# 2. which direction did the change took place in (bool, bool) --> (bool)
# 3. number of direction changes within a time range (int, time) --> (int)
# 4. difference in WMA periods (int, int) --> int


def wma_graph(date_values, date_labels, candle_prices, min_candle, max_candle, pair, candle_width):
    plt.figure(1)
    plt.axis([min(date_values), max(date_values), min_candle, max_candle])
    plt.title('Bar Chart of ' + pair)
    ax = plt.subplot(212)
    plt.subplot(211)
    plt.plot_date(dates, candle_wma[0], 'm-')
    plt.plot_date(dates, candle_wma[1], 'g-')
    plt.xticks(np.arange(min(date_values), max(date_values), 0.1), date_labels, rotation='vertical')
    candlestick_ohlc(ax, candle_prices, candle_width / 1000, colorup='b', colordown='r')
    plt.legend()
    plt.show(block=False)
    plt.draw()

	
def trade():
    global lastTrade
    global shape

    seconds = 0

    profit = []
    upper = []
    lower = []

    top_offset = 20.0
    bottom_offset = -20.0
    top_unreal_pl = top_offset

    while True:
        resptext = account()
        data = json.loads(resptext)
        unreal_pl = data['unrealizedPl']

        profit.append(unreal_pl)
        upper.append(top_offset)
        lower.append(bottom_offset)

        seconds += 1
        plot_graph(seconds, unreal_pl, top_offset, bottom_offset, len(profit), shape)
        print unreal_pl

        if unreal_pl > top_unreal_pl:
            top_offset = 20.0 + unreal_pl
            bottom_offset = -20.0 + (unreal_pl * 2)
            top_unreal_pl = unreal_pl

        if unreal_pl > top_offset or unreal_pl < bottom_offset:
            if lastTrade == "buy":
                lastTrade = "sell"
                shape = 'bD'
            else:
                lastTrade = "buy"
                shape = 'cD'
            close()
            order("USD_JPY", tradeSize, lastTrade)
            account()

            top_offset = 5.0
            bottom_offset = -20.0
            top_unreal_pl = top_offset

        time.sleep(0.2)


def plot_graph(seconds, profit, upper, lower, length, shape):
    plt.plot(seconds, profit, shape, seconds, upper, 'g.', seconds, lower, 'r.', seconds, 0, 'm,')
    plt.ylabel('Unrealized P/L')
    plt.axis([-100 + length, length, -30, 50])
    plt.draw()
    plt.show(block=False)


def init():
    global lastTrade
    close()
    lastTrade = "buy"
    shape = 'cD'
    order("USD_JPY", tradeSize, lastTrade)
    trade()

