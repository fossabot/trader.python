#!/usr/bin/env python
# bitfloor_client.py
# Created by genBTC 3/8/2013 updated 3/17/2013
# Universal Client for all things bitfloor
# Functionality _should_ be listed in README

#import args        #lib/args.py modified to use product 1 & bitfloor file
import bitfloor     #args was phased out and get_rapi() was moved to bitfloor and config.json moved to data/
import cmd
import time
from decimal import Decimal
from common import *
from book import *
import threading
import traceback

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
def printorderbook(size=15):
    entirebook = refreshbook()
    #start printing part of the order book (first 15 asks and 15 bids)
    printbothbooks(entirebook.asks,entirebook.bids,size)   #otherwise use the size from the arguments
      
class Shell(cmd.Cmd):
    def emptyline(self):      
        pass                #Do nothing on empty input line instead of re-executing the last command
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'Bitfloor CMD>'   # The prompt for a new user input command
        self.use_rawinput = False
        self.onecmd('help')
    #start out by printing the order book and the instructions
    printorderbook()
    #give a little user interface
    print 'Press Ctrl+Z to exit gracefully or  Ctrl+C to force quit'
    print 'Typing book will show the order book again'
    print 'Typing orders will show your current open orders'
    print 'Typing cancelall will cancel every single open order'
    print 'Typing help will show you the list of commands'
    print 'trade example: '
    print '   buy 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks'
    print ' '


    def do_liquidbot(self,arg):
        """incomplete - supposed to take advantage of the -0.1% provider bonus by placing linked buy/sell orders on the books (that wont be auto-completed)"""
        #make a pair of orders 30 cents below/above the 2nd highest/lowest bid/ask (safer, but less likely to work)
        def liquidthread(firstarg,stop_event):
            buyorderids = []
            sellorderids = []
            while(not stop_event.is_set()):
                entirebook = refreshbook()
                onaskbookprice = []
                onbidbookprice = []
                typedict = {0:"Buy",1:"Sell"}
                for ask in entirebook.asks:
                    onaskbookprice.append(float(ask.price))
                for bid in entirebook.bids:
                    onbidbookprice.append(float(bid.price))
                targetbid = onbidbookprice[1] - 0.30
                targetask = onaskbookprice[1] + 0.30
                while targetbid in onbidbookprice:
                    targetbid -= 0.01
                while targetask in onaskbookprice:
                    targetask += 0.01
                if len(buyorderids) == len(sellorderids) and not len(buyorderids) == 2:
                    buyorderids += spread('bitfloor',bitfloor,0,1,targetbid)
                    sellorderids += spread('bitfloor',bitfloor,1,1,targetask)
                else:
                    print "Nothing to do. Waiting on some action."
                stop_event.wait(35)
                orders = bitfloor.orders()
                allorders = buyorderids + sellorderids
                for x in allorders:
                    if not(x in str(orders)):
                        co = completedorder = bitfloor.order_info(x)
                        if "error" in co:
                            print "There was some kind of error retrieving the order information."
                        else:
                            print "%s order %s for %s BTC @ $%s has been %s!." % (typedict[co["side"]], co["order_id"],co["size"],co["price"],co["status"])
        def secondmethod(firstarg,stop_event):
            # make a pair of orders within 5 cents of the spread (not changing the spread) (still safe, less profit, more likely to work)
            buyorderids = []
            sellorderids = []
            while(not stop_event.is_set()):
                entirebook = refreshbook()
                onaskbookprice = []
                onbidbookprice = []
                typedict = {0:"Buy",1:"Sell"}
                for ask in entirebook.asks:
                    onaskbookprice.append(float(ask.price))
                for bid in entirebook.bids:
                    onbidbookprice.append(float(bid.price))
                targetbid = onbidbookprice[0] - 0.05
                targetask = onaskbookprice[0] + 0.05
                while targetbid in onbidbookprice:
                    targetbid -= 0.01
                while targetask in onaskbookprice:
                    targetask += 0.01                
                if len(buyorderids) < 1:
                    try:
                        buyorderids += spread('bitfloor',bitfloor,0,1,targetbid)
                        sellorderids += spread('bitfloor',bitfloor,1,1,targetask)
                    except:
                        traceback.exc_info()
                        bitfloor.cancel_all()
                else:
                    print "Nothing to do. Waiting on some action."
                    #check spread to see if we can go back to thirdmethod
                    spread = onaskbookprice[0] - onbidbookprice[0]
                    if spread >= 0.05:
                        thirdmethod(None,t1_stop)
                stop_event.wait(40)
                orders = bitfloor.orders()
                allorders = buyorderids + sellorderids
                for x in allorders:
                    if not(x in str(orders)):
                        co = completedorder = bitfloor.order_info(x)
                        if "error" in co:
                            print "There was some kind of error retrieving the order information."
                        else:
                            print "%s order %s for %s BTC @ $%s has been %s!." % (typedict[co["side"]], co["order_id"],co["size"],co["price"],co["status"])
        def thirdmethod(firstarg,stop_event):
            # make a pair of orders 1 cent ABOVE/BELOW the spread (DOES change the spread)(fairly risky, least profit per run, most likely to work)
            buyorderids = []
            sellorderids = []
            while(not stop_event.is_set()):
                entirebook = refreshbook()
                onaskbookprice = []
                onbidbookprice = []
                typedict = {0:"Buy",1:"Sell"}
                for ask in entirebook.asks:
                    onaskbookprice.append(float(ask.price))
                for bid in entirebook.bids:
                    onbidbookprice.append(float(bid.price))
                spread = onaskbookprice[0] - onbidbookprice[0]                    
                if spread < 0.05:
                    print "There is virtually no spread to take advantage of."
                    print "Trying second method:"
                    #default to method 2 if the spread fails (idealy we want to come back here and try again sometime.)
                    secondmethod(None,t1_stop)
                else:
                    while spread >= 0.05:
                        print "The spread was: %s" % spread
                        targetbid = onbidbookprice[0] + 0.01
                        targetask = onaskbookprice[0] - 0.01
                        #start eating into profits to find an uninhabited pricepoint
                        while targetbid in onbidbookprice and not(targetbid in onaskbookprice):
                            targetbid += 0.01
                        while targetask in onaskbookprice and not(targetbid in onaskbookprice):
                            targetask -= 0.01                
                        spread = targetask-targetbid
                        if len(buyorderids) < 1 and spread > 0.03:
                            try:
                                buyorderids += spread('bitfloor',bitfloor,0,1,targetbid)
                                sellorderids += spread('bitfloor',bitfloor,1,1,targetask)
                            except:
                                bitfloor.cancel_all()
                        elif spread < 0.03:
                            print "Spread was too low(%s) after checking which prices were inhabited by other people's orders." % spread
                        else:
                            print "Nothing to do. Waiting on some action."
                stop_event.wait(20)
                orders = bitfloor.orders()
                allorders = buyorderids + sellorderids
                for x in allorders:
                    if not(x in str(orders)):
                        co = completedorder = bitfloor.order_info(x)
                        if "error" in co:
                            print "There was some kind of error retrieving the order information."
                        else:
                            print "%s order %s for %s BTC @ $%s has been %s!." % (typedict[co["side"]], co["order_id"],co["size"],co["price"],co["status"])
                

        global t1_stop
        if arg == 'exit':
            print "Shutting down background thread..."
            t1_stop.set()
        else:
            t1_stop = threading.Event()
            thread1 = threading.Thread(target = thirdmethod, args=(None,t1_stop)).start()



    def do_buy(self, arg):
        """(limit order): buy size price \n""" \
        """(spread order): buy size price_lower price_upper chunks ("random")"""
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
        """(limit order): sell size price \n""" \
        """(spread order): sell size price_lower price_upper chunks("random")"""
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
        try:
            size = int(size)
            printorderbook(size)
        except:
            printorderbook()        
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
