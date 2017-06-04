#! /usr/bin/python3
# -*- coding: utf-8 -*-
'''
Cloud mining profit calc
by @fooblic
'''
import pylab as py
import requests
import yaml

CFG = yaml.load(open("investing.yml.example"))

API_BTC = "https://api.coinmarketcap.com/v1/ticker/bitcoin"
API_LTC = "https://api.coinmarketcap.com/v1/ticker/litecoin"
API_ETH = "https://api.coinmarketcap.com/v1/ticker/ethereum"

rep = requests.get(API_BTC)
if rep.status_code == 200:
    USD_BTC = float(rep.json()[0]['price_usd'])

rep = requests.get(API_LTC)
if rep.status_code == 200:
    LTC_BTC = float(rep.json()[0]['price_btc'])

rep = requests.get(API_ETH)
if rep.status_code == 200:
    ETH_BTC = float(rep.json()[0]['price_btc'])

print('''Exchange data:
BTC: %s USD
LTC: %s BTC
ETH: %s BTC
''' % (USD_BTC, LTC_BTC, ETH_BTC))

# https://hashflare.io/
SHA256 = { # https://alloscomp.com/bitcoin/calculator
    "NAME" : "BTC",
    "MINE" : 1.2,          # USD per 10GH/s
    "MAINT" : 0.0035,      # USD fee per 10GH/s per day
    "COINS" : 370 * 1e-8,  # satoshi per day for 10GH/s for current difficulty
    "EXRATE": 1,           # BTC
    "IN": CFG['BTC']       # USD investing
}

SCRYPT = { # http://www.coinwarz.com/calculators/litecoin-mining-calculator/
    "NAME" : "LTC",
    "MINE" : 13.5,     # USD per 1 MH/s
    "MAINT" : 0.01,    # USD fee per 1 MH/s per day
    "COINS" : 0.001951,  # coins per day
    "EXRATE": LTC_BTC,   # BTC
    "IN": CFG['LTC']     # USD investing
    
}

ETH = { # https://etherscan.io/ether-mining-calculator
    "NAME" : "ETH",
    "MINE" : 2.2,      # USD per 100 KH/s
    "MAINT" : 0,
    "COINS" : 7.1577 * 1e-5, # coins per day
    "EXRATE": ETH_BTC,      # BTC
    "IN": CFG['ETH']        # USD investing
}

DATA_ALL = [SHA256, SCRYPT, ETH]
DAYS = 365 * 1

report = '''investing: %s USD for %s days
revenue:   %.1f USD
maintance: %.1f USD
profit:    %.1f USD (%.1f %%)
'''

def outcome(ddays, ffee, invest):
    ''' Expences '''
    return invest + ffee * ddays

def income(ddays, dat, unit):
    ''' Revenue '''
    return USD_BTC * (dat["COINS"] * unit * dat["EXRATE"]) * ddays

num = 0
for data in DATA_ALL:
    units = data["IN"] / data["MINE"]
    fee = data["MAINT"] * units  # per day

    profit = []
    inc = []
    out = []
    for day in range(DAYS):
        out.append(outcome(day, fee, data["IN"]))
        inc.append(income(day, data, units))
        profit.append(inc[day] - out[day])
        if (profit[day-1] < 0) and (profit[day] >= 0):
            print(data["NAME"], "return in" , day, "days")
        if day == (DAYS - 1):
            pro = "%.1f" % (profit[day] / data["IN"] * 100)
            print(report %
                      (data["IN"], day,
                       inc[day],
                       out[day] - data["IN"],
                       profit[day],
                       profit[day] / data["IN"] * 100
                      )
                  )

    py.figure(num)
    py.title(data["NAME"] + " -> " + pro + "% per year")
    py.xlabel("days")
    py.plot(out, label="outcome")
    py.plot(inc, label="income")
    py.plot(profit, label="profit")
    py.legend(loc="best")
    #py.show()
    py.savefig("./img1/" + data["NAME"] + ".png")
    num += 1
