#!/usr/bin/env python
# adds a single order to mt.gox
# uses encrypted API keys

import mtgoxhmac
import cmd
import unlock_api_key

mtgox = mtgoxhmac.Client()

#get trade depth
#alltrades=mtgox.get_trades()
#print mtgox.get_info()
# def trade(side, arg):
    # try:
        # size, price = arg.split()
    # except:
        # print "Invalid arg {1}, expected size price".format(side, arg)
    # print mtgox.order_new(side=side, size=size, price=price)
    # time.sleep(4)
    # orders = mtgox.orders()
    # print orders['order_id']
	


class Shell(cmd.Cmd):
    def emptyline(self):
        pass
    print 'Last Mt.Gox Open order: ', mtgox.last_order()
    prompt = '(buy|sell size price) '
    def do_sell(self, arg):
        size, price = arg.split()
        mtgox.sell_btc(size,price)

    def do_buy(self, arg):
       size, price = arg.split()
       mtgox.buy_btc(size,price)
	   
    def do_EOF(self, arg):
        print "Any Trades have been Executed, Session Terminating......."
        return True

Shell().cmdloop()
