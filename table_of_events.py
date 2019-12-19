
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

import yaml
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


class MoonTrack:

    def __init__(self):
        self.year_period = (
            timescale.utc(YEAR, 1, 1),
            timescale.utc(YEAR, 12, 31, 23, 59, 59)
        )

    PERIGEE = "Perigee / 近地点"
    APOGEE = "Apogee / 远地点"

    def findApsides(self):
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

    ECLIPTIC_PASSAGE_ASCENDING = "Ecliptic Passage(Ascending) / 黄道升交点"
    ECLIPTIC_PASSAGE_DECENDING = "Ecliptic Passage(Decending) / 黄道降交点"

    def findEclipticPassage(self):
        def f(t):
            t._nutation_angles = iau2000b(t.tt)
            observ = Earth.at(t).observe(Moon).apparent().ecliptic_latlon()
            return observ[0].degrees
        f.rough_period = 14
        roots = root_finder(
            f=f,
            start_time=self.year_period[0], end_time=self.year_period[1]
        )
        outputs = []
        for t0, lat0 in roots:
            t1 = t0.ts.tt_jd(t0.tt + 1)
            ecllat1 = f(t1)
            outputs.append((
                t0,
                self.ECLIPTIC_PASSAGE_ASCENDING if ecllat1 > lat0 else
                self.ECLIPTIC_PASSAGE_DECENDING
            ))
        return outputs

    EQUATORIAL_PASSAGE_ASCENDING = "Equatorial Passage(Ascending) / 赤道升交点"
    EQUATORIAL_PASSAGE_DECENDING = "Equatorial Passage(Decending) / 赤道降交点"

    def findEquatorialPassage(self):
        def f(t):
            t._nutation_angles = iau2000b(t.tt)
            observ = Earth.at(t).observe(Moon).apparent().radec()
            return observ[1].degrees
        f.rough_period = 14
        roots = root_finder(
            f=f,
            start_time=self.year_period[0], end_time=self.year_period[1]
        )
        outputs = []
        for t0, dec0 in roots:
            t1 = t0.ts.tt_jd(t0.tt + 1)
            dec1 = f(t1)
            outputs.append((
                t0,
                self.EQUATORIAL_PASSAGE_ASCENDING if dec1 > dec0 else
                self.EQUATORIAL_PASSAGE_DECENDING
            ))
        return outputs

    EQUATORIAL_FARTHEST_NORTH = "Equatorial Farthest North / 赤纬北点"
    EQUATORIAL_FARTHEST_SOUTH = "Equatorial Farthest South / 赤纬南点"

    def findEquatorialFarthest(self):

        def f(t):
            t._nutation_angles = iau2000b(t.tt)
            observ = Earth.at(t).observe(Moon).apparent().radec()
            return observ[1].degrees
        f.rough_period = 14 
        critical_points = critical_point_finder(
            start_time=self.year_period[0],
            end_time=self.year_period[1],
            f=f
        )
        return [
            (
                t[1],
                (
                    self.EQUATORIAL_FARTHEST_SOUTH\
                    if y[2]-y[1]>0 and y[1]-y[0]<0\
                    else self.EQUATORIAL_FARTHEST_NORTH,
                    y[1]
                )
            )
            for t, y in critical_points
        ]

#for ti, yi in MoonTrack().findEquatorialFarthest():
#    print(ti.utc_iso(), yi)
#exit()




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
        def observe(t):
            t._nutation_angles = iau2000b(t.tt)
            moonApparent = Earth.at(t).observe(Moon).apparent()
            starApparent = Earth.at(t).observe(star).apparent()
            return moonApparent.radec('date'), starApparent.radec('date')
            
        def f(t):
            moonRadec, starRadec = observe(t)
            return moonRadec[0]._degrees - starRadec[0]._degrees
        f.rough_period = 29
        roots = root_finder(
            start_time=self.year_period[0],
            end_time=self.year_period[1],
            f=f
        )
        outputs = []
        for ti, _ in roots:
            moonRadec, starRadec = observe(ti)
            moonHalfSize = np.arctan(MOON_RADIUS / moonRadec[2].km) / np.pi * 180
            decDiff = starRadec[1].degrees - moonRadec[1].degrees

            outputs.append((ti, (decDiff, abs(decDiff) > moonHalfSize)))
            # (ti, (diff of declination, visible))
        return outputs


