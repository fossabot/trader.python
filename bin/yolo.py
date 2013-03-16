#!/usr/bin/env python
# Created by genBTC 3/9/2013
# Checks market conditions
# Order X amount of BTC between price A and B
# optional Wait time (default to instant gratification)


import bitfloor	#lib/args.py modified to use product 1 & bitfloor.json file
import cmd
import time
from common import *
from book import *

#this variable goes into args.py and will pass any API calls defined in the bitfloor.py RAPI
bitfloor = bitfloor.get_rapi()

def trade(entirebook,amount,lower,upper,waittime=0):
    totalBTC, totalprice, bidcounter, weightedavgprice, counter = (0,0,0,0,0)
    for price in entirebook:
        if price[0] >= lower:
            totalBTC+=price[1]
            totalprice+=price[0]*price[1]
            if totalBTC >= amount:
                totalprice-=price[0]*(totalBTC-amount)
                print 'There are %r BTC between %r and %r' % (totalBTC,lower,upper)
                print 'Your bid amount of %r BTC can be serviced by the first %r of orders' % (amount,totalBTC)
                totalBTC=amount
                weightedavgprice=totalprice/totalBTC
                break
    #time.sleep(float(waittime))
    if totalBTC == 0:
        print 'Your order cannot be serviced.'
    else:
        print '%r BTC @ $%.3f per each BTC is $%.3f' % (totalBTC, weightedavgprice,totalprice)

def refreshbook():
    #get the entire Lvl 2 order book    
    entirebook = Book.parse(bitfloor.book(2),True)
    #sort it
    entirebook.sort()
    return entirebook

#start printing part of the order book (first 15 asks and 15 bids)
def printorderbook(size):
    entirebook = refreshbook()
    #start printing part of the order book (first 15 asks and 15 bids)
    if size is '':
        uglyprintbooks(entirebook.asks,entirebook.bids,15)      #default to 15 if size is not given
    else:
        uglyprintbooks(entirebook.asks,entirebook.bids,int(size))   #otherwise use the size from the arguments
        
#some ideas
# if trying to buy start from lowerprice, check ask order book, buy if an order on order book is lower than lowerprice
#mtgox is @ 47.5 , you want to buy @ 47-46, you say "Buy 47" 
# NOT COMPLETE> SOMETHING IS TOTALLY WRONG WITH THIS FILE YOU CAUGHT ME IN THE MIDDLE OF IT
#if trying to sell start from higherprice, put higherprice on orderbook regardless, 

class Shell(cmd.Cmd):
    def emptyline(self):      
        pass                #Do nothing on empty input line instead of re-executing the last command
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'Bitfloor CMD>'           # The prompt for a new user input command
        self.use_rawinput = False
        self.onecmd('help')

	#start printing first 15 asks and 15 bids of the order book
    printorderbook(15)
    
    #give a little user interface
    print 'Press Ctrl+Z to exit gracefully or  Ctrl+C to force quit'
    print ' '
    prompt = '(buy|sell, amount, lower, upper, wait) '

	#pass arguments back up to trade() function
    def do_sell(self, arg):
        entirebook = refreshbook()
        try:
            amount, lower, upper, waittime = arg.split()
            amount = float(amount)
            lower = float(lower)
            upper = float(upper)
            waittime = float(waittime)
        except:
            print "Invalid arg {1}, expected amount price".format(arg)        
        trade(entirebook.asks,amount,lower,upper,waittime)
    def do_buy(self, arg):
        entirebook = refreshbook()
        try:
            amount, lower, upper, waittime = arg.split()
            amount = float(amount)
            lower = float(lower)
            upper = float(upper)
            waittime = float(waittime)
        except:
            print "Invalid arg {1}, expected amount price".format(arg)        
        trade(reversed(entirebook.bids),amount,lower,upper,waittime)

    def do_book(self,size):
        printorderbook(size)
#exit out if Ctrl+Z is pressed
    def do_exit(self,arg):      #standard way to exit
        """Exits the program"""
        print '\nSession Terminating.......'
        print 'Exiting......'
        return True
    def do_EOF(self,arg):        #exit out if Ctrl+Z is pressed
        """Exits the program"""
        return True
    def help_help(self):
        print 'Prints the help screen'

Shell().cmdloop()
