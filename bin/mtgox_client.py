#!/usr/bin/env python
# Created by genBTC 3/10/2013 Updated 4/4/2013 
# mtgox_client.py
# Universal Client for all things mtgox
# A complete command line Client with a menu
# Functionality _should_ be listed in README (functions in alpahabetical order)

import cmd
import time
import json
import traceback
import threading        #for subthreads
import datetime
from decimal import Decimal as D    #renamed to D for simplicity.
import os
import logging
import csv
import os
if os.name == 'nt':
    import winsound         #plays beeps for alerts 

from book import *
from common import *
import depthparser
import mtgox_prof7bitapi
import mtgoxhmac

mtgox = mtgoxhmac.Client()

bPrec = mtgox.bPrec
cPrec = mtgox.cPrec

threadlist = {}

class LogWriter():
    """connects to gox.signal_debug and logs it all to the logfile"""
    def __init__(self, gox):
        self.gox = gox
        logging.basicConfig(filename='goxtool.log'
                           ,filemode='a'
                           ,format='%(asctime)s:%(levelname)s %(message)s'
                           ,level=logging.DEBUG
                           )
        console_logger = logging.getLogger('')
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console_logger.addHandler(console)        
        self.gox.signal_debug.connect(self.slot_debug)

    def close(self):
        """stop logging"""
        #not needed
        pass

    # pylint: disable=R0201
    def slot_debug(self, sender, (msg)):
        """handler for signal_debug signals"""
        if "https://data.mtgox.com/api/2/money/order/lag" in msg:
            return
        else:
            logging.debug("%s:%s", sender.__class__.__name__, msg)       #change this to .info to see the messages on screen.


config = mtgox_prof7bitapi.GoxConfig()
secret = mtgox_prof7bitapi.Secret()
secret.decrypt(mtgox.enc_password)
gox = mtgox_prof7bitapi.Gox(secret, config)
logwriter = LogWriter(gox)
gox.start()
print "Starting to download fulldepth from mtgox....",
socketbook = gox.orderbook
while socketbook.fulldepth_downloaded == False:
    time.sleep(0.1)
print "Finished."


# data partial path directory
fullpath = os.path.dirname(os.path.realpath(__file__))
if os.name == 'nt':
    partialpath=os.path.join(fullpath + '\\..\\data\\')
else:
    partialpath=os.path.join(fullpath + '/../data/' + site)


"""
def decideto():
  #experimental, not working yet. Decide to sell or buy based on the ticker.

"""


def refreshbook(maxage=180):
    #get the FULL depth (current trade order) (API 2,gzip)
    depthvintage,fulldepth = updatedepthdata(mtgox,maxage)
    entirebook = Book.parse(fulldepth["data"],goxfulldepth=True)
    entirebook.sort()      #sort it
    return entirebook
def printorderbookapi0(length=15,maxage=60):
    entirebook = Book.parse(mtgox.get_depth())
    entirebook.sort()
    #start printing part of the order book (first 15 asks and 15 bids)
    printbothbooks(entirebook.asks,entirebook.bids,length)   #otherwise use the length from the arguments
def bal():
    balance = mtgox.get_balance()
    btcbalance = D(balance['btcs'])
    usdbalance = D(balance['usds'])
    return btcbalance,usdbalance
