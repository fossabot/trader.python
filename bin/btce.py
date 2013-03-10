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
BTC_api_key = "QTF6HEV3-UH8KISGW-FN1QP14X-IA37CCR1-CMDR1OT2"
BTC_api_secret = "8cc3cd5214c486e627d4bc81fe6215a8d9b7a6e9156cd47a54ec41da09a32455"
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