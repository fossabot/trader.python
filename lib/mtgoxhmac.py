"""
MtGoxHMAC v0.2

Copyright 2011 Brian Monkaba
Modified 3/21/2013 by genBTC 

This file *was* part of ga-bitbot. It was modified heavily and is now part of genBTC's program.

    ga-bitbot is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ga-bitbot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ga-bitbot.  If not, see <http://www.gnu.org/licenses/>.
"""

from contextlib import closing
from Crypto.Cipher import AES
import getpass
import base64
import hmac
import hashlib
import time
import json
import json_ascii
import urllib
import urllib2
import urlparse
import unlock_api_key
import ssl

class ServerError(Exception):
    def __init__(self, ret):
        self.ret = ret
    def __str__(self):
        return "Server error: %s" % self.ret
class UserError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg
    def __str__(self):
        return self.errmsg

class Client:
    def __init__(self, enc_password=""):
        self.key,self.secret,enc_password = unlock_api_key.unlock("mtgox")
        
        self.buff = ""
        self.timeout = 10
        self.__url_parts = "https://data.mtgox.com/api/"
        self.clock_window = time.time()
        self.clock = time.time()
        self.query_count = 0
        self.query_limit_per_time_slice = 5
        self.query_time_slice = 10

    def throttle(self):
        self.clock = time.time()
        tdelta = self.clock - self.clock_window
        if tdelta > self.query_time_slice:
            self.query_count = 0
            self.clock_window = time.time()
        self.query_count += 1
        if self.query_count > self.query_limit_per_time_slice:
            #throttle the connection
            print "### Throttled ###"
            time.sleep(self.query_time_slice - tdelta)
        return
       
    def perform(self, path, params,JSON=True,API_VERSION=0):
        self.throttle()
        nonce =  str(int(time.time()*1000))
        if params != None:
            params = params.items()
        else:
            params = []

        params += [(u'nonce',nonce)]
        post_data = urllib.urlencode(params)
        ahmac = base64.b64encode(str(hmac.new(base64.b64decode(self.secret),post_data,hashlib.sha512).digest()))

        if API_VERSION == 0:
            url = self.__url_parts + '0/' + path
        elif API_VERSION == 1: 
            url = self.__url_parts + '1/' + path
        else: #assuming API_VERSION 2
            url = self.__url_parts + '2/' + path
            api2postdatatohash = path + chr(0) + post_data          #new way to hash for API 2, includes path + NUL
            ahmac = base64.b64encode(str(hmac.new(base64.b64decode(self.secret),api2postdatatohash,hashlib.sha512).digest()))
        
        # Create header for auth-requiring operations
        header = {
            "User-Agent": 'genBTC-bot',
            "Rest-Key": self.key,
            "Rest-Sign": ahmac
            }

        while True:
            try:
                req = urllib2.Request(url, post_data, header)
                with closing(urllib2.urlopen(req, post_data,timeout=self.timeout)) as res:
                    if JSON == True:
                        try:
                            data = json.load(res,object_hook=json_ascii.decode_dict)
                            if "error" in data:
                                if data["error"] == "Not logged in.":
                                    print UserError(data["error"])
                                else:
                                    print ServerError(data["error"])
                            else:
                                return data
                        except ValueError as e:
                            print "JSON Error: %s. Most likely BLANK Data. Still trying to figure out what happened here." % e
                            data = "dummy"
                            unchobj = res
                            print unchobj.read()
                    else:
                        data = res.read()
                        return data
            except urllib2.HTTPError as e:
                print e
            except urllib2.URLError as e:
                print "URL Error %s: %s." % (e.reason,e) 
            except ssl.SSLError as e:
                print "SSL Error: %s." % e
            except Exception as e:
                print "General Error: %s" % e
            print "Retrying Connection...."


    def request(self, path, params,JSON=True,API_VERSION=0):
        ret = self.perform(path, params,JSON,API_VERSION)
        if JSON == True:
            if "error" in ret:
                raise UserError(ret["error"])
            else:
                return ret
        return ret

    #public api
    def get_bid_history(self,OID):
        params = {"type":'bid',"order":OID}
        return self.request('generic/private/order/result',params,API_VERSION=1)
    def get_ask_history(self,OID):
        params = {"type":'ask',"order":OID}
        return self.request('generic/private/order/result',params,API_VERSION=1)

    def get_bid_tids(self,OID):
        #used to link an OID from an API order to a list of TIDs reported in the account history log
        try:
            history = self.get_bid_history(OID)
        except:
            #OID not found, return an empty list
            return []
        else:
            trade_ids = []
            if history['result'] == 'success':
                for trade in history['return']['trades']:
                    trade_ids.append(trade['trade_id'])
                    #return the list of trade ids
                    return trade_ids
            else:
                return []

    def get_ask_tids(self,OID):
        #used to link an OID from an API order to a list of TIDs reported in the account history log
        try:
            history = self.get_ask_history(OID)
        except:
            #OID not found, return an empty list
            return []
        else:
            trade_ids = []
            if history['result'] == 'success':
                for trade in history['return']['trades']:
                    trade_ids.append(trade['trade_id'])
                    #return the list of trade ids
                    return trade_ids
            else:
                return []

    def lag(self):
        return self.request('generic/order/lag',None,API_VERSION=1)["return"]
    def get_history_btc(self):
        return self.request('history_BTC.csv',None,JSON=False)
    def get_history_usd(self):
        return self.request('history_USD.csv',None,JSON=False)
    def get_info(self):
        #return self.request('info.php', None)          #deprecated 
        return self.request('generic/private/info',None,API_VERSION=1)["return"]
    def get_ticker2(self):
        return self.request("BTCUSD/money/ticker",None,API_VERSION=2)["data"]
    def get_ticker(self):
        return self.request("ticker.php",None)["ticker"]
    def get_depth(self):
        return self.request("data/getDepth.php", {"Currency":"USD"})
    def get_fulldepth(self):
        return self.request("BTCUSD/money/depth/full",None,API_VERSION=2)
    def get_trades(self):
        return self.request("data/getTrades.php",None)
    def get_balance(self):
        #return self.request("getFunds.php", None)              #deprecated since multicurrency
        #info = self.request('info.php', None)["Wallets"]       
        info = self.get_info()["Wallets"]
        balance = { "usds":float(info["USD"]["Balance"]["value"]), "btcs":float(info["BTC"]["Balance"]["value"]) }
        return balance
    def get_orders(self):
        return self.request("getOrders.php",None)
    def entire_trade_history(self):
        return self.request("BTCUSD/money/trades/fetch",None, API_VERSION=2)
    def last_order(self):
        try:
            orders = self.get_orders()['orders']
            max_date = 0
            last_order = orders[0]
            for o in orders:
                if o['date'] > last_order['date']:
                    last_order = o
                return last_order
        except:
            print 'no orders found'
            return

    def get_spread(self):
        depth = self.get_depth()
        lowask = depth["asks"][0][0]
        highbid = depth["bids"][-1][0]
        spread = lowask - highbid
        return spread

    def buy_btc(self, amount, price=None):
        #omit the price to place a market order
        #
        #new mtgox market orders begin in a pending state
        #so we have to make a second delayed call to verify the order was actually accepted
        #there is a risk here that the mtgox system will not be able to verify the order before
        #the second call so it could reported as still pending. 
        #In this case, the host script will need to verify the order at a later time.
        #to do: check how the system responds to instant orders and partialy filled orders.
        if amount < 0.01:
            print "Minimum amount is 0.01btc"
            return 0
        if price:
            params = {"amount":str(amount), "price":str(price)}
        else:
            params = {"amount":str(amount)}
        buy = self.request("buyBTC.php", params)
        oid = buy['oid']
        #check the response for the order
        for order in buy['orders']:
            if order['oid'] == oid:
                return order
        #if it wasn't reported yet...check again
        time.sleep(2)
        orders = self.get_orders()['orders']
        for order in orders:
            if order['oid'] == oid:
                return order
        else:
            return None
        


    def sell_btc(self, amount, price=None):
        #omit the price to place a market order
        if amount < 0.01:
            print "Minimum amount is 0.01btc"
            return 0
        if price:
            params = {"amount":str(amount), "price":str(price)}
        else:
            params = {"amount":str(amount)}
        sell = self.request("sellBTC.php", params)
        oid = sell['oid']
        #check the response for the order
        for order in sell['orders']:
            if order['oid'] == oid:
                return order
        #if it wasn't reported yet...check again
        time.sleep(2)
        orders = self.get_orders()['orders']
        for order in orders:
            if order['oid'] == oid:
                return order
        else:
            return None
        
    def cancel_buy_order(self, oid):
        params = {"oid":str(oid), "type":str(2)}
        return self.request("cancelOrder.php", params)

    def cancel_sell_order(self, oid):
        params = {"oid":str(oid), "type":str(1)}
        return self.request("cancelOrder.php", params)
        
    def cancelall(self):
        orders = self.get_orders()
        for order in orders['orders']:
            type = order['type']
            oid = order['oid']
            params = {"oid":str(oid), "type":str(type)}
            self.request("cancelOrder.php", params)
            print 'OID: %s Successfully Cancelled!' % (oid)
        if orders['orders']:
            print "All Orders have been Cancelled!!!!!"
        else:
            print "No Orders found!!"
        
