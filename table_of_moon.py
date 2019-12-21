#!/usr/bin/env python3


from skyfield import api, almanac
from skyfield.api import load, Topos
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time
from skyfield.nutationlib import iau2000b

from _calendar import listDates
from _constants import *
from save_calculations import CalculationResults, cached

import numpy as np
import sys
import json
from pytz import timezone


TOPIC = "moonphase"
YEAR = int(sys.argv[1])
assert 2000 < YEAR < 3000

locations = [
    (20,        api.Topos('20 N', '0 E')),
    (30,        api.Topos('30 N', '0 E')),
    (35,        api.Topos('35 N', '0 E')),
    (40,        api.Topos('40 N', '0 E')),
    (45,        api.Topos('45 N', '0 E')),
    (50,        api.Topos('50 N', '0 E')),
    (55,        api.Topos('55 N', '0 E')),
]

def moonrise_moonset(ephemeris, topos):

    """Build a function of time that returns whether the moon is up.
    The function that this returns will expect a single argument that is
    a :class:`~skyfield.timelib.Time` and will return ``True`` if the
    moon is up, else ``False``.
    """
    moon = Moon
    topos_at = (Earth + topos).at

    def is_moon_up_at(t):
        """Return `True` if the moon has risen by time `t`."""
        t._nutation_angles = iau2000b(t.tt)
        observation = topos_at(t).observe(moon).apparent()
        alt, az, distance = observation.altaz()

        moonRadius = MOON_RADIUS / distance.km / np.pi * 180.0 # 月球半径
        parallax = EARTH_RADIUS / distance.km / np.pi * 180.0  # 月球视差
        
        return observation.altaz()[0].degrees > -0.5666 - moonRadius + parallax 

    is_moon_up_at.rough_period = 0.5  # twice a day
    return is_moon_up_at



def translateTime(t):
    if t is None: return "---"
    return t.utc_strftime("%H:%M")

def translatePhase(phase):
    if phase is None: return ""
    ti, yi = phase
    name = ["朔", "上弦", "望", "下弦"][yi]
    return "%s %s" % (translateTime(ti), name)


@cached(TOPIC, YEAR)
def calculateMoonPhase(year):

    # 1. initialize founds dict for collecting results
    founds = {}
    for yyyy, mm, dd in listDates(year):
        if mm not in founds: founds[mm] = {}
        founds[mm][dd] = {
            "riseset": {},
            "phase": None,
            "phase-iso": None,
        }
        for lat, _ in locations:
            founds[mm][dd]["riseset"][lat] = {'rise': None, 'set': None}

    # 2. calculate rise and set times
    for yyyy, mm, dd in listDates(year):
        utcStart = timescale.utc(yyyy, mm, dd, 0, 0, 0)
        utcEnd   = timescale.utc(yyyy, mm, dd, 23, 59, 59) 

        for calcLat, calcTopo in locations:
            t, y = almanac.find_discrete(
                utcStart,
                utcEnd, 
                moonrise_moonset(ephemeris421, calcTopo)
            )

            for ti, yi in zip(t, y):
                founds[mm][dd]["riseset"][calcLat]["rise" if yi else "set"] = \
                    translateTime(ti)

    # 3. calcualte moon phases
    utcStart = timescale.utc(year, 1, 1)
    utcEnd   = timescale.utc(year, 12, 31, 23, 59, 59)
    t, y = almanac.find_discrete(utcStart, utcEnd, almanac.moon_phases(ephemeris421))
    for ti, yi in zip(t, y):
        yyyy, mm, dd, _, __, ___ = ti.utc
        founds[mm][dd]["phase-iso"] = (ti.utc_iso(), int(yi))
        founds[mm][dd]["phase"] = translatePhase((ti, yi))

    return founds

# ----------------------------------------------------------------------------

founds = calculateMoonPhase()

# print out all info



with CalculationResults("moon_rise_and_set", YEAR) as writer:
    
    lastMonth = None
    for year, month, day in list(listDates(YEAR)):

        if lastMonth != None and lastMonth != month:
            writer.writeline("\\hline")
        lastMonth = month

        line = []
        result = founds[month][day]

        line.append("%d/%d" % (month, day))
        line.append(result["phase"] or " ")

        for lat, _ in locations:
            riseset = result["riseset"][lat]
            line.append(riseset["rise"] or "---")
            line.append(riseset["set"] or "---")

        writer.writeline(" & ".join(line) + " \\\\")


with CalculationResults("moonphase", YEAR, "json") as writer:
    jsondump = {}
    for month in founds:
        for day in founds[month]:
            phaseData = founds[month][day]["phase-iso"]
            if phaseData is None: continue
            jsondump["%02d-%02d" % (month, day)] = {
                "phase": phaseData[1],
                "time": phaseData[0],
            }

    writer.writeline(json.dumps(jsondump))


