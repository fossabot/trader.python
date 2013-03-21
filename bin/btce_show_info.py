#!/usr/bin/python
import btce
import json
import json_ascii
from time import strftime, localtime

info = btce.getinfo()['return']
#print 'Info: ', info
print "Funds:"
for currency in ['BTC', 'USD', 'LTC']:
    print "\t", currency, info['funds'][currency.lower()]
print

#print 'Trade_History: ', btce.trade_history()
#print 'Order_List', btce.order_list()
#print 'Depth: ', btce.depth('btc_usd')
#print 'All Trades: ', btce.trades('btc_usd')
#print 'Trans_History', btce.trans_history()
ticker = btce.ticker('btc_usd')
print 'Ticker: ', ticker

if info['open_orders']:
	print "Open orders (" + str(info['open_orders']) + "):"
	print "id\t\tdirection\tamount\t\trate\t\ttime"
	orders = btce.order_list()
	for id, data in orders.items()['return']:
		pair = data['pair'].split('_')
		if data['type'] == 'buy':
			pair[0], pair[1] = pair[1], pair[0]
		print str(id) + "\t\t" + pair[0] + '->' + pair[1] + "\t" + str(data['amount']) + "\t\t" + str(data['rate']) + "\t\t" + strftime('%d.%m.%Y %H:%M:%S', localtime(data['timestamp_created']))

