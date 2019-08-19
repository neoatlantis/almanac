#!/usr/bin/env python3

import sys
import datetime
import os
import json

from lunardate import LunarDate
import dateutil.parser
from pytz import timezone

from _calendar import listDates
from _constants import *
import numpy as np
import svgwrite


YEAR = int(sys.argv[1])
assert YEAR > 2000 and YEAR < 3000

calculations = {
    Mercury: [],
    Venus: [],
    Earth: [],
    Mars: [],
    Jupiter: [],
    Saturn: [],
    Uranus: [],
    Neptune: [],
}

for year, month, day in listDates(YEAR):
    ts = timescale.utc(year, month, day, 0, 0, 0)
    for planet in calculations:
        calculations[planet].append((
            year, month, day,
            Sun.at(ts).observe(planet).ecliptic_latlon()[1].degrees
        ))





for planet in calculations:
    imax = len(calculations[planet])
    for i in range(0, imax-1):
        if calculations[planet][i][-1] > calculations[planet][i+1][-1]:
            for k in range(i+1, imax):
                a,b,c,d = calculations[planet][k]
                calculations[planet][k] = (a,b,c,d+360) 


MULTICIRCLES = [Mercury, Venus]
LESSLABELS = [Jupiter, Saturn]
NOLABELS = [Uranus, Neptune]

LABELINTERVAL = {
    Mercury: 1, Venus: 1, Earth: 1, Mars: 1,
    Jupiter: 3, Saturn: 6,
    Uranus: 12, Neptune: 12
}

SIZE = 600
coord = lambda x, y: (x + SIZE / 2, SIZE / 2 - y)
START_RADIUS = SIZE / 10
STEP = (SIZE/2 - START_RADIUS) / (len(calculations.keys()) + 15)

dwg = svgwrite.Drawing("test.svg", size=(SIZE, SIZE))

startR = START_RADIUS
for planet in [Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune]:
    if planet not in calculations: continue

    xys = []
    for year, month, day, degrees in calculations[planet]:
        radians = degrees / 180.0 * np.pi
        if planet not in MULTICIRCLES:
            r = startR
        else:
            r = startR + degrees / 360 * STEP

        x = r * np.cos(radians)
        y = r * np.sin(radians)
        xys.append(coord(x, y))

        if month % LABELINTERVAL[planet] == 1 or LABELINTERVAL[planet] == 1:

            if day == 1:
                x1, y1 = (r-5) * np.cos(radians), (r-5) * np.sin(radians)
                x2, y2 = (r+5) * np.cos(radians), (r+5) * np.sin(radians)
                dwg.add(dwg.line(
                    coord(x1, y1), coord(x2, y2), stroke="black", fill="none"))

            if day == 15 and (planet not in NOLABELS):
                tx, ty = coord(x, y) # on graph, after coordinate transform
                dwg.add(dwg.text(
                    str(month), (tx-5, ty+5) ))
    
    dwg.add(dwg.polyline(points=xys, stroke="black", fill="none"))

    startR = r + STEP * 2


dwg.save()
