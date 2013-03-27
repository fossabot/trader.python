
import argparse
import goxapi
import logging
import locale
import math
import sys
import time
import traceback
import threading

class LogWriter():
    """connects to gox.signal_debug and logs it all to the logfile"""
    def __init__(self, gox):
        self.gox = gox
        logging.basicConfig(filename='goxtool.log'
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
        print "Exiting..."


      # conwin = WinConsole(stdscr, gox)
    # bookwin = WinOrderBook(stdscr, gox)
    # statuswin = WinStatus(stdscr, gox)
    # chartwin = WinChart(stdscr, gox)

    # printhook = PrintHook(gox)
    # strategy_manager = StrategyManager(gox, strat_mod_name)


    # try:
    #     while True:
    #         key = conwin.win.getch()
    #         if key == ord("q"):
    #             break
    #         if key == curses.KEY_F4:
    #             DlgNewOrderBid(stdscr, gox).modal()
    #         if key == curses.KEY_F5:
    #             DlgNewOrderAsk(stdscr, gox).modal()
    #         if key == curses.KEY_F6:
    #             DlgCancelOrders(stdscr, gox).modal()
    #         if key == curses.KEY_RESIZE:
    #             stdscr.erase()
    #             stdscr.refresh()
    #             conwin.resize()
    #             bookwin.resize()
    #             chartwin.resize()
    #             statuswin.resize()
    #             continue
    #         if key == ord("l"):
    #             strategy_manager.reload()
    #             continue
    #         if key > ord("a") and key < ord("z"):
    #             gox.signal_keypress(gox, (key))

    # except KeyboardInterrupt:
    #     gox.debug("got Ctrl+C, trying to shut down cleanly.")
    #     gox.debug("Hint: did you know you can also exit with 'q'?")
    # except Exception:
    #     gox.debug(traceback.format_exc())

    # strategy_manager.unload()
    #gox.stop()
    #printhook.close()
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

