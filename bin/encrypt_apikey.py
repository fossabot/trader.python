
"""
encrypt_api_key v0.01 
VERSION 0.2 REVISED by genBTC 
FOR MTGOX

Copyright 2011 Brian Monkaba

This file is part of ga-bitbot.

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


from Crypto.Cipher import AES
import hashlib
import json
import time
import random
import os

print "\n\nga-bitbot API Key Encryptor v0.2"
print "-" * 30
print "\n\n"

print "Enter the API KEY:"
key = raw_input()

print "\nEnter the API SECRET KEY:"
secret = raw_input()

print "Enter the site: "
site = raw_input()

print "\n\nEnter an encryption password:"
print "(This is the password required to execute trades)"
password = raw_input()


print "\n"
print "Generating the local password salt..."
pre_salt = str(time.time() * random.random() * 1000000) + 'H7gfJ8756Jg7HBJGtbnm856gnnblkjiINBMBV734'
salt = hashlib.sha512(pre_salt).digest()
partialpath=os.path.join(os.path.dirname(__file__) + '../keys/' + site)
f = open(os.path.join(partialpath + '_salt.txt'),'w')
f.write(salt)
f.close()


print "\n"
print "Generating the encrypted API KEY file..."
hash_pass = hashlib.sha256(password + salt).digest()
encryptor = AES.new(hash_pass, AES.MODE_CBC)
text = json.dumps({"key":key,"secret":secret})
#pad the text
pad_len = 16 - len(text)%16
text += " " * pad_len
ciphertext = encryptor.encrypt(text)
f = open(os.path.join(partialpath + '_key.txt'),'w')
f.write(ciphertext)
f.close()

print "Verifying encrypted file..."
f = open(os.path.join(partialpath + '_key.txt'),'r')
d = f.read()
f.close()
f = open(os.path.join(partialpath + '_salt.txt'),'r')
salt = f.read()
f.close()
hash_pass = hashlib.sha256(password + salt).digest()
decryptor = AES.new(hash_pass, AES.MODE_CBC)

def failed ():
    os.remove(os.path.join(partialpath + '_key.txt'))
    os.remove(os.path.join(partialpath + '_salt.txt'))
    print "Failed verification...try to re-run again. Make sure Length=160 or some multiple of 16"

print 'Length = ',len(d)
if len(d)%16 == 0:
    try:
        text = decryptor.decrypt(d)
        d = json.loads(text)
        if d['key'] == key and d['secret'] == secret:
            print "Passed verification"
            print "\nDon't forget your password:",password," This is what is REQUIRED to enable trading."
    except: 
        failed()
else:
    failed()