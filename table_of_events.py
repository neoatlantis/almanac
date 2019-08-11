
#!/usr/bin/env python3


from skyfield import api, almanac
from skyfield.api import load, Topos, Star
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time
from skyfield.nutationlib import iau2000b

from _utils import roundTimeToMinute
from _constants import *
from _rootfinder import  root_finder, critical_point_finder
from _spheric_dist import spherical_distance

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


class MoonApsidesFinder:

    PERIGEE = "Perigee / 近地点"
    APOGEE = "Apogee / 远地点"

    def __init__(self):
        self.year_period = (
            timescale.utc(YEAR, 1, 1),
            timescale.utc(YEAR, 12, 31, 23, 59, 59)
        )

    def find(self):
        def f(t):
            t._nutation_angles = iau2000b(t.tt)
            observ = Earth.at(t).observe(Moon).apparent().radec()
            return observ[2].km
        f.rough_period = 29
        critical_points = critical_point_finder(
            start_time=self.year_period[0],
            end_time=self.year_period[1],
            f=f,
            num=2048,
            epsilon=10000000
        )
        return [
            (
                t[1],
                self.PERIGEE if y[2]-y[1]>0 and y[1]-y[0]<0 else self.APOGEE,
            )
            for t, y in critical_points
        ]




class SunAspectFinder:

    CONJUNCTION = "Conjunction / 合日" 
    CONJUNCTION_INFERIOR = "Inferior Conjunction / 下合日"
    CONJUNCTION_SUPERIOR = "Superior Conjunction / 上合日"
    OPPOSITION = "Opposition / 冲日"
    QUADRATURE_WESTERN = "Western Quadrature / 西方照"
    QUADRATURE_EASTERN = "Eastern Quadrature / 东方照"


    def __init__(self):
        self.year_period = (
            timescale.utc(YEAR, 1, 1),
            timescale.utc(YEAR, 12, 31, 23, 59, 59)
        )

    def _deltaLambdaAu(self, planet, t):
        t._nutation_angles = iau2000b(t.tt)
        sunApparent = Earth.at(t).observe(Sun).apparent()
        planetApparent = Earth.at(t).observe(planet).apparent()
        sunPos = sunApparent.ecliptic_latlon('date')
        planetPos = planetApparent.ecliptic_latlon('date')

        return (
            sunPos[1].degrees - planetPos[1].degrees,
            sunPos[2].km - planetPos[2].km
        )

    def find(self, planet):
        
        def f(t):
            """Conjunction, opposition or quadature of planet with respect
            to sun. By searching the roots of f(t), all aspects will be
            determined. But remains unclear which aspect it is and shall
            be found out later."""
            return np.sin(self._deltaLambdaAu(planet, t)[0] / 90.0 * np.pi)
        f.rough_period = 30

        roots = root_finder(
            start_time=timescale.utc(YEAR, 1, 1),
            end_time=timescale.utc(YEAR, 12, 31, 23, 59, 59),
            f=f
        )

        results = []
        for ti, _ in roots:
            deltaLambda, deltaAu = self._deltaLambdaAu(planet, ti)

            if planet in [Mercury, Venus]:
                # Can only be conjunction(superior or inferior). By determining
                # the Au difference it's easy to tell
                results.append((
                    ti,
                    self.CONJUNCTION_INFERIOR
                    if deltaAu > 0 else self.CONJUNCTION_SUPERIOR
                ))
            else:
                sinL = round(np.sin(deltaLambda / 180.0 * np.pi))
                cosL = round(np.cos(deltaLambda / 180.0 * np.pi))
                results.append((ti, {
                    (0, 1) : self.CONJUNCTION,
                    (0, -1): self.OPPOSITION,
                    (1, 0):  self.QUADRATURE_WESTERN,
                    (-1, 0): self.QUADRATURE_EASTERN,
                }[(sinL, cosL)]))

        return results


class MoonConjunctionFinder:

    def __init__(self):
        self.year_period = (
            timescale.utc(YEAR, 1, 1),
            timescale.utc(YEAR, 12, 31, 23, 59, 59)
        )

    def find(self, star):
        def f(t):
            t._nutation_angles = iau2000b(t.tt)
            moonApparent = Earth.at(t).observe(Moon).apparent()
            starApparent = Earth.at(t).observe(star).apparent()
            return moonApparent.radec()[0]._degrees\
                - starApparent.radec()[0]._degrees
        f.rough_period = 29
        roots = root_finder(
            start_time=self.year_period[0],
            end_time=self.year_period[1],
            f=f
        )
        return roots


class GreatestSunElongation:

    def __init__(self):
        self.year_period = (
            timescale.utc(YEAR, 1, 1),
            timescale.utc(YEAR, 12, 31, 23, 59, 59)
        )
        self.sun = ephemeris["sun"]
        self.topos_at = ephemeris["earth"].at

    def findRough(self, star):

        def finder(t):
            t._nutation_angles = iau2000b(t.tt)
            sunRA, sunDec, _ = self.topos_at(t).observe(sun).apparent().radec('date')
            starRA, starDec, _ = self.topos_at(t).observe(star).apparent().radec('date')



            minRA = self.__minRA(star, t)
            return minRA < 1.0 / 60
        finder.rough_period = 1/29
        t, y = almanac.find_discrete(
            self.year_period[0], self.year_period[1],
            finder
        )


