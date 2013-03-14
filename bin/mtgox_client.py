#!/usr/bin/env python
# Created by genBTC 3/10/2013
# adds a multitude of orders between price A and price B of equal sized # of chunks on Mtgox.
# now this is turning into a complete command line Client with a menu

import mtgoxhmac
import cmd
import time
from book import Book, Order
from common import *
import cjson

class InputError(Exception):
    def __init__(self, message, arg=None, kind=None):
        if arg:
            self.arg = arg
            self.msg = "Invalid %s:" % (kind if kind else "argument")
        else:
            self.msg = message
            self.arg = u""
        Exception.__init__(self, message)
mtgox = mtgoxhmac.Client()

#get 24 hour trade history - cached
#alltrades=mtgox.get_trades()

#display info like account balance & funds
#print mtgox.get_info()
class JsonParser:
    @staticmethod
    def parse(obj, force = False):
        u"Parse json-strings."
        # cjson is fast and good enough for our purposes
        json = cjson.decode(obj)
        if u"error" in json and not force:
            raise MtGoxError(json[u"error"])
        else:
            return json

    @staticmethod
    def build(obj):
        u"Build json-strings from object(s)."
        return cjson.encode(obj)

class DepthParser(object):
    def __init__(self, currencyDecimals, args = []):
        self._cPrec = Decimal(1) / 10 ** currencyDecimals
        self.__sides = ("asks","bids")
        try:
            for arg,value in (arg.split("=") for arg in args):
                arg = arg.lower()
                if hasattr(self, arg):
                    try:
                        setattr(self, arg, value)
                    except InvalidOperation:
                        raise InputError( "Invalid value: %s" % value,
                                          kind = "value", arg = value )
                    except ValueError:
                        raise InputError( "Invalid value: %s" % value,
                                          kind = "value", arg = value )
                else:
                    raise InputError("Invalid argument: %s" % arg, arg = arg)
        except ValueError:
            raise InputError("Invalid argument")
            
    @property
    def side(self):
        try:
            return self._side
        except AttributeError:
            return None

    @side.setter
    def side(self,value):
        if value:
            if value == "bids":
                self._side = value
                self.__sides = ("bids",)
            elif value == "asks":
                self._side = value
                self.__sides = ("asks",)
            else:
                raise InputError( "Invalid value : %s" % value,
                                   kind = "value", arg = value )
        else:
            self._side = None
            self.__sides = ("asks","bids")

    @property
    def low(self):
        try:
            return self._minPrice
        except AttributeError:
            return None

    @low.setter
    def low(self, value):
        if value:
            self._minPrice = Decimal(value)
        else:
            self._minPrice = None

    @property
    def high(self):
        try:
            return self._maxPrice
        except AttributeError:
            return None

    @high.setter
    def high(self, value):
        if value:
            self._maxPrice = Decimal(value)
        else:
            self._maxPrice = None

    @property
    def amount(self):
        try:
            return self._maxAmount
        except AttributeError:
            return None

    @amount.setter
    def amount(self, value):
        if value:
            self._maxAmount = Decimal(value)
        else:
            self._maxAmount = None
        
    @property
    def value(self):
        try:
            return self._maxValue
        except AttributeError:
            return None

    @value.setter
    def value(self, value):
        if value:
            self._maxValue = Decimal(value)
        else:
            self._maxValue = None
        
    @property
    def steps(self):
        try:
            return self._steps
        except AttributeError:
            return None

    @steps.setter
    def steps(self, value):
        if value:
            self._steps = int(value)
        else:
            self._steps = False
        
    @property
    def iv(self):
        try:
            return self._iv
        except AttributeError:
            return False

    @iv.setter
    def iv(self, value):
        self._iv = self.readBool(value)
        
    @property
    def full(self):
        try:
            return self._full
        except AttributeError:
            return False

    @iv.setter
    def full(self, value):
        self._full = self.readBool(value)

    @property
    def cumulate(self):
        try:
            return self._cumulate
        except AttributeError:
            return False

    @cumulate.setter
    def cumulate(self, value):
        self._cumulate = self.readBool(value)
            
    def readBool(self, value):
        if value:
            if isinstance(value, str):
                try:
                    value = {"true":True,"false":False}[value.lower()]
                except KeyError:
                    raise InputError( "Invalid value : %s" % value,
                                       kind = "value", arg = value )
            return bool(value)
        else:
            return False
    def _stepList(self, orders, side, min, max):
        u"Slice a big list of orders and merge each slice to one order," + \
        u" lists of bids needs to be reversed when passed as argument."
        stepList = list()
        if side == "asks":
            stepSize = (max - min) / self.steps
            # Price increases for each ask
            stepEnd = min + stepSize
            withinStep = lambda orderPrice: orderPrice <= stepEnd
        else:
            # Reverse if not allready done (roughly tuple/list, not generator)
            if hasattr(orders, "__getitem__"):
                if orders[-1] < orders[0]:
                    orders = reversed(orders)
            # Price decreases for each bid
            stepSize = (max - min) * -1 / self.steps
            withinStep = lambda orderPrice: orderPrice >= stepEnd
            stepEnd = max + stepSize
        if self.iv:
            # Values included in orders
            calcStep = lambda amount, orderAmount, orderPrice, value: \
                ( amount + orderAmount , value + (orderAmount * orderPrice) )
        else:
            # Don't include value
            calcStep = lambda amount, orderAmount, orderPrice, value: \
                ( amount + orderAmount, False )
        amount,value,stamp = 0,0,0
        for order in orders:
            orderPrice  = order[0]
            orderAmount = order[1]
            orderStamp = time.time()
            price  = orderPrice
            if withinStep(orderPrice):
                # Return total amount and value of step
                amount, value = calcStep(amount, orderAmount, orderPrice, value)
                price         = orderPrice
                stamp = time.time()
            else:
                stepList.append(
                    self._manipulateOrder(
                        dict(),
                        price_int  = price,
                        amount_int = amount,
                        stamp      = stamp,
                        precision  = self._cPrec,
                        iv         = value
                        )
                    )
                # Set Amount,Value,Stamp to this order's values
                if not self.cumulate:
                    amount, value = calcStep(0, orderAmount, orderPrice, 0)
                stamp = orderStamp
                # Set next step end
                stepEnd += stepSize
        else:
            if withinStep(price):
                # Add step if orders has been parsed since last step was added
                stepList.append(
                    self._manipulateOrder(
                        dict(),
                        price_int  = price,
                        amount_int = amount,
                        stamp      = stamp,
                        precision  = self._cPrec,
                        iv         = value
                        )
                    )
        return stepList

    def _stripRange(self, orders, side, minPrice, maxPrice):
        u"Strip list of all orders outside of the range between minPrice" + \
        u" and maxPrice. All generator-objects is treated like they're"   + \
        u" allready reversed when parsing bids."
        if side == "asks":
            # Allow all orders above minPrice
            withinRange = lambda price: int(price) >= minPrice
            # Break when iteration has reached order above maxPrice
            breakPoint  = lambda price: int(price) >  maxPrice
        else:
            if hasattr(orders, "__getitem__"):
                if orders[-1] < orders[0]:
                    orders = reversed(orders)
            # Allow all orders below maxPrice
            withinRange = lambda price: int(price) <= maxPrice
            # Break when iteration has reached order below minPrice
            breakPoint  = lambda price: int(price) <  minPrice
        # Iterate over list,
        #  Asks: Low  -> High
        #  Bids: High -> Low
        for order in orders:
            if withinRange(order[u"price_int"]):
                if breakPoint(order[u"price_int"]):
                    break
                else:
                    yield order
        
            
    def process(self, json, raw = True):
        u"Parse depth-table from Mt.Gox, returning orders matching arguments"
        # Check if user has applied any arguments
        steps     = self.steps
        oMinPrice = self.low
        oMaxPrice = self.high
        maxAmount = self.amount
        maxValue  = self.value
        cumulate  = self.cumulate
        iv        = self.iv
        # Get the decimal precision for currency
        cPrec    = self._cPrec
        bPrec    = Decimal("0.00000001")
        # Setup empty table
        gen      = (i for i in json.iteritems() if i[0] not in ("asks","bids"))
        table    = dict(( (key, value) for key, value in gen ))
        if maxAmount: maxAmount = int(maxAmount / bPrec)
        if maxValue:  maxValue  = int(maxValue / cPrec / bPrec)
        if self.side:
            if self.side == "asks":
                table["bids"] = []
            else:
                table["asks"] = []
        else:
            table["gap"] = dict()
            table["gap"]["upper"]     = json["asks"][0][0]
            table["gap"]["upper_int"] = int(json["asks"][0][0])
            table["gap"]["lower"]     = json["bids"][-1][0]
            table["gap"]["lower_int"] = int(json["bids"][-1][0])
        for side in self.__sides:
            # Parse sides independently
            orders = json[side]
            # Read lowest and highest price of orders on current side
            lowest  = orders[0][0]
            highest = orders[-1][0]
            print "lowest %r and highest %r" % (lowest,highest)
            # Convert minimum and maximum price from arguments to int
            #  and check if any orders are within that range.
            if oMinPrice == None: minPrice = None
            else:
                minPrice = oMinPrice
                if minPrice > highest:
                    # Argument input totally out of range, return empty
                    table[side] = []
                    continue
                elif minPrice < lowest:
                    # Adjust argument to range
                    minPrice = lowest
            if oMaxPrice == None: maxPrice = None
            else:
                maxPrice = oMaxPrice
                if maxPrice < lowest:
                    # Argument input totally out of range, return empty
                    table[side] = []
                    continue
                elif maxPrice > highest:
                    # Adjust argument to range
                    maxPrice = highest
            # Check wether argument input is within the range of
            # the table returned from Mt.Gox.
            if any(( steps,
                     minPrice,
                     maxPrice,
                     maxAmount,
                     maxValue,
                     cumulate,
                     iv )):
                if any((minPrice, maxPrice)):
                    # Get generator yielding orders within given pricerange.
                    if minPrice == None: minPrice = lowest
                    if maxPrice == None: maxPrice = highest
                    orders = self._stripRange(
                        orders,
                        side,
                        minPrice,
                        maxPrice
                        )
                if any((maxAmount, maxValue)):
                    # Filter orders from price and out, only keeping those
                    #  that have either lower value or amount (cumulated).
                    orders = self._processList(
                        orders, side,
                        precision = cPrec,
                        cumulate  = False if steps else cumulate,
                        maxAmount = maxAmount,
                        maxValue  = maxValue,
                        iv        = False if steps else iv
                        )
                elif not steps and any((iv, cumulate)):
                    # If no other option is set except possibly min-/maxPrice,
                    #  add value-item to orders and/or cumulate list.
                    orders = self._processList(
                        orders, side,
                        precision = cPrec,
                        cumulate  = cumulate,
                        iv        = iv
                        )
                if steps:
                    if any((maxAmount, maxValue, minPrice, maxPrice)) and orders:
                        # Slice list into <steps> slices and then merge
                        #  them into one order per slice.
                        if any((maxAmount, maxValue)):
                            if side == "asks":
                                min = orders[0][0]
                                max = orders[-1][0]
                            else:
                                min = orders[-1][0]
                                max = orders[0][0]
                        else:
                            min = minPrice
                            max = maxPrice
                        orders = self._stepList(
                            orders, side,
                            min, max
                            )
                        # Flip back orderlist and resturn
                        if side == "bids":
                            try:
                                # Reverse list from processList
                                orders = reversed(orders)
                            except TypeError:
                                # Reverse generator from stripRange
                                orders = list(orders)
                                orders.reverse()
                    else:
                        # Grab speciefied amount of orders closest to price.
                        if side == "asks":
                            orders = orders[:steps]
                        else:
                            orders = orders[steps*-1:]
                        if cumulate or iv:
                            # Iterate and sum previous orders
                            orders = self._processList(
                                orders, side,
                                precision = cPrec,
                                cumulate  = cumulate,
                                iv        = iv
                                )
                            # Flip back orderlist and resturn
                            if side == "bids": orders = reversed(orders)
                else:
                    # Flip back orderlist and resturn
                    if not isinstance(orders, list): orders = list(orders)
                    if side == "bids": orders = reversed(orders)
            table[side] = list(orders)
        json = {
                "return":table,
                "result":"success"
                }
        return json
        #return JsonParser.build(json) if raw else json
    def _processList(self,
            orders, side,
            cumulate  = False,
            precision = None,
            maxAmount = False,
            maxValue  = False,
            iv        = False):
        u"Iterates over orders. Adds value and/or cumulate amounts. If list" + \
        u" is a generator it is bids being parsed the generator needs to"    + \
        u" contain a reversed list."
        latestStamp = 0
        totalA  = 0
        totalV  = 0
        current = []
        # Reverse bid-orders if not allready done or if object is a generator.
        if side == "bids" and hasattr(orders, "__getitem__"):
            if orders[1][0] < orders[0][0]:
                orders = reversed(orders)
        # Set up lambdas to get rid of some code when iterating over orders.
        if iv:
            # Generated orders will Include Values, ->
            if cumulate:
                # -> and also be cumulated.
                lambda_add = lambda order, amount, totalA, value, totalV: \
                    self._manipulateOrder(
                        order,
                        amount_int = totalA,
                        precision  = precision,
                        iv         = totalV
                        )
            else:
                # -> but will not be cumulated.
                lambda_add = lambda order, amount, totalA, value, totalV: \
                    self._manipulateOrder(
                        order,
                        amount_int = amount,
                        precision  = precision,
                        iv         = value
                        )
        else:
            # Generated orders will not include values, ->
            if cumulate:
                # -> but will be cumulated.
                lambda_add = lambda order, amount, totalA, value, totalV: \
                    self._manipulateOrder(
                        order,
                        amount_int = totalA,
                        precision  = precision
                        )
            else:
                # -> neither will they be cumulated.
                lambda_add = lambda order, amount, totalA, value, totalV: \
                    self._manipulateOrder(
                        order,
                        amount_int = amount,
                        precision  = precision
                        )
        for order in orders:
            # Read each order, decrementing by price if bids
            if maxAmount and totalA > maxAmount: break
            if maxValue and totalV > maxValue: break
            amount = order[1]
            price  = order[0]
            value   = amount * price
            # Increase total amount and total value in currency
            totalA += amount
            totalV += value
            # Generate new order and append to (current) orders
            order   = lambda_add(order, amount, totalA, value, totalV)
            current.append(order)

        return current
    def _manipulateOrder(self, order,
            price_int  = False,
            amount_int = False,
            stamp      = False,
            precision  = False,
            iv         = False):
        u"Update existing order with new data such as price, amount or value."
        #print "AMOUNT IS: ",amount_int, "BTC and PRICE IS: $",price_int
        bPrec = Decimal("0.00000001")
        if not any([price_int, amount_int, stamp, precision, iv]):
            return order
        if price_int:
            if precision:
                # Converting price to decimal with proper length
                price = Decimal(price_int).quantize(precision)
                # Saving as float for cjson encoding
                order[0]     = float(price)
                #order["price_int"] = price_int
            else:
                raise AttributeError("precision")
        if amount_int:
            # Converting amount to decimal with proper length
            amount = Decimal(amount_int).quantize(bPrec)
            # Saving as float for cjson encoding
            order[1] = float(amount)
        if iv:
            # Adds BTC value in currency to result
            value = iv
            value = value.quantize(precision)
            order[0] = float(value)
        return order

    
