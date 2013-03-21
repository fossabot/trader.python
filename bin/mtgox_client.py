#!/usr/bin/env python
# Created by genBTC 3/10/2013 Updated 3/21/2013
# mtgox_client.py
# Universal Client for all things mtgox
# Functionality _should_ be listed in README
# now this is turning into a complete command line Client with a menu

import mtgoxhmac
import cmd
import time
from book import Book, Order
from common import *
import depthparser
import json
import json_ascii
import traceback
import pyreadline
import winsound        #plays beeps for alerts :)

mtgox = mtgoxhmac.Client()


# data partial path directory
datapartialpath=os.path.join(os.path.dirname(__file__) + '../data/')


def refreshbook():
    #get current trade order book (depth)  - uses simple depth (api 0)
    entirebook=Book.parse(mtgox.get_depth())
    #sort it
    entirebook.sort()
    return entirebook
def printorderbook(size):
    entirebook = refreshbook()
    #start printing part of the order book (first 15 asks and 15 bids)
    if size is '':
        printbothbooks(entirebook.asks,entirebook.bids,15)
    else:
        printbothbooks(entirebook.asks,entirebook.bids,int(size))      
def bal():
    balance = mtgox.get_balance()
    btcbalance = float(balance['btcs'])
    usdbalance = float(balance['usds'])
    return btcbalance,usdbalance
def get_tradefee():
    return (float(mtgox.get_info()['Trade_Fee'])/100)
def calc_fees():
    last = mtgox.get_ticker()['last']
    btcbalance,usdbalance = bal()
    tradefee = get_tradefee()
    totalfees = btcbalance * tradefee * last
    return btcbalance,totalfees,last
def print_calcedfees(amount,last,totalfees):
    print 'Balance of %f BTC worth $%.2f USD Value total' % (amount,amount*last)
    print 'Total Fees are $%.2f USD total @ $%.2f per BTC' % (totalfees,last)

