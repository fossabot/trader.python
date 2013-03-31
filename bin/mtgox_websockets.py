import websocket # websocket-client>=0.4.1 (included, otherwise downloadble)
import cjson
import time

def serialize(obj):
    return cjson.encode(obj)

def deserialize(msg):
    return cjson.decode(msg)

CHANNELS = {}
CHANNELS["dbf1dee9-4f2e-4a08-8cb7-748919a71b21"] = "trades"
CHANNELS["d5f06780-30a8-4a48-a2f8-7ed181b4a13f"] = "ticker"
CHANNELS["85174711-be64-4de1-b783-0628995d7914"] = "lag"
#CHANNELS["24e67e0d-1cad-4cc0-9e7a-f8523ef460fe"] = "depth"


CURRENCY = "USD"

def int2str(value_int, CURRENCY):
    """return currency integer formatted as a string"""
    if CURRENCY == "BTC":
        return ("%6.8g" % (value_int / 100000000.0))
    if CURRENCY == "JPY":
        return ("%12.3g" % (value_int / 1000.0))
    else:
        return ("%7.5g" % (value_int / 100000.0))

def on_op_private_ticker(msg):
    """handle incoming ticker message (op=private, private=ticker)"""
    msg = msg["ticker"]
    if msg["sell"]["currency"] != CURRENCY:
        return
    ask = int(msg["sell"]["value_int"])
    bid = int(msg["buy"]["value_int"])

    print " tick:  BID:", int2str(bid, CURRENCY)
    print "        ASK:", int2str(ask, CURRENCY)


def on_op_private_depth(msg):
    """handle incoming depth message (op=private, private=depth)"""
    msg = msg["depth"]
    if msg["currency"] != CURRENCY:
        return
    type_str = msg["type_str"]
    price = int(msg["price_int"])
    volume = int(msg["volume_int"])
    total_volume = int(msg["total_volume_int"])

    print "depth:  ", type_str+":", int2str(price, CURRENCY),"vol:", int2str(volume, "BTC"),"total:", int2str(total_volume, "BTC")


def on_op_private_trade(msg):
    """handle incoming trade mesage (op=private, private=trade)"""
    msg = msg["trade"]
    if msg["price_currency"] != CURRENCY:
        return
    typ = msg["trade_type"]
    date = int(msg["date"])
    price = int(msg["price_int"])
    volume = int(msg["amount_int"])

    print "TRADE: ", typ+":", int2str(price, CURRENCY),"vol:", int2str(volume, "BTC")

def on_message(ws, message):
    data = deserialize(message)
    channel = CHANNELS.get(data.get('channel'))
    if channel == "trades":
        on_op_private_trade(data)        
    elif channel == "depth":
        on_op_private_depth(data)
    elif channel == "ticker":
        now = float(data["ticker"]["now"]) / 1E6
        if now - ws.LASTTICKER > 25:    #only show the ticker every 25 seconds.
            ws.LASTTICKER = now
            on_op_private_ticker(data)
    elif channel == "lag":
        now = float(data["lag"]["stamp"]) / 1E6
        if now - ws.LASTLAG > 25:
            ws.LASTLAG = now
            lag = str(float(data["lag"]["age"] / 1E6))
            print " LAG: ",lag, "seconds"
    else:
        pass

def on_error(ws, error):
    print error

def on_close(ws):
    print "#### closed ####"

def on_open(ws):
    print "#### connected ####"

if __name__ == "__main__":
#infinite loop
    while True:
        websocket.enableTrace(False)
        
        url = 'ws://websocket.mtgox.com/mtgox'
        ws = websocket.WebSocket()
        ws.LASTTICKER = time.time() - 25       #sets the last ticker 25 seconds prior to now to show it once at the start.
        ws.LASTLAG = time.time() - 25
        ws.connect(url)
        on_open(ws)
        subscribetolag = serialize({"op":"mtgox.subscribe", "type":"lag"})        
        ws.send(subscribetolag)
        while True:
            data = ws.recv()
            on_message(ws,data)
        ws.close()
        time.sleep(8)      #wait 8 seconds before retrying after a dropped connection