#! /usr/bin/python3
# -*- coding: utf-8 -*-
'''
Cloud mining payouts calc
by @fooblic
'''
import os
import time

import pylab as py
import requests
import yaml

import pandas as pd
import pprint

pp = pprint.PrettyPrinter(indent=4)
TODAY = time.strftime("%y%m%d")
TD = time.strftime("%b %d, %Y")
reporting = TD + "\n"

CFG = yaml.load(open("payout.yml"))
pp.pprint(CFG)

CURRENCY = CFG.keys()

URL_BASE = "https://api.coinmarketcap.com/v1/ticker/"
records = {"BTC": {"API": URL_BASE + "bitcoin"},
           "LTC": {"API": URL_BASE + "litecoin"},
           "ETH": {"API": URL_BASE + "ethereum"},
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

reporting += "\n---\nBTC_USD: %s\n" % BTC_USD
for cur in CURRENCY:
    reporting += '''%s:
  BTC: %s  # price
''' % (cur, records[cur]["price"])

reporting += pprint.pformat(CFG, indent=4)

print(reporting)

COL = list(CFG["BTC"].keys())
ADDCOL = ["diff", "price_btc", "usd_day", "usd_100", "usd_rate", "roi"]
table = pd.DataFrame([], columns=COL+ADDCOL, index=CURRENCY)

# Fill-in table
for cur in CURRENCY:
    table.loc[cur]["invest"] = CFG[cur]["invest"]
    table.loc[cur]["hashrate"] = CFG[cur]["hashrate"]
    table.loc[cur]["metric"] = CFG[cur]["metric"]
    table.loc[cur]["payout"] = CFG[cur]["payout"]
    table.loc[cur]["maint"] = CFG[cur]["maint"]
    table.loc[cur]["price_btc"] = records[cur]["price"]

table["diff"] = table["payout"] - table["maint"]
table["usd_day"] = table["diff"] * table["price_btc"] * BTC_USD

# LTC payout in BTC
table.loc["LTC"]["usd_day"] = table.loc["LTC"]["diff"] * BTC_USD

table["usd_100"] = table["usd_day"] / table["invest"] * 100
table["usd_rate"] = table["usd_day"] / table["hashrate"]
table["roi"] = table["invest"] / table["usd_day"] / 30

table.sort_values(by="usd_100", inplace=True, ascending=False)
table.to_csv("./report/payout %s.csv" % TODAY, sep="\t", index=True)

with open("./report/payout_report" + TODAY + ".log", "w") as FILE:
    FILE.write(reporting)

print(table)
