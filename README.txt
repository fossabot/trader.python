#trader.python customized by genBTC

##Features
Secure Authentication via password using 256-bit AES Encryption of your API-key and API-secret (see Usage->Login with API-key/secret)
###Buy and sell bitcoins
Simple - Buy/Sell X amount of BTC    TODO:   (Specify buy/sell amounts in USD ) 
Spread - Buy/Sell some BTC between price A and price B of equal sized chunks"""
List your orders
Cancel ALL orders at once (or a single one)	TODO: (Specify a cancel range somehow)
Display account balance
Display ticker (sell,buy,last,vol,vwap,high,low,avg)	the time frame for high, low, vol, avg, vwap ... is sliding 24 hours
Log the ticker to a file (and check or print it out later)
Display the bid/ask spread 
Show the current Mt.Gox Lag (trading lag)

###Depth Functions
Print the order books out to howmany length you want (Display depth) (current order book of bids/asks)
calculate and print the total BTC between price A and B

###Fees
Find out your current fee rate (Mt.Gox's commission)

###Market Orders
Match any order to the opposite site of the order book (ie: if buying find a seller or vice versa) - market order
Given the amount of BTC and price range, check to see if it can be filled as a market order
calculate the total price of the order and the average weighted price of each bitcoin 

###History 
Prints out your entire trading history of BTC transactions
Prints out your entire history of USD transactions (including deposits)

# Includes frameworks (libs) for Mt.Gox, Bitfloor, BTCE
# All scripts located in bin/
# API Framework located in lib/
# Simple Example files in example/

FEATURES:
+) Diversify your position into "chunks" of a specified size between price A and B (WORKS GREAT, todo: check market conditions, use VWAP to pick, select desired patience level or instant gratification) (# spread trade function including Chunk Trade spread logic & Confirmation)
+) Print the order books out to X length


+) For Market Orders
#TODO: optional Wait time (default to instant gratification) 
#Checks exact price (total and per bitcoin) @ Market prices
#   by checking opposite Order Book depth for a given size and price range (lower to upper)
#   and alerts you if cannot be filled immediately, and lets you place a limit order instead

+) Bitcoin Functions:
#calculate and print the total BTC between price A and B
#match any order to the opposite site of the order book (ie: if buying find a seller) - market order
	given the amount of BTC and price range check to see if it can be filled as a market order
	calculate the total price of the order and the average weighted price of each bitcoin 


TO BEGIN:
---------------
Windows binaries are included! (for encrypt_api_key, bitfloor_client, and mtgox_client)

Create a new API key on each website. If using Bitfloor remember the passphrase. It will be required to use your API key.

encrypt_apikey.py:  	You need to generate encrypted keys beforehand with the encrypt_apikey.py command
			*Sometimes the generation does not work (just re-run this script - it can take up to 5 times until it is verified)*

	Use bitfloor as the site name for Bitfloor
	Use mtgox as the site name for Mt. Gox	
	Use btc-e as the site name for BTC-E
	Where it says "Enter an encryption password: (This is the password required to execute trades)"
		-For bitfloor this is your passphrase that you entered on the website.
		-For mtgox You can create your own password, just make sure to remember it.
		-For btce You can create your own password, just make sure to remember it.


INSTRUCTIONS:
--------------------

Call any script by opening a command window (cmd.exe) to the directory:
	python simple.py

bin/
-encrypt_api_key - REQUIRED to use this suite, generates an encrypted API key file in keys/ with the site name (see above)
-bitfloor_client.py - Advanced Trading on bitfloor!
-mtgox_client.py - Advanced Trading on mtgox!

-mtgox_simple.py - CLI prompt for simple trading on mt.gox (simple, Buy/Sell, Amount, Price on mtgox)
-bitfloor_cancel_all - 3 lines of code to cancel every order on bitfloor (very simple, passes the cancel order function to the framework lib/bitfloor.py)
-bitfloor_check_orders - print out current orders on bitfloor (simple, just prints out open orders)
-bitfloor_mirror_mtgox - mirror the mt.gox order book over to bitfloor (NOT WORKING FULLY)
-bitfloor_rand_latency - Test the ordering and cancellation latency on bitfloor (fairly non-useful since bitfloor latency is usually very low (~3 seconds))
-bitfloor_single - CLI prompt for simple trade execution on bitfloor (simple, Buy/Sell, Amount, Price on bitfloor) 

-btce_show_info - uses the framework of lib/btce.py to make several queries , like price ticker, open orders, order book, transaction history, etc

-bcbookie (taken from ga-bitbot) on github - NOT USED directly.
-goxcli (taken from Trasp/GoxCLI) on github - NOT USED directly. -goxcli.xml datafile for goxcli - NOT USED 




lib/
-unlock_api_key.py - Decrypts the encrypted API keys that we make from keys/ 
-mtgoxhmac.py - Actual Mt.Gox Framework that should be used to make API calls
-bitfloor.py - Bitfloor Framework with all API calls
-args.py - was needed for bitfloor plaintext keyfile which has been 90% phased out in favor of encrypted API keys
-btce.py - BTC-E Framework with all api calls (some HTTP error checking)
-book.py -  # will parse any json book in standard form

-fencebot.py - pretty sure this is OBSOLETE (bitfloor_rand_latency does this)
common.py - Common trading functionality was merged in here for bitfloor_client.py and mtgox_client.py
-depthparser.py - imported a portion of goxcli into this file for use in mtgox. 
-json_ascii.py - # json decode strings as ascii instead of unicode
-liquidbot.py  		>	Both of these are taken from https://github.com/chrisacheson/liquidbot
-liquidbot_mtgox.py	>	Self-sufficient but not utilized in this suite (YET) he has a few good ideas
-mtgox2.py - an alternate Mt.gox framework

data/
config.json  - stores the hostname and port of the bitfloor API interface. thats it.
nonce_state_btce - required for the btce framework to generate a nonce(Saving this to a file is useful, since if the nonce messes up you have to recreate the API key)

keys/
{exchange}_key.txt and {exchange}_salt.txt   = this is what is written by encrypt_api_key and what is used to unlock your API keys to access the trading console


+) Programming Functions:
#turn a whole list or tuple into a float
#turn a whole list or tuple into a decimal
#get the mean of an entire list or tuple
#pretty print and pretty write a dict

PYTHON ON WINDOWS INFORMATION
-------------------------------
To use on windows some environment variables may be needed:
(trader.python) is the directory I put this entire project in.

echo PYTHONPATH=%PYTHONPATH%;C:\python27\;C:\python27\libs\;C:\python27\trader.python\lib\
echo PATH=%PATH%;C:\python27\
You will also need a bunch of py modules mostlikely:
###-crypto
-pyreadline
-readline
-requests (1.1.0)
-cjson
AND PROBABLY MORE,
To enable command line tab completion inside the scripts :
copy "C:\Python27\Lib\site-packages\pyreadline\configuration\pyreadlineconfig.ini" %HOMEPATH%
(tab completion was phased out in favor of command history (on windows))

(NOT implemented)
Abort commands with SIGINT (ctrl-c on *nix) without exiting, if Mt. Gox is being slow (soon)
Withdraw bitcoins
Sequence multiple commands using semicolons
Tab completion of commands
Calculate profitable short/long prices from an initial price
Sample trader implementation in Python, for Bitfloor and Mt.Gox & some BTC-e!
