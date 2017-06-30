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

TODAY = time.strftime("%y%m%d")

CFG = yaml.load(open("investing.yml.example"))

URL_BASE = "https://api.coinmarketcap.com/v1/ticker/"
records = {"BTC": 
               {"API": URL_BASE + "bitcoin",
                "price": 0,
                "mining": # https://alloscomp.com/bitcoin/calculator
                    {
                    "MINE" : 1.2,          # USD per 10GH/s
                    "MAINT" : 0.0035,      # USD fee per 10GH/s per day
                    "COINS" : 353 * 1e-8,  # satoshi per day for 10GH/s for current difficulty
                    "IN": CFG['BTC']       # USD investing
                    }
                },
            "LTC": 
                {"API": URL_BASE + "litecoin",
                 "price": 0,
                 "mining": # http://www.coinwarz.com/calculators/litecoin-mining-calculator/
                     {
                     "MINE" : 13.5,     # USD per 1 MH/s
                     "MAINT" : 0.01,    # USD fee per 1 MH/s per day
                     "COINS" : 0.002067,  # coins per day
                     "IN": CFG['LTC']     # USD investing
                     }
                },
            "ETH": 
                {"API": URL_BASE + "ethereum",
                 "price": 0,
                 "mining": # https://etherscan.io/ether-mining-calculator
                     {
                     "MINE" : 2.2,      # USD per 100 KH/s
                     "MAINT" : 0,
                     "COINS" : 4.3849 * 1e-5, # coins per day
                     "IN": CFG['ETH']        # USD investing
                     }
                 },
            "DASH": 
                {"API": URL_BASE + "dash",
                 "price": 0,
                 "mining": # http://www.coinwarz.com/calculators/litecoin-mining-calculator/
                     {
                     "MINE" : 5.8,      # USD per 1 MH/s
                     "MAINT" : 0,
                     "COINS" : 0.00013255, # coins per day
                     "IN": CFG['DASH']        # USD investing
                     }
                },
            "ZEC": 
                {"API": URL_BASE + "zcash",
                 "price": 0,
                 "mining": # https://www.coinwarz.com/calculators/zcash-mining-calculator/
                     {
                     "MINE" : 2.0,      # USD per 0.1 H/s
                     "MAINT" : 0,
                     "COINS" : 0.00000257, # coins per day
                     "IN": CFG['ZEC']        # USD investing
                     }
                }
}

CURRENCY = ["BTC", "LTC", "ETH", "DASH", "ZEC"]

print("Getting ex-rates...\n")
# BTC/USD rate
rep = requests.get(URL_BASE + "bitcoin")
if rep.status_code == 200:
    BTC_USD = float(rep.json()[0]["price_usd"])

# Ex-rates in BTC
for cur in CURRENCY:
    rep = requests.get(records[cur]["API"])
    if rep.status_code == 200:
        records[cur]["price"] = float(rep.json()[0]["price_btc"])

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

os.mkdir("img" + TODAY)
num = 0
DAYS = 365 * 1

for cur in CURRENCY:
    print("Calculating %s..." % cur)
    data = records[cur]["mining"]
    units = data["IN"] / data["MINE"]
    fee = data["MAINT"] * units  # per day

    profit = []
    inc = []
    out = []

    reporting += "\n" + cur
    for day in range(DAYS):
        out.append(outcome(day, fee, data["IN"]))
        inc.append(income(day, data["COINS"], records[cur]["price"], units))
        profit.append(inc[day] - out[day])

        if (profit[day-1] < 0) and (profit[day] >= 0):
            reporting += " return in " + str(day) + " days"

        if day == (DAYS - 1):
            pro = "%.1f" % (profit[day] / data["IN"] * 100)
            reporting += TEMPL % (data["IN"], day,
                                  inc[day],
                                  out[day] - data["IN"],
                                  profit[day],
                                  profit[day] / data["IN"] * 100
                                 )

    py.figure(num)
    py.title(cur + " -> " + pro + "% per year")
    py.xlabel("days")
    py.plot(out, label="outcome")
    py.plot(inc, label="income")
    py.plot(profit, label="profit")
    py.legend(loc="best")
    #py.show()
    py.savefig("./img" + TODAY +"/" + cur + ".png")
    num += 1

with open("report" + TODAY + ".txt", "w") as FILE:
    FILE.write(reporting)

print(reporting)

