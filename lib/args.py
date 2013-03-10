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

def get_rapi():
    print "MtGoxHMAC: Enter your API key file encryption password."
    enc_password = getpass.getpass()#raw_input()
    try:	
        f = open('../keys/bitfloor_salt.txt','r')
        salt = f.read()
        f.close()
        hash_pass = hashlib.sha256(enc_password + salt).digest()
        f = open('../keys/bitfloor_key.txt')
        ciphertext = f.read()
        f.close()
        decryptor = AES.new(hash_pass, AES.MODE_CBC)
        plaintext = decryptor.decrypt(ciphertext)
        d = json.loads(plaintext)
        key = d['key']
        secret = d['secret']
        passphrase = enc_password
    except:
        print "\n\n\nError: you may have entered an invalid password or the encrypted api key file doesn't exist"
        print "If you haven't yet generated the encrypted key file, run the encrypt_api_key.py script."
        while 1:
            pass

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