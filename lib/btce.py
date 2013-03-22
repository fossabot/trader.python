# BTCE API calls
# sample from website heavily modified to use encrypted API keys and "Requests" HTTP library calls
# begin to declare all API functions
# genBTC 3/10/2013  Modified 3/21/2013

import sys
import os
import httplib
import urllib
import urllib2
import requests
import json
import json_ascii
import hashlib
import hmac
import time
import unlock_api_key


class BTCEError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

#must already have this nonce file in ../data/
def nonce_generator():
    partialpath=os.path.join('../data/')
    fd = open(os.path.join(partialpath + 'nonce_state_btce'),'r')
    nonce = int(fd.read())
    fd.close()
    while (True):
        nonce = nonce+1
        fd = open(os.path.join(partialpath + 'nonce_state_btce'),'w')
        fd.write(str(nonce))
        fd.close()
        yield nonce

#unlock the encrypted API key file
key,secret,unused = unlock_api_key.unlock("btc-e")

def api_request(method, misc_params = {}):
    nonce = nonce_generator()
    # method name and nonce go into the POST parameters
    params = {"method": method,
              "nonce": nonce.next()}
    #Update params
    params.update(misc_params)
    # Hash the params string to produce the Sign header value
    H = hmac.new(str(secret), digestmod=hashlib.sha512)
    H.update(urllib.urlencode(params))
    sign = H.hexdigest()

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key":key,
               "Sign":sign}
    #NEW CODE using Requests lib
    while True:
        url = 'https://btc-e.com/tapi'
        r = requests.post(url,data=params,headers=headers)
        if r.status_code == '502':
            print "Caught 502 Error(Bad Gateway)."
        elif r.status_code == requests.codes.ok:
            try:
                rj = r.json()
                if rj['return']:
                    return json.loads(r.text, object_hook=json_ascii.decode_dict)
                if rj['success'] == 0:
                    print ("API returned error: " + rj['error'])
            except Exception as e:
                print "JSON Error or non-JSON. %s" % e
                try:
                    print r.text
                except:
                    print "Not able to print the response body for later debugging of the error."
                    print ("Unexpected error: " + str(sys.exc_info()[0]))
        else:
            print "Caught HTTP Error %s." % r.status_code
        time.sleep(5)
        print "Retrying connection..."


def pubapi_request(pair, type):
    #NEW CODE using Requests lib
    while True:
        try:
            r = requests.post('https://btc-e.com/api/2/' + pair + '/' + type)
            return json.loads(r.text, object_hook=json_ascii.decode_dict)
            break
        except r.status_code == '404':
            print "Caught URL Error, sleeping..."
            time.sleep(3)
            print "Retrying connection"
            continue
        except r.status_code != requests.codes.ok:
            print "Caught HTTP Error, sleeping..."
            time.sleep(3)
            print "Retrying connection now"
            continue        
        except IOError as e:
            print "IO Error. %s" % e
            print r.url
            print r.text

#TODO: can also support btc_eur, nmc_btc, eur_usd
#correct_pairs = [['btc', 'usd'], ['ltc', 'btc'], ['ltc','usd']]
class genpairs():
    def __init__(self):
        self.tickerDict = {}
        self.url = 'https://btc-e.com/api/2/' #append pair, method
        self.btc_usd = {}
        self.btc_eur = {}
        self.btc_rur = {}
        self.ltc_btc = {}
        self.ltc_usd = {}
        self.ltc_rur = {}
        self.nmc_btc = {}
        self.usd_rur = {}
        self.eur_usd = {}
    def update(self,pairs):
        '''update pairs, assumes pairs is a dict'''
        for pair in pairs:
            if pairs[pair] == 'True':
                self.updatepair(pair)
        return self.tickerDict
    def parsePublicApi(self,url):
        '''public api parse method, returns dict, sleeps and retries on url/http errors'''
        while True:
            try:
                request = urllib2.Request(url)
                response = json.loads(urllib2.urlopen(request).read())
                break
            except urllib2.URLError:
                print "Caught URL Error, sleeping..."
                time.sleep(3)
                print "Retrying connection"
                continue
            except urllib2.HTTPError:
                print "Caught HTTP Error, sleeping..."
                time.sleep(3)
                print "Retrying connection now"
                continue
      
    def updatepair(self,pair):
        '''modular update pair method'''
        tick = ticker(pair)
        data = {}
        data['high'] = tick.get('high',0)
        data['low'] = tick.get('low',0)
        data['last'] = tick.get('last',0)
        data['buy'] = tick.get('buy',0)
        data['sell'] = tick.get('sell',0)
        data['vol'] = tick.get('vol',0)
        data['volCur'] = tick.get('vol_cur',0)
        data['avg'] = tick.get('avg',0)
        # uncomment for gigantic dict
        #data['depth'] = self.depth(pair)
        #data['trades'] = self.trades(pair)
        self.tickerDict[pair] = data
        return data


def ticker(pair):
    return pubapi_request(pair, "ticker")['ticker']

def trades(pair):
    return pubapi_request(pair, "trades")

def depth(pair):
    return pubapi_request(pair, "depth")

def getinfo():
    return api_request('getInfo')['return']

def order_list(filter = {}):
    return api_request('OrderList', filter)

def trans_history(filter = {}):
    return api_request('TransHistory', filter)

def trade_history(filter = {}):
    return api_request('TradeHistory', filter)

def prepare_trade(from_currency, to_currency, rate, amount):
    pair = [from_currency, to_currency]
    for p in correct_pairs:
        if pair == p:
            type = 'sell'
        elif pair == [p[1], p[0]]:
            type = 'buy'
            pair = p
            amount = float(amount) / float(rate)
    pair = '_'.join(pair)
    if not type:
        raise BTCEError("Unsupported currency pair: " + pair[0] + "_" + pair[1])
    return pair, type, rate, amount

def trade(pair, type, rate, amount):
#	print pair, type, amount, rate
    return api_request('Trade', { 'pair': pair, 'type': type, 'rate': rate, 'amount': amount })

def cancel_order(id):
    return api_request('CancelOrder', {'order_id': id})


pairs = {'ltc_btc': 'True', 'ltc_usd': 'True', 'btc_usd': 'True', 
        'ltc_rur': 'False', 'eur_usd': 'False', 'nmc_btc': 'False',
        'btc_eur': 'False', 'btc_rur': 'False', 'usd_rur': 'False'}

tick = genpairs()        

#print tick.update(pairs)
pairsdata = tick.update(pairs)
#print pairsdata