if __name__ == "__main__":
    print "\nMTGoxHMAC module test"
    print "**warning: running this script will initiate then cancel an order on the MtGox exchange.**"

    print "\ndownloaded examples of the MtGox json format will be stored in the test_data folder."
    c = Client()
    """
    b = ppdict(pwdict(c.buy_btc(1.5,0.25),'./test_data/mg_buy.txt'))
    s = ppdict(pwdict(c.sell_btc(1.0,100.00),'./test_data/mg_sell.txt'))
    ppdict(pwdict(c.get_info(),'./test_data/mg_info.txt'))
    ppdict(pwdict(c.get_ticker(),'./test_data/mg_ticker.txt'))
    ppdict(pwdict(c.get_depth(),'./test_data/mg_depth.txt'))
    ppdict(pwdict(c.get_balance(),'./test_data/mg_balance.txt'))	
    ppdict(pwdict(c.get_orders(),'./test_data/mg_orders.txt'))
    ppdict(pwdict(c.cancel_buy_order(b['oid']),'./test_data/mg_cancel_buy.txt'))
    ppdict(pwdict(c.cancel_sell_order(s['oid']),'./test_data/mg_cancel_sell.txt'))
    ppdict(pwdict(c.get_history_btc(),'./test_data/mg_history_btc.txt'))
    ppdict(pwdict(c.get_history_usd(),'./test_data/mg_history_usd.txt'))
    ppdict(pwdict(c.get_bid_history(b['oid']),'./test_data/mg_bid_history.txt'))
    ppdict(pwdict(c.get_ask_history(s['oid']),'./test_data/mg_ask_history.txt'))
    print "done."
    """

