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

class UserError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg
    def __str__(self):
        return self.errmsg

#For Market Orders (not limit)
# Checks market conditions
# Order X amount of BTC between price A and B
# optional Wait time (default to instant gratification)
#Checks exact price (total and per bitcoin) @ Market prices
#   by checking opposite Order Book depth for a given size and price range (lower to upper)
#   and alerts you if cannot be filled immediately, and lets you place a limit order instead
def markettrade(bookside,action,amount,lowest,highest,waittime=0):

    depthsumrange(bookside,lowest,highest)
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
        """(market order): buy size \n""" \
        """(limit order): buy size price \n""" \
        """(spread order): buy size price_lower price_upper chunks"""
        try:
            args = arg.split()
            newargs = tuple(floatify(args))
            if len(newargs) not in (1,3):
                spread('bitfloor',bitfloor, 0, *newargs)
            else:
                raise UserError
        except Exception as e:
            print "Invalid args given!!! Proper use is:"
            print "buy size price"
            print "buy size price_lower price_upper chunks"
            return
            
    def do_sell(self, arg):
        """(market order): sell size \n""" \
        """(limit order): sell size price \n""" \
        """(spread order): sell size price_lower price_upper chunks"""
        try:
            args = arg.split()
            newargs = tuple(floatify(args))
            if len(newargs) not in (1,3):
                spread('bitfloor',bitfloor, 1, *newargs)
            else:
                raise UserError
        except Exception as e:
                print "Invalid args given!!! Proper use is:"
                print "sell size price"
                print "sell size price_lower price_upper chunks"
                return

    def do_marketbuy(self, arg):
        """working on new markettrade buy function"""
        """usage: amount lowprice highprice"""
        entirebook = refreshbook()
        try:
            args = arg.split()
            newargs = tuple(decimalify(args))
            side = entirebook.asks
            markettrade(side,'buy',*newargs)
        except Exception as e:
            print "Invalid args given. Proper use is: "
            self.onecmd('help marketbuy')
            return

    def do_marketsell(self, arg):
        """working on new markettrade sell function"""
        """usage: amount lowprice highprice"""
        entirebook = refreshbook()
        try:
            args = arg.split()
            newargs = tuple(decimalify(args))
            side = entirebook.bids
            side.reverse()
            markettrade(side,'buy',*newargs)    
        except Exception as e:
            print "Invalid args given. Proper use is: "
            self.onecmd('help marketsell')
            return
        
    def do_sellwhileaway(self,arg):
        """Check balance every 60 seconds for <amount> and once we have received it, sell! But only for more than <price>."""
        """Usage: amount price"""
        args = arg.split()
        amount,price = tuple(floatify(args))
        #seed initial balance data so we can check it during first run of the while loop
        balance = floatify(bitfloor.accounts())
        #seed the last price just in case we have the money already and we never use the while loop
        last = float(bitfloor.ticker()['price'])
        while balance[0]['amount'] < amount:
            balance = floatify(bitfloor.accounts())
            last = float(bitfloor.ticker()['price'])
            print 'Your balance is %r BTC and $%.2f USD ' % (balance[0]['amount'],balance[1]['amount'])
            print 'Account Value: $%.2f @ Last BTC Price of %.2f' % (balance[0]['amount']*last+balance[1]['amount'],last)
            time.sleep(60)
        if last > price:
            spread('bitfloor',bitfloor,1,balance[0]['amount'],last,last+1,2)
    def do_ticker(self,arg):
        """Print the entire ticker out or use one of the following options:\n""" \
        """[--buy|--sell|--last|--vol|--low|--high]"""
        last = floatify(bitfloor.ticker()['price'])
        dayinfo = floatify(bitfloor.dayinfo())
        low,high,vol = dayinfo['low'],dayinfo['high'],dayinfo['volume']
        book = floatify(bitfloor.book())
        buy, sell = book['bid'][0],book['ask'][0]
        if not arg:
            print "BTCUSD ticker | Best bid: %.2f, Best ask: %.2f, Bid-ask spread: %.2f, Last trade: %.2f, " \
                "24 hour volume: %d, 24 hour low: %.2f, 24 hour high: %.2f" % (buy,sell,sell-buy,last,vol,low,high)
        else:
            try:
                print "BTCUSD ticker | %s = %s" % (arg,ticker[arg])
            except:
                print "Invalid args. Expecting a valid ticker subkey."
                self.onecmd('help ticker')
    def do_balance(self,arg):
        """Shows your current account balance and value of your portfolio based on last ticker price"""
        balance = floatify(bitfloor.accounts())
        last = float(bitfloor.ticker()['price'])
        print 'Your balance is %r BTC and $%.2f USD ' % (balance[0]['amount'],balance[1]['amount'])
        print 'Account Value: $%.2f @ Last BTC Price of %.2f' % (balance[0]['amount']*last+balance[1]['amount'],last)
    def do_book(self,size):
        """Download and print the order book of current bids and asks of depth $size"""
        printorderbook(size)      
    def do_orders(self,arg):
        """Print a list of all your open orders"""
        time.sleep(1)
        orders = bitfloor.orders()
        for order in orders:
            ordertype="Sell" if order['side']==1 else "Buy"
            print ordertype,'order %r  Price $%.5f @ Amount: %.5f' % (str(order['timestamp']),float(order['price']),float(order['size']))
    def do_cancelall(self,arg):
        """Cancel every single order you have on the books"""
        bitfloor.cancel_all()
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
