#!/usr/bin/env python3

from skyfield.api import load
from skyfield import almanac
from skyfield.constants import DAY_S, tau
from skyfield.nutationlib import iau2000b
from skyfield.units import Angle

import sys
from pytz import timezone

from save_calculations import CalculationResults



YEAR = int(sys.argv[1])
assert YEAR > 2000 and YEAR < 3000



objects = load("de421.bsp")
sun = objects["Sun"]
earth = objects["Earth"]
BJT = timezone("Asia/Shanghai")

timescale = load.timescale()

definitions = "立春 雨水 惊蛰 春分 清明 谷雨 立夏 小满 芒种 夏至 小暑 大暑 立秋 处暑 白露 秋分 寒露 霜降 立冬 小雪 大雪 冬至 小寒 大寒".split(" ")



t0 = timescale.utc(YEAR, 1, 1)
t1 = timescale.utc(YEAR, 12, 31)

def solartermsAt(t):
    t._nutation_angles = iau2000b(t.tt)
    e = earth.at(t)
    _, slon, _ = e.observe(sun).apparent().ecliptic_latlon('date')
    return (slon.radians // (tau / 24) % 24).astype(int)
solartermsAt.rough_period=15



t, y = almanac.find_discrete(t0, t1, solartermsAt)


convertT = lambda t: t.astimezone(BJT).strftime("%m月%d日 %H:%M")

orderedOutput = [(
    definitions[y[i]], convertT(t[i]),
    definitions[y[i+12]], convertT(t[i+12]))
    for i in range(0, 12)
]

with CalculationResults("solarterms", YEAR) as writer:
    for line in orderedOutput:
        writer.writeline(" & ".join(list(line)) + "\\\\")
