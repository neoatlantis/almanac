
#!/usr/bin/env python3


from skyfield import api, almanac
from skyfield.api import load, Topos, Star
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time
from skyfield.nutationlib import iau2000b

from _utils import roundTimeToMinute

from _calendar import listDates
from save_calculations import CalculationResults

import json
import os
import sys
import numpy as np
from pytz import timezone
import dateutil.parser

YEAR = int(sys.argv[1])
assert 2000 < YEAR < 3000



moonPhasePath = os.path.join("calculations", str(YEAR), "moonphase.json")
if not os.path.exists(moonPhasePath):
    print("Run `python3 table_of_moon.py %d` first." % YEAR)
    exit(1)
moonPhases = json.loads(open(moonPhasePath, "r").read())

solartermsPath = os.path.join("calculations", str(YEAR), "solarterms.json")
if not os.path.exists(solartermsPath):
    print("Run `python3 table_of_solarterms.py %d` first." % YEAR)
    exit(1)
solarterms = json.loads(open(solartermsPath, "r").read())




ephemeris421 = load("de421.bsp")
timescale = load.timescale()
BJT = timezone("Asia/Shanghai")


Regulus         = Star(ra_hours=(10, 8, 21.98), dec_degrees=(11, 58, 3.0))      # 轩辕十四
Aldebaran       = Star(ra_hours=(4, 35, 55.33), dec_degrees=(16, 30, 29.6))     # 毕宿五
Spica           = Star(ra_hours=(13, 25, 11.53), dec_degrees=(-11, 9, 41.5))    # 角宿一

Mercury = ephemeris421["Mercury"]
Venus   = ephemeris421["Venus"]
Earth   = ephemeris421["Earth"]
Moon    = ephemeris421["Moon"]
Mars    = ephemeris421["Mars"]
Jupiter = ephemeris421["JUPITER BARYCENTER"]
Saturn  = ephemeris421["SATURN BARYCENTER"]
Uranus  = ephemeris421["Uranus Barycenter"]
Neptune = ephemeris421["Neptune Barycenter"]
Pluto   = ephemeris421["Pluto Barycenter"]


##############################################################################

def derivate(f):
    # A derivate decorator.
    #
    # First order derivate of discrete function f. The first value is kept
    # same with the first difference result, therefore making derivate(f)
    # the same length of f.
    def derivate_of_f(t):
        fs = f(t) # t is a 1-d numpy.array
        gs = np.diff(fs, n=1)
        np.insert(gs, -1, np.array([gs[-1]]))
        return gs
    return derivate_of_f



class PtolemaicAspects:

    CONJUNCTION = 1     # 合
    OPPOSITION = 2      # 冲

    def __init__(self, ephemeris, year, withStar):
        self.year_period = (
            timescale.utc(YEAR-1, 6, 1),
#            timescale.utc(YEAR, 4, 30, 23, 59, 59)
            timescale.utc(YEAR+1, 6, 30, 23, 59, 59)
        )
        self.withStar = withStar
        self.earth_at = ephemeris["earth"].at

    def find(self, star, rough_period):
        
        @derivate
        def d_deltaRA(t):
            t._nutation_angles = iau2000b(t.tt)
            baseApparent = self.earth_at(t).observe(self.withStar).apparent()
            starApparent = self.earth_at(t).observe(star).apparent()
            baseRA = baseApparent.radec('date')[0].hours
            starRA = starApparent.radec('date')[0].hours
            deltaRA1 = np.abs(baseRA - starRA)
            deltaRA2 = 24 - deltaRA1
            return np.minimum(deltaRA1, deltaRA2)

        def finder(t):
            return d_deltaRA(t) > 0
        finder.rough_period = rough_period

        t, y = almanac.find_discrete(
            self.year_period[0], self.year_period[1],
            finder
        )

        output = []
        for ti, yi in zip(t, y):
            output.append((ti, self.CONJUNCTION if yi else self.OPPOSITION))
        return output

##############################################################################
# Register of all found events
# Each list entry is given as (time, data)

founds = {
    "moon_conjunctions": {
        Regulus: [],
        Aldebaran: [],
        Spica: [],
        Mercury: [],
        Venus: [],
        Mars: [],
        Jupiter: [],
        Saturn: [],
        Uranus: [],
        Neptune: [],
        Pluto: [],
    },
    "moon_phases": [],
    "solarterms": [],
}

