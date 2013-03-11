#!/usr/bin/env python
# Created by genBTC 3/10/2013
# adds a multitude of orders between price A and price B of sized chunks on Mtgox.

import mtgoxhmac
import cmd
import httplib
import urllib
import json
import json_ascii
import hashlib
import hmac
import time
import unlock_api_key
from book import Book, Order

mtgox = mtgoxhmac.Client()

# trade function including Chunk Trade spread logic & Confirmation
def trade(side, size, price_lower, price_upper, chunks):
    loop_price = float(price_lower)
    for x in range (0, int(chunks)):
        price_range = float(price_upper) - float(price_lower)
        price_chunk = float(price_range)/ float(chunks)
        chunk_size = float(size) / float(chunks)
        print "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
        print bitfloor.order_new(side=side, size=chunk_size, price=loop_price)
        loop_price += price_chunk

#get 24 hour trade history - cached
alltrades=mtgox.get_trades()
#get current trade depth book
entirebook=Book.parse(mtgox.get_depth())
entirebook.sort()
#print type(entirebook), type(mtgoxdepth)
#print mtgoxdepth
#display info like account balance & funds
#print mtgox.get_info()
#
# def trade(side, arg):
    # try:
        # size, price = arg.split()
    # except:
        # print "Invalid arg {1}, expected size price".format(side, arg)
    # print mtgox.order_new(side=side, size=size, price=price)
    # time.sleep(4)
    # orders = mtgox.get_orders()
    # print orders['order_id']
def trade(side, size, price_lower, price_upper, chunks):
    loop_price = float(price_lower)
    for x in range (0, int(chunks)):
        price_range = float(price_upper) - float(price_lower)
        price_chunk = float(price_range)/ float(chunks)
        chunk_size = float(size) / float(chunks)
        print "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
        if side == 'buy':
            print mtgox.buy_btc(amount=chunk_size, price=loop_price)
        else:
            print mtgox.sell_btc(amount=chunk_size, price=loop_price) 
        loop_price += price_chunk
    
        
class Shell(cmd.Cmd):
    def emptyline(self):
        pass
#get the entire Lvl 2 order book    
    #entirebook = bitfloor.entirebook()    
 
#start printing part of the order book (first 10 asks and 10 bids)
    for o in reversed(entirebook.asks[:15]):
        print '                              $',o.price,o.size, '--ASK-->'
    
    # print '                    |||||||||||'

    for o in entirebook.bids[:15]:
       print '<--BID--$',o.price,o.size
    
#give a little user interface
    print 'Press Ctrl+Z to exit gracefully or  Ctrl+C to force quit'
    print ' '
    prompt = '(buy|sell size price_lower price_upper #chunks) '

#pass arguments back up to trade() function
    def do_sell(self, arg):
        try:
            size, price_lower, price_upper, chunks = arg.split()
        except:
            print "Invalid arg {1}, expected size price".format(self, arg)        
        trade(self, size, price_lower, price_upper, chunks)

    def do_buy(self, arg):
        try:
            size, price_lower, price_upper, chunks = arg.split()
        except:
            print "Invalid arg {1}, expected size price".format(self, arg)        
        trade(self, size, price_lower, price_upper, chunks)

#exit out if Ctrl+Z is pressed
    def do_EOF(self, arg):
        print "Any Trades have been Executed, Session Terminating......."
        return True

Shell().cmdloop()
