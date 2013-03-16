#!/usr/bin/env python
# randomly adds/cancels orders
# keeps track of average latency of ordering and cancelling

#import random
import math
import time
import os
import json
import json_ascii  # unnecessary
import time
import collections

#following 8 lines are Modified from hobsonlane's fork
import bitfloor
import bitfloor

# path = os.path.join('/etc','security','bfl.json')
# with open(path) as f:
    # config = json.load(f, object_hook=json_ascii.decode_dict)
# print config
#bf = RAPI(product_id=1, key=config['key'], secret=config['secret'])

bf = bitfloor = bitfloor.get_rapi()
olatency = [] # order latency
clatency = [] # cancel latency


def floatify(l):
    if isinstance(l, (list, tuple)):
        return [floatify(v) for v in l]
    elif isinstance(l, collections.Mapping):
        return {floatify(k): floatify(l[k]) for k in l}
    try:
        return float(l)
    except:
        pass
    if isinstance(l, basestring) and len(l):
        return l
    return 0.0

def mean(l):
    l = floatify(l)
    if getattr(l,'__len__',[].__len__)():
        if isinstance(l, (list, tuple)) and len(l[0])==2 and all(isinstance(v, (float, int)) for v in l[0]) :
            return float(sum(p * v for p, v in l))/sum(v for p, v in l)
        elif isinstance(l, collections.Mapping):
            return {k: mean(l[k]) for k in l}
        elif isinstance(l, (tuple, list)):
            return float(sum(l))/len(l) if len(l) else None
    return floatify(l)

orders = []
while True:
    try:
        err = False
        last = float(bf.ticker()['price'])
        book = floatify(bf.book(2))
        print 'BOOOOOK'
        print book
        brink = floatify(bf.book(1))
        print 'BRIIIIINK'
        print brink
        mean_book = mean(book)
        print 'mean_book %r, last %r, brink %r' % (mean_book, last, brink)
    except:
        err = True
    print '-' * 60
    time.sleep(3.723)
        