class StationaryFinder:

    def __init__(self):
        self.year_period = (
            timescale.utc(YEAR, 1, 1),
            timescale.utc(YEAR, 12, 31, 23, 59, 59)
        )

    def find(self, planet):
        def g(t):
            t._nutation_angles = iau2000b(t.tt)
            ra1 = Earth.at(t).observe(planet).radec()[0].hours
            ra2 = 24 - ra1
            return np.amin(np.array([ra1, ra2]), axis=0)
        g.rough_period = 20 
        found = []
        critical_points = critical_point_finder(
            start_time=timescale.utc(2019, 1, 1),
            end_time=timescale.utc(2019, 12, 31, 23, 59, 59),
            f=g
        )
        for t, y in critical_points:
            found.append(( t[1], None))
        return found




##############################################################################
# Register of all found events
# Each list entry is given as (time, data)

founds = {
    "moon_apsides": [],
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
    "stationaries": {
        Mercury: [],
        Venus: [],
        Mars: [],
        Jupiter: [],
        Saturn: [],
        Uranus: [],
        Neptune: [],
        Pluto: [],
    },
    "planet_aspects": {
        Mercury: [],
        Venus: [],
        Mars: [],
        Jupiter: [],
        Saturn: [],
        Uranus: [],
        Neptune: [],
        Pluto: [],
    }
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
    print("Searching for moon conjunctions...")
    moonConjunctionFinder = MoonConjunctionFinder()
    for star in founds["moon_conjunctions"]:
        founds["moon_conjunctions"][star] = moonConjunctionFinder.find(star)
        print(".")

#-----------------------------------------------------------------------------
# Find out stationaries
if True:
    print("Searching for stationaries...")
    stationariesFinder = StationaryFinder()
    for star in founds["stationaries"]:
        founds["stationaries"][star] = stationariesFinder.find(star)
        print(".")

#-----------------------------------------------------------------------------
# Find out planet aspects to sun
print("Searching for planet aspects...")
sunAspectFinder = SunAspectFinder()
for planet in founds["planet_aspects"]:
    founds["planet_aspects"][planet] = sunAspectFinder.find(planet)
    print(".")

#-----------------------------------------------------------------------------
# Find out moon apsides
print("Searching for moon apsides...")
founds["moon_apsides"] = MoonApsidesFinder().find()

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

def translateMoonApsides(eventsList):
    return [
        (t, utcT, "月球过" + data.split("/")[-1].strip())
        for t, utcT, data in eventsList
    ]

def translateMoonConjunctionEvents(eventsList, starName):
    output = []
    for t, utcT, data in eventsList:
        output.append((t, utcT, "%s合月" % starName)) # TODO: 掩？
    return output

def translatePlanetAspects(eventsList, starName):
    return [
        (t, utcT, "%s%s" % (
            starName,
            event.split("/")[-1].strip() # CN name defined in finder class
        )) for t, utcT, event in eventsList
    ]

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

def translateStationaries(eventsList, starName):
    return [
        (t, utcT, "%s留" % starName)
        for t, utcT, data in eventsList
    ]
        

for month in range(1, 13):
    monthEvents = []

    # 月相

    monthEvents += translateMoonPhases(
        filterEvents(founds["moon_phases"], month))

    # 近地点 远地点

    monthEvents += translateMoonApsides(
        filterEvents(founds["moon_apsides"], month))

    # 二十四节气

    monthEvents += translateSolarterms(
        filterEvents(founds["solarterms"], month))

    listStar = { Regulus: "轩辕十四", Aldebaran: "毕宿五", Spica: "角宿一" }

    listPlanet = {
        Mercury: "水星", Venus: "金星", Mars: "火星", Jupiter: "木星",
        Saturn: "土星", Uranus: "天王星", Neptune: "海王星", Pluto: "冥王星"
    }

    for star in listStar:
        # 合月
        monthEvents += translateMoonConjunctionEvents(filterEvents(
            founds["moon_conjunctions"][star], month), listStar[star])

    for planet in listPlanet:
        # 合月
        monthEvents += translateMoonConjunctionEvents(filterEvents(
            founds["moon_conjunctions"][planet], month), listPlanet[planet])
        # 留
        monthEvents += translateStationaries(filterEvents(
            founds["stationaries"][planet], month), listPlanet[planet])
        # 冲、合、方照
        monthEvents += translatePlanetAspects(filterEvents(
            founds["planet_aspects"][planet], month), listPlanet[planet])




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
	月 & 日 & 时刻 & 天象 &          月 & 日 & 时刻 & 天象 &
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
