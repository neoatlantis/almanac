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


def moonrise_moonset(ephemeris, topos):

    """Build a function of time that returns whether the moon is up.
    The function that this returns will expect a single argument that is
    a :class:`~skyfield.timelib.Time` and will return ``True`` if the
    moon is up, else ``False``.
    """
    moon = ephemeris['moon']
    topos_at = (ephemeris['earth'] + topos).at

    def is_moon_up_at(t):
        """Return `True` if the moon has risen by time `t`."""
        t._nutation_angles = iau2000b(t.tt)
        return topos_at(t).observe(moon).apparent().altaz()[0].degrees > -31/60

    is_moon_up_at.rough_period = 0.5  # twice a day
    return is_moon_up_at




locations = [
    (20,        api.Topos('20 N', '0 E')),
    (30,        api.Topos('30 N', '0 E')),
    (35,        api.Topos('35 N', '0 E')),
    (40,        api.Topos('40 N', '0 E')),
    (45,        api.Topos('45 N', '0 E')),
    (50,        api.Topos('50 N', '0 E')),
    (55,        api.Topos('55 N', '0 E')),
]

founds = {}
for year, month, day in listDates(YEAR):
    utcStart = timescale.utc(year, month, day, 0, 0, 0)
    utcEnd = timescale.utc(year, month, day, 23, 59, 59) 
    
    founds[(month, day)] = {
        "riseset": {},
        "phase": None,
    }

    for calcLat, calcTopo in locations:
        t, y = almanac.find_discrete(
            utcStart,
            utcEnd, 
            moonrise_moonset(ephemeris421, calcTopo)
        )

        founds[(month, day)]["riseset"][calcLat] = {'rise': None, 'set': None}
        for ti, yi in zip(t, y):
            founds[(month, day)]["riseset"][calcLat]["rise" if yi else "set"] = ti


utcStart = timescale.utc(YEAR, 1, 1)
utcEnd   = timescale.utc(YEAR, 12, 31, 23, 59, 59)
t, y = almanac.find_discrete(utcStart, utcEnd, almanac.moon_phases(ephemeris421))

for ti, yi in zip(t, y):
    year, month, day, _, __, ___ = ti.utc
    founds[(month, day)]["phase"] = (ti, yi)


# print out all info

def translateTime(t):
    if t is None: return "---"
    return t.utc_strftime("%H:%M")

def translatePhase(phase):
    if phase is None: return ""
    ti, yi = phase
    name = ["朔", "上弦", "望", "下弦"][yi]
    return "%s %s" % (translateTime(ti), name)


with CalculationResults("moon_rise_and_set", YEAR) as writer:
    
    lastMonth = None
    for year, month, day in list(listDates(YEAR)):
        

        if lastMonth != None and lastMonth != month:
            writer.writeline("\\hline")
        lastMonth = month

        line = []
        result = founds[(month, day)]

        line.append("%d/%d" % (month, day))
        line.append(translatePhase(result["phase"]))

        for lat, _ in locations:
            riseset = result["riseset"][lat]
            line.append(translateTime(riseset["rise"]))
            line.append(translateTime(riseset["set"]))


        writer.writeline(" & ".join(line) + " \\\\")