#!/usr/bin/env python
# bitfloor_client.py
# Created by genBTC 3/8/2013 updated 3/17/2013
# Universal Client for all things bitfloor
# Functionality _should_ be listed in README

#import args	    #lib/args.py modified to use product 1 & bitfloor file
import bitfloor     #args was phased out and get_rapi() was moved to bitfloor and config.json moved to data/
import cmd
import time
from decimal import Decimal
from common import *
from book import *

bitfloor = bitfloor.get_rapi()


#For Market Orders (not limit)
# Checks market conditions
# Order X amount of BTC between price A and B
# optional Wait time (default to instant gratification)
#Checks exact price (total and per bitcoin) @ Market prices
#   by checking opposite Order Book depth for a given size and price range (lower to upper)
#   and alerts you if cannot be filled immediately, and lets you place a limit order instead
def markettrade(bookside,action,amount,lowest,highest,waittime=0):

    depthsum(bookside,lowest,highest)
    depthmatch(bookside,amount,lowest,highest)

    if action == 'sell':
        if lowest > bookside[-1].price and highest:
            print "Market order impossible, price too high."
            print "Your Lowest sell price of $%s is higher than the highest bid of $%s" % (lowest,bookside[-1].price)
            print "Place [L]imit order on the books for later?   or......"
            print "Sell to the [H]ighest Bidder? Or [C]ancel?"
            print "[L]imit Order / [H]ighest Bidder / [C]ancel: "
            choice = raw_input()
            if choice =='H' or choice == 'h' or choice =='B' or choice =='b':
                pass                 #sell_on_mtgox_i_forgot_the_command_

    if action == 'buy':
        if highest < bookside[0].price:
            print "Suboptimal behavior detected."
            print "You are trying to buy and your highest buy price is lower than the lowest ask is."
            print "There are cheaper bitcoins available than ", highest
            print "[P]roceed / [C]ancel: "
            choice = raw_input()
            if choice =='P' or choice =='Proceed':
                pass                 #buy_on_mtgox_i_forgot_the_command_

    depthprice(bookside,amount,lowest,highest)

    #time.sleep(Decimal(waittime))

#some ideas
# if trying to buy start from lowerprice, check ask order book, buy if an order on order book is lower than lowerprice
#mtgox is @ 47.5 , you want to buy @ 47-46, you say "Buy 47" 
#if trying to sell start from higherprice, put higherprice on orderbook regardless, 
# FILE IS MORE COMPLETE THAN IT WAS



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
        printbothbooks(entirebook.asks,entirebook.bids,15)      #default to 15 if size is not given
    else:
        printbothbooks(entirebook.asks,entirebook.bids,int(size))   #otherwise use the size from the arguments
      
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
    #give a little user interface
    print 'Press Ctrl+Z to exit gracefully or  Ctrl+C to force quit'
    print 'Typing book will show the order book again'
    print 'Typing orders will show your current open orders'
    print 'Typing cancelall will cancel every single open order'
    print 'Typing help will show you the list of commands'
    print 'trade example: '
    print '   buy 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks'
    print ' '

    def do_buy(self, arg):
        try:        #pass arguments back up to spread() function
            size, price_lower, price_upper, chunks = arg.split()
            # adds a multitude of orders between price A and price B of sized chunks
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
                # adds a multitude of orders between price A and price B of sized chunks
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

    def do_marketbuy(self, arg):
        entirebook = refreshbook()
        try:
            amount, lower, upper, waittime = arg.split()
            amount = Decimal(amount)
            lower = Decimal(lower)
            upper = Decimal(upper)
            waittime = Decimal(waittime)
            side = entirebook.asks
        except:
            print "Invalid arg {1}, expected amount price".format(arg)        
        markettrade(side,'buy',amount,lower,upper,waittime)


    def do_marketsell(self, arg):
        entirebook = refreshbook()
        try:
            amount, lower, upper, waittime = arg.split()
            amount = Decimal(amount)
            lower = Decimal(lower)
            upper = Decimal(upper)
            waittime = Decimal(waittime)
            side = entirebook.bids
            side.reverse()
        except:
            print "Invalid arg {1}, expected amount price".format(arg)    
        markettrade(side,'sell',amount,lower,upper,waittime)    
        

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
        orders = bitfloor.orders()
        if orders:
            bitfloor.cancel_all()
            print "All Orders have been Cancelled!!!!!"
        else:
            print "No Orders found!!"

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
