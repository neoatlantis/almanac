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

class MonthShifter:

    def __init__(self, year, month):
        self.year = year
        self.month = month

    def __add__(self, value):
        year = self.year
        month = self.month + value
        while not 1 <= month <= 12:
            if month > 12:
                month -= 12
                year += 1
            if month < 1:
                month += 12
                year -= 1
        return (year, month)

    def __sub__(self, value):
        return self.__add__(-value)
