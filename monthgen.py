#!/usr/bin/env python3

import os
import sys
import calendar
from subprocess import run
import datetime
import dateutil.parser
from math import ceil
from pytz import timezone

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

def convertHM(ra):
    sign, h, m, _ = ra.signed_hms()
    return "%s%d<tspan class='sup' dy='-3'>h</tspan>" % (convertSign(sign), h) +\
        "<tspan dy='3'>%02d</tspan><tspan class='sup' dy='-3'>m</tspan>" % m 

def convertHMS(ra):
    sign, h, m, s = ra.signed_hms()
    return "%s%d<tspan class='sup' dy='-3'>h</tspan>" % (convertSign(sign), h) +\
        "<tspan dy='3'>%02d</tspan><tspan class='sup' dy='-3'>m</tspan>" % m +\
        "<tspan dy='3'>%02d</tspan><tspan class='sup' dy='-3'>s</tspan>" % s

def convertDeg(deg):
    sign, d, m, _ = deg.signed_dms()
    return "%s%d<tspan class='red'>°</tspan>%02d<tspan class='red'>'</tspan>"\
        % (convertSign(sign), d, m)

def convertSidereal(sr):
    sign, _, m, s = sr.signed_hms()
    return "%s%d<tspan class='sup' dy='-3'>m</tspan>" % (convertSign(sign), m) +\
        "<tspan dy='3'>%02d</tspan><tspan class='sup' dy='-3'>s</tspan>" % s



        



def svgTable(
    table, headers,
    fontsize=10, lineheight=1.6, headerwidth=1.37
):

    g = SVGNode("g")

    headerWidth = [
        len(header) * fontsize * headerwidth 
        for header in headers
    ]

    text = lambda x, y, l: SVGNode("text", **{
        "x": x,
        "y": y,
#        "textLength": l,
        "class": "common",
#        "lengthAdjust": "spacingAndGlyphs"
#        "text-anchor": "middle",
    })

    x, y = 0, 0
    for i in range(0, len(headers)):
        n = text(x,y, headerWidth[i]).append(headers[i])
        n.attrs["class"] += " table-header"
        g.append(n)
        x += headerWidth[i]
    y += fontsize * lineheight 

    for row in table:
        x = 0
        for i in range(0, len(row)):
            n = text(x,y, headerWidth[i]).append(row[i])
            n.attrs["class"] += " table-cell"
            if i == 0: n.attrs["class"] += " table-first-cell"
            g.append(n)
            x += headerWidth[i]
        y += fontsize * lineheight

    return g
        