#-----------------------------------------------------------------------------
# sort out moonphase.json and append to register
for datestr in moonPhases:
    month, day = tuple([int(e) for e in datestr.split("-")])
    t = dateutil.parser.parse(moonPhases[datestr]["time"])
    p = moonPhases[datestr]["phase"]
    ts = timescale.utc(t)
    founds["moon_phases"].append((ts, p))

#-----------------------------------------------------------------------------
# sort out solarterms.json and append to register
for solarterm in solarterms:
    solartermTime = dateutil.parser.parse(solarterms[solarterm])
    ts = timescale.utc(solartermTime)
    founds["solarterms"].append((ts, solarterm))

#-----------------------------------------------------------------------------
# Find out conjunctions with a few stars

if True:
    moonConjFinder = PtolemaicAspects(ephemeris421, YEAR, Moon)
    for star in founds["moon_conjunctions"]:
        for ti, yi in moonConjFinder.find(star, rough_period=29):
            if yi != PtolemaicAspects.CONJUNCTION: continue
            founds["moon_conjunctions"][star].append((ti, yi))

##############################################################################
# Sort out events into month and push to table buffer
tableBuffer = [[], [], [], [], [], [], [], [], [], [], [], []]

def filterEvents(source, month):
    output = []
    for t, data in source:
        utcT = t.utc_datetime()
        if utcT.year != YEAR or utcT.month != month: continue
        output.append((t, utcT, data))
    return output

def translateMoonConjunctionEvents(eventsList, starName):
    output = []
    for t, utcT, data in eventsList:
        output.append((t, utcT, "%s合月" % starName)) # TODO: 掩？
    return output

def translateMoonPhases(eventsList):
    output = []
    for t, utcT, data in eventsList:
        output.append((t, utcT, ["朔", "上弦", "望", "下弦"][data]))
    return output

def translateSolarterms(eventsList):
    output = []
    for t, utcT, solarterm in eventsList:
        output.append((t, utcT, solarterm))
    return output
        

for month in range(1, 13):
    monthEvents = []

    monthEvents += translateMoonPhases(
        filterEvents(founds["moon_phases"], month))

    monthEvents += translateSolarterms(
        filterEvents(founds["solarterms"], month))

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Regulus], month), "轩辕十四")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Aldebaran], month), "毕宿五")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Spica], month), "角宿一")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Mercury], month), "水星")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Venus], month), "金星")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Mars], month), "火星")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Jupiter], month), "木星")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Saturn], month), "土星")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Uranus], month), " 天王星")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Neptune], month), "海王星")

    monthEvents += translateMoonConjunctionEvents(filterEvents(
        founds["moon_conjunctions"][Pluto], month), "冥王星")

    monthEvents.sort(key=lambda entry: entry[0].tt)

    #monthIsWritten = False
    #if month != 1:
    #    writer.writeline("\\hline")


    for ts, utcT, description in monthEvents:
        tableBuffer[month-1].append([ 
            str(utcT.month),# if not monthIsWritten else "")
            #monthIsWritten = True
            str(utcT.day),
            "%02d:%02d" % (utcT.hour, utcT.minute),
            description
        ])


##############################################################################
# tableBuffer is now a list containing 12 sub-lists of monthly events as rows.

MERGED = 4
SINGLECOLUMN_COLUMNS = 4


def writeTableHead():
    return """
\\begin{tabular}{llll|llll|llll|llll}
\hline
	月 & 日 & 时刻 & 天象 &
	月 & 日 & 时刻 & 天象 &
	月 & 日 & 时刻 & 天象 &
	月 & 日 & 时刻 & 天象 \\tabularnewline
\\hline"""

def writeTableFoot():
    return """\\hline \\end{tabular}"""


with CalculationResults("events", YEAR) as writer:

    for m in range(1, 13, MERGED):
        writer.writeline(writeTableHead())

        while True:
            line = []
            poped = False
            for i in range(0, MERGED):
                if tableBuffer[m+i-1]:
                    linebuffer = " & " .join(tableBuffer[m+i-1].pop(0))
                    poped = True
                else:
                    linebuffer = " & " * (SINGLECOLUMN_COLUMNS - 1)
                line.append(linebuffer)
            if not poped: break
            print(line)

            writer.writeline(" & ".join(line) + " \\tabularnewline")
        
        writer.writeline(writeTableFoot())