def printorderbook(size):
    #get current trade order book (depth)
    entirebook=Book.parse(mtgox.get_depth())
    entirebook.sort()
    #start printing part of the order book (first 15 asks and 15 bids)
    if size is '':
        uglyprintbooks(entirebook.asks,entirebook.bids,15)
    else:
        uglyprintbooks(entirebook.asks,entirebook.bids,int(size))
        
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
    def emptyline(self):      
        pass                #Do nothing on empty input line instead of re-executing the last command
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = 'MtGox CMD>'      # The prompt for a new user input command
        self.use_rawinput = False
        self.onecmd('help')
    #give a little user interface
    print 'Type exit to exit gracefully or Ctrl+Z or Ctrl+C to force quit'
    print 'Type help to show the available commands'
    print 'sample trade example: '
    print '   buy 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks'
    

    #start out by printing the order book and the instructions
    printorderbook(15)
    
    def do_new(self,args):
        u"Takes arguments: (bid|ask), (btc|usd), amount, price=optional "
        #currency = opts.currency.upper() if opts.currency else self.standard
        decimals = 5
        bPrec = Decimal("0.00000001")
        cPrec = Decimal(Decimal(1) / 10 ** decimals)
        # if args > 9:
            # try:
                # kind, opts, price, amount = args.split()
                # amount = Decimal(amount)
            # except ValueError:
                # try:
                    # kind, opts, price  = args.split()
                # except:
                    # raise InputError("Expected 4 or 3 arguments, got %s" % len(args))
            
        # else:
            # raise InputError("Expected 4 or 3 arguments, got %s" % len(args))
        if len(args.split()) > 3:
            kind,opts,amount,price = args.split()  
        else: 
            price = None
            try:
                kind,opts,amount = args.split()
            except:
                raise InputError("Expected 3 or 4 arguments, got %s" % len(args.split()))
        amount = Decimal(amount)
        if price:
            price = Decimal(price)
            # Create order with specified price and amount
            if opts == 'usd':
                # Convert amount specified in currency (value) to BTC
                amount = amount / price
        else:
            # Generate order with a certain amount or value
            side   = "bids" if kind == "ask" else "asks"
            json   = mtgox.get_depth()
            depth  = DepthParser(decimals)
            depth.side  = side
            if opts == 'btc':
                # Get price
                depth.steps  = 15
                depth.amount = amount
                json  = depth.process(json, raw = False)
                print json 
                print "That was the json after depth.process"
                price = json["return"][side][0][0]
                print "this is the price is opts = btc", price
            else:
                # Amount given in currency-value.
                depth.value = amount
                depth.iv    = True
                # Convert value to to int
                total = amount
                # Get price and amount
                orders  = depth.process(json, raw = False)[side]
                current = 0
                amount  = 0
                order   = orders.pop(0)
                while orders:
                    # Count amount of all orders up to the last one.
                    current += Decimal(order[0])
                    amount  += Decimal(order[1])
                    order    = orders.pop(0)
                else:
                    # Take price and the rest of the amount that's needed.
                    rest   = total - current
                    price  = Decimal(order[0])
                    amount = current + ( rest / price )
        amount, price = str(amount), str(price)
        #return self.api.add_order(kind, amount, price, currency)
        print "kind ", kind, " amount ", amount, " price ", price
    def do_updown(self,arg):
        try:
            low, high = arg.split()
            low = float(low)
            high = float(high)
            #entirebook=Book.parse(mtgox.get_depth())
            #entirebook.sort()
            entirebook = process(mtgox.get_depth())
            type (entirebook)
            print entirebook
            
        except:
            print "You need to give a high and low range: low high"
        partialpath=os.path.join(os.path.dirname(__file__) + '../data/')
        while True:
            last = float(mtgox.get_ticker()['last'])
            f = open(os.path.join(partialpath + 'mtgox_last.txt'),'a')
            text = json.dumps({"time":time.time(),"lastprice":last})
            f.write(text)
            f.write("\n")
            f.close()
            if last > low and last < high:
                #last falls between given variance range, keep tracking
                time.sleep(30)
            elif last >= high:
                print "then make some sales mtgox.sell_btc"
                
            else:
                #spread('mtgox',mtgox,'buy', 111, last, low, 5)
                print "then make some buys- mtgox.buy_btc"

            #time(sleep,30)
                
                    
                
