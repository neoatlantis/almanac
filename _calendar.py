#!/usr/bin/env python3

def listDates(year):
    assert type(year) == int
    if year % 100 == 0:
        leapYear = (year % 400 == 0)
    else:
        leapYear = (year % 4 == 0)
    days = [31, 29 if leapYear else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    for month in range(1, 13):
        for day in range(1, days[month-1]+1):
            yield (year, month, day)
