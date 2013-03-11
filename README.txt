# Sample bitfloor trader implementation in Python, beginning gox & btce
# Includes frameworks (libs) for Mt.Gox, Bitfloor, BTCE

Create a new API key on the bitfloor website. Remember the passphrase. It will be required to use your API key.

encrypt_apikey.py:  	You need to generate encrypted keys beforehand with the encrypt_apikey.py command
			Sometimes the generation does not work (just re-run this script - it can take up to 5 times until it is verified)

	Use bitfloor as the site name for Bitfloor
	Use mtgox as the site name for Mt. Gox	
	Use btc-e as the site name for BTC-E
	Where it says "Enter an encryption password: (This is the password required to execute trades)"
		-For bitfloor this is your passphrase that you entered on the website.
		-For mtgox You can create your own password, just make sure to remember it.
		-For btce You can create your own password, just make sure to remember it.

All scripts located in bin/
API Framework located in lib/
Simple Example files in example/

INSTRUCTIONS:
--------------------

Call any script by opening a command window (cmd.exe) to the directory:
	python simple.py

bin/
-simpletrademtgox.py: amount of buy or sale must be given leading zero if decimal (0.025 not .025)
-bcbookie (taken from ga-bitbot) on github - NOT USED ATM
-bitfloor_cancel_all - 3 lines of code to cancel every order on bitfloor (passes a function to the framework lib/bitfloor.py)
-bitfloor_check_orders - print out current orders on bitfloor
-bitfloor_mirror_mtgox - mirror the mt.gox order book over to bitfloor (NOT WORKING FULLY)
-bitfloor_rand_latency - Test the ordering and cancellation latency on bitfloor
-bitfloor_single - CLI prompt for simple trade execution on bitfloor (Buy/Sell, Amount, Price ) 
-btce_show_info - uses the framework of lib/btce.py to make several queries , like price ticker, open orders, order book, transaction history, etc
-encrypt_api_key - REQUIRED to use this suite, generates an encrypted API key file in keys/ with the site name (see above)
-goxcli (taken from Trasp/GoxCLI) on github - NOT USED ATM
-goxcli.xml datafile for goxcli - NOT USED ATM
-nonce_state_btce - required for the btce framework to generate a nonce(Saving this to a file is useful, since if the nonce messes up you have to recreate the API key)
-simpletrademtgox.py - CLI prompt for simple trading on mt.gox (Buy/sell, amount, price)
-spread.py - Advanced Trading on bitfloor - Diversify your position into "chunks" of a specified size between price A and B (WORKS GREAT, todo: check market conditions, use VWAP to pick, select desired patience level or instant gratification)
-yolo.py  -  Trying to do the above todolist (NOT AT ALL COMPLETE, possibly not working)

lib/
args.py - was needed for bitfloor plaintext keyfile which has been 90% phased out in favor of encrypted API keys
bitfloor.py - Bitfloor Framework with all API calls
book.py -  #will parse any json book in standard form

btce.py - BTC-E Framework with all api calls (some HTTP error checking)
fencebot.py - pretty sure this is OBSOLETE (bitfloor_rand_latency does this)
functions.py - A bunch of functions that is only 2 functions now
json_ascii.py - # json decode strings as ascii instead of unicode
liquidbot.py  		>	Both of these are taken from https://github.com/chrisacheson/liquidbot
liquidbot_mtgox.py	>	Self-sufficient but not utilized in this suite (YET) he has a few good ideas
mtgox2.py - an alternate Mt.gox framework
mtgoxhmac.py - Actual Mt.Gox Framework that should be used to make API calls
unlock_api_key.py - Decrypts the encrypted API keys that we make from keys/ 


PYTHON ON WINDOWS INFORMATION
-------------------------------
To use on windows some environment variables may be needed:
(trader.python) is the directory I put this entire project in.

echo PYTHONPATH=%PYTHONPATH%;C:\python27\;C:\python27\libs\;C:\python27\trader.python\lib\
echo PATH=%PATH%;C:\python27\
You will need a bunch of py modules:
-crypto
-readline
-cjson
-requests
-probably more