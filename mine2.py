#! /usr/bin/python3
# -*- coding: utf-8 -*-
'''
Cloud vs CPE mining profit calc
by @fooblic
'''
import os
import time

import pylab as py
import requests
import yaml

import pandas as pd
from tabulate import tabulate
import pprint

import matplotlib as mpl
import matplotlib.pyplot as plt
from numpy import arange

pp = pprint.PrettyPrinter(indent=4)
TODAY = time.strftime("%y%m%d")
TD = time.strftime("%b %d, %Y")

CFG = yaml.load(open("mine.yml"))
pp.pprint(CFG["Coins"])

CURRENCY = CFG["Coins"].keys()
CLOUD = CFG["Cloud"].keys()

# CPE mining data
GEARS = CFG["CPE"].keys()
HASH = CFG["HASH"] 

MINING = list(CLOUD) + list(GEARS)
CPE_NUM = len(GEARS) * len(HASH)

reporting = TD + "\n"
for mine in CLOUD:
    reporting += "\n%s\n" % mine
    reporting += pprint.pformat(CFG["Cloud"][mine], indent=4)

cpe = pd.DataFrame([],
                    columns=["cpe", "cost", "alg", "rate", "units", "power", "mine", "maint"],
                    index=arange(CPE_NUM))
numb = 0
for item in GEARS:
    for alg in HASH:
        try:
            cpe.loc[numb]["cpe"] = item
            cpe.loc[numb]["cost"] = CFG["CPE"][item]["Cost"] / CFG["USD_CUR"]
            cpe.loc[numb]["alg"] = alg
            cpe.loc[numb]["rate"] = CFG["CPE"][item]["Hash"][alg]["Rate"]
            cpe.loc[numb]["units"] = CFG["Units"][alg]
            cpe.loc[numb]["power"] = CFG["CPE"][item]["Hash"][alg]["Power"]
            cpe.loc[numb]["mine"] = cpe.loc[numb]["cost"] / cpe.loc[numb]["rate"]
            cpe.loc[numb]["maint"] = CFG["KWH"] / CFG["USD_CUR"] * cpe.loc[numb]["power"] / 1000 * 24 / cpe.loc[numb]["rate"]
        except KeyError:
            #print("Error key: %s %s" % (item, alg))
            pass
        numb += 1

cpe = cpe[cpe["maint"] > 0]
cpe_report = tabulate(cpe, headers="keys", tablefmt="orgtbl", showindex=False)
reporting += "\n" + cpe_report + "\n"
print(cpe_report)

URL_BASE = CFG["URL_BASE"]
records = dict.fromkeys(CURRENCY)
for cur in CURRENCY:
    records[cur] = dict({"API": URL_BASE + CFG["API"][cur]} )

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
#pp.pprint(records)

INDX = []  # index for pandas df
# Get mining data from config
for cur in CURRENCY:
    for mine in MINING:
        records[cur].update(mine={})
        if mine in GEARS:
            try:
                cpe_table = cpe[cpe["cpe"] == mine]
                miner = {
                    "MINE": cpe_table[cpe_table["alg"] == CFG["ALG"][cur]]["mine"].item(),
                    "MAINT": cpe_table[cpe_table["alg"] == CFG["ALG"][cur]]["maint"].item()}
                INDX.append("%s-%s" % (cur, mine))
                records[cur][mine] = miner
            except ValueError:
                #print("error: ", cur, mine)
                pass
        else:
            try:
                miner = {
                    "MINE": CFG["Cloud"][mine][cur]["mine"],
                    "MAINT": CFG["Cloud"][mine][cur]["maint"]}
                INDX.append("%s-%s" % (cur, mine))
                records[cur][mine] = miner
            except KeyError:
                #print("error: ", cur, mine)
                pass

# Get mining dataframe from config
mining = pd.DataFrame([],
                      columns=["rate", "coins", "price", "mine", "maint"],
                      index=INDX)

for cur in CURRENCY:
    for mine in MINING:
        try:
            mining.loc["%s-%s" % (cur, mine)]["rate"] = CFG["Units"][CFG["ALG"][cur]]
            mining.loc["%s-%s" % (cur, mine)]["coins"] = CFG["Coins"][cur]
            mining.loc["%s-%s" % (cur, mine)]["price"] = records[cur]["price"]
            if mine in GEARS:
                cpe_table = cpe[cpe["cpe"] == mine]
                mining.loc["%s-%s" % (cur, mine)]["mine"] = cpe_table[cpe_table["alg"] == CFG["ALG"][cur]]["mine"].item()
                mining.loc["%s-%s" % (cur, mine)]["maint"] = cpe_table[cpe_table["alg"] == CFG["ALG"][cur]]["maint"].item()
            else:
                mining.loc["%s-%s" % (cur, mine)]["mine"] = CFG["Cloud"][mine][cur]["mine"]
                mining.loc["%s-%s" % (cur, mine)]["maint"] = CFG["Cloud"][mine][cur]["maint"]
        except KeyError:
            #print("error: ", cur, mine)
            pass

