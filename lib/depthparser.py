#!/usr/bin/env python
from decimal import Decimal
import cjson
import sys
import time

class InputError(Exception):
    def __init__(self, message, arg=None, kind=None):
        if arg:
            self.arg = arg
            self.msg = "Invalid %s:" % (kind if kind else "argument")
        else:
            self.msg = message
            self.arg = u""
        Exception.__init__(self, message)

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
            withinRange = lambda price: iprice >= minPrice
            # Break when iteration has reached order above maxPrice
            breakPoint  = lambda price: price >  maxPrice
        else:
            if hasattr(orders, "__getitem__"):
                if orders[-1] < orders[0]:
                    orders = reversed(orders)
            # Allow all orders below maxPrice
            withinRange = lambda price: price <= maxPrice
            # Break when iteration has reached order below minPrice
            breakPoint  = lambda price: price <  minPrice
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
            print "The else case of process() meaning self.side was not given"
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
            print "Lowest %r and Highest %r" % (lowest,highest)
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
            iv        = True):
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
#            if maxAmount and totalA > maxAmount: break
#            if maxValue and totalV > maxValue: break
            amount = order[1]
            price  = order[0]
            value   = amount * price
            # Increase total amount and total value in currency
            totalA += amount
            totalV += value
            # Generate new order and append to (current) orders
            order   = lambda_add(order, amount, totalA, value, totalV)
            current.append(order)
#        print current
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
                order[0] = float(price)
            else:
                raise AttributeError("precision")
        if amount_int:
            # Converting amount to decimal with proper length
            amount = Decimal(amount_int).quantize(bPrec)
            # Saving as float for cjson encoding
            order[1] = float(amount)
        if iv:
            value = iv
            value = float(Decimal(value).quantize(precision))
            order.append(value)
        return order

def goxnewcalc(mtgox,args):
# 	u"Takes arguments: (bid|ask), (btc|usd), amount, price=optional"
    decimals=5
    bPrec = Decimal("0.00000001")
    cPrec = Decimal(Decimal(1) / 10 ** decimals)
    if len(args.split()) > 3:
        kind,opts,amount,price = args.split()  
    else: 
        price = None
        try:
            kind,opts,amount = args.split()
        except ValueError:
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
        totalamount = amount
        totalprice = 0
        if opts == 'btc':
            # Get price
            print 'How do you want to slice this list'
            depth.steps  = raw_input()
            depth.amount = amount
            json  = depth.process(json, raw = False)
            price = json["return"][side][0][0]
            print "this is the price is opts = btc", price
        else:
            # Amount given in currency-value.
            depth.value = amount
            depth.iv    = True
            orders  = depth.process(json, raw = False)
            orders = orders["return"][side]
            for order in orders:
                # Count amount of all orders up to the last one.
                totalprice += Decimal(order[2])
                totalamount  += Decimal(order[1])
                # Take price and the rest of the amount that's needed.
            avgprice  = totalprice / totalamount
    #amount, price = str(amount), str(price)
    avgprice = price

    #return self.api.add_order(kind, amount, price, currency)
    print "kind ", kind, " totalamount ", float(totalamount), " avg price ", float(avgprice), "total price ", float(totalprice)