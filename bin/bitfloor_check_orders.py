#!/usr/bin/env python
# Adds a single order and Checks orders
# must be run with Side (0=buy,1=sell), Size, Price as arguments on the command line

import args
import cmd
import sys
import time

bitfloor = args.get_rapi()

side,size,price = sys.argv[1:]

print bitfloor.order_new(side=side, size=size, price=price)
time.sleep(4)
orders = bitfloor.orders()
for order in orders:
    print order['order_id'], order['size'], order['price']
	