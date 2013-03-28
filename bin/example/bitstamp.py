#bitstamp.py
import json
import json_ascii
import urllib,urllib2
from decimal import Decimal as D
import datetime

APIURL="https://www.bitstamp.net/api/"

def get(url,params=None):
	url = APIURL + url
	if params:
		params = urllib.urlencode(params)
		url = url + '?' + params	
	req = urllib2.Request(url)		#GET
	response = urllib2.urlopen(req)
	data = json.loads(response.read(),object_hook=json_ascii.decode_dict)
	return data


def post(url,params=None):
	url = APIURL + url
	postdata = {"user": "80653",
			"password": "/mkoCQzP9vB5"
			}
	if params:
		params = urllib.urlencode(params)
		url = url + '?' + params
	postdata = urllib.urlencode(postdata)
	req = urllib2.Request(url,postdata)			#POST
	response = urllib2.urlopen(req)
	data = json.loads(response.read(),object_hook=json_ascii.decode_dict)
	return data
#
#PUBLIC FUNCTIONS
#
def ticker():
#Ticker function
	url = "ticker/"
def orderbook():
#Open orders book with bids and asks
	url = "order_book/"
	
def get_transactions(timedelta=3600):
	url = "transactions/"
	params = {"timedelta":timedelta}
	data = get(url,params)
	return data

def bitinstant_reserves():
#Bitinstant reserves
	url = "bitinstant/"
def eur_usd():
#EUR_USD conversion rate
	url = "eur_usd/"

#
#PRIVATE FUNCTIONS
#

def account_balance():
#USD/BTC balance, on hold, available, and current fee
	url = "balance/"


def get_user_transactions(timedelta=86400):
#user transactions in the past timdelta
	url = "user_transactions/"
	params = {"timedelta":timedelta}
	data = post(url,params)
	return data

def open_orders():
	url = "open_orders/"



def cancel_order():
	url = "cancel_order/"
def buy():
#limit order
	url = "buy/"
def sell():
#limit order
	url = "sell/"

def create_bitstampcode():
#Create a bitstamp code
	url = "check_code/"

def redeem_bitstampcode():
#Redeem a bitstamp code
	url = "redeem_code/"

def send_touser():
#send funds to a customerID
	url = "sentouser/"

def withdrawal_requests():
#return a list of all withdrawal requests
	url = "withdrawal_requests/"
def withdraw():
#withdraw bitcoins to an address
	url = "bitcoin_withdrawal/"

def get_depositaddress():
#find out your bitcoin deposit address
	url = "bitcoin_deposit_address/"


def get_tradefee(timedelta=2592000):
	timedelta=2592000		#the past 30 days (what the fee is based off)
	data = get_transactions(timedelta)
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

if __name__ == "__main__":
	print "Total amount is: %s Your trade fee is: %s " %(get_tradefee())
	howlong = raw_input("How many seconds of history do you want to grab")
	data = get_usertransactions(howlong)
	print "Your user history is: " % (data)
	# earliestdate = min(D(x["date"]) for x in data)
	# latestdate = max(D(x["date"]) for x in data)
	# earliestdate = datetime.datetime.fromtimestamp(earliestdate)
	# latestdate = datetime.datetime.fromtimestamp(latestdate)
	# print earliestdate,latestdate