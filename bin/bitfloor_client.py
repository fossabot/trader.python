#!/usr/bin/env python
# bitfloor_client.py
# Created by genBTC 3/8/2013 updated 3/17/2013
# Universal Client for all things bitfloor
# Functionality _should_ be listed in README

#import args        #lib/args.py modified to use product 1 & bitfloor file
import bitfloorapi     #args was phased out and get_rapi() was moved to bitfloor and config.json moved to data/
import cmd
import time
from decimal import Decimal as D    #got annoyed at having to type Decimal every time.
from common import *
from book import *
import threading
import signal
import traceback
import logging
import sys


bitfloor = bitfloorapi.Client()
cPrec = '0.01'
bPrec = '0.00001'

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

    #time.sleep(D(waittime))

#some ideas
# if trying to buy start from lowerprice, check ask order book, buy if an order on order book is lower than lowerprice
#mtgox is @ 47.5 , you want to buy @ 47-46, you say "Buy 47" 
#if trying to sell start from higherprice, put higherprice on orderbook regardless, 

#get update the entire order book
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
      
#Console
class Shell(cmd.Cmd):
    def emptyline(self):      
        pass                #Do nothing on empty input line instead of re-executing the last command
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'Bitfloor CMD>'   # The prompt for a new user input command
        self.use_rawinput = False
        self.onecmd('help')
        
    #CTRL+C Handling
    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt as e:
            print "Press CTRL+C again to exit, or ENTER to continue."
            try:
                wantcontinue = raw_input()
            except KeyboardInterrupt:
                return self.do_exit(self)
            self.cmdloop()
               
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
        def liquidthread(firstarg,stop_event):
            # make a pair of orders 1 cent ABOVE/BELOW the spread (DOES change the spread)(fairly risky, price can change. least profit per run, most likely to work)
            # so far this works. needs a whole bunch more work though.

            class StreamToLogger(object):
               """Fake file-like stream object that redirects writes to a logger instance."""
               def __init__(self, logger, log_level=logging.DEBUG):
                  self.logger = logger
                  self.log_level = log_level
                  self.linebuf = ''
               def write(self, buf):
                  for line in buf.rstrip().splitlines():
                     self.logger.log(self.log_level, line.rstrip())

            logging.basicConfig(filename='liquidbotlog.txt'
                   ,filemode='a'
                   ,format='%(asctime)s: %(message)s'
                   ,datefmt='%m-%d %H:%M:%S'
                   ,level=logging.DEBUG
                   )

            stdout_logger = logging.getLogger('STDOUT')
            sl = StreamToLogger(stdout_logger, logging.DEBUG)
            stdout_logger.setLevel(logging.DEBUG)

            console_logger = logging.getLogger('')
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console_logger.addHandler(console)         
            # sys.stdout = sl
            # print "This is how I redirect and redisplay stdout to the logfile."
            # sys.stdout = sys.__stdout__
#pre inits
            TRADEAMOUNT = D('0.888')           #<--------- number of bitcoins to buy in each go.
            BUYMAXPRICE = D('1000.0')         #<------max price for buys 
            SELLMINPRICE = D('1.0')          #<------min price for sells
            buyorderids = []
            sellorderids = []
            allorders = []
            countbuys,countsells = 0,0
            amtbought,amtsold = 0,0
            countcycles = 0
            initcountbuys,initcountsells = 0,0       #   <---------Modify these numbers if you want it to make up for past runs in a certain way
            numbought,numsold = initcountbuys,initcountsells       
            typedict = {0:"Buy",1:"Sell"}
            logging.info("Liquidbot started.")
            successes = open("successlog.txt",'a')
            successes.write("Began at %s" % time.time())
            #TRADEAMOUNT = raw_input("How much do you want the bot to trade per order:  ")
            while(not stop_event.is_set()):
