#!/usr/bin/env python
# bitstamp_client.py
# Created by genBTC 4/4/2013
# Universal Client for all things bitstamp
# Functionality _should_ be listed in README

#import args        #lib/args.py modified to use product 1 & bitstamp file
import bitstampapi     #args was phased out and get_rapi() was moved to bitstamp and config.json moved to data/
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
import socket


bitstampapi = bitstampapi.Client()

cPrec = D('0.01')
bPrec = D('0.00000001')

threadlist = {}

class UserError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg
    def __str__(self):
        return self.errmsg


def bal():
    balance = bitstamp.account_balance()
    btcbalance = D(balance['btc_balance'])
    usdbalance = D(balance['usd_balance'])
    return btcbalance,usdbalance

def reserved():
    balance = bitstamp.account_balance()
    btcreserved = D(balance['btc_reserved'])
    usdreserved = D(balance['usd_reserved'])
    return btcreserved,usdreserved

def available():
    balance = bitstamp.account_balance()
    btcavailable =D(balance['btc_available'])
    usdavailable = D(balance['usd_available'])
    return btcavailable,usdavailable


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



#get update the entire order book
def refreshbook():
    #get the entire order book  (already sorted.)
    entirebook = bitstamp.entirebook()
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
        self.prompt = 'Bitstamp CMD>'   # The prompt for a new user input command
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
               
    #start out by printing the order book
    printorderbook()

    #give a little user interface
    print 'Type exit to exit gracefully or Ctrl+Z or Ctrl+C to force quit'
    print 'Typing help will show you the list of commands'
    print 'sample trade example: '
    print '   buy 2.8 140 145 64 = buys 2.8 BTC between $140 to $145 using 64 chunks'
    print ' '


    def do_balance(self,arg):
        """Shows your current account balance and value of your portfolio based on last ticker price"""
        btc,usd = bal()
        last = D(bitstamp.ticker()['last'])
        print 'Your balance is %r BTC and $%.2f USD ' % (btc,usd)
        print 'Account Value: $%.2f @ Last BTC Price of %.2f' % (btc*last+usd,last)


    def do_book(self,size):
        """Download and print the order book of current bids and asks of depth $size"""
        try:
            size = int(size)
            printorderbook(size)
        except:
            printorderbook()        


    def do_buy(self, arg):
        """(limit order): buy size price \n""" \
        """(spread order): buy size price_lower price_upper chunks ("random") (random makes chunk amounts slightly different)"""
        try:
            args = arg.split()
            newargs = tuple(decimalify(args))
            if len(newargs) not in (1,3):
                spread('bitstamp',bitstamp, 0, *newargs)
            else:
                raise UserError
        except Exception as e:
            traceback.print_exc()
            print "Invalid args given!!! Proper use is:"
            self.onecmd('help buy')

    def do_sell(self, arg):
        """(limit order): sell size price \n""" \
        """(spread order): sell size price_lower price_upper chunks ("random") (random makes chunk amounts slightly different)"""
        try:
            args = arg.split()
            newargs = tuple(decimalify(args))
            if len(newargs) not in (1,3):
                spread('bitstamp',bitstamp, 1, *newargs)
            else:
                raise UserError
        except Exception as e:
            traceback.print_exc()
            print "Invalid args given!!! Proper use is:"
            self.onecmd('help sell')
       

    def do_cancel(self,args):
        """Cancel an order by number,ie: 7 or by range, ie: 10 - 25""" \
        """Use with arguments after the cancel command, or without to view the list and prompt you"""
        try:
            if args:
                useargs = True
            orders = bitstamp.open_orders()
            orders = sorted(orders, key=lambda x: x['price'])
            numorder = 0
            numcancelled = 0
            for order in orders:
                ordertype="Sell" if order['type'] == 1 else "Buy"
                numorder += 1
                OPX = 'O'
                print '%s = %s %s %s | %s BTC @ $%s' % (numorder,ordertype,OPX,order['id'],order['amount'],order['price'])
            print "Use spaces or commas to seperate order numbers: 1,2,3"
            print "Use a - to specify a range: 1-20. "
            while True:
                if useargs == True:
                    orderlist = args
                    useargs = False
                else:
                    orderlist = ""
                    userange=False
                    numorder = 0
                    orderlist = raw_input("Which order numbers would you like to cancel?: [ENTER] quits.\n")
                if orderlist == "":
                    break
                orderlist = stripoffensive(orderlist,',-')
                if "," in orderlist:
                    orderlist = orderlist.split(',')
                if '-' in orderlist:
                    userange = True
                    orderlist = orderlist.split('-')
                else:
                    orderlist = orderlist.split()
                for order in orders:
                    numorder += 1
                    if userange == True:
                        if numorder >= int(orderlist[0]) and numorder <= int(orderlist[1]):
                            result = mtgox.cancel_order(order['id'])
                            numcancelled += 1
                    elif str(numorder) in orderlist:
                        result = mtgox.cancel_order(order['id'])
                        numcancelled += 1
                if numcancelled > 1:
                    print "%s Orders have been Cancelled!!!!!" % numcancelled
        except Exception as e:
            print e
            return            

    def do_cancelall(self,arg):
        """Cancel every single order you have on the books"""
        bitstamp.cancel_all()


    def do_gethistory(self,args):
