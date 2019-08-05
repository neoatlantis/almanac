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



convertSign = lambda i: "" if i >= 0 else "-"

def convertRA(ra):
    sign, h, m, _ = ra.signed_hms()
    return "$%s%d^h %02d^m$" % (convertSign(sign), h, m)

def convertDeg(deg):
    sign, d, m, _ = deg.signed_dms()
    return "$%s%d^{\circ}%d'$" % (convertSign(sign), d, m)

def convertSidereal(sr):
    sign, _, m, s = sr.signed_hms()
    return "$%s%d^m %02d^s$" % (convertSign(sign), m, s)
    



with CalculationResults("sun", YEAR) as writer:
    
    lastMonth = None
    for year, month, day in list(listDates(YEAR))[:]:
        tdb0 = timescale.tdb(year, month, day, 0, 0, 0)
        tt0 = timescale.tt(year, month, day, 0, 0, 0)
        utc0 = timescale.utc(year, month, day, 0, 0, 0)
        ut10 = timescale.ut1(year, month, day, 0, 0, 0)

        astrometric = earth.at(tdb0).observe(sun).apparent()
        ra, dec, distance = astrometric.radec(epoch='date')
        ecllat, ecllon, _ = astrometric.ecliptic_latlon(epoch='date')

        equation_of_time = sidereal_time(ut10) - ra.hours + 12
        if equation_of_time > 1: equation_of_time -= 24

        if lastMonth != None and lastMonth != month:
            writer.writeline("\\hline")
        lastMonth = month

        writer.writeline(" & ".join([    
            "%d/%d" % (month, day),
            convertRA(ra),
            convertDeg(dec),
            convertDeg(ecllon),                                       # 视黄经
            convertSidereal(Angle(hours=equation_of_time)),           # 均时差
        ]) + " \\\\")

    writer.writeline("\\hline")

