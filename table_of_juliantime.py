#!/usr/bin/env python3


from skyfield.api import load, Topos
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time

from _calendar import listDates
from save_calculations import CalculationResults

import sys

YEAR = int(sys.argv[1])
assert 2000 < YEAR < 3000



objects = load("de421.bsp")
sun = objects["Sun"]
earth = objects["Earth"]


timescale = load.timescale()



with CalculationResults("juliancalc", YEAR) as writer:


    lastMonth = None
    for year, month, day in list(listDates(YEAR)):
        
        utc0 = timescale.ut1(year, month, day, 0, 0, 0)

        if lastMonth != None and lastMonth != month:
            writer.writeline("\\hline")
        lastMonth = month
        
        writer.writeline(" & ".join([str(i) for i in [
            month, day,
            "%.1f" % utc0.tt,
            "$%02d^h%02d^m%02d^s$" % Angle(hours=sidereal_time(utc0)).hms()[-3:]
        ]]) + " \\\\")
