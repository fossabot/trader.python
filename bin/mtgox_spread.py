#!/usr/bin/env python
# Created by genBTC 3/10/2013
# adds a multitude of orders between price A and price B of sized chunks on Mtgox.

import mtgoxhmac
import readline
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

#get 24 hour trade history - cached
alltrades=mtgox.get_trades()
#get current trade depth book
entirebook=Book.parse(mtgox.get_depth())
entirebook.sort()
#display info like account balance & funds
#print mtgox.get_info()

# trade function including Chunk Trade spread logic
def trade(side, price_lower, price_upper, size, chunks):
    loop_price = float(price_lower)
    for x in range (0, int(chunks)):
        price_range = float(price_upper) - float(price_lower)
        price_chunk = float(price_range)/ float(chunks)
        chunk_size = float(size) / float(chunks)
        if side == 'buy':
            print 'Buying...', "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
            mtgox.buy_btc(amount=chunk_size, price=loop_price)
        elif side == 'sell' :
            print 'Selling...', "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
            mtgox.sell_btc(amount=chunk_size, price=loop_price) 
        loop_price += price_chunk
 
#start printing part of the order book (first 10 asks and 10 bids)
def printorderbook():
    for o in reversed(entirebook.asks[:15]):
        print '                              $',o.price,o.size, '--ASK-->'
    print '                    |||||||||||'
    for o in entirebook.bids[:15]:
        print '<--BID--$',o.price,o.size
#give a little user interface
    print 'Press Ctrl+Z to exit gracefully or  Ctrl+C to force quit'
    print 'Typing book will show the order book again'
    print 'Typing orders will show your current open orders'
    print 'trade example: '
    print '   buy 40 41 6.4 128 = buys 128 chunks totaling 6.4 BTC between $40 and $41'
    print ' '
    
class Shell(cmd.Cmd):
    def emptyline(self):
        pass
    #start out by printing the order book and the instructions
    printorderbook()
    #trading command prompt
    prompt = 'buy/sell, price_lower, price_upper, amount(BTC), chunks(#)'

#pass arguments back up to trade() function
    def do_buy(self, arg):
        try:
            price_lower, price_upper, size, chunks = arg.split()
        except:
            print "Invalid arg {1}, expected size price".format(size, price)        
        trade('buy', price_lower, price_upper, size, chunks)
 
    def do_sell(self, arg):
        try:
            price_lower, price_upper, size, chunks = arg.split()
        except:
            print "Invalid arg {1}, expected size price".format(size, price)        
        trade('sell', price_lower, price_upper, size, chunks)
        
    def do_book(self, arg):
        printorderbook()
        
    def do_orders(self,arg):
        time.sleep(1)
        orders = mtgox.get_orders()['orders']
        for order in orders:
            if order['status'] == 1:
                if order['type']== 1:
                    type="Sell"
                else:
                    type="Buy"
                print type,'order %r  Price $%.5f @ Amount: %.5f' % (str(order['priority']),float(order['price']),float(order['amount']))
            else:
                print type,'order %r Not enough Funds' % (str(order['priority']))

#exit out if Ctrl+Z is pressed
    def do_EOF(self, arg):
        print "Any Trades have been Executed, Session Terminating......."
        return True

Shell().cmdloop()