mine_report = tabulate(mining, headers="keys", tablefmt="orgtbl", showindex=True)
reporting += "\n" + mine_report + "\n"
print(mine_report)

# Logging
reporting += "\n---\nBTC_USD: %s\n" % BTC_USD
TEMPL = '''
  investing: %s  # USD for %s days
  income:   %.1f  # USD
  maintenance: %.1f  # USD
  profit:    %.1f  # USD (%.1f %%)
'''


def outcome(ddays, ffee, invest):
    ''' Expences '''
    return invest + ffee * ddays


def income(ddays, coins, exrate, unit):
    ''' Revenue '''
    return BTC_USD * (coins * unit * exrate) * ddays

if CFG["Figures"]:
    try:
        os.mkdir("img" + TODAY)
    except:
        print("Could not create %s" % ("img" + TODAY))

DAYS = 365 * 1
COL = ["invest", "fee", "earn", "ratio",
   "revenue", "maintenance", "profit", "return", "percent"]

table = pd.DataFrame([], columns=COL, index=INDX)

for cur in CURRENCY:
    cur_price = records[cur]["price"]
    for mine in MINING:

        num = cur + "-" + mine
        if num in INDX:

            investing = CFG["Investing"][cur]
            table.loc[num]["invest"] = investing
            units = investing / mining.loc[num]["mine"]
            fee = mining.loc[num]["maint"] * units  # per day USD
            earn = CFG["Coins"][cur] * units * cur_price * BTC_USD  # USD
            ratio = (earn - fee) / CFG["Investing"][cur] * 100  # profit per day per investment %

            table.loc[num]["fee"] = fee
            table.loc[num]["earn"] = earn
            table.loc[num]["ratio"] = ratio

            out = []
            inc = []
            profit = []

            reporting += "\n%s:" % num
            for day in range(DAYS):
                out.append(outcome(day, fee, investing))
                inc.append(income(day, CFG["Coins"][cur], cur_price, units))
                profit.append(inc[day] - out[day])

                if (profit[day-1] < 0) and (profit[day] >= 0):  # point of investment return
                    roi = day/30
                    reporting += "  # return in %.1f monthes" % roi
                    table.loc[num]["return"] = roi

                if day == (DAYS - 1):  # end of the days
                    calc = ""
                    pro = "%.1f" % (profit[day] / investing  * 100)
                    calc = TEMPL % (investing, day,
                                    inc[day],
                                    out[day] - investing,
                                    profit[day], profit[day] / investing * 100
                                   )
                    #print(calc)
                    reporting += calc

            if CFG["Figures"]:
                py.figure(num)
                py.title("%s (%s) -> %s%% (%s)"  %  (cur, mine, pro, TD))
                py.xlabel("days")
                py.plot(out, label="outcome")
                py.plot(inc, label="income")
                py.plot(profit, label="profit")
                py.legend(loc="best")
                #py.show()
                py.savefig("./img" + TODAY +"/" + cur + "_" + mine + ".png")

table["revenue"] = table["earn"] * DAYS
table["maintenance"] = table["fee"] * DAYS
table["profit"] = table["revenue"] - table["maintenance"] - table["invest"]
table["percent"] = table["profit"] / table["invest"] * 100

table.sort_values(by="percent", inplace=True, ascending=False)
table.to_csv("./report~/report %s.csv" % TODAY, sep="\t", index=True)

with open("./report~/report" + TODAY + ".log", "w") as FILE:
    FILE.write(reporting)

#print(reporting)
print(table)

# Graph
plt.rcdefaults()
#mpl.rcParams["font.family"] = "serif"
#mpl.rcParams["font.size"] = 14
fig, ax = plt.subplots()
y_pos = arange(len(table.index))
ax.barh(y_pos - 0.5, table["percent"])
ax.set_yticks(y_pos)
ax.set_yticklabels(table.index.values)
ax.set_xlabel('Percents per year, %')
ax.invert_yaxis()
plt.autoscale(tight=True)
plt.subplots_adjust(left=0.22)
plt.grid()
plt.savefig("./report~/percent-%s.png" % TODAY)
#plt.show()
