#!/usr/bin/env python3

import sys
import calendar
import datetime
from math import ceil

from lunardate import LunarDate

from skyfield.api import load, Topos
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time

from _svgnode import *
from _calendar import listDates
from save_calculations import cached, CalculationResults, getCached



objects = load("de421.bsp")
sun = objects["Sun"]
earth = objects["Earth"]
timescale = load.timescale()


convertSign = lambda i: "" if i >= 0 else "-"

def convertRA(ra):
    sign, h, m, _ = ra.signed_hms()
    return "%s%dh%02dm" % (convertSign(sign), h, m)

def convertDeg(deg):
    sign, d, m, _ = deg.signed_dms()
    return "%s%d°%02d'" % (convertSign(sign), d, m)

def convertSidereal(sr):
    sign, _, m, s = sr.signed_hms()
    return "%s%dm%02ds" % (convertSign(sign), m, s)






        



def svgTable(table, headers, fontsize=10):
    g = SVGNode("g")

    headerWidth = [
        len(header) * fontsize * 1.35 
        for header in headers
    ]

    text = lambda x, y: SVGNode("text", **{
        "x": x,
        "y": y,
        "class": "common",
#        "text-anchor": "middle",
    })

    x, y = 0, 0
    for i in range(0, len(headers)):
        g.append(text(x, y).append(headers[i]))
        x += headerWidth[i]
    y += fontsize * 1.6

    for row in table:
        x = 0
        for i in range(0, len(row)):
            g.append(text(x, y).append(row[i]))
            x += headerWidth[i]
        y += fontsize * 1.6

    return g
        



class MonthGenerator:

    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.monthLastDay = calendar.monthrange(year, month)[1]

        self.calculationResults = {
            "moonphase": getCached("moonphase", self.year),
        }

        self.svg = SVGNode(
            "svg",
            viewBox="0 0 842pt 595pt",
            xmlns="http://www.w3.org/2000/svg"
        )

        self.svg.append("""
        <style>
        text{
            font-family: monospace;
            font-size: 7pt;
            fill: black;
            white-space: pre;
            z-index:1000;
        }
        .title{
            font-family: serif;
            font-weight: bold;
            font-size: 15pt;
            fill: black;
        }
        
        </style>""")

        self.svg.append(SVGNode("rect", 
            x=0, y=0, width="842pt", height="595pt",
            fill="#DDDDDD", stroke="red", 
        ))

        midday = ceil(self.monthLastDay / 2) 

        table1 = self._tableOfMonth(1, midday)
        table1.attrs["transform"] = "translate(30 40)"
        self.svg.append(table1)

        table2 = self._tableOfMonth(midday+1, self.monthLastDay)
        table2.attrs["transform"] = "translate(30 %d)" % (7 * 50)
        self.svg.append(table2)


        self.svg.append(SVGNode("text", **{
            "x": "421pt", "y": "240pt", "class": "title",
            "text-anchor": "middle",
        }).append("%d年%d月 天文普及月历" % (self.year, self.month)))



    def _tableOfMonth(self, start, end):
        data = []
        data.append(["农历"] + list(self._rowLunarDate(start, end)))
        data.append([" "])

        data.append(["儒略日"] + list(self._rowJulian(start, end)))
        data.append(["恒星时"] + list(self._rowSidereal(start, end)))
        for e in self._rowsSun(start,end): data.append(e)
        data.append([" "])
        for e in self._rowsMoon(start, end): data.append(e)

        headers = [" " * 8]
        for i in range(start, end+1):
            dt = datetime.datetime(self.year, self.month, i)
            weekday = "一二三四五六日"[dt.weekday()]
            headers.append("%02d (%s)" % (i, weekday))

        table = svgTable(data, headers, fontsize=7)
        return table 

    def _rowLunarDate(self, start, end):
        for day in range(start, end+1):
            ld = LunarDate.fromSolarDate(self.year, self.month, day)
            ldMonth = "正二三四五六七八九十冬腊"[ld.month-1] + "月"
            if ld.isLeapMonth:
                ldMonth = "闰" + ldMonth
            if ld.day <= 10:
                ldDay = "初" + "一二三四五六七八九十"[ld.day-1]
            elif ld.day < 20:
                ldDay = "十" + "一二三四五六七八九"[ld.day-11]
            elif ld.day == 20:
                ldDay = "二十"
            elif ld.day < 30:
                ldDay = "廿" + "一二三四五六七八九"[ld.day-21]
            elif ld.day == 30:
                ldDay = "三十"
            yield ldMonth + ldDay

    def _rowJulian(self, start, end):
        for day in range(start, end+1):
            utc0 = timescale.ut1(self.year, self.month, day, 0, 0, 0)
            yield "%.1f" % utc0.tt

    def _rowSidereal(self, start, end):
        for day in range(start, end+1):
            utc0 = timescale.ut1(self.year, self.month, day, 0, 0, 0)
            yield "%02dh%02dm%02ds" % Angle(hours=sidereal_time(utc0)).hms()[-3:]

    def _rowsSun(self, start, end):
        retRA, retDEC = ["视赤经"], ["视赤纬"]
        retEcllon, retEq = ["视黄经"], ["均时差"]

        for day in range(start, end+1):
            tdb0 = timescale.tdb(self.year, self.month, day, 0, 0, 0)
            tt0  = timescale.tt(self.year, self.month, day, 0, 0, 0)
            utc0 = timescale.utc(self.year, self.month, day, 0, 0, 0)
            ut10 = timescale.ut1(self.year, self.month, day, 0, 0, 0)

            astrometric = earth.at(tdb0).observe(sun).apparent()
            ra, dec, distance = astrometric.radec(epoch='date')
            ecllat, ecllon, _ = astrometric.ecliptic_latlon(epoch='date')

            equation_of_time = sidereal_time(ut10) - ra.hours + 12
            if equation_of_time > 1: equation_of_time -= 24

            retRA.append( convertRA(ra) )
            retDEC.append( convertDeg(dec) )
            retEcllon.append( convertDeg(dec) )
            retEq.append( convertSidereal(Angle(hours=equation_of_time)) )
        
        return [retRA, retDEC, retEcllon, retEq]

    def _rowsMoon(self, start, end):
        monthdata = self.calculationResults["moonphase"][self.month]
        ret = []
        for lat in [20, 30, 35, 40, 45, 50]:
            retRise = ["%02dN 月出" % lat]
            retSet  = ["    月落"] 
            for day in range(start, end+1):
                retRise.append(
                    monthdata[day]["riseset"][lat]["rise"] or "---")
                retSet.append(
                    monthdata[day]["riseset"][lat]["set"] or "---")
            ret.append(retRise)
            ret.append(retSet)
        return ret
                



    def save(self, path):
        open(path, "w+").write(str(self.svg))







if __name__ == "__main__":
    x = MonthGenerator(2020, 1)
    x.save("2020-01.svg")
