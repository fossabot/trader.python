#!/usr/bin/env python
# Created by genBTC 3/8/2013
# adds a multitude of orders between price A and price B of sized chunks

import args	#lib/args.py modified to use product 1 & bitfloor file
import cmd
import time
from decimal import Decimal
from common import *

bitfloor = args.get_rapi()
        
#start printing part of the order book (first 15 asks and 15 bids)
def printorderbook(size):
    #get the entire Lvl 2 order book    
    entirebook = floatify(bitfloor.book(2))
    if size is '':
        uglyprintbooks(entirebook['asks'],entirebook['bids'],15)      #default to 15 if size is not given
    else:
        uglyprintbooks(entirebook['asks'],entirebook['bids'],int(size))   #otherwise use the size that was given after calling book        
        
#give a little user interface
    print 'Press Ctrl+Z to exit gracefully or  Ctrl+C to force quit'
    print 'Typing book will show the order book again'
    print 'Typing orders will show your current open orders'
    print 'Typing cancelall will cancel every single open order'
    print 'Typing help will show you the list of commands'
    print 'trade example: '
    print '   buy 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks'
    print ' '
    
class Shell(cmd.Cmd):
    def emptyline(self):      
        pass                #Do nothing on empty input line instead of re-executing the last command
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'Bitfloor CMD>'   # The prompt for a new user input command
        self.use_rawinput = False
        self.onecmd('help')
    #start out by printing the order book and the instructions
    printorderbook(15)

    def do_buy(self, arg):
        try:        #pass arguments back up to spread() function
            size, price_lower, price_upper, chunks = arg.split()
            spread('bitfloor',bitfloor, 0, size, price_lower, price_upper, chunks)
        except:
            try:
                size,price_lower = arg.split()
                spread('bitfloor',bitfloor, 0, size, price_lower)
            except:
                print "Invalid args given. Expecting: size price"
        
            
    def do_sell(self, arg):
        try:
            size, price_lower, price_upper, chunks = arg.split()
            try:
                spread('bitfloor',bitfloor, 1, size, price_lower, price_upper, chunks)
            except:
                print 'Trade failed'
        except:
            try:
                size,price_lower = arg.split()
                try:
                    spread('bitfloor',bitfloor, 1, size, price_lower)
                except:
                    print 'Trade failed'
            except:
                print "Invalid args given. Expecting: size price"
        

    def do_book(self,size):
        printorderbook(size)
        
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
