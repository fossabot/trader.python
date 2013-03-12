#!/usr/bin/env python
# adds a single order to mt.gox
# uses encrypted API keys

import mtgoxhmac
import cmd

mtgox = mtgoxhmac.Client()

#get trade depth
#alltrades=mtgox.get_trades()

class Shell(cmd.Cmd):
    def emptyline(self):
        pass
    print 'Last Mt.Gox Open order: ', mtgox.last_order()
    print mtgox.get_info()
    prompt = '(buy|sell size price) '
    def do_sell(self, arg):
        size, price = arg.split()
        mtgox.sell_btc(size,price)

    def do_buy(self, arg):
       size, price = arg.split()
       mtgox.buy_btc(size,price)

    def do_orders(self,arg):
        orders = mtgox.get_orders()
        try:
            print orders['order_id']
        except:
            return
        
    def do_EOF(self, arg):
        print "Session Terminating......."
        return True


Shell().cmdloop()
