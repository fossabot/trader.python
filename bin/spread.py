#!/usr/bin/env python
# Created by genBTC 3/8/2013
# adds a multitude of orders between price A and price B of sized chunks

import args	#lib/args.py modified to use product 1 & bitfloor file
import cmd

bitfloor = args.get_rapi()

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


class Shell(cmd.Cmd):
    def emptyline(self):
        pass
#get the entire Lvl 2 order book    
    entirebook = bitfloor.entirebook()    
 
#start printing part of the order book (first 10 asks and 10 bids)
    for askprice in reversed(entirebook['asks'][:10]):
        print '                              $',askprice[0][:-6],askprice[1][:-3], '--ASK-->'
    
    print '                    |||||||||||'

    for bidprice in entirebook['bids'][:10]:
        print '<--BID--$',bidprice[0][:-6],bidprice[1][:-3]    
    
#give a little user interface
    print 'Press Ctrl+Z to exit gracefully or  Ctrl+C to force quit'
    print ' '
    prompt = '(buy|sell size price_lower price_upper #chunks) '

#pass arguments back up to trade() function
    def do_sell(self, arg):
        try:
            size, price_lower, price_upper, chunks = arg.split()
        except:
            print "Invalid arg {1}, expected size price".format(side, arg)        
        trade(1, size, price_lower, price_upper, chunks)

    def do_buy(self, arg):
        try:
            size, price_lower, price_upper, chunks = arg.split()
        except:
            print "Invalid arg {1}, expected size price".format(side, arg)        
        trade(0, size, price_lower, price_upper, chunks)

#exit out if Ctrl+Z is pressed
    def do_EOF(self, arg):
        print "Any Trades have been Executed, Session Terminating......."
        return True

Shell().cmdloop()
