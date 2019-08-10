#!/usr/bin/env python3

import numpy as np


def rootfinder(
    start_time, end_time, f,
    num=12,
    epsilon1=1e-6,      # in julian days
    epsilon2=1e-4       # relative to f range
):
    """Given f(t) as a function of time, find out it's continuous zero-points.

    A series of time from [start_time, end_time] is generated and f(times) are
    calculated. From this discrete series of value we find out
        f(time_i) and f(time_i+1)
    with different signs. This indicates a possible zero point between
        time_i and time_i+1

    Having located the boundaries, a bisection method is applied to reduce the
    above section to [time_a, time_b] where
        time_b-time_a < epsilon1
    indicates a sufficiently small time interval. This however doesn't
    necessarily results a zero point, since we require continuation, there
    must be also
        abs( f(time_b) - f(time_a) ) < epsilon2

    In calculating e.g. moon conjunctions with given star, we desire finding
        RA(moon) == RA(star)
    However, since right ascension is measured with time angle 0-24h, it's
    possible the moon travels over equinox within a month, resulting a
    suddenly change in RA from 23h59m to 0h00m. This negative jump results
    no possibilty for a conjunction solution due to its mathematically
    non-continuation nature and shall be filtered out:

        RA
        /|\                RA of the moon
     24  |    /|    /|    /
         |   / |   / |   /                      RA of a star
         |--x--o--x--o--x--------------------------------------------
         | /   | /   | /
      0  |/    |/    |/
         +--------------------------------------------------------------> t

         x: a real conjunction result
         o: a fake conjunction due to non-continuation

    """


    jd1 = end_time.tt
    jd0 = start_time.tt
    ts = start_time.ts
    assert jd0 < jd1

    periods = (jd1 - jd0) / f.rough_period
    if periods < 1.0:
        periods = 1.0

    jd = np.linspace(jd0, jd1, periods * num // 1.0)

    ts_n = ts.tt_jd(jd)
    y_n = f(ts_n)

    yrange = np.amax(y_n) - np.amin(y_n)

    founds = []

    for i in range(0, len(ts_n)-1):
        ts_i0, y_i0 = ts_n[i], y_n[i]
        ts_i1, y_i1 = ts_n[i+1], y_n[i+1]

        if abs(y_i0) < epsilon2 * yrange: # almost zero, treat as zero
            founds.append((ts_i0, y_n[ts_i0]))
            continue
        if y_i0 * y_i1 > 0: continue # same sign, continue

        # find between ts_i0 and ts_i1
        jd_a, jd_b = ts_i0.tt, ts_i1.tt
        y_a, y_b = y_i0, y_i1
        
        while jd_b - jd_a > epsilon1:
            jd_x = (jd_a + jd_b) / 2
            ts_x = ts.tt_jd(jd_x)
            y_x = f(ts_x)

            if y_x * y_a < 0:
                y_b = y_x
                jd_b = jd_x
            else:
                y_a = y_x
                jd_a = jd_x

        if abs(y_a - y_b) < epsilon2 * yrange:
            founds.append((ts_x, y_x))

    return founds 

            


    


if __name__ == "__main__":
    from _constants import *


    def f(t):
        t._nutation_angles = iau2000b(t.tt)
        moonApparent = Earth.at(t).observe(Moon).apparent()
        starApparent = Earth.at(t).observe(Regulus).apparent()
        moonRA = moonApparent.radec('date')[0].hours
        starRA = starApparent.radec('date')[0].hours
        return moonRA - starRA
    f.rough_period = 29

    roots = rootfinder(
        start_time=timescale.utc(2019, 1, 1),
        end_time=timescale.utc(2019, 12, 31, 23, 59, 59),
        f=f
    )

    for t, y in roots:
        print(t.utc_iso(), "\t", y)


