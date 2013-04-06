#THIS IS A TESTING PROGRAM (yes it works but it has replacements and improvements elsewhere)
#This is set up using goxapi.py in the lib/ folder, and I edited that file from the original 
#The editing consisted of modifying the way it writes the log so it prints to the screen as well,

#>>>>>>>>>!!
#in addition only TRADE channel is subscribed to. 
#To change this go into goxapi.py and comment out lines 808/809.
#line 814 channel_subscribe is commented out. this is a major function.
#it itself had lines commented out of it until i decided to scrap it entirely.
#The channel_subscribe has lag channel turned on but its redundant and it prints out quite often. 
#To turn the lag channel off, go to line 573 and comment it out.
#<<<<<<<<<

import argparse
import logging
import locale
import math
import sys
import time
import traceback
import threading

import goxapi

class LogWriter():
    """connects to gox.signal_debug and logs it all to the logfile"""
    def __init__(self, gox):
        self.gox = gox
        logging.basicConfig(filename='socketiobeta.log'
                           ,filemode='w'
                           ,format='%(asctime)s:%(levelname)s:%(message)s'
                           ,level=logging.DEBUG
                           )
        self.gox.signal_debug.connect(self.slot_debug)

    def close(self):
        """stop logging"""
        #not needed
        pass

    # pylint: disable=R0201
    def slot_debug(self, sender, (msg)):
        """handler for signal_debug signals"""
        logging.debug("%s:%s", sender.__class__.__name__, msg)


def main():
    """main funtion, called from within the curses.wrapper"""


    config = goxapi.GoxConfig("goxtool.ini")
    secret = goxapi.Secret()
    secret.prompt_decrypt() 
    gox = goxapi.Gox(secret, config)

      
    logwriter = LogWriter(gox)
    gox.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        print "got Ctrl+C, trying to shut down cleanly."
    except Exception:
        gox.debug(traceback.format_exc())

    #gox.stop()
    #logwriter.close()
    # The End.

    for loc in ["en_US.UTF8", "en_GB.UTF8", "en_EN", "en_GB", "C"]:
        try:
            locale.setlocale(locale.LC_NUMERIC, loc)
            break
        except locale.Error:
            continue



if __name__ == "__main__":
    main()