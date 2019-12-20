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
import time

import PyGnuplot as gp




class DiagramOfPlanets:

    ALL_OBJECTS = [
        Sun, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune
    ]

    ALL_OBJECTS_NAME = "太阳 水星 金星 火星 木星 土星 天王星 海王星".split(" ")

    #OBJECT_SYMBOLS = "\u2609\u263f\u2640\u2642\u2643\u2644\u26E2\u2646"
    OBJECT_SYMBOLS = "日水金火木土天海"

    def __init__(self, year, month, extension=2):
        midtime = timescale.utc(year, month, 15)
        starttime = timescale.ut1(jd=midtime.tt - (31 * extension +1 ))
        endtime   = timescale.ut1(jd=midtime.tt + (31 * extension +32))
        starttime = timescale.utc(starttime.utc[0], starttime.utc[1], 1)
        endMonthLastDay = calendar.monthrange(
            endtime.utc[0], endtime.utc[1])[1]
        endtime   = timescale.utc(endtime.utc[0], endtime.utc[1], 1)
#            endtime.utc[0], endtime.utc[1], endMonthLastDay, 23, 59, 59)

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

    def _discontinuities(self, series, e=1):
        i = 0
        while i < len(series) - 1:
            value1 = series[i]
            value2 = series[i+1]
            if abs(value1-value2) > e:
                series[i+1] = '"?"'
                i += 2
            else:
                i += 1
        return series

    def _setupGnuplot(self, width=580):
        gp.c("reset")
        gp.c("set term svg size %d,270" % width)
        gp.c('set output "temp.svg"')

        gp.c("""set ydata time""")
        gp.c("set timefmt \"%Y-%m-%dT%H:%M:%S\"")
        gp.c("set format y \"%Y-%m\"")
        gp.c('set yrange ["%s":"%s"]' % (
            self.timerange[0].utc_strftime("%Y-%m-%d"),
            self.timerange[1].utc_strftime("%Y-%m-%d")
        ))
        gp.c('set ytics 2592746')



    def decDiagram(self):
        ts_n = self.data["ts_n"]
        data = [ts_n.utc_strftime("%Y-%m-%dT%H:%M:%S")]

        for o in self.ALL_OBJECTS:
            decs = [
                self.data[o][1].degrees[i] # Dec
                for i in range(0, len(ts_n))
            ]
            data.append(decs)

        self._setupGnuplot(width=480)
        gp.s(data)

        gp.c("set format x \"%02.0f\"")

        gp.c("""set xrange [30:-30]""")
        gp.c("""set xtics 10""")
        gp.c("""set mxtics 5""")
        gp.c("""set format y ''""")
        gp.c('set x2label "赤纬"')

        gp.c('set nokey')
        gp.c('set grid xtics ytics')
        #gp.c("""plot for[n=2:9] "tmp.dat" u n:1""")

        gp.c("plot " + ",".join([
            '"tmp.dat" using %d:1 title "%s" enhanced with linespoints pi 30 ps 1 pt "%s" lt rgb "black" dt 1' % 
            (i+2, self.ALL_OBJECTS_NAME[i], self.OBJECT_SYMBOLS[i])
            for i in range(0, len(self.ALL_OBJECTS))
        ]))

        gp.c("unset output")
        while True:
            time.sleep(0.1)
            ret = open("temp.svg", "r").read()
            if "</svg>" in ret: break 
        os.unlink("temp.svg")
        os.unlink("tmp.dat")
        return ret





    def hourAngleDiagram(self):
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
            data.append(self._discontinuities(meridianTimes))

        for ra in range(0, 25, 2):
            data.append(self._discontinuities([
                meridianTime(ra, self.data["sidereal"][i], deltas[i])
                for i in range(0, len(deltas))
            ]))

        self._setupGnuplot()

        gp.c('set datafile missing "?"')
        gp.s(data)


        gp.c("set format x \"%02.0f\"")
        gp.c("""set xrange [24:0]""")
        gp.c("""set xtics 1""")
        gp.c('set x2label "上中天时刻"')


        #gp.c('set key outside reverse samplen 1 width -4 font "monospace,8pt"')
        gp.c('set nokey')
        gp.c('set grid xtics ytics')
        #gp.c("""plot for[n=2:9] "tmp.dat" u n:1""")

        gp.c("plot " + ",".join([
            '"tmp.dat" using ($%d):1 title "%dh" at end with lines  lc rgb "#FF6666" ' % 
            (i + 10, i*2)
            for i in range(0, 13)
        ] + [
            '"tmp.dat" using ($%d):1 title "%s" enhanced with linespoints pi 30 pt "%s" lt rgb "black" dt 1' % 
            (i+2, self.ALL_OBJECTS_NAME[i], self.OBJECT_SYMBOLS[i])
            for i in range(0, len(self.ALL_OBJECTS))
        ]))

        gp.c("unset output")
        while True:
            time.sleep(0.1)
            ret = open("temp.svg", "r").read()
            if "</svg>" in ret: break 
        os.unlink("temp.svg")
        #os.unlink("tmp.dat")
        return ret



if __name__ == "__main__":
    YEAR = int(sys.argv[1])
    assert 2000 < YEAR < 3000

    c = DiagramOfPlanets(YEAR, 6)
    print(c.hourAngleDiagram())
    #print(c.decDiagram())
