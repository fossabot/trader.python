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
    movingavg = sum(x['price'] for x in trades["return"]) / len(trades["return"])
    return movingavg

#this is the refined mean function thta i plan to use    
def mean(l): 
    if isinstance(l, dict):
        print "The dict has [\"return\"] still attached and we have a dict of a list of dicts"
        return sum(float(x['price']) for x in l["return"]) / len(l["return"])
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
everything[0],everything[1] = everything[1],everything[0]

new = json.loads(everything[0])
newnew = common.floatify(new["return"])
# newlist = []
# for x in newnew:
    # newlist.append(x['price'])
newlist = [x['price'] for x in newnew]      #list comprehension way replaces the 3 lines above

#print "type of newlist is:",type(newlist),newlist[14999]
#print common.mean(newlist)
#print "The SMA is: ", SMA                              #just a bunch of crap test lines.... erase soon.
# print "Type is: ", type(new)
# print "The length is: ", len(new)
# print "The Mean of the %s is: %s" % (type(new),mean(new))
# print "The Mean of the %s is: %s" % (type(newnew),mean(newnew))
#print newnew
totaleachprice = 0
numtrades = 0
totaleachamount = 0
vwapcum = 0
valcum =0
highestprice,highestamount =0,0
lowestprice,lowestamount =15000000,15000000
earliesttime = int(time.time()) * 1000000
latesttime=0
1363662863
1363662863617449
for x in new["return"]:                                         #try to rewrite with list comprehension somehow
    price  = float(x['price'])
    amount = float(x['amount'])
    tid = int(x['tid'])
    totaleachprice += price
    totaleachamount += amount
    vwapcum+= price * amount
    if price > highestprice:  highestprice = price
    if price < lowestprice:  lowestprice = price
    if amount > highestamount: highestamount = amount
    if amount < lowestamount: lowestamount = amount
    if tid < earliesttime: earliesttime = tid
    if tid > latesttime: latesttime = tid
    
print "Sum of all prices: $%f &  Sum of all amounts: %f BTC" % (totaleachprice, totaleachamount)
avgprice = totaleachprice / len(new["return"])
avgamt = totaleachamount / len(new["return"])
print "Mean Price is $%f and Mean Amount is %f BTC" % (avgprice,avgamt)
vwap = vwapcum / totaleachamount
print "VWAP is: $", vwap
print "Highest Price: $%g & Lowest Price: $%g" % (highestprice,lowestprice)
print "Highest Amount: %f BTC & Lowest Amount: %f BTC" % (highestamount,lowestamount)
print "Earliest time is: %s & Latest time is: %s" % (datetime.datetime.fromtimestamp(earliesttime/1000000),datetime.datetime.fromtimestamp(latesttime/1000000))