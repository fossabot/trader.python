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



Abort commands with SIGINT (ctrl-c on *nix) without exiting, if Mt. Gox is being slow

(NOT implemented)
Withdraw bitcoins
Sequence multiple commands using semicolons
Tab completion of commands
Calculate profitable short/long prices from an initial price