#loop inits                 
                entirebook = refreshbook()
                onaskbookprice = []
                onbidbookprice = []                
                bookdict = {0:onbidbookprice,1:onaskbookprice}
                iddicts = {0:buyorderids,1:sellorderids}
                for ask in entirebook.asks:
                    onaskbookprice.append(ask.price)
                for bid in entirebook.bids:
                    onbidbookprice.append(bid.price)
                lowask = onaskbookprice[0]
                highbid = onbidbookprice[0]             
                spr = lowask - highbid
                orders = bitfloor.orders()
                allorders = buyorderids + sellorderids
#order mgmt
                for x in allorders:
                    co = bitfloor.order_info(x)
                    if co["status"]=='open':
                        v0 = D(str(co["price"]))
                        v1 = bookdict[co["side"]][0]
                        v2 = bookdict[co["side"]][1]
                        s = co["side"]
                        if (s==0 and (v0<v1 and v0<v2)) or (s==1 and (v0>v1 and v0>v2)):        #shorthand to Check that we have the best (or 2nd best) bid/ask
                            sys.stdout = sl
                            logging.debug(bitfloor.order_cancel(x))
                            logging.debug("Order ID Listed above = CANCELLED")
                            countbuys = initcountbuys+numbought
                            countsells = initcountsells+numsold
                            sys.stdout = sys.__stdout__
                            allorders.remove(x)
                            iddicts[co["side"]].remove(x)
                    if not(x in str(orders)):
                        if "error" in co:
                            logging.warning("There was some kind of error retrieving the order information.")
                        elif "status" in co:
                            if co["status"]=='filled':
                                print "\n"
                                size = D(co["size"])
                                price = D(co["price"])
                                result = size * price
                                logging.info("Success!! %s %s @ $ %s for %s BTC = %s <<<<<<><-><>>>>>>" % (typedict[co["side"]],co["status"],price,size,result))
                                if co["side"]==0:
                                    numbought += 1
                                    amtbought += size
                                else:
                                    numsold += 1
                                    amtsold += size
                                logging.debug("Size of all buys: %s . Size of all sells: %s ." % (amtbought,amtsold))
                                successes.write("%s %s @ %s = %s , %s %s" % (typedict[co["side"]],size,price,result,amtbought,amtsold))
                                successes.flush()
                            if co["status"]=='cancelled':
                                logging.debug("%s order %s for %s BTC @ $%s has been %s!." % (typedict[co["side"]], co["order_id"],co["size"],co["price"],co["status"]))
                            iddicts[co["side"]].remove(co["order_id"])
                            allorders = buyorderids + sellorderids                
                countcycles +=1 
#order placement                
                logging.debug("The spread is now: %s...NEW ORDERING CYCLE starting: # %s" % (spr,countcycles))
#method 1
                if spr > D('0.10') and (highbid <= BUYMAXPRICE  or lowask >= SELLMINPRICE):
                    #set the target prices of the order pair to 1 cent higher or lower than the best order book prices
                    targetbid = highbid + D('0.01')
                    targetask = lowask - D('0.01')
                    #start eating into profits to find an uninhabited pricepoint
                    #do not exceed values specified by BUYMAXPRICE or SELLMINPRICE
                    while targetbid in onbidbookprice and not(targetbid in onaskbookprice):
                        targetbid += D('0.01')
                    while targetask in onaskbookprice and not(targetask in onbidbookprice):
                        targetask -= D('0.01')
                    if len(buyorderids) < 2 and spr > D('0.10') and numsold >= numbought:
                        if targetbid <= BUYMAXPRICE:
                            try:
                                sys.stdout = sl
                                buyorderids += spread('bitfloor',bitfloor,0,TRADEAMOUNT,targetbid)
                                sys.stdout = sys.__stdout__
                                countbuys += 1
                            except:
                                logging.error(traceback.print_exc())
                        else:
                            logging.debug("EXCEEDED BUYMAXPRICE of: %s" % BUYMAXPRICE)
                    if len(sellorderids) < 2 and spr > D('0.10') and numbought >= numsold:
                        if targetask >= SELLMINPRICE:
                            try:
                                sys.stdout = sl
                                sellorderids += spread('bitfloor',bitfloor,1,TRADEAMOUNT,targetask)
                                sys.stdout = sys.__stdout__
                                countsells += 1
                            except:
                                logging.error(traceback.print_exc())
                        else:
                            logging.debug("EXCEEDED SELLMINPRICE of: %s" % SELLMINPRICE)