class MonthGenerator:

    DEFS = """
    <defs>
    <style>
    @font-face{
        font-family: NotoMono;
        src: url("./NotoMono.ttf");
    }
    </style>
    </defs>
    """

    STYLE = """
        .table-first-cell{
            text-align: right;
        }
        .red{ fill: red; }
        .sup{ font-size: 6pt; fill: red; }
        .common,.table-cell,.table-header{
            font-family: NotoMono, monospace;
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
            z-index:1000;
        }
        .cheatsheet{
            font-size:30pt; font-family:sans; font-weight:bold;
            fill: white;
        }
    """

    PAGE_SIZE = (1052, 744)
    ANCHOR_TOP_LEFT = (30, 30)
    ANCHOR_MIDDLE_LEFT = (30, 520)
    ANCHOR_BOTTOM_LEFT = (30, 630)

    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.monthLastDay = calendar.monthrange(year, month)[1]

        self.frontRange = (1, 16)
        self.backRange = (self.monthLastDay - 15, self.monthLastDay)

        self.calculationResults = {
            "moonphase": getCached("moonphase", self.year),
            "solarterms": getCached("solarterms", self.year),
            "sunriseset": getCached("sunriseset", self.year),
            "events": getCached("events", self.year),
            "planets": getCached("planets", self.year),
        }

        self.fig1 = open("fig1.svg", "r").read().split("\n")
        self.fig1 = "".join(self.fig1[3:])

        self.front = SVGNode(
            "svg",
            viewBox="0 0 %dpt %dpt" % (self.PAGE_SIZE),
            xmlns="http://www.w3.org/2000/svg"
        )
        self.back = SVGNode(
            "svg",
            viewBox="0 0 %dpt %dpt" % (self.PAGE_SIZE),
            xmlns="http://www.w3.org/2000/svg"
        )

        tableE, tableECols = self._tableOfEvents(1, self.monthLastDay)
        tableE.attrs["transform"] = "translate(%d %d)" % (self.ANCHOR_BOTTOM_LEFT)

        table1 = self._tableOfMonth(1, 16)
        table1.attrs["transform"] = "translate(%d %d)" % (self.ANCHOR_TOP_LEFT)

        table2 = self._tableOfMonth(self.monthLastDay-15, self.monthLastDay)
        table2.attrs["transform"] = "translate(%d %d)" % (self.ANCHOR_TOP_LEFT)

        self.front.append(self.DEFS).append("<style>%s</style>" % self.STYLE)
        self.back.append(self.DEFS).append("<style>%s</style>" % self.STYLE)
        self.decoratePage(self.front, withFigure=(tableECols <= 4))
        self.decoratePage(self.back, withFigure=(tableECols <= 4))

        self.front.append(table1)
        self.back.append(table2)

        tableE.appendTo(self.front).appendTo(self.back)

        x, y = self.ANCHOR_MIDDLE_LEFT 
        for day in [1, 5, 9, 13, 17]:
            self._tableOfPlanets(day)\
            .attr("transform", "translate(%d %d)" % (x, y))\
            .appendTo(self.front)
            x += 180

        x, y = self.ANCHOR_MIDDLE_LEFT 
        for day in [12, 16, 20, 24, self.monthLastDay]:
            self._tableOfPlanets(day)\
            .attr("transform", "translate(%d %d)" % (x, y))\
            .appendTo(self.back)
            x += 180


    def _addCheatsheet(self, page):
        # write formula onto background in white
        def addtext(x, y, r, text):
            g = SVGNode("g", transform="translate(%d %d) rotate(%d)" % (x,y,r))
            SVGNode("text", **{
                "x": "0", "y": "0",
                "class": "cheatsheet",
                "text-anchor": "left",
            }).append(text).appendTo(g)
            g.appendTo(page)

        addtext(100, 400, -60, "时差=视太阳时-平太阳时")
        addtext(120, 700, -70, "当地恒星时=格林尼治恒星时+经度")
        addtext(800, 200, 80, "经度差1度=时间差4分钟")


    def decoratePage(self, page, withFigure=True):
        SVGNode("rect", 
            x=0, y=0, width="100%", height="100%",
            fill="#DFDFDF"
        ).appendTo(page)

        SVGNode("text", **{
            "x": "50%",
            "y": "55%",
            "style": "font-size:300pt; font-family:sans; font-weight:bold",
            "fill": "white",
            "text-anchor": "middle",
        }).append( str(self.month) ).appendTo(page)

        SVGNode("text", **{
            "x": "50%",
            "y": "80%",
            "style": "font-size:150pt; font-family:sans; font-weight:bold",
            "fill": "white",
            "text-anchor": "middle",
        }).append( str(self.year) ).appendTo(page)

        self._addCheatsheet(page)

        logo = SVGNode("g", transform="translate(965 720)").append(
            SVGNode("text", **{
                "x": "0", "y": "0", "class": "title",
                "text-anchor": "left",
                "transform": "rotate(-90)"
            }).append( "%04d年%02d月" % (self.year, self.month) )
        ).append(
            SVGNode("text", **{
                "x": "0", "y": "20", "class": "title",
                "text-anchor": "left",
                "transform": "rotate(-90)"
            }).append( "天文普及月历" )
        ).append(
            SVGNode("text", **{
                "x": "0", "y": 40,
                "text-anchor": "left",
                "transform": "rotate(-90)",
            }).append("采用本初子午圈. 所有时间为UTC.")
        ).append(
            SVGNode("text", **{
                "x": "0", "y": 55,
                "text-anchor": "left",
                "transform": "rotate(-90)",
            }).append("作者: NeoAtlantis")
        )
        logo.appendTo(page)

        if withFigure:
            SVGNode("g",
                transform="translate(%d %d) scale(0.4 0.4)" % (
                    720, self.ANCHOR_BOTTOM_LEFT[1] - 15 
                )
            ).append(self.fig1).appendTo(page)


    def _tableOfPlanets(self, day):
        headers = ["%02d日" % day, "视赤经", "视赤纬", "视黄经"]
        items = [
            ("Mercury", "水星"),
            ("Venus", "金星"),
            ("Mars", "火星"),
            ("Jupiter", "木星"),
            ("Saturn", "土星"),
            ("Uranus", "天王星"),
            ("Neptune", "海王星"),
        ]
        data = []
        for planetName, planetTranslation in items:
            src = self.calculationResults["planets"][planetName][self.month][day]
            data.append([
                planetTranslation,
                convertHM(  Angle(hours=src["ra"]) ),
                convertDeg( Angle(degrees=src["dec"]) ),
                convertDeg( Angle(degrees=src["ecllon"]) ),
            ])

            
        table = svgTable(
            data, headers,
            fontsize=7, lineheight=1.7, headerwidth=1.9
        )
        return table 



    def _tableOfEvents(self, start, end):
        node = SVGNode("g")
        data = []
        x = 0
        y = 0
        count = 0
        MAXROWS = 10 
        COLWIDTH = 180
        for each in self.calculationResults["events"][self.month-1]:
            day = int(each[1])
            if not (start <= day <= end): continue
            count += 1
            n = SVGNode("text", **{
                "x": x,
                "y": y,
                "class": "common"
            }).append("%02d日 %s %s" % (
                day, each[2], each[3]
            ))
            node.append(n)
            y += 10
            if count % MAXROWS == 0:
                y = 0
                x += COLWIDTH
        return node, ceil(count / MAXROWS)


    def _tableOfMonth(self, start, end):
        data = []
        row1, row2 = self._rowSubcalendar(start, end)
        data.append([""] + row1)
        data.append([""] + row2)
        #data.append(["农历"] + list(self._rowLunarDate(start, end)))
        #data.append(["月相"] + list(self._rowMoonPhase(start, end)))
        
        data.append([" "])
        data.append(["UTC=0h..儒略日"] + list(self._rowJulian(start, end)))
        data.append(["........恒星时"] + list(self._rowSidereal(start, end)))
        for e in self._rowsSun(start,end): data.append(e)
        

        data.append([" "])
        for e in self._rowsRiseset(start, end): data.append(e)

        headers = [" " * 8]
        for i in range(start, end+1):
            dt = datetime.datetime(self.year, self.month, i)
            weekday = "一二三四五六日"[dt.weekday()]
            headers.append("%02d (%s)" % (i, weekday))

        table = svgTable(data, headers, fontsize=7, lineheight=1.7)
        return table 

    def _rowSubcalendar(self, start, end):
        solartermTable = {}
        solarterms = self.calculationResults["solarterms"]["solarterms-iso"]
        UTC = timezone("UTC") 
        for solartermName in solarterms:
            stDatetime = dateutil.parser\
                .parse(solarterms[solartermName]).astimezone(UTC)
            solartermTable[(stDatetime.month, stDatetime.day)] = (
                solartermName,
                stDatetime
            )
        moondata = self.calculationResults["moonphase"][self.month]

        row1, row2 = [], []
        # row1: by default lunar dates
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
            row1.append( ldMonth + ldDay )
        # row2: by default solarterm or moon phase
        display = lambda x, y: x + y.rjust(7-len(x), " ")
        for day in range(start, end+1):
            displaySolarterm = None
            if (self.month, day) in solartermTable:
                st = solartermTable[(self.month, day)]
                displaySolarterm = display(st[0], st[1].strftime("%H%M"))
            displayMoonPhase = None
            if moondata[day]["phase"]:
                displayMoonPhase = moondata[day]["phase"].replace(":", "")
                displayMoonPhase = displayMoonPhase.split(" ")
                displayMoonPhase.reverse()
                displayMoonPhase = display(*displayMoonPhase)
            if not displaySolarterm and not displayMoonPhase:
                row2.append(" ")
            elif bool(displaySolarterm) ^ bool(displayMoonPhase):
                row2.append(displaySolarterm or displayMoonPhase)
            else:
                row2.append(displayMoonPhase)
                row1[len(row2) - 1] = displaySolarterm
        return row1, row2


    def _rowJulian(self, start, end):
        for day in range(start, end+1):
            utc0 = timescale.ut1(self.year, self.month, day, 0, 0, 0)
            yield "%.1f" % utc0.tt

    def _rowSidereal(self, start, end):
        for day in range(start, end+1):
            utc0 = timescale.ut1(self.year, self.month, day, 0, 0, 0)
            yield convertHMS(Angle(hours=sidereal_time(utc0)))

    def _rowsSun(self, start, end):
        retRA, retDEC = ["....太阳 视赤经"], ["........视赤纬"]
        retEcllon, retEq = ["........视黄经"], ["........均时差"]

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

            retRA.append( convertHM(ra) )
            retDEC.append( convertDeg(dec) )
            retEcllon.append( convertDeg(ecllon) )
            retEq.append( convertSidereal(Angle(hours=equation_of_time)) )
        
        return [retEq, retRA, retDEC, retEcllon]

    def _rowsRiseset(self, start, end):
        moondata = self.calculationResults["moonphase"][self.month]
        sundata =  self.calculationResults["sunriseset"][-0.8333][self.month]
        ctwidata = self.calculationResults["sunriseset"][-6][self.month]
        atwidata = self.calculationResults["sunriseset"][-18][self.month]

        ret = []
        for lat in [20, 30, 35, 40, 45, 50]:
            retSun  = ["%02dN...日出日没" % lat]
            retCTwi = ["...民用晨昏蒙影"]
            retATwi = ["...天文晨昏蒙影"]
            retMoon = ["......月出月没"]
            merge = lambda x, y: \
                ((x or "-无-") + "/" + (y or "-无-")).replace(":", "")
            for day in range(start, end+1):
                retSun.append(merge(
                    sundata[day][lat]["rise"],
                    sundata[day][lat]["set"]
                ))
                retCTwi.append(merge(
                    ctwidata[day][lat]["rise"],
                    ctwidata[day][lat]["set"]
                ))
                retATwi.append(merge(
                    atwidata[day][lat]["rise"],
                    atwidata[day][lat]["set"]
                ))
                retMoon.append(merge(
                    moondata[day]["riseset"][lat]["rise"],
                    moondata[day]["riseset"][lat]["set"]
                ))
            ret.append(retSun)
            ret.append(retCTwi)
            ret.append(retATwi)
            ret.append(retMoon)
            ret.append([""])
        return ret
                



    def save(self, path="."):
        frontname = "%d-%d-front" % (self.year, self.month)
        backname  = "%d-%d-back" % (self.year, self.month)
        open(
            os.path.join(path, frontname + ".svg"), "w+"
        ).write(str(self.front))
        open(
            os.path.join(path, backname + ".svg"), "w+"
        ).write(str(self.back))

        run([
            "rsvg-convert",
            "-f", "pdf",
            "-o", frontname + ".pdf",
            frontname + ".svg"
        ])
        
        run([
            "rsvg-convert",
            "-f", "pdf",
            "-o", backname + ".pdf",
            backname + ".svg"
        ])
        os.unlink(frontname + ".svg")
        os.unlink(backname + ".svg")

        return (frontname + ".pdf", backname + ".pdf")






if __name__ == "__main__":
    YEAR = int(sys.argv[1])
    assert YEAR > 2000 and YEAR < 3000
    filenames = []
    for i in range(1, 13):
        print("Generating for %d month %d..." % (YEAR, i))
        x = MonthGenerator(YEAR, i)
        a, b = x.save()
        filenames.append(a)
        filenames.append(b)

    run(["pdfunite"] + filenames + ["%d.pdf" % YEAR])
    for f in filenames:
        os.unlink(f)
