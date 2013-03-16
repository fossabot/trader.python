#!/usr/bin/env python
# cancels all the user's orders

import bitfloor

bitfloor = bitfloor.get_rapi()

bitfloor.cancel_all()