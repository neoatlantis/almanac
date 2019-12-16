#!/usr/bin/env python3

import sys
import datetime

from skyfield.api import load, Topos
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time

from _calendar import listDates
from save_calculations import cached, CalculationResults



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
    return "%s%d°%d'" % (convertSign(sign), d, m)

def convertSidereal(sr):
    sign, _, m, s = sr.signed_hms()
    return "%s%dm%02ds" % (convertSign(sign), m, s)






class SVGNode(dict):

    def __init__(self, name, **kvargs):
        self.name = name
        self.attrs = kvargs
        self.children = []

    def append(self, what):
        self.children.append(what)
        return self

    def __str__(self):
        return "<%s %s>%s</%s>" % (
            self.name,
            " ".join(["%s=\"%s\"" % (k, self.attrs[k]) for k in self.attrs]),
            "".join([str(e) for e in self.children]),
            self.name
        )
        



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
    y += fontsize * 1.5

    for row in table:
        x = 0
        for i in range(0, len(row)):
            g.append(text(x, y).append(row[i]))
            x += headerWidth[i]
        y += fontsize * 1.5

    return g
        



class MonthGenerator:

    def __init__(self, year, month):
        self.year = year
        self.month = month

        self.svg = SVGNode(
            "svg",
            viewBox="0 0 842pt 595pt",
            xmlns="http://www.w3.org/2000/svg"
        )

        self.svg.append("""
            <style>text{
                font-family: monospace;
                font-size: 7pt;
                fill: black;
                white-space: pre;
                z-index:1000;
            }</style>""")

        self.svg.append(SVGNode("rect", 
            x=0, y=0, width="842pt", height="595pt",
            fill="#DDDDDD", stroke="red", 
        ))

        
        t = svgTable(
            [
                ["农历"],
                ["视赤经", "18h40m", "18h40m", "18h40m"],
                ["视赤纬", "-23°15'"],
                ["视黄经", "180°15'"],
                ["均时差", "-15h33m"],

                ["20N 月出", "09:00", "18:00"],
                ["    月没", "09:00", "18:00"],

                ["30N 月出", "09:00", "18:00"],
                ["    月没", "09:00", "18:00"],

                ["35N 月出", "09:00", "18:00"],
                ["    月没", "09:00", "18:00"],

                ["40N 月出", "09:00", "18:00"],
                ["    月没", "09:00", "18:00"],

                ["45N 月出", "09:00", "18:00"],
                ["    月没", "09:00", "18:00"],

                ["50N 月出", "09:00", "18:00"],
                ["    月没", "09:00", "18:00"],
            ],
            [ "        " ] + [ "%02d (一)" % i for i in range(1,17) ],
            fontsize=7,
        )
        t = self._tableOfMonth(1, 16)
        t.attrs["transform"] = "translate(10 30)"


        self.svg.append(t)


    def _tableOfMonth(self, start, end):
        data = []
        data.append(["儒略日"] + list(self._rowJulian(start, end)))
        data.append(["恒星时"] + list(self._rowSidereal(start, end)))
        for e in self._rowsSun(start,end): data.append(e)

        headers = [" " * 9]
        for i in range(start, end+1):
            dt = datetime.datetime(self.year, self.month, i)
            weekday = "一二三四五六日"[dt.weekday()]
            headers.append("%02d (%s)" % (i, weekday))
        table = svgTable(data, headers, fontsize=7)
        return table 


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


    def save(self, path):
        open(path, "w+").write(str(self.svg))







if __name__ == "__main__":
    x = MonthGenerator(2020, 1)
    x.save("2020-01.svg")
