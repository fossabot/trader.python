#!/usr/bin/env python
# Created by genBTC 3/8/2013
# adds a multitude of orders between price A and price B of sized chunks

import args	#lib/args.py modified to use product 1 & bitfloor file
import cmd
import time

bitfloor = args.get_rapi()

# trade function including Chunk Trade spread logic & Confirmation
def trade(side, price_lower, price_upper, size, chunks):
    loop_price = float(price_lower)
    for x in range (0, int(chunks)):
        price_range = float(price_upper) - float(price_lower)
        price_chunk = float(price_range)/ float(chunks)
        chunk_size = float(size) / float(chunks)
        if side == 0:
            print 'Buying...', "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
            bitfloor.order_new(side=side, size=chunk_size, price=loop_price)
        elif side == 1 :
            print 'Selling...', "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
            bitfloor.order_new(side=side, size=chunk_size, price=loop_price) 
        loop_price += price_chunk
        
#start printing part of the order book (first 10 asks and 10 bids)
def printorderbook():
    #get the entire Lvl 2 order book    
    entirebook = bitfloor.entirebook()
    for askprice in reversed(entirebook['asks'][:15]):
        print '                              $',askprice[0][:-6],askprice[1][:-3], '--ASK-->'
    print '                    |||||||||||'
    for bidprice in entirebook['bids'][:15]:
        print '<--BID--$',bidprice[0][:-6],bidprice[1][:-3]    
#give a little user interface
    print 'Press Ctrl+Z to exit gracefully or  Ctrl+C to force quit'
    print 'Typing book will show the order book again'
    print 'Typing orders will show your current open orders'
    print 'Typing cancelall will cancel every single open order'
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
            print "Invalid arg {1}, expected size price".format(side, arg)        
        trade(0,  price_lower, price_upper, size, chunks)
            
    def do_sell(self, arg):
        try:
            price_lower, price_upper, size, chunks = arg.split()
        except:
            print "Invalid arg {1}, expected size price".format(side, arg)        
        trade(1,  price_lower, price_upper, size, chunks)

    def do_book(self, arg):
        printorderbook()
        
    def do_orders(self,arg):
        time.sleep(1)
        orders = bitfloor.orders()
        for order in orders:
            if order['side']== 1:
                type="Sell"
            else:
                type="Buy"
            print type,'order %r  Price $%.5f @ Amount: %.5f' % (str(order['timestamp']),float(order['price']),float(order['size']))
    def do_cancelall(self,arg):
        bitfloor.cancel_all()
        print "All Orders have been Cancelled!!!!!"

#exit out if Ctrl+Z is pressed
    def do_EOF(self, arg):
        print "Any Trades have been Executed, Session Terminating......."
        return True

Shell().cmdloop()
