#!/usr/bin/env python
# will parse any json book in standard form

import decimal
from decimal import Decimal

class Order(object):
    def __init__(self, price, size):
        self.price = price
        self.size = size
    def __repr__(self):
        return str([self.price,self.size])   
    def __getitem__(self,index):
        alist=[self.price,self.size]
        return alist[index]
    
class Book(object):
    @classmethod
    def parse(cls, d, isbitfloor=False):
        def parse_side(arr):
            orders = []
            for a in arr:                       #iterate over the array
                price = str(a[0])
                size = str(a[1])
                # if len(price) >= 11:          #replaced with isbitfloor=False
                #     if price[-9] == '.':
                #         if price[-1] and price[-2] == '0':
                if isbitfloor:                                    #all bitfloor data starts as 8 decimals
                    price = Decimal(price).quantize(Decimal('0.01'))        #valid prices are 2 decimals
                    size = Decimal(size).quantize(Decimal('0.00001'))       #valid sizes are 5 decimals
                else:  #every other site
                    if len(price) in (2,4):            #if the price is too short (ie 47 or 47.1)  then
                        price = Decimal(price).quantize(Decimal('0.01'))    #pad it to 2 decimals
                    else:
                        price = Decimal(price)                          
                    if '.' not in size:                 #if the size is an integer and has no dot, then
                        size = Decimal(size).quantize(Decimal('0.1'))       #pad it to 1 decimal
                    size = Decimal(size)
                orders.append(Order(price,size))        #generate this side of the book as a class Order object
            return orders                               #and return it

        bids = parse_side(d['bids'])
        asks = parse_side(d['asks'])
        return cls(bids, asks)

    def __init__(self, bids, asks):
        self.bids = bids
        self.asks = asks

    # def __getitem__(self,index):
    #     return self.index(index)

    def sort(self):
        self.bids.sort(key=lambda o: o.price, reverse=True)
        self.asks.sort(key=lambda o: o.price)

    def flatten(self, increment):
        def floor_inc(n):
            return (Decimal(str(n))/Decimal(increment)).quantize(Decimal('1'), rounding=decimal.ROUND_DOWN)*Decimal(increment)
        def ceil_inc(n):
            return (Decimal(str(n))/Decimal(increment)).quantize(Decimal('1'), rounding=decimal.ROUND_UP)*Decimal(increment)

        bids = {}
        asks = {}

        def add(d, price, size):
            o = d.get(price)
            if o is None:
                d[price] = Order(price,size)
            else:
                o.size += size


        for o in self.bids:
            price = floor_inc(o.price)
            add(bids, price, o.size)

        for o in self.asks:
            price = ceil_inc(o.price)
            add(asks, price, o.size)

        self.bids = bids.values()
        self.asks = asks.values()

    def subtract(self, other):
        bids = {}
        asks = {}
        for o in self.bids:
            bids[o.price] = o
        for o in self.asks:
            asks[o.price] = o

        def subtract_size(d, price, size):
            o = d.get(price)
            if o is not None:
                o.size -= size
            else:
                d[price] = Order(price,-size)

        # remove order sizes book
        if other:
            for o in other.bids:
                subtract_size(bids, o.price, o.size)
            for o in other.asks:
                subtract_size(asks, o.price, o.size)

        self.bids = bids.values()
        self.asks = asks.values()
