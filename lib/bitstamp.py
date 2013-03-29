#bitstamp.py
"""BitStamp API Library Framework 
Copyright 3/28/2013 by genBTC

This file -is- part of genBTC's trader.python program"""

import json
import json_ascii
import urllib,urllib2
from decimal import Decimal as D
import datetime
import unlock_api_key
import io
import gzip

APIURL="https://www.bitstamp.net/api/"

class Client:
    def __init__(self, enc_password=""):
        #This is part of my encrypt_api_key and unlock_api_key file.
        #without these, set self.key and self.secret to your User ID and password  
        self.key,self.secret,_ = unlock_api_key.unlock("bitstamp",enc_password)

    def get(self,url,params=None):
        url = APIURL + url
        if params:
            params = urllib.urlencode(params)
            url = url + '?' + params    
        req = urllib2.Request(url)      #GET
        req.add_header('Accept-encoding', 'gzip')       
        response = urllib2.urlopen(req)
        if response.info().get('Content-Encoding') == 'gzip':
            buf = io.BytesIO(response.read())
            response = gzip.GzipFile(fileobj=buf)
        return json.loads(response.read(),object_hook=json_ascii.decode_dict)


    def post(self,url,params=None):
        url = APIURL + url
        postdata = {"user": self.key,
                "password": self.secret}
        if params:
            params = urllib.urlencode(params)
            url = url + '?' + params
        postdata = urllib.urlencode(postdata)
        req = urllib2.Request(url,postdata)         #POST
        req.add_header('Accept-encoding', 'gzip')       
        response = urllib2.urlopen(req)
        if response.info().get('Content-Encoding') == 'gzip':
            buf = io.BytesIO(response.read())
            response = gzip.GzipFile(fileobj=buf)
        return json.loads(response.read(),object_hook=json_ascii.decode_dict)

    ####
    #PUBLIC DATA FUNCTIONS
    ####

    def ticker(self):
    #Ticker function
        url = "ticker/"
        return self.get(url) #Json dict. Keys: last - last BTC price, high - last 24 hours price high, low - last 24 hours price low, 
            #volume - last 24 hours volume, bid - highest buy order, ask - lowest sell order

    def entirebook(self,ordergrouping=1):
    #Open orders book with bids and asks
        url = "order_book/"
        params = {"group":ordergrouping}    #group orders with the same price (0 - false; 1 - true). Default: 1
        orderbook = self.get(url,params) 
        from book import Book
        entirebook = Book.parse(orderbook)
        entirebook.sort()
        return entirebook       #Returns a sorted Book class object,containing entirebook.bids and entirebook.asks

    def get_transactions(self,timedelta=3600):
    #get a history of everybody's transactions
        url = "transactions/"
        params = {"timedelta":timedelta}
        return self.get(url,params)  #List of Json dicts. Keys:
            #date - unix timestamp date and time, tid - transaction id, price - BTC price, amount - BTC amount

    def bitinstant_reserves(self):
    #Bitinstant reserves
        url = "bitinstant/"
        return self.get(url) #JSON dict. Keys: usd - Bitinstant USD reserves

    def eur_usd(self):
    #EUR_USD conversion rate
        url = "eur_usd/"
        return self.get(url) #JSON dict. Keys: buy - buy conversion rate , sell - sell conversion rate

    ####
    #PRIVATE FUNCTIONS
    ####

    def account_balance(self):
    #USD/BTC balance, on hold, available, and current fee
        url = "balance/"
        return self.post(url) #Json dict. Keys: usd_balance - USD balance, btc_balance - BTC balance, 
            #usd_reserved - USD reserved in open orders, btc_reserved - BTC reserved in open orders, 
            #usd_available- USD available for trading, btc_available - BTC available for trading, fee - customer trading fee

    def get_usertransactions(self,timedelta=86400):
    #user transactions in the past timdelta
        url = "user_transactions/"
        params = {"timedelta":timedelta}    # return transactions for the last 'timedelta' seconds. Default: 86400  
        return self.post(url,params)  #List of JSON dicts. Keys: datetime - date and time, id - transaction id, 
            #type - transaction type (0 - deposit; 1 - withdrawal; 2 - market trade), usd - USD amount, btc - BTC amount, fee - transaction fee

    def open_orders(self):
    #List your open orders
        url = "open_orders/"
        return self.post(url)    #List of json dicts. Keys: id - order id, datetime - date and time, type - buy or sell (0 - buy; 1 - sell)
            #price - price, amount - amount

    def cancel_order(self,orderid):
    #Cancel a single order
        url = "cancel_order/"
        params = {"id":orderid}
        return self.post(url)    #Returns 'True' if found and canceled.

    def buy(self,amount,price):
    #limit order
        url = "buy/"
        params = {"amount":amount,
                "price":price}
        return self.post(url,params) #Json dict. Keys: id - order id, datetime - date and time, type - buy or sell (0 - buy; 1 - sell), price - price, amount - amount

    def sell(self,amount,price):
    #limit order
        url = "sell/"
        params = {"amount":amount,
            "price":price}
        return self.post(url,params) #Json dict. Keys: id - order id, datetime - date and time, type - buy or sell (0 - buy; 1 - sell), price - price, amount - amount

    def create_bitstampcode(self,usd=None,btc=None):
    #Create a bitstamp code
        url = "check_code/"
        if usd != None:
            params = {"usd":usd} #optional
        elif btc != None:
            params = {"btc":btc} #optional
        return self.post(url,params) #Returns Bitstamp code string

    def redeem_bitstampcode(self,code):
    #Redeem a bitstamp code
        url = "redeem_code/"
        params = {"code":code}
        return self.post(url,params) #Json dict containing USD and BTC amount added to user's account (not very clear)

    def send_touser(self,customer_id,currency,amount):
    #send funds to a customerID
        url = "sendtouser/"
        params = {"customer_id":customer_id,
                "currency":currency,
                "amount":amount}
        return self.post(url,params) #Returns true if successful.

    def withdrawal_requests(self):
    #return a list of all withdrawal requests
        url = "withdrawal_requests/"
        return self.post(url)    #List of Json dicts. Keys: id - order id, datetime - date and time, 
            #type - (0 - SEPA; 1 - bitcoin; 2 - WIRE transfer; 3 and 4 - bitstamp code; 5 - Mt.Gox code)
            #amount - amount, status - (0 - open; 1 - in process; 2 - finished; 3 - canceled; 4 - failed)
            #data - additional withdrawal request data (Mt.Gox code, etc.)

    def bitcoin_withdraw(self,amount,address):
    #bitcoin withdrawal to an address
        url = "bitcoin_withdrawal/"
        params = {"amount":amount,
                "address":address}
        return self.post(url,params) #Returns true if successful.

    def get_depositaddress(self):
    #find out your bitcoin deposit address
        url = "bitcoin_deposit_address/"
        return self.post(url)    #Returns your bitcoin deposit address.


    def get_tradefee(self,timedelta=2592000):
        timedelta=2592000       #the past 30 days (what the fee is based off)
        data = self.get_usertransactions(timedelta)
        totalamount = sum(D(x["amount"]) for x in data)
        feedict = {
            500:0.50,
            1000:0.48,
            2000:0.46,
            4000:0.44,
            6000:0.42,
            10000:0.40,
            15000:0.38,
            20000:0.36,
            25000:0.34,
            37500:0.32,
            50000:0.30,
            62500:0.28,
            75000:0.26,
            100000:0.24,
            150000:0.22,
        }
        fee = 0.22  #<-if greater than 150,000 the following will never define a fee.
        for x in sorted(feedict.iterkeys(),reverse=True):
            if totalamount < D(str(x)): fee = D(str(feedict[x]))
        return totalamount,fee





#Test functions for the API
#Will flesh out to become client
if __name__ == "__main__":
    bitstamp = Client()
    print "Total amount is: %s Your trade fee is: %s " %(bitstamp.get_tradefee())
    
    #data = bitstamp.get_transactions(int(howmany)) not working
    #print "If the entire site was a person, its trade_fee would be: " % (data)
    # earliestdate = min(D(x["date"]) for x in data)
    # latestdate = max(D(x["date"]) for x in data)
    # earliestdate = datetime.datetime.fromtimestamp(earliestdate)
    # latestdate = datetime.datetime.fromtimestamp(latestdate)
    # print earliestdate,latestdate
    address = bitstamp.get_depositaddress()
    print "Your bitcoin deposit address is: %s" % (address)
    entirebook = bitstamp.entirebook()
#    from book import *
    from common import *

    howmany = raw_input("How many orders do you want to print out?: ")
    printbothbooks(entirebook.asks,entirebook.bids,int(howmany))
 