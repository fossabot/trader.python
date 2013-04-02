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
from decimal import Decimal as D
import random

fullpath = os.path.dirname(os.path.realpath(__file__))
partialpath=os.path.join(fullpath + '\\..\\data\\')

#write the FULL depth to a log file
def writedepth(mtgox):
    with open(os.path.join(partialpath + "mtgox_fulldepth.txt"),'w') as f:
        print "Starting to download fulldepth from mtgox....",
        fulldepth = mtgox.get_fulldepth()
        depthvintage = str(time.time())
        f.write(depthvintage)
        f.write('\n')
        json.dump(fulldepth,f)
        f.close()
        print "Finished."
    return depthvintage,fulldepth
def readdepth():            
    with open(os.path.join(partialpath + "mtgox_fulldepth.txt"),'r') as f:
        everything = f.readlines()
    depthvintage = everything[0]
    fulldepth = json.loads(everything[1])
    return depthvintage, fulldepth

def updatedepthdata(mtgox,maxage=120):
    global depthvintage
    global fulldepth
    depthvintage,fulldepth = readdepth()
    if (time.time() - float(depthvintage)) > maxage :   # don't fetch from gox more often than every 2 min
        depthvintage,fulldepth = writedepth(mtgox)
    return depthvintage,fulldepth

def movavg(trades):
    #movingavg = sum(map(lambda x: x['price'], trades)) / len(trades)
    movingavg = sum(x['price'] for x in trades) / len(trades)       #uses list comprehension instead of a map and lambda
    return movingavg

#return the last N (window) lines of a file, ie: linux's tail command"
def tail(f, window=20):
    BUFSIZ = 1024
    f.seek(0, 2)
    bytes = f.tell()
    size = window
    block = -1
    data = []
    while size > 0 and bytes > 0:
        if (bytes - BUFSIZ > 0):
            # Seek back one whole BUFSIZ
            f.seek(block*BUFSIZ, 2)
            # read BUFFER
            data.append(f.read(BUFSIZ))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            data.append(f.read(bytes))
        linesFound = data[-1].count('\n')
        size -= linesFound
        bytes -= BUFSIZ
        block -= 1
    return '\n'.join(''.join(data).splitlines()[-window:])

#turn a whole list or tuple into a float
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

#turn a whole list or tuple into a decimal
def decimalify(l):
    if isinstance(l, (list, tuple)):
        return [decimalify(v) for v in l]
    elif isinstance(l, collections.Mapping):
        return {decimalify(k): decimalify(l[k]) for k in l}
    try:
        return D(l)
    except:
        pass
    if isinstance(l, basestring) and len(l):
        return l
    return 0.0    

#get the mean of an entire list or tuple
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

def average(s): return sum(s) * 1.0 / len(s)

def variance(thing,avg):
    return map(lambda x: (x - avg)**2, thing)

def stddev(x):
    import math
    return math.sqrt(average(x))

def obip(mtgox,amount,isUSD='BTC'):
    """Order book implied price. Weighted avg price of BTC <width> up and down from the spread."""
    """usage: obip(mtgoxobject,amount,"USD"/"BTC"(optional))"""
    updatedepthdata(mtgox)
    amount = float(amount)
    s=fulldepth["data"]['asks']
    b=fulldepth["data"]['bids']
    s=floatify(s)
    b=floatify(b)
    b.reverse()
    
    def do_obip(l,amount,isUSD='BTC'):
        totalBTC, totalprice = (0,0)
        if isUSD=='BTC':
            for x in l:
                if totalBTC < amount:
                    totalBTC+=x['amount']
                    totalprice+=x['price'] * x['amount']
                    if totalBTC >= amount:
                        totalprice-=x['price']*(totalBTC-amount)
                        totalBTC=amount
                        obip=totalprice/totalBTC
        else:
            for x in l:
                if totalprice < amount:
                    totalBTC+=x['amount']
                    totalprice+=x['price'] * x['amount']
                    if totalprice >= amount:
                        overBTC = ((totalprice-amount) / x['price'])
                        totalBTC -= overBTC
                        totalprice -= x['price'] * overBTC
                        obip=totalprice/totalBTC
        return obip,totalBTC

    obips,sbtc = do_obip(s,amount,isUSD)
    obipb,bbtc = do_obip(b,amount,isUSD)
    obip = (obips+obipb)/2.0 
    if isUSD=='USD':
        print "The ask side was: %s BTC. The bid side was %s BTC." % (sbtc,bbtc)
    print "The ask side OBIP was: $%.5f. The bid side OBIP was: $%.5f" % (obips,obipb)
    print "The weighted average price(OBIP) of BTC, %s %s up and down from the spread is:" % (amount,isUSD),
    print "$%.5f USD. Data vintage: %.2f seconds."  % (obip,(time.time() - float(depthvintage)))

#calculate and print the total BTC between price A and B
def depthsumrange (bookside,lowest=1,highest=100):
    """Usage is: bookside(Book object) lowest(optional) highest(optional)"""
    totalBTC,totalprice = (0,0)
    for order in bookside:
        if order.price >= lowest and order.price <= highest:
            totalBTC+=order.size
            totalprice+=order.price * order.size
    print 'There are %s BTC total between $%s and $%s' % (totalBTC,lowest,highest)
    return totalBTC,totalprice