#pass arguments back to spread() function in common.py
    def do_buy(self, arg):
        """Sell some BTC between price A and price B of equal sized chunks"""
        """Format is buy amount(BTC) price_lower price_upper chunks(#)"""
        """ie:   buy 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks"""
        try:
            size, price_lower, price_upper, chunks = arg.split()
            spread('mtgox',mtgox,'buy', size, price_lower, price_upper, chunks)
        except:
            try:
                size,price_lower = arg.split()
                spread('mtgox',mtgox,'buy', size, price_lower)
            except:
                print "Invalid args given. Expecting: size price"   
    def do_sell(self, arg):
        """Sell some BTC between price A and price B of equal sized chunks"""
        """Format is sell amount(BTC) price_lower price_upper chunks(#)"""
        """ie:   sell 6.4 40 41 128 = buys 6.4 BTC between $40 to $41 using 128 chunks"""
        try:
            size, price_lower, price_upper, chunks = arg.split()
            spread('mtgox',mtgox,'sell', size, price_lower, price_upper, chunks)
        except:
            try:
                size,price_lower = arg.split()
                spread('mtgox',mtgox,'sell', size, price_lower)
            except:
                print "Invalid args given. Expecting: size price" 
        
    def do_book(self,size):
        """Download and print the order book of current bids and asks of depth $size"""
        printorderbook(size)
        
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
