#!/usr/bin/env python3

from skyfield.api import load, Topos
from skyfield.units import Angle

from _calendar import listDates


objects = load("de421.bsp")
sun = objects["Sun"]
earth = objects["Earth"]

gcrs = earth + Topos(
    latitude_degrees=0,
    longitude_degrees=0,
    elevation_m=-6378136.6,
)

timescale = load.timescale()


outputTable = []
outputTableHeaders = [
    "月/日",
    "视赤经",
    "视赤纬",
    "视黄经",
    "均时差",
]

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
    

def writeline(s):
    print(s)
    


lastMonth = None

for year, month, day in list(listDates(2014))[:]:
    tdb0 = timescale.tdb(year, month, day, 0, 0, 0)
    tt0 = timescale.tt(year, month, day, 0, 0, 0)
    utc0 = timescale.utc(year, month, day, 0, 0, 0)
    utc12 = timescale.utc(year, month, day, 12, 0, 0)

    astrometric = earth.at(tdb0).observe(sun).apparent()
    ra, dec, distance = astrometric.radec(epoch='date')
    ecllat, ecllon, _ = astrometric.ecliptic_latlon(epoch='date')

    sidereal = utc0.gmst - ra.hours + 12
    if sidereal > 1: sidereal -= 24

    if lastMonth != None and lastMonth != month:
        writeline("\\hline")
    lastMonth = month

    writeline(" & ".join([    
        "%d/%d" % (month, day),
        convertRA(ra),
        convertDeg(dec),
        convertDeg(ecllon),                                       # 视黄经
        convertSidereal(Angle(hours=sidereal)),                   # 均时差
    ]) + " \\\\")

writeline("\\hline")

