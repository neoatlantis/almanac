#!/usr/bin/env python3

from skyfield import api, almanac
from skyfield.api import load, Topos, Star
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time
from skyfield.nutationlib import iau2000b
from skyfield.earthlib import sidereal_time

from _utils import roundTimeToMinute
from _constants import *
from _rootfinder import  root_finder, critical_point_finder
from _spheric_dist import spherical_distance

from _calendar import listDates
from save_calculations import CalculationResults

from math import ceil
import calendar
import yaml
import json
import os
import sys
import numpy as np
from pytz import timezone
import dateutil.parser

import PyGnuplot as gp




class DiagramOfPlanets:

    ALL_OBJECTS = [
        Sun, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune
    ]

    ALL_OBJECTS_NAME = "太阳 水星 金星 火星 木星 土星 天王星 海王星".split(" ")

    def __init__(self, year, month, extension=2):
        midtime = timescale.utc(year, month, 15)
        starttime = timescale.ut1(jd=midtime.tt - extension * 32)
        endtime   = timescale.ut1(jd=midtime.tt + extension * 32)
        starttime = timescale.utc(starttime.utc[0], starttime.utc[1], 1)
        endMonthLastDay = calendar.monthrange(
            endtime.utc[0], endtime.utc[1])[1]
        endtime   = timescale.utc(
            endtime.utc[0], endtime.utc[1], endMonthLastDay, 23, 59, 59)

        self.timerange = (starttime, endtime)
        self._calc()

    def _calc(self):
        days = self.timerange[1].tt - self.timerange[0].tt
        jd = np.linspace(
            self.timerange[0].tt, self.timerange[1].tt, ceil(days))
        ts_n = timescale.tt_jd(jd)

        observe = lambda p: Earth.at(ts_n).observe(p).apparent().radec()[:2]
        self.data = {
            "ts_n":     ts_n,
            "sidereal": sidereal_time(ts_n),
        }
        for each in self.ALL_OBJECTS:
            self.data[each] = observe(each)

    def hourAngleDiagramm(self):
        def meridianTime(ra, sidereal, delta):
            mt = ra - (sidereal - delta)
            if mt > 24: mt -= 24
            if mt < 0: mt += 24
            return mt

        ts_n = self.data["ts_n"]
        data = [ts_n.utc_strftime("%Y-%m-%dT%H:%M:%S")]

        deltas = []
        for i in range(0, len(self.data["sidereal"])):
            delta = ts_n[i].tt - timescale.utc(*ts_n[i].utc[:3], 0, 0, 0).tt
            delta *= 24
            deltas.append(delta)

        for o in self.ALL_OBJECTS:
            meridianTimes = [
                meridianTime(
                    self.data[o][0].hours[i], # RA
                    self.data["sidereal"][i], # sidereal time
                    deltas[i]                 # diff to UTC=0
                )
                for i in range(0, len(deltas))
            ]
            data.append(meridianTimes)

        for ra in range(0, 25, 2):
            data.append([
                meridianTime(ra, self.data["sidereal"][i], deltas[i])
                for i in range(0, len(deltas))
            ])



        gp.s(data)

        gp.c('set size ratio 0.4')
        gp.c("""set ydata time""")
        gp.c("set timefmt \"%Y-%m-%dT%H:%M:%S\"")
        gp.c("set format y \"%Y-%m\"")
        gp.c('set yrange ["%s":"%s"]' % (
            self.timerange[0].utc_strftime("%Y-%m-%d"),
            self.timerange[1].utc_strftime("%Y-%m-%d")
        ))
        gp.c('set ytics 2592746')

        gp.c("set format x \"%02.0f\"")
        gp.c("""set xrange [24:0]""")
        gp.c("""set xtics 1""")

        gp.c('set key outside reverse samplen 1 width -3 font "monospace,8pt"')
        gp.c('set grid xtics ytics')
        #gp.c("""plot for[n=2:9] "tmp.dat" u n:1""")

        gp.c("plot " + ",".join([
            '"tmp.dat" using %d:1 title "%s" enhanced with linespoints pi 10 lt rgb "black" dt 1' % 
            (i+2, self.ALL_OBJECTS_NAME[i])
            for i in range(0, len(self.ALL_OBJECTS))
        ] + [
            '"tmp.dat" using %d:1 title "%d" at end with points pt 0 ps 1 lc rgb "black" ' % 
            (i + 10, i*2)
            for i in range(0, 13)
        ]))
            




if __name__ == "__main__":
    YEAR = int(sys.argv[1])
    assert 2000 < YEAR < 3000

    c = DiagramOfPlanets(YEAR, 1)
    c.hourAngleDiagramm()
