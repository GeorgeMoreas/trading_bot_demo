import httplib
import urllib
import json
import time
import threading

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


def order(pair='USD_JPY', units='1000', buysell='buy'):
    now = datetime.now()
#    expire = now + datetime.timedelta(days=1)
#    expire = expire.isoformat('T') + "Z"
    conn = httplib.HTTPSConnection(rest_practice)
    params = urllib.urlencode({"instrument": pair,
                               "units": units,
                               "type": "market",
                               "side": buysell
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
    url = ''.join(["/v1/prices?instruments=", pair])
    conn.request("GET", url, "", headers)
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
    url = ''.join(["/v1/candles?instrument=", pair, "&count=", str(period), \
          "&granularity=", str(granularity), "&candleFormat=midpoint"])
    conn.request("GET", url, "", headers)
    conn_json = conn.getresponse().read()
#    print conn_json
    return conn_json


def w(period=30, gran='S5', pair='USD_JPY', wma_period_max=10):
    t = threading.Timer(5.0, w)
    t.daemon = True
    t.start()

    conn_json = get_candles(period, gran, pair)
    resp = json.loads(conn_json)
    candles = resp['candles']
    candles_data = []

    keys = ['date_label', 'date_value', 'price', 'wma']

    i = 0
    for candle in candles:
        candle_time_labels = time.strptime(str(candle['time']),  '%Y-%m-%dT%H:%M:%S.%fZ')
        candle_date_values = date2num(datetime.strptime(candle['time'], '%Y-%m-%dT%H:%M:%S.%fZ'))
        candle_date_labels = (str(candle_time_labels[1]) + '-' +
                           str(candle_time_labels[2]) + '-' +
                           str(candle_time_labels[0]) + ' ' +
                           str(candle_time_labels[3]) + ':' +
                           str(candle_time_labels[4]) + ':' +
                           str(candle_time_labels[5]))
        candle_prices = [candle_date_values, candle['openMid'], candle['highMid'], candle['lowMid'], candle['closeMid']]

        candle_wma = []

        if i > wma_period_max - 1:
            for wma_period in range(2, wma_period_max):
                wma_total = 0
                wma_denominator = (wma_period * (wma_period + 1)) / 2

                for j in range(wma_period):
                    wma_total += candles[i - j - 1]['closeMid'] * (wma_period - j)
                if wma_denominator != 0:
                    wma = float("{0:.4f}".format(wma_total / wma_denominator))
                else:
                    wma = 0
                candle_wma.append(wma)

        current_candle_data = [candle_date_labels, candle_date_values, candle_prices, candle_wma]
        candles_data.append(dict(zip(keys, current_candle_data)))
        i += 1
		
	graph_wma(candles_data, pair)
		
#    for k in candles_data:
#        print ''
#        print k

def graph_wma(candles_data, pair)
    x1 = []
    x2 = []
    x3 = []
    xlabels = []
    y1 = []
    y2 = []
    y3 = []
	candle_width = 10

    l = 0
    for a in candles_data:
        x1.append(a['price'][0])
        if l > wma_period_max - 1:
            x2.append(a['price'][0])
            x3.append(a['price'][0])
            y2.append(a['wma'][0])
            y3.append(a['wma'][1])
        y1.append(a['price'][4])
        xlabels.append(a['date_label'])
        l += 1

    plt.clf()

    plt.title('Bar Chart of ' + pair)
    ax = plt.subplot(212)
    plt.subplot(211)
    plt.axis([min(x1), max(x1), min(y1), max(y1)])
    candlestick_ohlc(ax, y1, candle_width, colorup='b', colordown='r')
#    plt.plot(x1, y1, 'r-', label='price')
    plt.plot(x2, y2, 'g-', label='wma 2')
    plt.plot(x3, y3, 'b-', label='wma 3')
    plt.legend(loc='upper left')
    plt.xticks(np.arange(min(x1), max(x1), 0.1), xlabels, rotation='vertical')
    plt.yticks(np.arange(min(y1), max(y1), 0.1), y1, rotation='horizontal')
    plt.draw()
    plt.show(block=False)

    last_wma_short = candles_data[len(candles_data) - 1]['wma'][0]
    last_wma_long = candles_data[len(candles_data) - 1]['wma'][1]

    check_wma_crossing(last_wma_short, last_wma_long)


current_wma_state = ''
current_state_changed = False


def check_wma_crossing(s, l):
    global current_wma_state
    global current_state_changed

    current_state_changed = False

    if current_wma_state == 'A':
        if s < l:
            current_wma_state = 'B'  # B = s is below
            current_state_changed = True
            order("USD_JPY", 10000, 'buy')
    else:
        if s > l:
            current_wma_state = 'A'  # A = s is above
            current_state_changed = True
            order("USD_JPY", 10000, 'sell')

		
def compare_wma(candles_data_array):
    pass
    for candle in candles_data_array:
        print ''
        print candle
        print ''

#add functionality to take in an array of wma periods, and compare them all
#against each other, with the following variables for AB testing:
# 1. distance between the direction changes (int, int) --> (int)
# 2. which direction did the change took place in (bool, bool) --> (bool)
# 3. number of direction changes within a time range (int, time) --> (int)
# 4. difference in WMA periods (int, int) --> int


