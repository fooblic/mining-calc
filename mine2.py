#! /usr/bin/python3
# -*- coding: utf-8 -*-
'''
Cloud mining profit calc
by @fooblic
'''
import os
import time

import pylab as py
import requests
import yaml

import pandas as pd

TODAY = time.strftime("%y%m%d")

CFG = yaml.load(open("investing.yml"))

CURRENCY = CFG["Coins"].keys()  #["BTC", "LTC", "ETH", "DASH", "ZEC"]
MINING = CFG["Mining"].keys()  #["HF", "GM"]
qty = len(CURRENCY) * len(MINING)

URL_BASE = "https://api.coinmarketcap.com/v1/ticker/"
records = {"BTC": 
               {"API": URL_BASE + "bitcoin"},
            "LTC": 
                {"API": URL_BASE + "litecoin"},
            "ETH": 
                {"API": URL_BASE + "ethereum"},
            "DASH": 
                {"API": URL_BASE + "dash"},
            "ZEC": 
                {"API": URL_BASE + "zcash"}
}

print("Getting ex-rates...\n")
# BTC/USD rate
rep = requests.get(URL_BASE + "bitcoin")
if rep.status_code == 200:
    BTC_USD = float(rep.json()[0]["price_usd"])

# Ex-rates in BTC
for cur in CURRENCY:
    rep = requests.get(records[cur]["API"])
    records[cur].update(price=0)
    if rep.status_code == 200:
        records[cur]["price"] = float(rep.json()[0]["price_btc"])

# Get mining data from config
for cur in CURRENCY:
    for mine in MINING:
        records[cur].update(mine={})
        miner = {
             "MINE" : CFG["Mining"][mine][cur]["mine"],
             "MAINT" : CFG["Mining"][mine][cur]["maint"]
        }
        records[cur][mine] = miner

reporting = "BTC_USD: %s USD\n" % BTC_USD
for cur in CURRENCY:
    reporting += "%s: %s BTC\n" % (cur, records[cur]["price"])

TEMPL = '''
investing: %s USD for %s days
revenue:   %.1f USD
maintance: %.1f USD
profit:    %.1f USD (%.1f %%)
'''

def outcome(ddays, ffee, invest):
    ''' Expences '''
    return invest + ffee * ddays

def income(ddays, coins, exrate, unit):
    ''' Revenue '''
    return BTC_USD * (coins * unit * exrate) * ddays

try:
    os.mkdir("img" + TODAY)
except:
    print("Could not create %s" % ("img" + TODAY))

num = 0
DAYS = 365 * 1
col = ["currency", "mining", "invest", "revenue", "maintance", "profit",
               "return", "percent"]
table = pd.DataFrame([], columns=col, index=range(qty))

for cur in CURRENCY:
    for mine in MINING:
        print("Calculating %s %s..." % (cur, mine))

        table.loc[num]["currency"] = cur
        table.loc[num]["mining"] = mine

        data = records[cur][mine]
        investing = CFG["Investing"][cur]
        table.loc[num]["invest"] = investing
        units = investing / data["MINE"]
        fee = data["MAINT"] * units  # per day
        print("Units %.1f / Fee %s" % (units, fee))

        profit = []
        inc = []
        out = []

        reporting += "\n %s %s" % (cur, mine) 
        for day in range(DAYS):
            out.append(outcome(day, fee, investing))
            inc.append(income(day, CFG["Coins"][cur], records[cur]["price"], units))
            profit.append(inc[day] - out[day])

            if (profit[day-1] < 0) and (profit[day] >= 0):
                roi = day/30
                reporting += " return in %.1f monthes" % roi
                table.loc[num]["return"] = roi

            if day == (DAYS - 1):
                calc = ""
                pro = "%.1f" % (profit[day] / investing  * 100)
                calc = TEMPL % (investing, day,
                                inc[day],
                                out[day] - investing,
                                profit[day],
                                profit[day] / investing * 100
                                )
                #print(calc)
                reporting += calc
                table.loc[num]["revenue"] = inc[day]
                table.loc[num]["maintance"] = out[day] - investing
                table.loc[num]["profit"] = profit[day]
                table.loc[num]["percent"] = profit[day] / investing * 100

        py.figure(num)
        py.title(cur + "_" + mine + " -> " + pro + "% per year")
        py.xlabel("days")
        py.plot(out, label="outcome")
        py.plot(inc, label="income")
        py.plot(profit, label="profit")
        py.legend(loc="best")
        #py.show()
        py.savefig("./img" + TODAY +"/" + cur + "_" + mine + ".png")
        num += 1

with open("report" + TODAY + ".txt", "w") as FILE:
    FILE.write(reporting)

#print(reporting)
print(table.sort(["percent"]))
