from __future__ import with_statement
try:
    import json
except ImportError:
    import simplejson as json
import random
import sys
from trumpet.service import TrumpetMaker


serviceMaker = TrumpetMaker()
