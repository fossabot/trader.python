#!/usr/bin/env python
# Created by genBTC 3/19/2013
# reading trade history data from a file and gathering stats on it and
# testing mean functions with list comprehension 
import sys
import os
import json
import common 
import pyreadline
import time
import datetime

#thought this would compute simple moving average(SMA) all it does is a simple "mean" calculation
def movavg(trades):
    #movingavg = sum(map(lambda x: x['price'], trades)) / len(trades)
    movingavg = sum(x['price'] for x in trades["data"]) / len(trades["data"])
    return movingavg

#this is the refined mean function thta i plan to use    
def mean(l): 
    if isinstance(l, dict):
        print "The dict has [\"data\"] still attached and we have a dict of a list of dicts"
        return sum(float(x['price']) for x in l["data"]) / len(l["data"])
    elif isinstance(l, list) and isinstance(l[0],dict):
        print "Return has been taken off and now dealing with a list of dicts"
        return sum(float(x['price']) for x in l) / len(l)
    elif isinstance(l,list):
        return sum(l) / len(l)
    else:
        raise TypeError()

filetoopen = raw_input("Enter the filename in the data/ directory to open: ")
datapartialpath=os.path.join(os.path.dirname(__file__) + '../data/')
with open(os.path.join(datapartialpath + filetoopen),'r') as f:
    everything = f.readlines()
print "Is this a Trade History file (not a full depth file)? Yes"
isdepthfile = raw_input("N/No or Leave blank for Yes(default)")
if not(isdepthfile):
    everything[0],everything[1] = everything[1],everything[0]       #then by default its a history file

new = json.loads(everything[0])
newnew = common.floatify(new["data"])

[earliesttime],[latesttime] = [[func(x[thing] for x in newnew) for thing in ['tid']] for func in [min,max]]
# for x in newnew:                                        
#     price  = float(x['price'])
#     amount = float(x['amount'])


#rewritten with list comprehension somehow (see below)
vwapcum = sum(x['price']*x['amount'] for x in newnew)
[lowestprice,lowestamount],[highestprice,highestamount],[totaleachprice,totaleachamount] = \
    [[func(x[thing] for x in newnew) for thing in ['price','amount']] for func in [min,max,sum]]


print "Sum of all prices: $%f &  Sum of all amounts: %f BTC" % (totaleachprice, totaleachamount)
avgprice = totaleachprice / len(new["data"])
avgamt = totaleachamount / len(new["data"])
print "Mean Price is $%f and Mean Amount is %f BTC" % (avgprice,avgamt)
vwap = vwapcum / totaleachamount
print "VWAP is: $", vwap
print "Highest Price: $%g & Lowest Price: $%g" % (highestprice,lowestprice)
print "Highest Amount: %f BTC & Lowest Amount: %f BTC" % (highestamount,lowestamount)
print "Earliest time is: %s & Latest time is: %s" % (datetime.datetime.fromtimestamp(earliesttime/1E6),datetime.datetime.fromtimestamp(latesttime/1E6))