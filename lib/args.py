from Crypto.Cipher import AES
from contextlib import closing
import sys
import os
import json
import getpass
import base64
import hmac
import hashlib
from bitfloor import RAPI
import unlock_api_key


def get_rapi():
    key,secret,passphrase = unlock_api_key.unlock("bitfloor")
    return RAPI(1,key,secret,passphrase)

#old method of using bitfloor.json keyfile    
#def get_rapi():
#    print 
#    if len(sys.argv) < 3: # awww, it's a heart!
#        print "Usage: {0} product_id keyfile".format(sys.argv[0])
#        sys.exit(1)
#
#    product_id, keyfile = sys.argv[1:]
#    product_id = 1
#    keyfile = "bitfloor"
#    path = os.path.join(os.path.join(os.path.dirname(__file__), '../keys'), keyfile + '.json')
#    with open(path) as f:
#        config = json.load(f, object_hook=json_ascii.decode_dict)
#
#    return RAPI(product_id=product_id, key=config['key'], secret=config['secret'])