#method 2
                if spr < D('0.10'):
                    logging.debug("Starting second method. ")
                    #Try to place order INSIDE the spread.
                    targetbid = onaskbookprice[1]           #gave up and took the second price point
                    targetask = onbidbookprice[1]
                    if len(buyorderids) < 2 and numsold >= numbought:
                        if targetbid <= BUYMAXPRICE:
                            try:
                                sys.stdout = sl
                                buyorderids += spread('bitfloor',bitfloor,0,TRADEAMOUNT,targetbid)
                                sys.stdout = sys.__stdout__
                                countbuys += 1
                            except:
                                logging.error(traceback.print_exc())
                        else:
                            logging.debug("EXCEEDED BUYMAXPRICE of: %s" % BUYMAXPRICE)
                    if len(sellorderids) < 2 and numbought >= numsold:
                        if targetask >= SELLMINPRICE:
                            try:
                                sys.stdout = sl
                                sellorderids += spread('bitfloor',bitfloor,1,TRADEAMOUNT,targetask)
                                sys.stdout = sys.__stdout__
                                countsells += 1
                            except:
                                logging.error(traceback.print_exc())
                        else:
                            logging.debug("EXCEEDED SELLMINPRICE of: %s" % SELLMINPRICE)                                    
#restart the loop 
                stop_event.wait(10)
                
                
        global t1_stop
        if arg == 'exit':
            print "Shutting down background thread..."
            t1_stop.set()
        else:
            t1_stop = threading.Event()
            thread1 = threading.Thread(target = liquidthread, args=(None,t1_stop)).start()

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
        orders = sorted(orders, key=lambda x: x['price'])
        for order in orders:
            buytotal,selltotal = 0,0
            numbuys,numsells = 0,0
            amtbuys,amtsells = 0,0
            buyavg,sellavg = 0,0
            uuid = order['order_id']
            shortuuid = uuid[:8]+'-?-'+uuid[-12:]
            ordertype="Sell" if order['side']==1 else "Buy"
            print '%s order %r. Price $%.5f @ Amount: %.5f' % (ordertype,shortuuid,float(order['price']),float(order['size']))
            if order['type'] == 0:
                buytotal += D(order['price'])*D(order['size'])
                numbuys += D('1')
                amtbuys += D(order['size'])
            elif order['type'] == 1:
                selltotal += D(order['price'])*D(order['size'])
                numsells += D('1')
                amtsells += D(order['size'])
        if amtbuys:
            buyavg = D(buytotal/amtbuys).quantize(D(cPrec))
        if amtsells:
            sellavg = D(selltotal/amtsells).quantize(D(cPrec))
        print "There are %s Buys. There are %s Sells" % (numbuys,numsells)
        print "Avg Buy Price: $%s. Avg Sell Price: $%s" % (buyavg,sellavg)
    def do_cancelall(self,arg):
        """Cancel every single order you have on the books"""
        bitfloor.cancel_all()
#exit out if Ctrl+Z is pressed
    def do_exit(self,arg):      #standard way to exit
        """Exits the program"""
        try:
            t1_stop.set()
            print "Shutting down threads..."
        except:
            pass
        print "\n"
        print "Session Terminating......."
        print "Exiting......"
        return True
    def do_EOF(self,arg):        #exit out if Ctrl+Z is pressed
        """Exits the program"""
        return self.do_exit(arg)
    def help_help(self):
        print 'Prints the help screen'

Shell().cmdloop()
