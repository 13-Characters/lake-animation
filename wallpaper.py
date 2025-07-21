import numpy as np
import sys
from datetime import datetime
import math
from pathlib import Path

LATITUDE = float(sys.argv[1])
LONGITUDE = float(sys.argv[2])
now = math.floor(datetime.now().timestamp())

