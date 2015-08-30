import httplib
import urllib
import json
import datetime
import time

import matplotlib.pyplot as plt


access_token = 'a0fce8d9a47637254bdef08a4e059641-b03e0bd3095df91751f3fbb7592f2579'
account_id = '270129'
headers = {"Content-Type" : "application/x-www-form-urlencoded", 'Authorization' : 'Bearer ' + access_token}
lastTrade = "buy"
shape = 'cD'
tradeSize = "30000"

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


def trade():
    global lastTrade
    global shape

    seconds = 0

    profit = []
    upper = []
    lower = []

    top_offset = 5.0
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

        top_offset += 0.5
        bottom_offset += 0.3

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

        time.sleep(0.1)

        print unreal_pl


def graph(seconds, profit, upper, lower, length, shape):
    plt.plot(seconds, profit, shape, seconds, upper, 'g.', seconds, lower, 'r.', seconds, 0, 'm-')
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