def get_tradefee():
    return (D(mtgox.get_info()['Trade_Fee'])/100)
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
        print "Your current trading fee is: {:.2%}".format(get_tradefee())
    def do_balance(self,args):
        """Calculate how much fees will cost if you sold off your entire BTC Balance"""
        btcbalance,totalfees,last = calc_fees()
        print_calcedfees(btcbalance,last,totalfees)
        self.do_getfee(self)
    def do_calc(self,amount):
        """Calculate how much fees will cost on X amount\n""" \
        """Give X amount as a paramter ie: calc 50"""
        try:
            amount = D(str(amount))
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
        
    #Shut down all threads cleanly.
    def threadshutdown(self):
        threads = False
        for k,v in threadlist.iteritems():
            v.set()
            threads = True
        if threads:
            print "Shutting down threads..."        

    #CTRL+C Handling
    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt:
            print "Press CTRL+C again to exit, or ENTER to continue."
            try:
                wantcontinue = raw_input()
            except KeyboardInterrupt:
                self.threadshutdown()
                self.do_exit(self)
                return
            self.cmdloop()
        except:                     #catch every exception!
            traceback.print_exc()
            self.cmdloop()


    #start out by printing the order book (the new socket book)
    printOrderBooks(socketbook.asks,socketbook.bids,15)

    #give a little user interface       
    print 'Type exit to exit gracefully or Ctrl+Z or Ctrl+C to force quit'
    print 'Type help to show the available commands'
    print 'sample trade example: '
    print '   buy 2.8 140 145 64 = buys 2.8 BTC between $140 to $145 using 64 chunks'


    def do_asks(self,args):
        """Calculate the amount of bitcoins for sale at or under [pricetarget].\n""" \
        """If 'over' option is given, find coins or at or over [pricetarget]."""
        #Using the Socketbook 

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
        if response == 'over':
            f = lambda price,pricetarget: price >= pricetarget*1E5
        else:
            f = lambda price,pricetarget: price <= pricetarget*1E5
        n_coins = 0.0
        total = 0.0

        for ask in reversed(socketbook.asks):
            if f(ask.price, pricetarget):
                n_coins += ask.volume/1E8
                total += (ask.volume/1E8 * ask.price/1E5)
        print "There are %.11g bitcoins offered at or %s %s USD, worth $%.2f USD in total."  % (n_coins,response, pricetarget, total)

    def do_bids(self,args):
        """Calculate the amount of bitcoin demanded at or over [pricetarget].\n""" \
        """If 'under' option is given, find coins or at or under [pricetarget]"""
        #Using the Socketbook 

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
        if response == 'under':
            f = lambda price,pricetarget: price <= pricetarget*1E5
        else:
            f = lambda price,pricetarget: price >= pricetarget*1E5
        n_coins = 0.0
        total = 0.0

        for bid in socketbook.bids:
            if f(bid.price, pricetarget):
                n_coins += bid.volume/1E8
                total += (bid.volume/1E8 * bid.price/1E5)
        print "There are %.11g bitcoins demanded at or %s %s USD, worth $%.2f USD in total."  % (n_coins,response,pricetarget, total)


    def do_balance(self,args):
        """Shows your current account balance and value of your portfolio based on last ticker price"""
        btc,usd = bal()
        last = D(str(mtgox.get_ticker()['last']))
        print 'Your balance is %s BTC and $%.2f USD ' % (btc,usd)
        print 'Account Value: $%.2f @ Last BTC Price of $%s' % (btc*last+usd,last)


    def do_balancenotifier(self,args):
        """Check your balance every 30 seconds and BEEP and print something out when you receive the funds (either btc or usd)"""
        def bn(firstarg,notifier_stop,btc,usd):
            while(not notifier_stop.is_set()):
                btcnew,usdnew = bal()
                if btcnew > btc or usdnew > usd:
                    last = D(str(mtgox.get_ticker()['last']))
                    print '\nBalance: %s BTC + $%s USD = $%.5f @ $%.5f (Last)' % (btcnew,usdnew,(btcnew*last)+usdnew,last)
                    for x in xrange(0,3):
                        if os.name == 'nt':
                            winsound.Beep(1200,1000)
                            winsound.Beep(1800,1000)
                        else:
                            print '\a\a'
                    btc,usd = btcnew,usdnew
                notifier_stop.wait(30)

        try:
            global notifier_stop
            btc,usd = bal()
            args = stripoffensive(args)
            args = args.split()
            if 'exit' in args:
                print "Shutting down background thread..."
                notifier_stop.set()
            else:   
                notifier_stop = threading.Event()
                threadlist["balancenotifier"] = notifier_stop
                notifier_thread = threading.Thread(target = bn, args=(None,notifier_stop,btc,usd))
                notifier_thread.daemon = True
                notifier_thread.start()
        except Exception as e:
            traceback.print_exc()
            print "An error occurred."
            self.onecmd('help balancenotifier')


    def do_book(self,length):
        """Uses the constantly updated data from the websocket/socket.io depth/trades/ticker channels\n""" \
        """usage: book [length]"""
        try:
            length = stripoffensive(length)
            length = int(length)
            vintage = (time.time() - socketbook.fulldepth_time)
            if vintage > 300:
                print "Starting to download fulldepth from mtgox....",
                gox.client.request_fulldepth()
                while socketbook.fulldepth_downloaded == False:
                    time.sleep(0.1)
                print "Finished."
            printOrderBooks(socketbook.asks,socketbook.bids,length)
        except:
            printOrderBooks(socketbook.asks,socketbook.bids)

    def do_bookfull(self,length):
        """Downloads the API 2 Full Depth at most once every 3 minutes, then prints out the order book."""
        entirebook = refreshbook()
        try:
            length = stripoffensive(length)
            length = int(length)
            printbothbooks(entirebook.asks,entirebook.bids,length)
        except:
            printbothbooks(entirebook.asks,entirebook.bids,15)

    def do_bookquick(self,length):
        """Downloads API 0 getDepth at most once every 60 seconds, then prints out the order book."""
        try:
            length = stripoffensive(length)
            length = int(length)
            printorderbookapi0(length=length)
        except:
            printorderbookapi0(length=15)



    def do_btchistory(self,args):
        """Prints out your entire history of BTC transactions"""
        filename = os.path.join(partialpath + 'mtgox_btchistory.csv')
        download = prompt("Download a new history?",False)
        if download:
            btchistory=mtgox.get_history_btc().decode('utf-8')
            with open(filename,'w') as f:
                f.write(btchistory.encode('utf8'))
                print "Finished writing file."
        print "%s" % btchistory.encode('utf8')                
        csvfile = open(filename, 'rb')
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        fulllist = []
        firstrow = True
        for row in spamreader:
            if firstrow == True:
                keys = row
                firstrow = False
                continue
            eachlist = []
            itemdict = []
            listoflist = []
            for x in xrange(len(row)):
                onelist = [keys[x],row[x]]
                listoflist.append(onelist)
                fulldict = {x[0]:x[1] for x in listoflist}
            fulllist.append(fulldict)

        #print fulllist
        allfees = D('0')
        amtbtcin = D('0')
        valuein = D('0')
        amtbtcout = D('0')
        valueout = D('0')
        for item in fulllist:
            if item["Type"] == "fee":
                onefee = D(item["Value"])
                allfees += onefee.quantize(D('0.00000001'))
            if item["Type"] == "in" or item["Type"] == "out":
                info = item["Info"]
                try:
                    price=D(info[info.find("$")+1:])
                except:
                    price=D(info[info.find("BTC at")+7:info.find("\xe2")-2])
                amount=D(item["Value"])
            if item["Type"] == "in":
                amtbtcin += amount
                valuein += D(price*amount).quantize(D('0.00001'))
            if item["Type"] == "out":
                amtbtcout += amount
                valueout += D(price*amount).quantize(D('0.00001'))


        print "Sum of all fees is: %s BTC" % allfees
        print "Sum of all BTC bought is %s BTC:" % amtbtcin
        print "Sum of all BTC sold is: %s BTC" % amtbtcout
        print "Value of all BTC bought is: $%s" % valuein
        print "Value of all BTC sold is: $%s" % valueout

    def do_usdhistory(self,args):
        """Prints out your entire trading history of USD transactions"""
        filename = os.path.join(partialpath + 'mtgox_usdhistory.csv')
        download = prompt("Download a new history?",False)
        if download:
            usdhistory=mtgox.get_history_usd().decode('utf-8')
            with open(filename,'w') as f:
                f.write(usdhistory.encode('utf8'))
                print "Finished writing file."
        print "%s" % usdhistory.encode('utf8')                
        csvfile = open(filename, 'rb')
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        fulllist = []
        firstrow = True
        for row in spamreader:
            if firstrow == True:
                keys = row
                firstrow = False
                continue
            eachlist = []
            itemdict = []
            listoflist = []
            for x in xrange(len(row)):
                onelist = [keys[x],row[x]]
                listoflist.append(onelist)
                fulldict = {x[0]:x[1] for x in listoflist}
            fulllist.append(fulldict)

        #print fulllist
        allfees = D('0')
        amtusdin = D('0')
        amtusdout = D('0')
        for item in fulllist:
            if item["Type"] == "fee":
                onefee = D(item["Value"])
                allfees += onefee.quantize(D('0.00001'))
            amount=D(item["Value"])
            if item["Type"] == "earned":
                amtusdin+=amount
            elif item["Type"] == "spent":
                amtusdout+=amount
        print "Sum of all fees is: $%s USD" % allfees
        print "Sum of all usd bought is: $%s USD" % amtusdin
        print "Sum of all usd sold is: $%s USD" % amtusdout

    def do_buy(self, args):
        """(market order): buy volume \n""" \
        """(spend-x order): buy $USD$ usd (specify the amount of $USD$, and get the last ticker price-market) \n"""\
        """(limit order): buy volume price \n""" \
        """(spread order): buy volume price_lower price_upper chunks ("random") (random makes chunk amounts slightly different)"""
        # adds a multitude of orders between price A and price B of equal volumed # of chunks on Mtgox.
        try:
            args = stripoffensive(args)
            args = args.split()
            newargs = tuple(decimalify(args))
            if len(newargs) == 1:
                mtgox.order_new('bid',*newargs)
            elif "usd" in newargs:                      #place an order of $X USD
                buyprice = mtgox.get_ticker()["buy"]    
                amt = D(newargs[0]) / D(buyprice)       #convert USD to BTC.
                mtgox.order_new('bid',amt.quantize(bPrec),buyprice)  #goes as a limit order (can be market also if you delete buyprice here)           
            elif not(len(newargs) == 3):
                spread('mtgox',mtgox,'bid', *newargs)
            else:
                raise UserError
        except Exception as e:
            traceback.print_exc()
            print "Invalid args given!!! Proper use is:"
            self.onecmd('help buy')

    def do_sell(self, args):
        """(market order): sell volume \n""" \
        """(spend-x order): buy $USD$ usd (specify the amount of $USD$, and get the last ticker price-market) \n""" \
        """(limit order): sell volume price \n""" \
        """(spread order): sell volume price_lower price_upper chunks ("random") (random makes chunk amounts slightly different)"""
        try:
            args = stripoffensive(args)
            args = args.split()
            newargs = tuple(decimalify(args))
            if len(newargs) == 1:
                mtgox.order_new('ask',*newargs)
            elif "usd" in newargs:                      #place an order of $X USD
                sellprice = mtgox.get_ticker()["sell"]
                amt = D(newargs[0]) / D(sellprice)       #convert USD to BTC.
                mtgox.order_new('ask',amt.quantize(bPrec),sellprice) #goes as a limit order (can be market also if you delete buyprice here)
            elif not(len(newargs) == 3):
                spread('mtgox',mtgox,'ask', *newargs)
            else:
                raise UserError
        except Exception as e:
            traceback.print_exc()
            print "Invalid args given!!! Proper use is:"
            self.onecmd('help sell')
    

    def do_cancel(self,args):
        """Cancel an order by number,ie: 7 or by range, ie: 10 - 25\n""" \
        """Use with arguments after the cancel command, or without to view the list and prompt you"""
        try:
            orders = mtgox.get_orders()['orders']
            orders = sorted(orders, key=lambda x: float(x['price']))
            numorder = 0
            numcancelled = 0            
            useargs = False
            if args:
                useargs = True
            else:
                for order in orders:
                    ordertype="Sell" if order['type'] == 1 else "Buy"
                    numorder += 1
                    if order['status'] == 1:
                        OPX = 'O'
                    elif order['status'] == 2:
                        OPX = 'P'
                    elif order['status'] == 0:
                        OPX = 'X'
                    else:
                        OPX = '|'
                    print '%s = %s %s %s BTC @ $%s %s' % (numorder,ordertype,OPX,order['price'],order['amount'],order['oid'])
                print "Use spaces or commas to seperate order numbers: 1,2,3"
                print "Use a - to specify a range: 1-20. "
            while True:         #loop until quit
                userange=False
                numorder = 0
                if useargs == True:
                    orderlist = args
                    useargs = False
                else:
                    orderlist = ""
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
                            result = mtgox.cancel_one(order['oid'])
                            numcancelled += 1
                    elif str(numorder) in orderlist:
                        result = mtgox.cancel_one(order['oid'])
                        numcancelled += 1
                if numcancelled > 1:
                    print "%s Orders have been Cancelled!!!!!" % numcancelled
        except Exception as e:
            print e
            return

    def do_cancelall(self,args):
        """Cancel every single order you have on the books"""
        mtgox.cancel_all()


    def do_depth(self,args):
        """Shortcut for the 2 depth functions in common.py\n""" \
        """usage: depth (sum/price) (bids/asks)"""
        try:
            args = stripoffensive(args)
            args = args.split()
            mydict = {"buy":socketbook.asks,"bids":socketbook.asks,"bid":socketbook.asks,"sell":socketbook.bids,"ask":socketbook.bids,"asks":socketbook.bids}
            for x in mydict.keys():
                if x in args:
                    args.remove(x)
                    whichbook = mydict[x]
            functlist = ["sum","range","price"]
            for x in functlist:
                if x in args:
                    args.remove(x)
                    newargs = tuple(decimalify(args))
                    func = x
            functdict = {"sum":depthsumrange,"range":depthsumrange,"price":depthprice}[func](whichbook,*newargs,ismtgox=True)
        except:
            print "Invalid args given. Proper use is:"
            self.onecmd('help depth')


    def do_fees(self,args):
        """Loads the fee module to calculate fees"""
        Feesubroutine().cmdloop()


    def do_getaddress(self,args):
        """Generate a new personal bitcoin deposit address for your mtgox account (needs deposit priveleges to work)"""
        mtgox.bitcoin_address()

    def do_lag(self,args):
        """Shows the current Mt.Gox trading engine lag time"""
        lag = mtgox.lag()
        print "Current order lag is %r seconds " % (lag['lag_secs'])

    

    def do_obip(self, args):
        """Calculate the "order book implied price", by finding the weighted\n""" \
        """average price of coins <width> BTC up and down from the spread.\n""" \
        """Order book implied price. Weighted avg price of BTC <width> up and down from the spread.\n""" \
        """Usage: <width> optional:(BTC/USD) \n""" \
        """usage: obip amount "USD"/"BTC"(optional) \n"""
        def obip(amount,isBTCUSD="BTC"):
            amount = float(amount)
            def calc_obip(l,amount,isBTCUSD="BTC"):
                totalBTC, totalprice = 0,0
                if isBTCUSD.upper()=='BTC':
                    for x in l:
                        if totalBTC < amount:
                            totalBTC+=(x.volume/1E8)
                            totalprice+=(x.price/1E5) * (x.volume/1E8)
                            if totalBTC >= amount:
                                totalprice-=(totalBTC-amount) * (x.price/1E5)
                                totalBTC=amount
                                obip=(totalprice/totalBTC)
                else:
                    for x in l:
                        if totalprice < amount:
                            totalBTC+=(x.volume/1E8)
                            totalprice+=(x.price/1E5) * (x.volume/1E8)
                            if totalprice >= amount:
                                overBTC = (totalprice-amount) / (x.price/1E5)
                                totalBTC -= overBTC
                                totalprice -= (x.price/1E5) * overBTC
                                obip=(totalprice/totalBTC)
                return obip,totalBTC

            obips,sbtc = calc_obip(socketbook.asks,amount,isBTCUSD)
            obipb,bbtc = calc_obip(socketbook.bids,amount,isBTCUSD)
            obip = (obips+obipb)/2.0
            if isBTCUSD.upper()=='USD':
                print "The ask side was: %s BTC. The bid side was %s BTC." % (sbtc,bbtc)
            print "The ask side OBIP was: $%.5f. The bid side OBIP was: $%.5f" % (obips,obipb)
            print "The VWAP(OBIP) of BTC, %s %s up and down from the spread is: $%.5f USD." % (amount,isBTCUSD,obip)

        args = stripoffensive(args)
        args = args.split()
        newargs = tuple(args)
        obip(*newargs)


    def do_orders(self,args):
        """Print a list of all your open orders, including pending and lacking enough funds"""
        try:
            args = stripoffensive(args)
            orders = mtgox.get_orders()['orders']
            orders = sorted(orders, key=lambda x: float(x['price']))
            buytotal,selltotal = 0,0
            numbuys,numsells = 0,0
            amtbuys,amtsells = 0,0
            buyavg,sellavg = 0,0
            numorder = 0
            for order in orders:
                ordertype="Sell" if order['type'] == 1 else "Buy"
                numorder += 1
                if order['status'] == 1:
                    OPX = 'O'
                elif order['status'] == 2:
                    OPX = 'P'
                elif order['status'] == 0:
                    OPX = 'X'
                else:
                    OPX = '|'
                print '%s = %s %s %s BTC @ $%s %s' % (numorder,ordertype,OPX,order['price'],order['amount'],order['oid'])
                if order['type'] == 2:
                    buytotal += D(order['price'])*D(order['amount'])
                    numbuys += D('1')
                    amtbuys += D(order['amount'])
                elif order['type'] == 1:
                    selltotal += D(order['price'])*D(order['amount'])
                    numsells += D('1')
                    amtsells += D(order['amount'])
            if amtbuys:
                buyavg = D(buytotal/amtbuys).quantize(cPrec)
            if amtsells:
                sellavg = D(selltotal/amtsells).quantize(cPrec)
            print "There are %s Buys. There are %s Sells" % (numbuys,numsells)
            print "Avg Buy Price: $%s. Avg Sell Price: $%s" % (buyavg,sellavg)
        except Exception as e:
            print e
            return


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
            return s
        except ValueError as e:
            self.onecmd('help readtickerlog')


    def do_readtradehist24(self,args):
        """reading trade history data from a file and gathering stats on it"""
        import tradehistory
        filetype = prompt("Is this a Trade History file (not a full depth file)?",True)
        if filetype:
            tradehistory.readhist24()
        else:
            tradehistory.readdepth()


    def do_spread(self,args):
        """Print out the bid/ask spread"""
        try:
            print "High Bid is: $", socketbook.bid/1E5
            print "Low ask is: $", socketbook.ask/1E5
            print "The spread is: $%f" % socketbook.ask/1E5 - socketbook.bid/1E5
        except:
            self.onecmd('help spread')


    def do_stoploss(self,args):
      #Finished. Works.
        """Usage: stoploss amount of position , avg position price, percent willing to accept\n""" \
        """   ie: stoploss 13.88512098 136.50 95"""
        def stoplossbot(firstarg,stop_event,amount,price,percent):
            try:
                found = False
                while(not stop_event.is_set()):
                    last = D(socketbook.ask)
                    percent = percent / D('100')
                    if price*percent < last:
                        order = mtgox.order_new('ask',amount,protection=False)
                        while found == False:
                            stop_event.wait(2)
                            response = mtgox.get_ask_history(order['data'])
                            if not(response["result"] == "error"):
                                found = True
                        avgprice = response['return']['avg_cost']['display']
                        print "%s Sold with stop-loss @of c %s" % (order['data'],avgprice)
                        stop_event.set()
                    stop_event.wait(2)
            except Exception as e:
                try:    #DEBUGGING ONLY
                    print "Order was: ", order, "Result was: ", result
                except:
                    traceback.print_exc()
                    print "An error occurred."
                    self.onecmd('help stoploss')

        try:
            global stopbot_stop
            args = stripoffensive(args)
            args = args.split()
            newargs = tuple(decimalify(args))
            if 'exit' in args:
                print "Shutting down background thread..."
                stopbot_stop.set()
            else:
                stopbot_stop = threading.Event()
                threadlist["stopbot"] = stopbot_stop
                args = (None,stopbot_stop) + newargs
                stopbot_thread = threading.Thread(target = stoplossbot, args=args)
                stopbot_thread.daemon = True
                stopbot_thread.start()
        except Exception as e:
            traceback.print_exc()
            print "An error occurred."
            self.onecmd('help stoploss')


    def do_ticker(self,arg):
        """Print the entire ticker out or use one of the following options:\n""" \
        """[--buy|--sell|--last|--high|--low|--vol|--vwap|--avg] """
        ticker = mtgox.get_ticker()
        if not arg:
            print "BTCUSD ticker | Best bid: %s, Best ask: %s, Bid-ask spread: %.5f, Last trade: %s, " \
                "24 hour volume: %s, 24 hour low: %s, 24 hour high: %s, 24 hour vwap: %s, 24 hour avg: %s" % \
                (ticker['buy'], ticker['sell'], \
                D(ticker['sell']) - D(ticker['buy']), \
                ticker['last'], ticker['vol'], \
                ticker['low'], ticker['high'], \
                ticker['vwap'],ticker['avg'])
        else:
            try:
                print "BTCUSD ticker | %s = %s" % (arg,ticker[arg])
            except:
                print "Invalid args. Expecting a valid ticker subkey."
                self.onecmd('help ticker')

    def do_ticker2(self,args):
        """Print the entire ticker out or use one of the following options:\n""" \
        """[--buy|--sell|--last|--high|--low|--vol|--vwap|--avg] """
        args = stripoffensive(args)
        ticker = mtgox.get_ticker2()
        svrtime = D(int(ticker["now"]) / 1E6).quantize(D("0.001"))
        if not args:
            print "BTCUSD ticker | Best bid: %s, Best ask: %s, Bid-ask spread: %.5f, Last trade: %s, " \
                "24 hour volume: %s, 24 hour low: %s, 24 hour high: %s, 24 hour vwap: %s, 24 hour avg: %s" % \
                (ticker['buy']['value'], ticker['sell']['value'], \
                D(ticker['sell']['value']) - D(ticker['buy']['value']), \
                ticker['last']['value'], ticker['vol']['value'], \
                ticker['low']['value'], ticker['high']['value'], \
                ticker['vwap']['value'],ticker['avg']['value'])
            print "Time of ticker: ", datetime.datetime.fromtimestamp(svrtime).strftime("%Y-%m-%d %H:%M:%S"), "Ticker Lag: %.3f" % (D(time.time())-svrtime)
        else:
            try:
                print "BTCUSD ticker | %s = %s" % (args,ticker[args])
            except:
                print "Invalid args. Expecting a valid ticker subkey."
                self.onecmd('help ticker2')

    def do_tickerfast(self,args):
        """Print the entire ticker out or use one of the following options:\n""" \
        """[--buy|--sell|--last """
        args = stripoffensive(args)
        ticker = mtgox.get_tickerfast()
        svrtime = D(int(ticker["now"]) / 1E6).quantize(D("0.001"))
        if not args:
            print "BTCUSD ticker | Best bid: %s, Best ask: %s, Bid-ask spread: %.5f, Last trade: %s, "  % \
                (ticker['buy']['value'], ticker['sell']['value'], \
                D(ticker['sell']['value']) - D(ticker['buy']['value']), \
                ticker['last']['value'])
            print "Time of ticker: ", datetime.datetime.fromtimestamp(svrtime).strftime("%Y-%m-%d %H:%M:%S"), "Ticker Lag: %.3f" % (D(time.time())-svrtime)
        else:
            try:
                print "BTCUSD ticker | %s = %s" % (args,ticker[args])
            except:
                print "Invalid args. Expecting a valid ticker subkey."
                self.onecmd('help tickerfast')


    def do_tradehist24(self,args):
        """Download the entire trading history of mtgox for the past 24 hours. Write it to a file"""
        print "Starting to download entire trade history from mtgox....",
        eth = mtgox.entire_trade_history()
        filename = os.path.join(partialpath + 'mtgox_entiretrades.txt')
        with open(filename,'w') as f:
            depthvintage = str(time.time())
            f.write(depthvintage)
            f.write('\n')
            json.dump(eth,f)
            f.close()
            print "Finished."


    def do_updown(self,args):
        """Logs ticker to file, spits out an alert and beeps if last price is above or below the range given\n""" \
        """Range window is modified and readjusted\n""" \
        """NOTE: RUNS AS A BACKGROUND PROCESS!!!!!!\n""" \
        """usage: updown <low> <high>\n""" \
        """Shutdown: updown exit  """
        def tickeralert(firstarg,tickeralert_stop):
            try:
                low, high = floatify(args.split())
            except Exception as e:
                print "You need to give a high and low range: low high"
                return
            #Log lastprice to the ticker log file
            with open(os.path.join(partialpath + 'mtgox_last.txt'),'a') as f:
                while(not tickeralert_stop.is_set()):
                    ticker =mtgox.get_ticker()
                    last = float(ticker['last'])
                    text = json.dumps({"time":time.time(),"lastprice":last})
                    f.write(text)
                    f.write("\n")
                    f.flush()
                    if last > low and last < high:
                        #last falls between given variance range, keep tracking
                        pass
                    elif last >= high:
                        print "ALERT!! Ticker has risen above range %s-%s. Price is now: %s" % (low,high,last)
                        for x in range(2,25):           #ascending beeps
                            if os.name == 'nt':
                                winsound.Beep(x*100,90)  #frequency(Hz),duration(ms)
                            else:
                                print '\a\a\a\a\a\a'
                        low = high - 0.5
                        high = low + 3
                        #decideto()
                        #lowsell = low*(1+txfee*2)
                        #spread('mtgox',mtgox,'sell', 1, lowsell, lowsell+1, 3)
                        print "New range is: %s-%s" % (low,high)
                    elif last == low or last == high:
                        print "ALERT!! Ticker is exactly on the boundary of %s" % (last)
                    else:
                        print "ALERT!! Ticker has fallen below range %s-%s. Price is now: %s" % (low,high,last)
                        for x in range(25,2,-1):        #descending beeps
                            if os.name == 'nt':
                                winsound.Beep(x*100,90)  #frequency(Hz),duration(ms)
                            else:
                                print '\a\a\a\a\a\a'
                        high = low + 1
                        low = high -3
                        #decideto()
                        #spread('mtgox',mtgox,'buy', 1, low+1, high-1, 5)
                        print "New range is: %s-%s" % (low,high)
                    tickeralert_stop.wait(40)

        try:
            global tickeralert_stop
            args = stripoffensive(args)
            if args == 'exit':
                print "Shutting down background thread..."
                tickeralert_stop.set()
            else:
                tickeralert_stop = threading.Event()
                threadlist["tickeralert"] = tickeralert_stop
                tickeralert_thread = threading.Thread(target = tickeralert, args=(None,tickeralert_stop))
                tickeralert_thread.daemon = True
                tickeralert_thread.start()
        except Exception as e:
            traceback.print_exc()
            print "An error occurred."
            self.onecmd('help updown')


    def do_withdraw(self,args):
        """Withdraw Bitcoins to an address (needs withdraw priveleges to work)"""
        address = raw_input("Enter the address you want to withdraw to: ")
        normalfee = prompt("The default fee is 0.0005. Accept + Deduct this from the amount?",True)
        if normalfee == False:
            fee = D(raw_input("Enter the fee of the transaction: "))
        else:
            fee = D('0.0005')
        totalbalance = prompt("Do you want to withdraw your ENTIRE balance?",False)
        if totalbalance == False:
            amount = D(raw_input("Enter the amount of BTC to withdraw: "))
        else:
            amount,_ = bal()
        mtgox.bitcoin_withdraw(address,amount*D(1E8),fee*D(1E8))


    def do_EOF(self,args):        #exit out if Ctrl+Z is pressed
        """Exits the program"""
        return self.do_exit(args)

    def do_exit(self,args):      #standard way to exit
        """Exits the program"""   
        print "\n"
        print "Session Terminating......."
        print "Exiting......"           
        return True

    def help_help(self):
        print 'Prints the help screen'
        

if __name__ == '__main__':
    Shell().cmdloop()