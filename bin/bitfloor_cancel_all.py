#!/usr/bin/env python
# cancels all the user's orders

import args

bitfloor = args.get_rapi()

bitfloor.cancel_all()