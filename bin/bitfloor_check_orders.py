#!/usr/bin/env python
# must be run with Side (0=buy,1=sell), Size, Price as arguments on the command line

import bitfloor
import cmd
import sys
import time

bitfloor = bitfloor.get_rapi()

side,size,price = sys.argv[1:]

time.sleep(4)
orders = bitfloor.orders()
for order in orders:
    print order['order_id'], order['size'], order['price']
	