class GreatestSunElongation:

    def __init__(self):
        self.year_period = (
            timescale.utc(YEAR, 1, 1),
            timescale.utc(YEAR, 12, 31, 23, 59, 59)
        )
        self.topos_at = Earth.at

    def find(self, planet):
        assert planet in [Mercury, Venus]
        def observ(t):
            return (
                self.topos_at(t).observe(Sun).apparent().position.au,
                self.topos_at(t).observe(planet).apparent().position.au
            )

        def g(t):
            t._nutation_angles = iau2000b(t.tt)
            vec1, vec2 = observ(t)

            def norm(v):
                v2 = v**2
                return (v2[0] + v2[1] + v2[2]) ** 0.5

            dotS = vec1[0]*vec2[0] + vec1[1]*vec2[1] + vec1[2]*vec2[2]
            cosVec1Vec2 = dotS / norm(vec1) / norm(vec2)
            angle = np.arccos(cosVec1Vec2)
            return angle
            #return sunEcllon.degrees - planetEcllon.degrees

        g.rough_period = 40
        critical_points = critical_point_finder(
            start_time=self.year_period[0],
            end_time=self.year_period[1],
            f=g
        )
        found = []
        for t3, _ in critical_points:
            t1 = t3[1].tt
            t0 = t1 - 1
            t2 = t1 + 1
            y3 = g(t3[1].ts.tt_jd(np.array([t0, t1, t2])))

            if (y3[0] < y3[1] and y3[2] < y3[1]):
                ti = t3[1].ts.tt_jd(t1)
                vec1, vec2 = observ(ti)
                k = 1 if np.cross(vec1, vec2)[2] > 0 else -1
                found.append((ti, k * y3[1] * 180 / np.pi ))
        return found # (timescale, separation angle (+: east, -: west))



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
            start_time=self.year_period[0],
            end_time=self.year_period[1],
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
    "moon_ecliptic_passages": [],
    "moon_equatorial_passages": [],
    "moon_equatorial_farthest": [],
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
    "sun_elongations": {
        Mercury: [],
        Venus: [],
    },
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
    },
    "meteor_showers": [],
}

#-----------------------------------------------------------------------------
# Load meteor showers
print("Loading meteor showers...")
meteorShowerTranslations = yaml.load(open(
    os.path.join("external_predictions", "meteor_shower_names.yaml"),
    "r").read())
meteorShowers = yaml.load(open(
    os.path.join("external_predictions", str(YEAR), "meteor_shower.yaml"),
    "r").read())
for each in meteorShowers:
    meteorShower = meteorShowers[each]
    meteorShower["name"] = meteorShowerTranslations[each]["zh_CN"]
    date = meteorShower["date"]
    date = date.replace(tzinfo=UTC)
    t = timescale.utc(date)
    founds["meteor_showers"].append((t, meteorShower))

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
# search for sun elongations
print("Searching for sun elongations for Mercury and Venus...")
sunElongationFinder = GreatestSunElongation()
for planet in founds["sun_elongations"]:
    founds["sun_elongations"][planet] = sunElongationFinder.find(planet)
#-----------------------------------------------------------------------------
# Find out conjunctions with a few stars
if 1:
    print("Searching for moon conjunctions...")
    moonConjunctionFinder = MoonConjunctionFinder()
    for star in founds["moon_conjunctions"]:
        founds["moon_conjunctions"][star] = moonConjunctionFinder.find(star)
        print(".")