#Very rough. pretty print it 
        """Prints out your user transactions in the past <timdelta>"""
        history=bitstamp.get_usertransactions()
        ppdict(history)


    def do_getaddress(self,args):
        """Find out your bitcoin deposit address"""
        bitstamp.get_depositaddress()


    def do_marketbuy(self, arg):
        """working on new market trade buy function"""
        """usage: amount lowprice highprice"""
        entirebook = refreshbook()
        try:
            args = arg.split()
            newargs = tuple(decimalify(args))
            side = entirebook.asks
            markettrade(side,'buy',*newargs)
        except Exception as e:
            traceback.print_exc()
            print "Invalid args given. Proper use is: "
            self.onecmd('help marketbuy')


    def do_marketsell(self, arg):
        """working on new market trade sell function"""
        """usage: amount lowprice highprice"""
        entirebook = refreshbook()
        try:
            args = arg.split()
            newargs = tuple(decimalify(args))
            side = entirebook.bids
            side.reverse()
            markettrade(side,'buy',*newargs)    
        except Exception as e:
            traceback.print_exc()
            print "Invalid args given. Proper use is: "
            self.onecmd('help marketsell')
 

    def do_orders(self,arg):
        """Print a list of all your open orders"""
        try:
            orders = bitstamp.open_orders()
            orders = sorted(orders, key=lambda x: x['price'])
            buytotal,selltotal = 0,0
            numbuys,numsells = 0,0
            amtbuys,amtsells = 0,0
            buyavg,sellavg = 0,0
            numorder = 0        
            for order in orders:
                numorder += 1
                uuid = order['id']
                shortuuid = uuid[:8]+'-??-'+uuid[-12:]
                ordertype="Sell" if order['type']==1 else "Buy"
                print '%s order %r. Price $%.5f @ Amount: %.5f' % (ordertype,shortuuid,order['price'],order['amount'])
                if order['type'] == 0:
                    buytotal += D(order['price'])*D(order['amount'])
                    numbuys += D('1')
                    amtbuys += D(order['amount'])
                elif order['type'] == 1:
                    selltotal += D(order['price'])*D(order['amount'])
                    numsells += D('1')
                    amtsells += D(order['amount'])
            if amtbuys:
                buyavg = D(buytotal/amtbuys).quantize(D(cPrec))
            if amtsells:
                sellavg = D(selltotal/amtsells).quantize(D(cPrec))
            print "There are %s Buys. There are %s Sells" % (numbuys,numsells)
            print "Avg Buy Price: $%s. Avg Sell Price: $%s" % (buyavg,sellavg)
        except Exception as e:
            print e
            return

                    
    def do_sellwhileaway(self,arg):
        """Check balance every 60 seconds for <amount> and once we have received it, sell! But only for more than <price>."""
        """Usage: amount price"""
        args = arg.split()
        amount,price = tuple(decimalify(args))
        #seed initial balance data so we can check it during first run of the while loop
        balance = decimalify(bitstamp.accounts())
        #seed the last price just in case we have the money already and we never use the while loop
        last = D(bitstamp.ticker()['price'])
        while balance[0]['amount'] < amount:
            balance = decimalify(bitstamp.accounts())
            last = D(bitstamp.ticker()['price'])
            print 'Your balance is %r BTC and $%.2f USD ' % (balance[0]['amount'],balance[1]['amount'])
            print 'Account Value: $%.2f @ Last BTC Price of %.2f' % (balance[0]['amount']*last+balance[1]['amount'],last)
            time.sleep(60)
        while balance[0]['amount'] > 6:
            if last > price+3:
                bitstamp.cancel_all()
                spread('bitstamp',bitstamp,1,5,last,last,1)
            if last > price:
                if balance > 5:
                    bitstamp.cancel_all()
                    spread('bitstamp',bitstamp,1,5,price,last+1,3)
            if price > last:
                if balance > 5 and price-last < 3:
                    bitstamp.cancel_all()
                    spread('bitstamp',bitstamp,1,5,last,price,2)

            last = D(bitstamp.ticker()['price'])                    
            balance = decimalify(bitstamp.accounts())
            time.sleep(45)

    def do_sellwhileaway2(self,arg):
        """Check balance every 60 seconds for <amount> and once we have received it, sell! But only for more than <price>."""
        """Usage: amount price"""
        try:
            args = arg.split()
            amount,price = tuple(decimalify(args))
            #seed initial balance data so we can check it during first run of the while loop
            balance = decimalify(bitstamp.accounts())
            #seed the last price just in case we have the money already and we never use the while loop
            last = D(bitstamp.ticker()['price'])
            while balance[0]['amount'] < amount:
                balance = decimalify(bitstamp.accounts())
                last = D(bitstamp.ticker()['price'])
                print 'Your balance is %r BTC and $%.2f USD ' % (balance[0]['amount'],balance[1]['amount'])
                print 'Account Value: $%.2f @ Last BTC Price of %.2f' % (balance[0]['amount']*last+balance[1]['amount'],last)
                time.sleep(60)
            sold=False
            while sold==False:
                if last > price:
                    bitstamp.cancel_all()
                    spread('bitstamp',bitstamp,1,balance[0]['amount'],last,last+1,2)
                else:
                    bitstamp.cancel_all()
                    spread('bitstamp',bitstamp,1,balance[0]['amount'],((last+price)/2)+0.5,price,2)
                balance = decimalify(bitstamp.accounts())
                last = D(bitstamp.ticker()['price'])
                time.sleep(60)
        except:
            print "Retrying:"
            self.onecmd(self.do_sellwhileaway2(amount,price))


    def do_spread(self,args):
        """Print out the bid/ask spread"""
        try:
            print "High Bid is: $", entirebook.bids[0].price
            print "Low ask is: $", entirebook.asks[0].price
            print "The spread is: $%f" % entirebook.asks[0].price - entirebook.bids[0].price
        except:
            self.onecmd('help spread')


    def do_ticker(self,arg):
        """Print the entire ticker out or use one of the following options:\n""" \
        """[--bid|--ask|--last|--vol|--low|--high]"""
        args = stripoffensive(args)
        ticker = floatify(bitstamp.ticker())
        last = ticker['last']
        low,high,vol = ticker['low'],ticker['high'],ticker['vol']
        bid,ask = ticker['bid'],ticker['ask']
        if not args:
            print "BTCUSD ticker | Best bid: %.2f, Best ask: %.2f, Bid-ask spread: %.2f, Last trade: %.2f, " \
                "24 hour volume: %d, 24 hour low: %.2f, 24 hour high: %.2f" % (bid,ask,ask-bid,last,vol,low,high)
        else:
            try:
                print "BTCUSD ticker | %s = %s" % (args,ticker[args])
            except:
                print "Invalid args. Expecting a valid ticker subkey."
                self.onecmd('help ticker')


    def do_tradehist24(self,args):
        """Download the entire trading history of bitstamp for the past 24 hours. Write it to a file"""
        print "Starting to download entire trade history from bitstamp....",
        eth = bitstamp.get_transactions(86400)
        with open(os.path.join(partialpath + 'bitstamp_entiretrades.txt'),'w') as f:
            depthvintage = str(time.time())
            f.write(depthvintage)
            f.write('\n')
            json.dump(eth,f)
            f.close()
            print "Finished."


    def do_withdraw(self,args):
        """Withdraw Bitcoins to an address"""
        try:
            address = raw_input("Enter the address you want to withdraw to: ")
            totalbalance = prompt("Do you want to withdraw your ENTIRE balance?",False)
            if totalbalance == False:
                amount = D(raw_input("Enter the amount of BTC to withdraw: "))
            else:
                amount,_ = bal()
            
            result = bitstamp.bitcoin_withdraw(address,amount)
            if result:
                print "%s BTC successfully sent to %s" % (amount,address)
            else:
                print "There was an error withdrawing."
        except:
            traceback.print_exc()
            print "Unknown error occurred."
            self.onecmd('help withdraw')


#exit out if Ctrl+Z is pressed
    def do_exit(self,arg):      #standard way to exit
        """Exits the program"""
        try:
            for k,v in threadlist.iteritems():
                v.set()
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
