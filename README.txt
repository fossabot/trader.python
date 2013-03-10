# Sample bitfloor trader implementation in Python

To use on windows some environment variables may be needed:
(trader.python) is the directory I put this entire project in.

echo PYTHONPATH=%PYTHONPATH%;C:\python27\;C:\python27\libs\;C:\python27\trader.python\lib\
echo PATH=%PATH%;C:\python27\

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

INSTRUCTIONS:
Call any script by opening a command window (cmd.exe) and typing:
	python simple.py

-simpletrademtgox.py: amount of buy or sale must be given leading zero if decimal (0.025 not .025)