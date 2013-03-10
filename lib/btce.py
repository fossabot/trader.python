# BTCE API calls
# sample from website heavily modified to use encrypted API keys
# begin to declare all API functions
# genBTC 3/10/2013

import httplib
import urllib
import json
import json_ascii
import hashlib
import hmac
import time
import unlock_api_key

# Come up with your own method for choosing an incrementing nonce
key,secret,unused = unlock_api_key.unlock("btc-e")
nonce = int(time.time())
print nonce, ' Nonce'
# method name and nonce go into the POST parameters
params = {"method":"getInfo",
          "nonce": nonce}
params = urllib.urlencode(params)
 
# Hash the params string to produce the Sign header value
H = hmac.new(str(secret), digestmod=hashlib.sha512)
H.update(params)
sign = H.hexdigest()

headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Key":key,
                   "Sign":sign}
conn = httplib.HTTPSConnection("btc-e.com")
conn.request("POST", "/tapi", params, headers)
response = conn.getresponse()
print response.status, response.reason
s = json.load(response,object_hook=json_ascii.decode_dict)
print s
#print s['return']['funds']['btc'], ' BTC available'
conn.close()