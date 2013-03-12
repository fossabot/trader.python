#!/usr/bin/env python
# Created by genBTC 3/10/2013
# adds a multitude of orders between price A and price B of equal sized # of chunks on Mtgox.
# now this is turning into a complete command line Client with a menu

import mtgoxhmac
import cmd
import time
#import readline
from book import Book, Order

mtgox = mtgoxhmac.Client()

#get 24 hour trade history - cached
#alltrades=mtgox.get_trades()

#display info like account balance & funds
#print mtgox.get_info()

# trade function including Chunk Trade spread logic
def trade(side, size, price_lower, price_upper, chunks):
    loop_price = float(price_lower)
    for x in range (0, int(chunks)):
        price_range = float(price_upper) - float(price_lower)
        price_chunk = float(price_range)/ float(chunks)
        chunk_size = float(size) / float(chunks)
        if side == 'buy':
            print 'Buying...', "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
            mtgox.buy_btc(amount=chunk_size, price=loop_price)
        elif side == 'sell' :
            print 'Selling...', "Chunk # ",x+1," = ",chunk_size," BTC @ $", loop_price
            mtgox.sell_btc(amount=chunk_size, price=loop_price) 
        loop_price += price_chunk
 
#start printing part of the order book (first 10 asks and 10 bids)
def printorderbook():
    #get current trade depth book
    entirebook=Book.parse(mtgox.get_depth())
    entirebook.sort()
    for o in reversed(entirebook.asks[:15]):
        print '                              $',o.price,o.size, '--ASK-->'
    print '                    |||||||||||'
    for o in entirebook.bids[:15]:
        print '<--BID--$',o.price,o.size
        
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
        amount = float(amount)
        btcbalance,totalfees,last = calc_fees()
        print_calcedfees(amount,last,totalfees)
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
    def __init__(self):
        cmd.Cmd.__init__(self)
        # The prompt for a new user input command
        self.prompt = 'Main CMD>'
        self.use_rawinput = False
        self.onecmd('help')
    #give a little user interface
    print 'Type exit to exit gracefully or Ctrl+Z or Ctrl+C to force quit'
    print 'Type help to show the available commands'
    print 'sample trade example: '
    print '   buy 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks'
    
    def emptyline(self):      
        pass                #Do nothing on empty input line instead of re-executing the last command
    #start out by printing the order book and the instructions
    printorderbook()

#pass arguments back up to trade() function
    def do_buy(self, arg):
        """Sell some BTC between price A and price B of equal sized chunks"""
        """Format is buy amount(BTC) price_lower price_upper chunks(#)"""
        """ie:   buy 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks"""
        try:
            size, price_lower, price_upper, chunks = arg.split()
        except:
            print "Incomplete Command. Retry"
            return
        trade('buy', size, price_lower, price_upper, chunks)
 
    def do_sell(self, arg):
        """Sell some BTC between price A and price B of equal sized chunks"""
        """Format is sell amount(BTC) price_lower price_upper chunks(#)"""
        """ie:   sell 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks"""
        try:
             size, price_lower, price_upper, chunks = arg.split()
        except:
            print "Incomplete Command. Retry"
            return
        trade('sell', size, price_lower, price_upper, chunks)
        
    def do_book(self,arg):
        """Download and print the order book of current bids and asks"""
        printorderbook()
        
    def do_orders(self,arg):
        """Print a list of all your open orders, including pending"""
        time.sleep(1)
        orders = mtgox.get_orders()['orders']
        for order in orders:
            if order['status'] == 1:
                if order['type']== 1:
                    type="Sell"
                else:
                    type="Buy"
                print type,'order %r  Price $%.5f @ Amount: %.5f' % (str(order['priority']),float(order['price']),float(order['amount']))
            elif order['status'] == 2:
                print 'order %r  PENDING Amount: %.5f or not enough Funds' % (str(order['priority']),float(order['amount']))
    def do_cancelall(self,arg):
        """Cancel every single order you have on the books"""
        mtgox.cancelall()
        print "All Orders have been Cancelled!!!!!"
    def do_lag(self,arg):
        """Shows the current Mt.Gox trading engine lag time"""
        lag = mtgox.lag()
        print 'Current order lag is %r' % (lag['lag_secs'])
    def do_balance(self,arg):
        """Shows your current account balance and value of your portfolio based on last ticker price"""
        balance = mtgox.get_balance()
        last = mtgox.get_ticker()['last']
        print 'Your balance is %r BTC and $%.2f USD ' % (float(balance['btcs']),float(balance['usds']))
        print 'Account Value: $%.2f @ Last BTC Price of %.2f' % (float(balance['btcs'])*last+float(balance['usds']),last)
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
    #the trading command prompt did not allow cmd.exe to store a history beyond multiple sessions
    #now it does store a history but we lose tab completion.
    Shell().cmdloop()
