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


access_token = 'a0fce8d9a47637254bdef08a4e059641-b03e0bd3095df91751f3fbb7592f2579'
account_id = '270129'
headers = {"Content-Type" : "application/x-www-form-urlencoded", 'Authorization' : 'Bearer ' + access_token}
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
        return 60*int(granularity[1:])
    elif granularity[0] == 'H':
        return 60*60*int(granularity[1:])
    elif granularity[0] == 'D':
        return 60*60*24
    elif granularity[0] == 'W':
        return 60*60*24*7
    #Does not take into account actual month length
    elif granularity[0] == 'M':
        return 60*60*24*30


def account():
    conn = httplib.HTTPSConnection("api-fxpractice.oanda.com")
    conn.request("GET", "/v1/accounts/" + account_id, "", headers)
    print conn.getresponse().read()


def order(pair, units, buysell):
    now = datetime.datetime.now()
    expire = now + datetime.timedelta(days=1)
    expire = expire.isoformat('T') + "Z"
    conn = httplib.HTTPSConnection("api-fxpractice.oanda.com")
    params = urllib.urlencode({"instrument": pair,
                               "units" : units,
                               "type" : "market",
                               "side" : buysell})
    conn.request("POST", "/v1/accounts/" + account_id + "/orders", params, headers)
    print conn.getresponse().read()


def close():
    conn = httplib.HTTPSConnection("api-fxpractice.oanda.com")
    conn.request("DELETE", "/v1/accounts/" + account_id + "/positions/" + "USD_JPY", "", headers)
    print conn.getresponse().read()


def price():
    conn = httplib.HTTPSConnection("api-fxpractice.oanda.com")
    conn.request("GET", "/v1/prices?instruments=" + "USD_JPY", "", headers)
    print conn.getresponse().read()


def positions():
    conn = httplib.HTTPSConnection("api-fxpractice.oanda.com")
    conn.request("GET", "/v1/accounts/" + account_id + "/positions", "", headers)
    print conn.getresponse().read()


## Calculates the WMA over 'period' candles of size 'granularity' for pair 'pair'
def WMA(period=20, granularity='M15', pair='USD_JPY', wma_period_1=5, wma_period_2=20):
    conn = httplib.HTTPSConnection("api-fxpractice.oanda.com")
#   conn.request("GET", "/v1/accounts/" + account_id, "", headers)

    url = ''.join(["/v1/candles?count=", str(period + 1), "&instrument=", pair, "&granularity=", str(granularity), "&candleFormat=midpoint"])
    conn.request("GET", url, "", headers)

    conn_json = conn.getresponse().read()
    resp = json.loads(conn_json)
    print conn_json

    candles = resp['candles']
    candlewidth = getGranularitySeconds(granularity)
    now = time.time() + utc_offset
    finalsma = 0
    count = 0
    oldest = now - (period * candlewidth)
    oldprice = 0

    x = 0.0
    min_candle = 10000
    max_candle = 0

    candle_wma_1 = []
    wma_denom_1 = (wma_period_1 * (wma_period_1 + 1)) / 2
    candle_wma_2 = []
    wma_denom_2 = (wma_period_2 * (wma_period_2 + 1)) / 2
    i = 0
    for candle in candles:
        wma_total_1 = 0
        wma_total_2 = 0

        for j in range(wma_period_1):
            wma_total_1 += candles[i - j]['highMid'] * (wma_period_1 - j)

        for j in range(wma_period_2):
            wma_total_2 += candles[i - j]['highMid'] * (wma_period_2 - j)

        wma_1 = wma_total_1 / wma_denom_1
        wma_2 = wma_total_2 / wma_denom_2
        candle_wma_1.append(wma_1)
        candle_wma_2.append(wma_2)
        print candle_wma_1[i - 1]
        print candle_wma_2[i - 1]
        i += 1

        if candle['closeMid'] < min_candle:
            min_candle = candle['lowMid']
        if candle['closeMid'] > max_candle:
            max_candle = candle['highMid']
    min_candle -= 0.1
    max_candle += 0.1

    dates = []
    date_label = []
    prices = []
    prices_1 = []

    plt.clf()
    plt.cla()

    for candle in candles:
        x += 1.0
        candleTimeLabels = time.strptime(str(candle['time']),  '%Y-%m-%dT%H:%M:%S.%fZ')
        candleTimeValues = date2num(datetime.strptime(candle['time'], '%Y-%m-%dT%H:%M:%S.%fZ'))
        date_label.append(str(candleTimeLabels[1]) + '-' +
                          str(candleTimeLabels[2]) + '-' +
                          str(candleTimeLabels[0]) + ' ' +
                          str(candleTimeLabels[3]) + ':' +
                          str(candleTimeLabels[4]) + ':' +
                          str(candleTimeLabels[5]))

        dates.append(candleTimeValues)
        prices.append([candleTimeValues, candle['openMid'], candle['highMid'], candle['lowMid'], candle['closeMid']])
        prices_1.append(candle['closeMid'])

        if candleTimeValues < oldest:
            oldprice = candle['closeMid']
            continue
        else:
            while oldest < candleTimeValues:
                count += 1
                finalsma += oldprice * count
                oldest += candlewidth
            oldprice = candle['closeMid']
    while oldest < now:
        count += 1
        finalsma += candles[-1]['closeMid'] * count
        oldest += candlewidth
    totalweight = 0
    for i in range(1, period + 1):
        totalweight += i

    plt.figure(1)
    plt.axis([min(dates), max(dates), min_candle, max_candle])
    plt.title('Bar Chart of ' + pair)
    ax = plt.subplot(212)
    plt.subplot(211)
    plt.plot_date(dates, candle_wma_1, 'm-')
    plt.xticks(np.arange(min(dates), max(dates), 0.01), date_label, rotation='vertical')
    candlestick_ohlc(ax, prices, 0.00025, colorup='b', colordown='r')
    #plt.plot(candle_wma_2)
    plt.legend()
    plt.draw()
    plt.show(block=False)

    #return float(finalsma)/float(totalweight)


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

    conn = httplib.HTTPSConnection("api-fxpractice.oanda.com")

    while True:
        conn.request("GET", "/v1/accounts/" + account_id, "", headers)
        response = conn.getresponse()
        resptext = response.read()
        data = json.loads(resptext)
        unreal_pl = data['unrealizedPl']

        profit.append(unreal_pl)
        upper.append(top_offset)
        lower.append(bottom_offset)

        seconds += 1
        graph(seconds, unreal_pl, top_offset, bottom_offset, len(profit), shape)
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


def graph(seconds, profit, upper, lower, length, shape):
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

