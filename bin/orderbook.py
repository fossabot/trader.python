#!/usr/bin/env python
# Created by genBTC 3/10/2013 Updated 4/4/2013 
# mtgox_client.py
# Universal Client for all things mtgox
# A complete command line Client with a menu
# Functionality _should_ be listed in README (functions in alpahabetical order)

import cmd
import time
import json
import traceback
import threading        #for subthreads
import datetime
from decimal import Decimal as D    #renamed to D for simplicity.
import os
import logging
import csv
import os
if os.name == 'nt':
    import winsound         #plays beeps for alerts 

from book import *
from common import *
import depthparser
import mtgox_prof7bitapi
import mtgoxhmac

mtgox = mtgoxhmac.Client()

bPrec = mtgox.bPrec
cPrec = mtgox.cPrec

threadlist = {}

class LogWriter():
    """connects to gox.signal_debug and logs it all to the logfile"""
    def __init__(self, gox):
        self.gox = gox
        logging.basicConfig(filename='goxtool.log'
                           ,filemode='a'
                           ,format='%(asctime)s:%(levelname)s %(message)s'
                           ,level=logging.DEBUG
                           )
        console_logger = logging.getLogger('')
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console_logger.addHandler(console)        
        self.gox.signal_debug.connect(self.slot_debug)

    def close(self):
        """stop logging"""
        #not needed
        pass

    # pylint: disable=R0201
    def slot_debug(self, sender, (msg)):
        """handler for signal_debug signals"""
        if "https://data.mtgox.com/api/2/money/order/lag" in msg:
            return
        else:
            logging.debug("%s:%s", sender.__class__.__name__, msg)       #change this to .info to see the messages on screen.


config = mtgox_prof7bitapi.GoxConfig()
secret = mtgox_prof7bitapi.Secret()
secret.decrypt(mtgox.enc_password)
gox = mtgox_prof7bitapi.Gox(secret, config)
logwriter = LogWriter(gox)
gox.start()
print "Starting to download fulldepth from mtgox....",
socketbook = gox.orderbook
while socketbook.fulldepth_downloaded == False:
    time.sleep(0.1)
print "Finished."



try:
    length = stripoffensive(length)
    length = int(length)
    vintage = (time.time() - socketbook.fulldepth_time)
    if vintage > 300:
        print "Starting to download fulldepth from mtgox....",
        gox.client.request_fulldepth()
        while socketbook.fulldepth_downloaded == False:
            time.sleep(0.1)
        print "Finished."
    printOrderBooks(socketbook.asks,socketbook.bids,length)
except:
    printOrderBooks(socketbook.asks,socketbook.bids)
