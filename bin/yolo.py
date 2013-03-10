#!/usr/bin/env python
# Created by genBTC 3/9/2013
# Checks market conditions
# Order X amount of BTC between price A and B
# optional Wait time (default to instant gratification)


import args	#lib/args.py modified to use product 1 & bitfloor.json file
import cmd
import time

#this variable goes into args.py and will pass any API calls defined in the bitfloor.py RAPI
bitfloor = args.get_rapi()

#get the entire Lvl 2 order book    
entirebook = bitfloor.entirebook()    

	# old trade function including Chunk Trade spread logic & Confirmation
	# def trade(side, amount, price_lower, price_upper, chunks):
    # loop_price = float(price_lower)
    # for x in range (0, int(chunks)):
        # price_range = float(price_upper) - float(price_lower)
        # price_chunk = float(price_range)/ float(chunks)
        # chunk_amount = float(amount) / float(chunks)
        # print "Chunk # ",x+1," = ",chunk_amount," BTC @ $", loop_price
        # print bitfloor.order_new(side=side, amount=chunk_amount, price=loop_price)
        # loop_price += price_chunk


def tradebids(side,amount,lower,upper,waittime=0):
    totalBTC=0
    totalprice=0
    bidcounter=0
    weightedavgprice=0
    counter=0
    for bidprice in entirebook['bids'][:10]:
        totalBTC+=float(bidprice[1])
        totalprice+=float(bidprice[0])*float(bidprice[1])
        if totalBTC >= float(amount):
            totalprice-=(float(bidprice[0])*(totalBTC-float(amount)))
            print 'Your bid amount of %r BTC can be serviced by the first %r of orders' % (float(amount),totalBTC)
            totalBTC= float(amount)
            break
        counter+=1
    weightedavgprice=totalprice/totalBTC
    time.sleep(float(waittime))
    print '%r BTC @ $%r per each BTC is $%r' % (totalBTC, weightedavgprice,totalprice)

def tradeasks(side,amount,lower,upper,waittime=0):
    totalBTC=0
    totalprice=0
    bidcounter=0
    weightedavgprice=0
    counter=0
    for askprice in reversed(entirebook['asks'][:10]):
        totalBTC+=float(askprice[1])
        totalprice+=float(askprice[0])*float(askprice[1])
        if totalBTC >= float(amount):
            totalprice-=(float(askprice[0])*(totalBTC-float(amount)))
            print 'Your ask amount of %r BTC can be serviced by the first %r of orders' % (float(amount),totalBTC)
            totalBTC= float(amount)
            break
        counter+=1
    weightedavgprice=totalprice/totalBTC
    time.sleep(float(waittime))
    print '%r BTC @ $%r per each BTC is $%r' % (totalBTC, weightedavgprice,totalprice)
 # if trying to buy start from lowerprice, check ask order book, buy if an order on order book is lower than lowerprice


#mtgox is @ 47.5 , you want to buy @ 47-46, you say "Buy 47" 
# NOT COMPLETE> SOMETHING IS TOTALLY WRONG WITH THIS FILE YOU CAUGHT ME IN THE MIDDLE OF IT
#if trying to sell start from higherprice, put higherprice on orderbook regardless, 
def addupasks(side,amount,lower,upper,waittime=0):
    totalBTC=0
    totalprice=0
    bidcounter=0
    weightedavgprice=0
    counter=0
    for askprice in reversed(entirebook['asks'][:10]):
        totalprice+=float(askprice[0])*float(askprice[1])
        totalBTC+=float(askprice[1])
        weightedavgprice=totalprice/totalBTC
        counter+=1
    time.sleep(float(waittime))
    print '$', totalprice, totalBTC, ' BTC', weightedavgprice, ' for ASKS'


class Shell(cmd.Cmd):
    def emptyline(self):
        pass

	#start printing part of the order book (first 10 asks and 10 bids)
    for askprice in reversed(entirebook['asks'][:10]):
        print '                              $',askprice[0][:-6],askprice[1][:-3], '--ASK-->'
    
    print '                    |||||||||||'

    for bidprice in entirebook['bids'][:10]:
        print '<--BID--$',bidprice[0][:-6],bidprice[1][:-3]    
    
#give a little user interface
    print 'Press Ctrl+Z to exit gracefully or  Ctrl+C to force quit'
    print ' '
    prompt = '(buy|sell, amount, lower, upper, wait) '

	#pass arguments back up to trade() function
    def do_sell(self, arg):
        try:
            amount, lower, upper, wait = arg.split()
        except:
            print "Invalid arg {1}, expected amount price".format(side, arg)        
        #trade(1, amount, lower, upper, wait)
        tradeasks(1,amount,lower,upper,wait)
    def do_buy(self, arg):
        try:
            amount, lower, upper, wait = arg.split()
        except:
            print "Invalid arg {1}, expected amount price".format(side, arg)        
        #trade(0, amount, lower, upper, wait)
        tradebids(0,amount,lower,upper,wait)

#exit out if Ctrl+Z is pressed
    def do_EOF(self, arg):
        print "Any Trades have been Executed, Session Terminating......."
        return True

Shell().cmdloop()
