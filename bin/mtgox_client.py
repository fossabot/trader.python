#!/usr/bin/env python
# Created by genBTC 3/10/2013 Updated 3/21/2013
# mtgox_client.py
# Universal Client for all things mtgox
# Functionality _should_ be listed in README
# now this is turning into a complete command line Client with a menu

import mtgoxhmac
import cmd
import time
from book import *
from common import *
import depthparser
import json
import json_ascii
import traceback
import pyreadline
import winsound         #plays beeps for alerts 
import threading        #for subthreads
import datetime
from decimal import Decimal as D    #renamed to D for simplicity.
import os
import re

mtgox = mtgoxhmac.Client()
cPrec = D('0.00001')
bPrec = D('0.00000001')

# data partial path directory
fullpath = os.path.dirname(os.path.realpath(__file__))
partialpath=os.path.join(fullpath + '\\..\\data\\')

def validatenum(strng):
    search=re.compile(r'[^0-9. ]').search
    return not bool(search(strng))

def validatechar(strng):
    search=re.compile(r'[^a-zA-Z ]').search
    return not bool(search(strng))

def validateboth(strng):
    search = re.compile(r'[^a-zA-Z0-9. ]').search
    return not bool(search(strng))

def stripoffensive(strng):
    pattern = r'[^a-zA-Z0-9. ]'
    new = re.sub(pattern, '', strng)
    return new


def refreshbook(maxage=180):
    #get the FULL depth (current trade order) (API 2,gzip)
    depthvintage,fulldepth = updatedepthdata(mtgox,maxage)
    entirebook = Book.parse(fulldepth["data"],goxfulldepth=True)
    entirebook.sort()      #sort it
    return entirebook
