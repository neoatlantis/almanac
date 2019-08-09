#!/usr/bin/env python3

from skyfield.timelib import Time

def roundTimeToMinute(t):
    return t # fix me
    assert isinstance(t, Time)
    return Time(tt=round(t.tt * 1440) / 1440.0)
