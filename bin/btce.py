# If you find this sample useful, please feel free to donate :)
# LTC: LePiC6JKohb7w6PdFL2KDV1VoZJPFwqXgY
# BTC: 1BzHpzqEVKjDQNCqV67Ju4dYL68aR8jTEe
 
import httplib
import urllib
import json
import json_ascii
import hashlib
import hmac
import time
 
# Replace these with your own API key data
BTC_api_key = "asdfg"
BTC_api_secret = "8asdfg5"
# Come up with your own method for choosing an incrementing nonce
nonce = int(time.time())
print nonce, ' Nonce'
# method name and nonce go into the POST parameters
params = {"method":"getInfo",
          "nonce": nonce}
params = urllib.urlencode(params)
 
# Hash the params string to produce the Sign header value
H = hmac.new(BTC_api_secret, digestmod=hashlib.sha512)
H.update(params)
sign = H.hexdigest()
 
headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Key":BTC_api_key,
                   "Sign":sign}
conn = httplib.HTTPSConnection("btc-e.com")
conn.request("POST", "/tapi", params, headers)
response = conn.getresponse()
print response.status, response.reason
s = json.load(response,object_hook=json_ascii.decode_dict)
print s['return']['funds']['btc'], ' BTC available'
conn.close()