def printorderbook(size=15,maxage=120):
    #entirebook = refreshbook(maxage)		#the full depth book was inaccurate from lag or something
    entirebook = Book.parse(mtgox.get_depth())
    entirebook.sort()
    #start printing part of the order book (first 15 asks and 15 bids)
    printbothbooks(entirebook.asks,entirebook.bids,size)   #otherwise use the size from the arguments
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
    def do_getfee(self,args):
        """Print out the current trade fee"""
        print "Your current trading fee is: %s%%" % (get_tradefee()*100)
    def do_balance(self,args):
        """Calculate how much fees will cost if you sold off your entire BTC Balance"""
        btcbalance,totalfees,last = calc_fees()
        print_calcedfees(btcbalance,last,totalfees)
        self.do_getfee(self)
    def do_calc(self,amount):
        """Calculate how much fees will cost on X amount\n""" \
        """Give X amount as a paramter ie: calc 50"""
        try:
            amount = float(amount)
            btcbalance,totalfees,last = calc_fees()
            print_calcedfees(amount,last,totalfees)
            self.do_getfee(self)
        except Exception as e: 
            self.onecmd('help calc')
            print "Invalid Args. Expected: amount"
    def do_back(self,args):
        """Exits out of the fee menu and goes back to the main level"""
        print '\nGoing back a level...'
        return True
    def do_exit(self,args):
        """Exits out of the fee menu and goes back to the main level"""
        print '\nReturning to the main level...'
        return True
    def do_EOF(self,args):
        """Exits out of the fee menu and goes back to the main level"""
        self.do_exit(self)
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

    #Grab the full_depth from mtgox at initial startup if its been more than 720 seconds since last grab.
    try:
        depthvintage,fulldepth = updatedepthdata(mtgox,maxage=720)
        pass
    except IOError as e:
        try:
            with open(os.path.join(partialpath + 'mtgox_fulldepth.txt'),'w') as f:
                f.flush()
                f.close()
            print "Attempting to write full depth to log file for the first time....."
            print "Download full depth and Create the full depth file? Y/n: "
            response = raw_input("N/No or Leave blank for Yes(default)")
            if not(response):
                depthvintage,fulldepth = writedepth(mtgox)
        except:
            traceback.print_exc()
            print "Something went wrong. IO Error trying to READ, then could not initially CREATE the fulldepth file."

    #start out by printing the order book and the instructions
    printorderbook()
    #give a little user interface       
    print 'Type exit to exit gracefully or Ctrl+Z or Ctrl+C to force quit'
    print 'Type help to show the available commands'
    print 'sample trade example: '
    print '   buy 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks'

    
    def do_balancenotifier(self,args):
        """Check your balance every 30 seconds and BEEP and print something out when you receive the funds (either btc or usd)"""
        def bn(firstarg,notifier_stop):
            while(not notifier_stop.is_set()):
                balance = mtgox.get_balance()
                btcnew,usdnew = (D(balance['btcs']),D(balance['usds']))
                if btcnew > btc or usdnew > usd:
                    last = float(mtgox.get_ticker2()['last']['value'])
                    print 'Your balance is %s BTC and $%s USD ' % (btcnew,usdnew)
                    print 'Last BTC Price of %.2f' % (last)
                    for x in range(2,25):
                        winsound.Beep(x*100,45)  #frequency(Hz),duration(ms)
                        winsound.Beep(x*100,45)
                    notifier_stop.set()
                notifier_stop.wait(30)
        global notifier_stop
        btc,usd = 0,0
        if args == 'exit':
            print "Shutting down background thread..."
            notifier_stop.set()
        else:   
            notifier_stop = threading.Event()
            notifier_thread = threading.Thread(target = bn, args=(None,notifier_stop)).start()

    def do_stoplossbot(self,args):
        """Not done, do not use.started work on this didnt finish."""
        def stoploss(firstarg,stop_event,side,size,price,percent):
            while(not stop_event.is_set()):
                #entirebook = refreshbook()
                #ticker = mtgox.get_ticker2()
                #last = D(ticker["last"]["value"])
                entirebook = Book.parse(mtgox.get_depth())
                entirebook.sort()
                lowask = entirebook.asks[0].price
                percent = D(percent) / D('100')
                price = D(price)
                if price*percent < last:
                    orders = spread('mtgox',mtgox,'sell',size,price)
                    for order in orders:
                        print order["oid"]
                stop_event.wait(60)
        
        try:
            args = stripoffensive(args)
            args = args.split()
            newargs = tuple(floatify(args))
            stoploss(*newargs)
        except Exception as e:
            traceback.print_exc()


        global stopbot_stop
        if args == 'exit':
            print "Shutting down background thread..."
            stopbot_stop.set()
        else:
            stopbot_stop = threading.Event()
            thread1 = threading.Thread(target = tickeralert, args=(None,stopbot_stop)).start()



    def do_new(self,args):
        """New function to test out new depth functions"""
        try:
            depthparser.goxnewcalc(mtgox,args)
        except Exception as e:
            print "Was expecting 3-4 arguments: (bid|ask), (btc|usd), amount, price=optional"

    def do_updown(self,args):
        """Logs ticker to file, spits out an alert and beeps if last price is above or below the range given\n""" \
        """Range window is modified and readjusted\n""" \
        """NOTE: RUNS AS A BACKGROUND PROCESS!!!!!!\n""" \
        """usage: updown <low> <high>\n""" \
        """Shutdown: updown exit  """
        def tickeralert(firstarg,stop_event):
            try:
                low, high = floatify(args.split())
            except Exception as e:
                #traceback.print_exc()
                #raise depthparser.InputError("You need to give a high and low range: low high")
                print "You need to give a high and low range: low high"
                return
            #Log lastprice to the ticker log file
            txfee = get_tradefee()
            with open(os.path.join(partialpath + 'mtgox_last.txt'),'a') as f:
                while(not stop_event.is_set()):
                    ticker =mtgox.get_ticker()
                    last = float(ticker['last'])
                    #svrtime = float(D(float(ticker["now"]) / 1E6).quantize(D("0.001")))
                    text = json.dumps({"time":time.time(),"lastprice":last})
                    f.write(text)
                    f.write("\n")
                    f.flush()
                    if last > low and last < high:
                        #last falls between given variance range, keep tracking
                        pass
                    elif last >= high:
                        print "ALERT!! Ticker has risen above range %s-%s. Price is now: %s" % (low,high,last)
                        for x in range(2,25):
                            winsound.Beep(x*100,90)  #frequency(Hz),duration(ms)
                        low = high - 0.5
                        lowsell = low*(1+txfee*2)
                        high = low + 3
                        #spread('mtgox',mtgox,'sell', 1, lowsell, lowsell+1, 3)
                        print "New range is: %s-%s" % (low,high)
                    elif last == low or last == high:
                        print "ALERT!! Ticker is exactly on the boundary of %s" % (last)
                    else:
                        print "ALERT!! Ticker has fallen below range %s-%s. Price is now: %s" % (low,high,last)
                        for x in range(25,2,-1):
                            winsound.Beep(x*100,90)
                        high = low + 1
                        low = high -3
                        #spread('mtgox',mtgox,'buy', 1, low+1, high-1, 5)
                        print "New range is: %s-%s" % (low,high)
                    stop_event.wait(40)

        args = stripoffensive(args)
        global t1_stop
        if args == 'exit':
            print "Shutting down background thread..."
            t1_stop.set()
        else:
            t1_stop = threading.Event()
            thread1 = threading.Thread(target = tickeralert, args=(None,t1_stop)).start()


    def do_readtickerlog(self,numlines=15):
        """Prints the last X lines of the ticker log file"""
        try:
            numlines = stripoffensive(numlines)
            numlines = int(numlines)
            with open(os.path.join(partialpath + 'mtgox_last.txt'),'r') as f:
                s = tail(f,numlines)
            print s
            l = s.splitlines()
            for x in l: pass
            j = json.loads(x)
            tickertime = j['time']
            print "Last ticker was:",datetime.datetime.fromtimestamp(tickertime).strftime("%Y-%m-%d %H:%M:%S")
            print "Current time is:",datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            self.onecmd('help readtickerlog')

    def do_depth(self,args):
        """Shortcut for the 3 depth functions in common.py"""

        try:
            entirebook = refreshbook(maxage=180)
            args = stripoffensive(args)
            args = args.split()
            mydict = {"buy":entirebook.bids,"bids":entirebook.bids,"bid":entirebook.bids,"sell":entirebook.asks,"ask":entirebook.asks,"asks":entirebook.asks}
            for x in mydict.keys():
                if x in args:
                    args.remove(x)
                    whichbook = mydict[x]
            functlist = ["sum","range","match","price"]
            for x in functlist:
                if x in args:
                    args.remove(x)
                    newargs = tuple(decimalify(args))
                    func = x
            functdict = {"sum":depthsumrange,"range":depthsumrange,"match":depthmatch,"price":depthprice}[func](whichbook,*newargs)
        except:
            print "Invalid args given. Proper use is:"
            print "depth (sum/match/price) (bids/asks)"

    def do_obip(self, args):
        """Calculate the "order book implied price", by finding the weighted\n""" \
        """average price of coins <width> BTC up and down from the spread.\n""" \
        """Usage: <width> optional:(BTC/USD) """
        args = stripoffensive(args)
        args = args.split()
        newargs = tuple(floatify(args))
        
        obip(mtgox,*newargs)

    def do_asks(self,args):
        """Calculate the amount of bitcoins for sale at or under <pricetarget>.\n""" \
        """If 'over' option is given, find coins or at or over <pricetarget>."""
        #right now this is using the FULL DEPTH data so we call update which will update if necessary

        args = stripoffensive(args)
        try:
            pricetarget = float(args)
            response = 'under'
        except:
            try:
                response, pricetarget = args.split()
                pricetarget = float(pricetarget)
            except:
                self.onecmd('help asks')
                return
        depthvintage,fulldepth = updatedepthdata(mtgox,maxage=180)
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
        print "There are %.11g bitcoins offered at or %s %s USD, worth $%.2f USD in total."  % (n_coins,response, pricetarget, total)
    
    def do_bids(self,args):
        """Calculate the amount of bitcoin demanded at or over <pricetarget>.\n""" \
        """If 'under' option is given, find coins or at or under <pricetarget>"""

        args = stripoffensive(args)
        try:
            pricetarget = float(args)
            response = 'over'
        except:
            try:
                response, pricetarget = args.split()
                pricetarget = float(pricetarget)
            except:
                self.onecmd('help bids')
                return
        depthvintage,fulldepth = updatedepthdata(mtgox,maxage=180)          
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
        print "There are %.11g bitcoins demanded at or %s %s USD, worth $%.2f USD in total."  % (n_coins,response,pricetarget, total)



    def do_buy(self, args):
        """(market order): buy size \n""" \
        """(limit order): buy size price \n""" \
        """(spread order): buy size price_lower price_upper chunks ("random") (random makes chunk amounts slightly different)"""
        # adds a multitude of orders between price A and price B of equal sized # of chunks on Mtgox.
        try:
            args = stripoffensive(args)
            args = args.split()
            newargs = tuple(floatify(args))
            if len(newargs) == 1:
                mtgox.buy_btc(*newargs)
            elif "usd" in newargs:
                buyprice = mtgox.get_ticker()["buy"]
                amt = D(newargs[0]) / D(buyprice)       #convert USD to BTC.
                mtgox.buy_btc(amt.quantize(bPrec),buyprice) #goes as a market order (can be limit also if buyprice omitted.)
            elif not(len(newargs) == 3):
                spread('mtgox',mtgox,'buy', *newargs)   # pass arguments back to spread() function in common.py
            else:
                raise UserError
        except Exception as e:
            traceback.print_exc()
            print "Invalid args given!!! Proper use is:"
            self.onecmd('help buy')

    def do_sell(self, args):
        """(market order): sell size \n""" \
        """(limit order): sell size price \n""" \
        """(spread order): sell size price_lower price_upper chunks ("random") (random makes chunk amounts slightly different)"""
        try:
            args = stripoffensive(args)
            args = args.split()
            newargs = tuple(floatify(args))
            if len(newargs) == 1:
                mtgox.sell_btc(*newargs)
            elif "usd" in newargs:
                sellprice = mtgox.get_ticker()["sell"]
                amt = D(newargs[0]) / D(sellprice)       #convert USD to BTC.
                mtgox.sell_btc(amt.quantize(bPrec),sellprice) #goes as a market order (can be limit also if buyprice omitted.)                
            elif not(len(newargs) == 3):
                spread('mtgox',mtgox,'sell', *newargs)
            else:
                raise UserError
        except Exception as e:
            traceback.print_exc()
            print "Invalid args given!!! Proper use is:"
            self.onecmd('help sell')

    def do_ticker(self,args):
        """Print the entire ticker out or use one of the following options:\n""" \
        """[--buy|--sell|--last|--high|--low|--vol|--vwap|--avg] """
        args = stripoffensive(args)
        ticker = mtgox.get_ticker2()
        svrtime = float(D(float(ticker["now"]) / 1E6).quantize(D("0.001")))
        if not args:
            print "BTCUSD ticker | Best bid: %s, Best ask: %s, Bid-ask spread: %.5f, Last trade: %s, " \
                "24 hour volume: %s, 24 hour low: %s, 24 hour high: %s, 24 hour vwap: %s, 24 hour avg: %s" % \
                (ticker['buy']['value'], ticker['sell']['value'], \
                float(ticker['sell']['value']) - float(ticker['buy']['value']), \
                ticker['last']['value'], ticker['vol']['value'], \
                ticker['low']['value'], ticker['high']['value'], \
                ticker['vwap']['value'],ticker['avg']['value'])
            print "Time of ticker: ", datetime.datetime.fromtimestamp(svrtime).strftime("%Y-%m-%d %H:%M:%S"), "Ticker Lag: %.3f" % (time.time()-svrtime)
        else:
            try:
                print "BTCUSD ticker | %s = %s" % (args,ticker[args])
            except:
                print "Invalid args. Expecting a valid ticker subkey."
                self.onecmd('help ticker')

    def do_spread(self,args):
        """Print out the bid/ask spread"""
        try:
            print "The spread is: %f" % mtgox.get_spread()
        except:
            self.onecmd('help spread')

    def do_book(self,size):
        """Download and print the order book of current bids and asks of depth $size"""
        try:
            size = stripoffensive(size)
            size = int(size)
            printorderbook(size,maxage=1)
        except:
            printorderbook(maxage=1) 

    def do_orders(self,args):
        """Print a list of all your open orders, including pending and lacking enough funds"""
        try:
            args = stripoffensive(args)
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
            return

    def do_tradehist24(self,args):
        """Download the entire trading history of mtgox for the past 24 hours. Write it to a file"""
        print "Starting to download entire trade history from mtgox....",
        eth = mtgox.entire_trade_history()
        with open(os.path.join(partialpath + 'mtgox_entiretrades.txt'),'w') as f:
            depthvintage = str(time.time())
            f.write(depthvintage)
            f.write('\n')
            json.dump(eth,f)
            f.close()
            print "Finished."

    def do_readtradehist24(self,args):
        """reading trade history data from a file and gathering stats on it"""
        import tradehistory
        print "Is this a Trade History file (not a full depth file)?"
        isdepthfile = raw_input("N/No or [Leave blank for Yes(default)]")
        if not(isdepthfile):
            tradehistory.readhist24()
        else:
            tradehistory.readdepth()

    def do_cancelall(self,args):
        """Cancel every single order you have on the books"""
        mtgox.cancelall()

    def do_lag(self,args):
        """Shows the current Mt.Gox trading engine lag time"""
        lag = mtgox.lag()
        print 'Current order lag is %r' % (lag['lag_secs'])

    def do_balance(self,args):
        """Shows your current account balance and value of your portfolio based on last ticker price"""
        balance = mtgox.get_balance()
        btc,usd = (balance['btcs'],balance['usds'])
        last = float(mtgox.get_ticker2()['last']['value'])
        print 'Your balance is %r BTC and $%.2f USD ' % (btc,usd)
        print 'Account Value: $%.2f @ Last BTC Price of %s' % (btc*last+usd,last)

    def do_btchistory(self,args):
        """Prints out your entire history of BTC transactions"""
        btchistory=mtgox.get_history_btc()
        print btchistory

    def do_usdhistory(self,args):
        """Prints out your entire trading history of USD transactions"""
        usdhistory=mtgox.get_history_usd()
        print usdhistory

    def do_fees(self,args):
        """Loads the fee module to calculate fees"""
        Feesubroutine().cmdloop()

    def do_exit(self,args):      #standard way to exit
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

    def do_EOF(self,args):        #exit out if Ctrl+Z is pressed
        """Exits the program"""
        return self.do_exit(args)

    def help_help(self):
        print 'Prints the help screen'
        

if __name__ == '__main__':
    Shell().cmdloop()