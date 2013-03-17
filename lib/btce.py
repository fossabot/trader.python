# BTCE API calls
# sample from website heavily modified to use encrypted API keys
# begin to declare all API functions
# genBTC 3/10/2013

import sys
import httplib
import urllib
import urllib2
import json
import json_ascii
import hashlib
import hmac
import time
import unlock_api_key
import requests

class BTCEError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

def nonce_generator():
    partialpath=os.path.join(os.path.dirname(__file__) + '../data/')
    fd = open(os.path.join(partialpath + 'nonce_state_btce', 'r'))
    nonce = int(fd.read())
    fd.close()
    while (True):
        nonce = nonce+1
        fd = open(os.path.join(partialpath + 'nonce_state_btce', 'w'))
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
#    params = urllib.urlencode(params)
    # Hash the params string to produce the Sign header value
    H = hmac.new(str(secret), digestmod=hashlib.sha512)
    H.update(urllib.urlencode(params))
    sign = H.hexdigest()

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key":key,
               "Sign":sign}
#    conn = httplib.HTTPSConnection("btc-e.com")
    while True:
#       conn.request("POST", "/tapi", params, headers)
        url = 'https://btc-e.com/tapi'
        r = requests.post(url,data=params,headers=headers)
        # print params
        # print headers
        # print r.headers
        # print r.status_code
        if r.status_code == '502':
            print "Caught 502 Error, sleeping..."
            time.sleep(6)
            print "Retrying connection"
            continue
        elif r.status_code == requests.codes.ok:
            rj = r.json()
 #           print rj
            if rj['success'] == 0:
                print rj['error']
                break
            if rj['return']:
                return json.loads(r.text, object_hook=json_ascii.decode_dict)
            else:
                break
        else:
            print "Caught HTTP Error, sleeping..."
            time.sleep(6)
            print "Retrying connection"
            continue     
        # except httplib.HTTPException:
            # print "Caught HTTP Error, sleeping..."
            # time.sleep(3)
            # print "Retrying connection now"
            # continue
        # try:
            # reply = json.load(conn.getresponse())
            # if reply['success'] == 1:
                # return reply['return']
            # else:
                # print ("API returned error: " + reply['error'])
                # time.sleep(3)
                # print "Retrying connection now"
                # continue
            # print response.status, response.reason
        # except:
            # print ("Unexpected error: " + str(sys.exc_info()[0]))
            # time.sleep(3)
            # print "Retrying connection now"
            # continue

#print s['return']['funds']['btc'], ' BTC available'
#    conn.close()
def pubapi_request(pair, type):
    #OLDEST CODE 
    # try:
        # f = urllib.urlopen(url)
        # return json.load(f)
    # except IOError:
        # print f.code()
    #OLD CODE
    # HTTPConn = httplib.HTTPSConnection
    # conn = HTTPConn("btc-e.com","443")
    # url = "/api/2/" + pair + "/" + type
    # conn.request("POST", url)
    # resp = conn.getresponse()
    # s = resp.read()
    # conn.close()
    # return json.loads(s, object_hook=json_ascii.decode_dict)
    #NEW CODE using requests lib
    while True:
        try:
            r = requests.post('https://btc-e.com/api/2/' + pair + '/' + type)
            print r.url
#            print json.loads(r.text, object_hook=json_ascii.decode_dict)
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
                return response
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
    def ticker(self,pair):
        url = self.url + pair + '/ticker' #construct url
        ticker = self.parsePublicApi(url)
        return ticker
 
    def depth(self,pair):
        url = self.url + pair + '/depth'
        depth = self.parsePublicApi(url)
        return depth
 
    def trades(self,pair):
        url = self.url + pair + '/trades'
        trades = self.parsePublicApi(url)
        return trades
       
    def updatepair(self,pair):
        '''modular update pair method'''
        tick = self.ticker(pair)
        tick = tick['ticker']
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

pairs = {'ltc_btc': 'True', 'ltc_usd': 'True', 'btc_usd': 'True', 
        'ltc_rur': 'False', 'eur_usd': 'False', 'nmc_btc': 'False',
        'btc_eur': 'False', 'btc_rur': 'False', 'usd_rur': 'False'}
tick = genpairs()        
print tick.update(pairs)

def ticker(pair):
    return pubapi_request(pair, "ticker")['ticker']

def trades(pair):
    return pubapi_request(pair, "trades")

def depth(pair):
    return pubapi_request(pair, "depth")

def getinfo():
    return api_request('getInfo')

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