#-----------------------------------------------------------------------------
# Find out stationaries
if 1:
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
moonTrack = MoonTrack()
print("Searching for moon apsides...")
founds["moon_apsides"] = moonTrack.findApsides()
print("Searching for moon ecliptic passages...")
founds["moon_ecliptic_passages"] = moonTrack.findEclipticPassage()
print("Searching for moon equatorial passages...")
founds["moon_equatorial_passages"] = moonTrack.findEquatorialPassage()
print("Searching for moon equatorial farthest...")
founds["moon_equatorial_farthest"] = moonTrack.findEquatorialFarthest()

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

def translateMeteorShower(eventsList):
    return [
        (t, utcT, "%s ZHR=%s" % (data["name"], data["ZHR"]))
        for t, utcT, data in eventsList
    ]

def translateMoonApsides(eventsList):
    return [
        (t, utcT, "月球过" + data.split("/")[-1].strip())
        for t, utcT, data in eventsList
    ]

def translateMoonEclipticOrEquatorialPassages(eventsList):
    return [
        (t, utcT, "月球过" + data.split("/")[-1].strip())
        for t, utcT, data in eventsList
    ]

def translateMoonEquatorialFarthest(eventsList):
    return [
        (
            t,
            utcT,
            "月球过" + data[0].split("/")[-1].strip() +\
            " %0.1f°" % abs(data[1])
        )
        for t, utcT, data in eventsList
    ]

def translateMoonConjunctionEvents(eventsList, starName):
    output = []
    for t, utcT, data in eventsList:
        decDiff, visible = data
        if not visible:
            output.append((t, utcT, "月掩%s" % starName))
        else:
            output.append((
                t, utcT,
                "%s合月 %.1f°%s" % (
                    starName,
                    abs(decDiff),
                    "N" if decDiff > 0 else "S"
                )
            ))
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

def translateSunElongations(eventsList, planetName):
    output = []
    for t, utcT, data in eventsList:
        direction = "东" if data > 0 else "西"
        output.append((
            t,
            utcT,
            "%s%s大距 %.2f°" % (planetName, direction, abs(data))
        ))
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

    # 流星雨
    monthEvents += translateMeteorShower(
        filterEvents(founds["meteor_showers"], month))

    # 月相

    monthEvents += translateMoonPhases(
        filterEvents(founds["moon_phases"], month))

    # 月球 近地点 远地点

    monthEvents += translateMoonApsides(
        filterEvents(founds["moon_apsides"], month))

    # 月球 黄道/赤道 升/降交点，赤纬南北点

    monthEvents += translateMoonEclipticOrEquatorialPassages(
        filterEvents(founds["moon_ecliptic_passages"], month))
    monthEvents += translateMoonEclipticOrEquatorialPassages(
        filterEvents(founds["moon_equatorial_passages"], month))
    monthEvents += translateMoonEquatorialFarthest(
        filterEvents(founds["moon_equatorial_farthest"], month))

    # 二十四节气

    monthEvents += translateSolarterms(
        filterEvents(founds["solarterms"], month))

    listStar = { Regulus: "轩辕十四", Aldebaran: "毕宿五", Spica: "角宿一" }

    listPlanet = {
        Mercury: "水星", Venus: "金星", Mars: "火星", Jupiter: "木星",
        Saturn: "土星", Uranus: "天王星", Neptune: "海王星", Pluto: "冥王星"
    }

    for planet in [Mercury, Venus]:
        monthEvents += translateSunElongations(
            filterEvents(founds["sun_elongations"][planet], month),
            listPlanet[planet]
        )

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

MERGED = 3
SINGLECOLUMN_COLUMNS = 4


def writeTableHead():
    return """
\\begin{tabular}{llll|llll|llll}
\hline
	月 & 日 & 时刻 & 天象 &         % 月 & 日 & 时刻 & 天象 &
	月 & 日 & 时刻 & 天象 &
	月 & 日 & 时刻 & 天象 \\tabularnewline
\\hline"""

def writeTableFoot():
    return """\\hline \\end{tabular}"""




with open("calculations-cache/events-%d.yaml" % YEAR, "w+") as writer:
    writer.write(yaml.dump(
        tableBuffer,
        allow_unicode=True,
        default_flow_style=False
    ))



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
