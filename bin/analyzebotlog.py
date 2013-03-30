#!/usr/bin/env python

#filetoopen = raw_input("Enter the filename in the data/ directory to open: ")
# filetoopen = "liquidbotlog.txt"

# filled = open("filled.txt",'w') 
# with open(filetoopen,'r') as f:
#     for line in f:
#     	if "filled" in line:
#     		filled.write(line)
# filled.close()
filled = open("filled.txt",'r') 
#buysell = open("filled2.txt",'w') 

buylinelist = []
selllinelist = []
for line in filled:
	#print line.split()
	if "Buy" in line and "order" in line:
		wordlist = line.split()
		buybtc = float(wordlist[5])
		buyprice = float(wordlist[8][1:])
		buylinelist.append([buybtc,buyprice])
	if "Sell" in line and "order" in line:
		wordlist = line.split()
		sellbtc = float(wordlist[5])
		sellprice = float(wordlist[8][1:])
		selllinelist.append([sellbtc,sellprice])
	

#print buylinelist
#print selllinelist
totalbuy = 0
totalsell = 0
for x in buylinelist:
	totalbuy += x[0]*x[1]
for x in selllinelist:
	totalsell += x[0]*x[1]
	
print totalbuy,totalsell