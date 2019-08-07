#!/usr/bin/env python3

import sys
import datetime
import os
import json

from lunardate import LunarDate

from _calendar import listDates
from save_calculations import CalculationResults


YEAR = int(sys.argv[1])
assert YEAR > 2000 and YEAR < 3000

solartermsPath = os.path.join("calculations", str(YEAR), "solarterms.json")
if not os.path.exists(solartermsPath):
    print("Run `python3 table_of_solarterms.py %d` first." % YEAR)
    exit(1)

solarterms = json.loads(open(solartermsPath, "r").read())



def writeTableHead(month):
    return """
\\paragraph*{%d月}
\\begin{tabular}{|ccccccc|}
\\hline
一 & 二 & 三 & 四 & 五 & 六 & 日 \\tabularnewline
\\hline""" % month

def writeTableFoot():
    return """\\hline \\end{tabular}"""



lines = []
linebuffer = [""] * 7

for year, month, day in listDates(YEAR):
    date = datetime.date(year, month, day)
    _, __, weekday = date.isocalendar()

    if day == 1:
        lines.append(linebuffer)
        if month != 1:
            lines.append(writeTableFoot())
        lines.append(writeTableHead(month))
        linebuffer = [""] * 7

    ld = LunarDate.fromSolarDate(year, month, day)
    subdisplay = None # 农历或节气显示

    # 节气优先显示
    for solarterm in solarterms:
        if solarterms[solarterm] == "%02d-%02d" % (month, day):
            subdisplay = solarterm
            break

    if subdisplay is None: # 非节气，显示农历

        if ld.day == 1:
            subdisplay = "正二三四五六七八九十冬腊"[ld.month-1]
            if ld.isLeapMonth: subdisplay = "闰" + lundardisplay
            subdisplay += "月"
        else:
            if ld.day <= 10:
                subdisplay = "初" + "一二三四五六七八九十"[ld.day-1]
            elif ld.day < 20:
                subdisplay = "十" + "一二三四五六七八九"[ld.day-11]
            elif ld.day == 20:
                subdisplay = "二十"
            elif ld.day < 30:
                subdisplay = "廿" + "一二三四五六七八九"[ld.day-21]
            elif ld.day == 30:
                subdisplay = "三十"

    linebuffer[weekday-1] = """
        \\begin{tabular}{@{}c@{}} %s \\\\ %s\\end{tabular}""" % (
            day,
            subdisplay
        )


    if weekday == 7:
        lines.append(linebuffer)
        linebuffer = [""] * 7

lines.append(linebuffer)
lines.append(writeTableFoot())



with CalculationResults("calendar", YEAR) as writer:
    
    for each in lines:
        if type(each) == str:
            writer.writeline(each)
        else:
            if not "".join(each): continue
            writer.writeline(" & ".join(each) + " \\tabularnewline")
