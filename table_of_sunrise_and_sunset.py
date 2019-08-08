#!/usr/bin/env python3


from skyfield import api, almanac
from skyfield.api import load, Topos
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time
from skyfield.nutationlib import iau2000b

from _calendar import listDates
from save_calculations import CalculationResults

import sys
from pytz import timezone

YEAR = int(sys.argv[1])
assert 2000 < YEAR < 3000



ephemeris421 = load("de421.bsp")
timescale = load.timescale()
BJT = timezone("Asia/Shanghai")


def sunrise_sunset(ephemeris , topos, crit=-0.8333):
    sun = ephemeris['sun']
    topos_at = (ephemeris['earth'] + topos).at

    def is_sun_up_at(t):
        """Return `True` if the sun has risen by time `t`."""
        t._nutation_angles = iau2000b(t.tt)
        return topos_at(t).observe(sun).apparent().altaz()[0].degrees > crit

    is_sun_up_at.rough_period = 0.5  # twice a day
    return is_sun_up_at




locations = [
    (20,        api.Topos('20 N', '0 E')),
    (30,        api.Topos('30 N', '0 E')),
    (35,        api.Topos('35 N', '0 E')),
    (40,        api.Topos('40 N', '0 E')),
    (45,        api.Topos('45 N', '0 E')),
    (50,        api.Topos('50 N', '0 E')),
    (55,        api.Topos('55 N', '0 E')),
]



utcStart = timescale.utc(YEAR, 1, 1)
utcEnd   = timescale.utc(YEAR, 12, 31, 23, 59, 59)
founds = {
    -0.8333: {},
    -6: {},
    -18: {},
}

for crit in founds:
    print("Calculating: sun is below horizont with %f degrees." % -crit)

    for year, month, day in listDates(YEAR):
        utcStart = timescale.utc(year, month, day, 0, 0, 0)
        utcEnd = timescale.utc(year, month, day, 23, 59, 59) 
        
        founds[crit][(month, day)] = {}

        for calcLat, calcTopo in locations:
            t, y = almanac.find_discrete(
                utcStart,
                utcEnd, 
                sunrise_sunset(ephemeris421, calcTopo, crit)
            )

            founds[crit][(month, day)][calcLat] = {'rise': None, 'set': None}
            for ti, yi in zip(t, y):
                founds[crit][(month, day)][calcLat]["rise" if yi else "set"] = ti




# print out all info

def translateTime(t):
    if t is None: return "---"
    return t.utc_strftime("%H:%M")


outputmapping = {
    -0.8333: "sunrise_and_set",
    -6: "civil_twilight",
    -18: "astro_twilight",
}


for crit in outputmapping:
    with CalculationResults(outputmapping[crit], YEAR) as writer:
        
        lastMonth = None

        skipCount = 0
        breakCount = 5

        for year, month, day in list(listDates(YEAR)):

            if skipCount > 0:
                skipCount -= 1
                continue
            else:
                skipCount = 10 - 1

            if breakCount > 0:
                breakCount -= 1
            else:
                breakCount = 4
                writer.writeline(" & " * (2*len(locations) + 1) + " \\\\")

            line = []
            result = founds[crit][(month, day)]

            if lastMonth != month:
                line.append(str(month))
            else:
                line.append("")
            line.append(str(day))
            lastMonth = month

            for lat, _ in locations:
                riseset = result[lat]
                line.append(translateTime(riseset["rise"]))
                line.append(translateTime(riseset["set"]))


            writer.writeline(" & ".join(line) + " \\\\")
