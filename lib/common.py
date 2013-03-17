#!/usr/bin/env python
# list of commonly used and useful functions
# NOW contains common client interface function calls to each individual API framework

import time
import random
import math
import time
import os
import json
import time
import collections
import decimal
from decimal import Decimal

def floatify(l):
    if isinstance(l, (list, tuple)):
        return [floatify(v) for v in l]
    elif isinstance(l, collections.Mapping):
        return {floatify(k): floatify(l[k]) for k in l}
    try:
        return float(l)
    except:
        pass
    if isinstance(l, basestring) and len(l):
        return l
    return 0.0

def decimalify(l):
    if isinstance(l, (list, tuple)):
        return [decimalify(v) for v in l]
    elif isinstance(l, collections.Mapping):
        return {decimalify(k): decimalify(l[k]) for k in l}
    try:
        return Decimal(l)
    except:
        pass
    if isinstance(l, basestring) and len(l):
        return l
    return 0.0    

def mean(l):
    l = floatify(l)
    if getattr(l,'__len__',[].__len__)():
        if isinstance(l, (list, tuple)) and len(l[0])==2 and all(isinstance(v, (float, int)) for v in l[0]) :
            return float(sum(p * v for p, v in l))/sum(v for p, v in l)
        elif isinstance(l, collections.Mapping):
            return {k: mean(l[k]) for k in l}
        elif isinstance(l, (tuple, list)):
            return float(sum(l))/len(l) if len(l) else None
    return floatify(l)

def depthsum (bookside,lowest,highest):
    totalBTC,totalprice = (0,0)
    for order in bookside:
        if order.price >= lowest and order.price <= highest:
            totalBTC+=order.size
            totalprice+=order.price * order.size
    print 'There are %s total BTC between %s and %s' % (totalBTC,lowest,highest)
    return totalBTC,totalprice

def depthmatch (bookside,amount,lowest,highest):
    totalBTC,totalprice = (0,0)
    for order in bookside:
        if order.price >= lowest and order.price <= highest:
            totalBTC+=order.size
            totalprice+=order.price * order.size
            if amount <= totalBTC:
                print 'Your bid amount of %s BTC can be serviced by the first %s of orders' % (amount,totalBTC)
                break
    return totalBTC

def depthprice (bookside,amount,lowest,highest):
    totalBTC, totalprice, weightedavgprice = (0,0,0)
    for order in bookside:
        if order.price >= lowest and order.price <= highest:
            totalBTC+=order.size
            totalprice+=order.price * order.size
            if totalBTC >= amount:
                totalprice-=order.price*(totalBTC-amount)
                totalBTC=amount
                weightedavgprice=totalprice/totalBTC
    if weightedavgprice > 0:
        print '%s BTC @ $%.5f/BTC equals: $%.5f' % (totalBTC, weightedavgprice,totalprice)
        return totalBTC,weightedavgprice,totalprice
    else: 
        print 'Your order cannot be serviced.'    

def printbothbooks(asks,bids,howmany):
    for price in reversed(asks[:howmany]):
        print ' '*30,'$%s, %s -----ASK-->' % (str(price[0]),str(price[1]))
    print ' '*10,'|'*6,'First %s Orders' % howmany,'|'*6
    for price in bids[:howmany]:
        print '<--BID-----$%s, %s' % (str(price[0]),str(price[1]))


# spread trade function including Chunk Trade spread logic & Confirmation
def spread(exchangename,exchangeobject, side, size, price_lower, price_upper=100000, chunks=1):
    loop_price = float(price_lower)
    for x in range (0, int(chunks)):
        price_range = float(price_upper) - float(price_lower)
        price_chunk = Decimal(float(price_range)/ float(chunks)).quantize(Decimal('0.01'))
        chunk_size = Decimal(float(size) / float(chunks)).quantize(Decimal('0.00001'))
        if side == 0 or side == 'buy':
            print 'Buying...', "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
            if exchangename == 'bitfloor':
                print exchangename,' order going through'
                exchangeobject.order_new(side=side, size=chunk_size, price=loop_price)
            elif exchangename == 'mtgox':
                print exchangename,' order going through'
                exchangeobject.buy_btc(amount=chunk_size, price=loop_price)
        elif side == 1 or side == 'sell':
            print 'Selling...', "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
            if exchangename == 'bitfloor':
                print exchangename,' order going through'
                exchangeobject.order_new(side=side, size=chunk_size, price=loop_price) 
            elif exchangename == 'mtgox':
                print exchangename,' order going through'
                exchangeobject.sell_btc(amount=chunk_size, price=loop_price)
        loop_price += float(price_chunk)
        
def ppdict(d):
    #pretty print a dict
    print "-"*40
    try:
        for key in d.keys():
            print key,':',d[key]			
    except:
        print d
    return d

def pwdict(d,filename):
    #pretty write a dict
    f = open(filename,'w')
    try:
        for key in d.keys():
            f.write(key + " : " + str(d[key]) + "\n")
    except:
        pass
    f.write('\n' + '-'*80 + '\n')
    f.write(str(d))
    f.close()
    return d