#match any order to the opposite site of the order book (ie: if buying find a seller) - market order
#given the amount of BTC and price range check to see if it can be filled as a market order
def depthmatch (bookside,amount,lowest,highest):
    """Usage is: bookside(Book object) amount lowest highest"""
    totalBTC,totalprice = depthsumrange(bookside,lowest,highest)
    if amount <= totalBTC:
        print "Your %s BTC is available from a total of: %s BTC" % (amount,totalBTC)
    else:
        print "This amount %s BTC is not available between %s and %s" % (amount,lowest,highest)
    return totalBTC

#match any order to the opposite side of the order book (ie: if selling find a buyer) - market order
#calculate the total price of the order and the average weighted price of each bitcoin 
def depthprice (bookside,amount,lowest,highest):
    """Usage is: bookside(Book object) amount lowest highest"""
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

#print the order books out to howmany length you want
def printbothbooks(asks,bids,howmany):
    for order in reversed(asks[:howmany]):
        pcstr = str(order[0])
        szstr = str(order[1])
        if len(szstr) <= 5:
            szstr += "   "
        print ' '*34,'$%s,\t%s  \t-----ASK-->' % (pcstr,szstr)
    print ' '*15,'|'*9,'First %s Orders' % howmany,'|'*9
    for order in bids[:howmany]:
        pcstr = str(order[0])
        szstr = str(order[1])        
        print '<--BID-----$%s,\t%s' % (pcstr,szstr)

def printOrderBooks(asks,bids,howmany=15):
    for order in reversed(asks[:howmany]):
        pcstr = str(order.price/1E5)
        szstr = str(order.volume/1E8)
        if len(szstr) <= 5:
            szstr += "   "
        print ' '*34,'$%s,\t%s  \t-----ASK-->' % (pcstr,szstr)
    print ' '*15,'|'*9,'First %s Orders' % howmany,'|'*9
    for order in bids[:howmany]:
        pcstr = str(order.price/1E5)
        szstr = str(order.volume/1E8)        
        print '<--BID-----$%s,\t%s' % (pcstr,szstr)        


# spread trade function including Chunk Trade spread logic & Confirmation
def spread(exchangename,exchangeobject, side, size, price_lower, price_upper=100000,chunks=1,dorandom='random',silent=False):
    """Sell some BTC between price A and price B of equal sized chunks"""
    """Format is sell amount(BTC) price_lower price_upper chunks(#)"""
    """ie:   sell 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks"""
    """Simple trade also allowed: (buy/sell) amount price"""
    """Added in some optional randomness to it"""
    orderids = []
    sidedict = {0:"Buy",1:"Sell","buy":"Buy","sell":"Sell"}
    mapdict = {"bitfloor":"order_id","mtgox":"oid"}
    randomnesstotal = 0
    loop_price = float(price_lower)
    price_range = float(price_upper) - float(price_lower)
    if exchangename == 'bitfloor':
        cPrec = '0.01'
        bPrec = '0.00001'
    elif exchangename == 'mtgox':
        cPrec = '0.00001'
        bPrec = '0.00000001'
    price_chunk = D(float(price_range)/ float(chunks)).quantize(D(cPrec))
    chunk_size = D(float(size) / float(chunks)).quantize(D(bPrec))
    for x in range (0, int(chunks)):
        randomchunk = chunk_size
        if dorandom.lower()=='random':
            if chunks > 1:
                if x+1 == int(chunks):
                    randomchunk -= randomnesstotal
                else:
                    randomness = D(D(random.random()) / D((random.random()*100))).quantize(D(bPrec))
                    randomnesstotal += randomness
                    randomchunk += randomness
        if silent == False:
            print '%sing... Chunk #%s = %s BTC @ $%s' % (sidedict[side],x+1,randomchunk,loop_price)
        if exchangename == 'bitfloor':
            result = exchangeobject.order_new(side=side, size=randomchunk, price=loop_price)
        elif exchangename == 'mtgox':
            result = {'buy':exchangeobject.buy_btc,'sell':exchangeobject.sell_btc}[side](amount=randomchunk, price=loop_price)            
        if result:
            if not("error" in result):
                orderids.append(result[mapdict[exchangename]])
        else:
            return
        if silent == False:
            if result:
                if not("error" in result):
                    print "Order submitted. orderID is: %s" % result[mapdict[exchangename]]
                elif "error" in result:
                    print "Order was submitted but failed because: %s" % result["error"]
            else:
                print "Order failed."

        loop_price += float(price_chunk)

    return orderids
        
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

def getSlope(values):
    points = []
    for i in range(len(values)):
      points.append({'x':i, 'y':values[i]})
    n = len(values)
    sx = sum([x['x'] for x in points])
    sy = sum([x['y'] for x in points])
    sxy = sum([x['x']*x['y'] for x in points])
    sxx = sum([x['x']*x['x'] for x in points])
    delta = (n*sxx)-(sx**2)
    if delta == 0:
      return UNDEFINED_SLOPE
    return ((n*sxy)-(sx*sy))/delta