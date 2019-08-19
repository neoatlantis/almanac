#!/usr/bin/env python3


from skyfield import api, almanac
from skyfield.api import load, Topos, Star
from skyfield.units import Angle
from skyfield.earthlib import sidereal_time
from skyfield.nutationlib import iau2000b

from pytz import timezone


ephemeris421 = load("de421.bsp")
timescale = load.timescale()
BJT = timezone("Asia/Shanghai")
UTC = timezone("UTC")


Regulus         = Star(ra_hours=(10, 8, 21.98), dec_degrees=(11, 58, 3.0))      # 轩辕十四
Aldebaran       = Star(ra_hours=(4, 35, 55.33), dec_degrees=(16, 30, 29.6))     # 毕宿五
Spica           = Star(ra_hours=(13, 25, 11.53), dec_degrees=(-11, 9, 41.5))    # 角宿一

Sun     = ephemeris421["Sun"]
Mercury = ephemeris421["Mercury"]
Venus   = ephemeris421["Venus"]
Earth   = ephemeris421["Earth"]
Moon    = ephemeris421["Moon"]
Mars    = ephemeris421["Mars"]
Jupiter = ephemeris421["JUPITER BARYCENTER"]
Saturn  = ephemeris421["SATURN BARYCENTER"]
Uranus  = ephemeris421["Uranus Barycenter"]
Neptune = ephemeris421["Neptune Barycenter"]
Pluto   = ephemeris421["Pluto Barycenter"]


MOON_RADIUS = 1737.1 # km
EARTH_RADIUS = 6378  # km