class Feesubroutine(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        print 'Calculate your fees: type back to go back\n'
        # The prompt for a new user input command
        self.prompt = 'Fees CMD>'
        self.use_rawinput = False
        self.onecmd('help')
    def do_balance(self,arg):
        """Calculate how much fees will cost if you sold off your entire BTC Balance"""
        btcbalance,totalfees,last = calc_fees()
        print_calcedfees(btcbalance,last,totalfees)
    def do_calc(self,amount):
        """Calculate how much fees will cost on X amount"""
        """Give X amount as a paramter ie: calc 50"""
        try:
            amount = float(amount)
            btcbalance,totalfees,last = calc_fees()
            print_calcedfees(amount,last,totalfees)
        except Exception as e: 
            self.onecmd('help calc')
            print "Invalid Args. Expected: amount"
    def do_exit(self,arg):
        """Exits out of the fee menu and goes back to the main level"""
        print '\nReturning to the main level...'
        return True
    def do_back(self,arg):
        """Exits out of the fee menu and goes back to the main level"""
        print '\nGoing back a level...'
        return True
    def do_EOF(self,arg):
        """Exits out of the fee menu and goes back to the main level"""
        print '\nReturning to the main level...'
        return True
    def help_help(self):
        print 'Prints the help screen'

class Shell(cmd.Cmd):
    def emptyline(self):      
        pass                #Do nothing on empty input line instead of re-executing the last command
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'MtGox CMD>'      # The prompt for a new user input commands
        #the trading command prompt did not allow cmd.exe to store a history beyond multiple sessions
        #now it does store a history but we lose tab completion. This is what use_rawinput = false means.
        self.use_rawinput = False
        self.onecmd('help')             #print out the possible commands (help) on first run

    #Grab the full_depth from mtgox at initial startup if its been more than 720 seconds since last grab.
    try:
        depthvintage,fulldepth = updatedepthdata(mtgox)
    except IOError as e:
        try:
            with open(os.path.join(datapartialpath + 'mtgox_fulldepth.txt'),'w') as f:
                f.flush()
                f.close()
            print "Attempting to write full depth to log file for the first time....."
            response = raw_input("Download full depth and Create the full depth file? Y/n: ")
            if response == 'Y' or response == 'y':
                depthvintage,fulldepth = writedepth(mtgox)
        except:
            traceback.print_exc()
            print "Something went wrong. IO Error trying to READ, then could not initially CREATE the fulldepth file."

    #start out by printing the order book and the instructions
    printorderbook(15)
    #give a little user interface       
    print 'Type exit to exit gracefully or Ctrl+Z or Ctrl+C to force quit'
    print 'Type help to show the available commands'
    print 'sample trade example: '
    print '   buy 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks'

    def do_new(self,args):
        """New function to test out new depth functions"""
        try:
            depthparser.goxnewcalc(mtgox,args)
        except Exception as e:
            print "Was expecting 3-4 arguments: (bid|ask), (btc|usd), amount, price=optional"
            return

    def do_updown(self,arg):
        """Logs ticker to file, spits out an alert if last price is above or below the range given"""
        """usage: updown <low> <high>"""
        def catchmeifyoucan(arg):
            low = high = 0
            low, high = arg.split()
            low = float(low)
            high = float(high)
            #entirebook = refreshbook()
            #depthgot   = mtgox.get_depth()
            #depth  = depthparser.DepthParser(5)
            #data  = depth.process(depthgot, raw = False)
            return low,high
        try:
            low, high = catchmeifyoucan(arg)
        except Exception as e:
            #traceback.print_exc()
            #raise depthparser.InputError("You need to give a high and low range: low high")
            print "You need to give a high and low range: low high"
            return
        #Log lastprice to the ticker log file
        with open(os.path.join(datapartialpath + 'mtgox_last.txt'),'a') as f:
            while True:
                ticker =mtgox.get_ticker2()
                last = float(ticker['last']['value'])
                svrtime = float(Decimal(float(ticker["now"]) / 1000000).quantize(Decimal("0.001")))
                text = json.dumps({"time":svrtime,"lastprice":last})
                f.write(text)
                f.write("\n")
                f.flush()
                if last > low and last < high:
                    #last falls between given variance range, keep tracking
                    pass
                elif last >= high:
                    print "ALERT!! Ticker has risen above range. Price is now: %s" % (last)
                    #print "then make some sales mtgox.sell_btc"
                    winsound.Beep(500,4000)     #frequency(Hz),duration(ms)
                else:
                    print "ALERT!! Ticker has fallen below range. Price is now: %s" % (last)
                    winsound.Beep(2500,1000)
                    winsound.Beep(2500,1000)
                    #spread('mtgox',mtgox,'buy', 111, last, low, 5)
                    #print "then make some buys- mtgox.buy_btc"
                try:
                    time.sleep(60)
                except KeyboardInterrupt as e:
                    print "CTRL+C was pressed, stopping logging."
                    return

    def do_readtickerlog(self,arg):
        """Prints the last X lines of the ticker log file"""
        arg = int(arg)
        with open(os.path.join(datapartialpath + 'mtgox_last.txt'),'r') as f:
            print tail(f,arg)

    def do_obip(self, width):
        """<width>
        Calculate the "order book implied price", by finding the weighted
        average price of coins <width> BTC up and down from the spread."""
        width = float(width)
        obip(mtgox,width)
    def do_asks(self,arg):
        """Calculate the amount of bitcoins for sale at or under <pricetarget>.""" 
        """If 'over' option is given, find coins or at or over <pricetarget>."""
        #right now this is using the FULL DEPTH data so we call update which will update if necessary
        depthvintage,fulldepth = updatedepthdata(mtgox)
        try:
            pricetarget = float(arg)
            response = 'under'
        except:
            response, pricetarget = arg.split()
            pricetarget = float(pricetarget)
        if response == 'over':
            f = lambda price,pricetarget: price >= pricetarget
        else:
            f = lambda price,pricetarget: price <= pricetarget
        n_coins = 0.0
        total = 0.0
        try:
            depth = fulldepth
            asks=depth["data"]["asks"]
        except KeyError:
            print "Failure to retrieve order book data. Try again later."
            return
        for ask in asks:
            if f(ask["price"], pricetarget):
                n_coins += ask["amount"]
                total += (ask["amount"] * ask["price"])
        print "There are currently %.8g bitcoins offered at or %s %s USD, worth %.2f USD in total."  % (n_coins,response, pricetarget, total)
        #return n_coins
    
    def do_bids(self,arg):
        """Calculate the amount of bitcoin demanded at or over <pricetarget>."""
        """If 'under' option is given, find coins or at or under <pricetarget>"""
        depthvintage,fulldepth = updatedepthdata(mtgox)
        try:
            pricetarget = float(arg)
            response = 'over'
        except:
            response, pricetarget = arg.split()
            pricetarget = float(pricetarget)
        if response == 'under':
            f = lambda price,pricetarget: price <= pricetarget
        else:
            f = lambda price,pricetarget: price >= pricetarget
        n_coins = 0.0
        total = 0.0
        try:
            depth = fulldepth
            bids=depth["data"]['bids']
        except KeyError:
            print "Failure to retrieve order book data. Try again later."
            return
        for bid in bids:
            if f(bid["price"], pricetarget):
                n_coins += bid["amount"]
                total += (bid["amount"] * bid["price"])
        print "There are currently %.8g bitcoins demanded at or %s %s USD, worth %.2f USD in total."  % (n_coins,response,pricetarget, total)
        #return n_coins

# pass arguments back to spread() function in common.py
# adds a multitude of orders between price A and price B of equal sized # of chunks on Mtgox.
    def do_buy(self, arg):
        """(market order): buy size \n""" \
        """(limit order): buy size price \n""" \
        """(spread order): buy size price_lower price_upper chunks"""
        try:
            size, price_lower, price_upper, chunks = arg.split()
            spread('mtgox',mtgox,'buy', size, price_lower, price_upper, chunks)
        except:
            try:
                size,price_lower = arg.split()
                spread('mtgox',mtgox,'buy', size, price_lower)
            except:
                try:
                    arg = float(arg)
                    mtgox.buy_btc(arg)
                except Exception as e:
                    print "Invalid args given!!! Proper use is:"
                    self.onecmd('help buy')
                    return

    def do_sell(self, arg):
        """(market order): sell size \n""" \
        """(limit order): sell size price \n""" \
        """(spread order): sell size price_lower price_upper chunks"""
        try:
            size, price_lower, price_upper, chunks = arg.split()
            spread('mtgox',mtgox,'sell', size, price_lower, price_upper, chunks)
        except:
            try:
                size,price_lower = arg.split()
                spread('mtgox',mtgox,'sell', size, price_lower)
            except:
                try:
                    arg = float(arg)
                    mtgox.sell_btc(size)
                except Exception as e:
                    print "Invalid args given!!! Proper use is:"
                    self.onecmd('help sell')
                    return

    def do_ticker(self,arg):
        """Print the entire ticker out or use one of the following options:\n""" \
        """[--buy|--sell|--last|--high|--low|--vol|--vwap|--avg] """
        ticker = mtgox.get_ticker2()
        if not arg:
            print "BTCUSD ticker | Best bid: %s, Best ask: %s, Bid-ask spread: %.5f, Last trade: %s, " \
                "24 hour volume: %s, 24 hour low: %s, 24 hour high: %s, 24 hour vwap: %s, 24 hour avg: %s" % \
                (ticker['buy']['value'], ticker['sell']['value'], \
                float(ticker['sell']['value']) - float(ticker['buy']['value']), \
                ticker['last']['value'], ticker['vol']['value'], \
                ticker['low']['value'], ticker['high']['value'], \
                ticker['vwap']['value'],ticker['avg']['value'])
        else:
            try:
                print "BTCUSD ticker | %s = %s" % (arg,ticker[arg])
            except:
                print "Invalid args. Expecting a valid ticker subkey."
                self.onecmd('help ticker')

    def do_spread(self,arg):
        """Print out the bid/ask spread"""
        print mtgox.get_spread()

    def do_book(self,size):
        """Download and print the order book of current bids and asks of depth $size"""
        printorderbook(size)
        
    def do_orders(self,arg):
        """Print a list of all your open orders, including pending and lacking enough funds"""
        try:    
            time.sleep(1)
            orders = mtgox.get_orders()['orders']
            for order in orders:
                ordertype="Sell" if order['type'] == 1 else "Buy"
                if order['status'] == 1:
                    print ordertype,'order %r  Price $%s @ Amount: %s' % (str(order['priority']),order['price'],order['amount'])
                elif order['status'] == 2:
                    print ordertype,'order %r PENDING - Price $%s @ Amount: %s' % (str(order['priority']),order['price'],order['amount'])
                elif order['status'] == 0:
                    print ordertype,'order %r NOT ENOUGH FUNDS for: %s BTC' % (str(order['priority']),order['amount'])
        except Exception as e:
            traceback.print_exc()
            print "Something went wrong."
            return

    def do_tradehist24(self,arg):
        """Download the entire trading history of mtgox for the past 24 hours. Write it to a file"""
        print "Starting to download entire trade history from mtgox....",
        eth = mtgox.entire_trade_history()
        with open(os.path.join(datapartialpath + 'mtgox_entiretrades.txt'),'w') as f:
            depthvintage = str(time.time())
            f.write(depthvintage)
            f.write('\n')
            json.dump(eth,f)
            f.close()
            print "Finished."

    def do_cancelall(self,arg):
        """Cancel every single order you have on the books"""
        mtgox.cancelall()
    def do_lag(self,arg):
        """Shows the current Mt.Gox trading engine lag time"""
        lag = mtgox.lag()
        print 'Current order lag is %r' % (lag['lag_secs'])
    def do_balance(self,arg):
        """Shows your current account balance and value of your portfolio based on last ticker price"""
        balance = mtgox.get_balance()
        last = float(mtgox.get_ticker2()['last']['value'])
        print 'Your balance is %r BTC and $%.2f USD ' % (balance['btcs'],balance['usds'])
        print 'Account Value: $%.2f @ Last BTC Price of %.2f' % (balance['btcs']*last+balance['usds'],last)
    def do_btchistory(self,arg):
        """Prints out your entire history of BTC transactions"""
        btchistory=mtgox.get_history_btc()
        print btchistory
    def do_usdhistory(self,arg):
        """Prints out your entire trading history of USD transactions"""
        usdhistory=mtgox.get_history_usd()
        print usdhistory
    def do_fees(self,arg):
        """Loads the fee module to calculate fees"""
        Feesubroutine().cmdloop()
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
        

if __name__ == '__main__':
    Shell().cmdloop()
