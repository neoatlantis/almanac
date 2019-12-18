

#!/usr/bin/env python3


from skyfield import api, almanac
from skyfield.api import load, Topos, Star
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time
from skyfield.nutationlib import iau2000b

from _utils import roundTimeToMinute
from _constants import *

from _calendar import listDates
from save_calculations import cached, CalculationResults

import yaml
import json
import os
import sys
import numpy as np
from pytz import timezone
import dateutil.parser

YEAR = int(sys.argv[1])
assert 2000 < YEAR < 3000


def listPlanet(year, planet):
    ret = {}

    for yyyy, mm, dd in list(listDates(year))[:]:
        utc0 = timescale.utc(yyyy, mm, dd, 0, 0, 0)
        if mm not in ret: ret[mm] = {}

        astrometric = Earth.at(utc0).observe(planet).apparent()
        ra, dec, distance = astrometric.radec(epoch='date')
        ecllat, ecllon, _ = astrometric.ecliptic_latlon(epoch='date')

        ret[mm][dd] = {
            "ra": float(ra.hours),
            "dec": float(dec.degrees),
            "ecllon": float(ecllon.degrees),
        }

    return ret



@cached("planets", YEAR)
def calculatePlanets(year):
    ret = {
        "Mercury": listPlanet(year, Mercury),
        "Venus":   listPlanet(year, Venus),
        "Mars":    listPlanet(year, Mars),
        "Jupiter": listPlanet(year, Jupiter),
        "Saturn":  listPlanet(year, Saturn),
        "Uranus":  listPlanet(year, Uranus),
        "Neptune": listPlanet(year, Neptune),
    }

    return ret

print(calculatePlanets())
