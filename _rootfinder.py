#!/usr/bin/env python3

import numpy as np

def critical_point_finder(
    start_time, end_time, f,
    num=12,
    epsilon=1e-4 # days
):
    """Given f(t) as a function of time, find out it's critical points
        df(t)/dt = 0

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

#    print("Discretize %d points." % len(ts_n))
#    for i in range(0, len(ts_n)):
#        print(ts_n[i].utc_iso().replace("T", " ").replace("Z", ""), "\t", y_n[i])
#    exit()

    founds = []
    for i in range(0, len(ts_n)-2):
        jd_i0, y_i0 = ts_n[i].tt, y_n[i]
        jd_i1, y_i1 = ts_n[i+1].tt, y_n[i+1]
        jd_i2, y_i2 = ts_n[i+2].tt, y_n[i+2]
        dydt1 = (y_i1 - y_i0) / (jd_i1 - jd_i0)
        dydt2 = (y_i2 - y_i1) / (jd_i2 - jd_i1)
        #average_dydt = (dydt1 + dydt2) / 2
        
        """if abs(average_dydt) < epsilon:
            founds.append((
                (ts_n[i], ts_n[i+1], ts_n[i+2]),
                (y_i0, y_i1, y_i2)
            ))
            continue"""

        #if dydt1 * dydt2 > 0: continue
        if (y_i1 - y_i0) * (y_i2 - y_i1) > 0: continue

        #print("Suspect:", ts_n[i].utc_iso(), dydt1, "\t", ts_n[i+2].utc_iso(), dydt2)

        # find between ts_i0 and ts_i2
        jd_a, jd_x, jd_b = jd_i0, jd_i1, jd_i2 
        y_a, y_x, y_b = y_i0, y_i1, y_i2
        dydt_a = dydt1
        dydt_b = dydt2
        
        while abs(jd_b - jd_a) > epsilon: #abs( (dydt_a + dydt_b) / 2 ) > epsilon:
            jd_x1 = (jd_a + jd_x) / 2
            jd_x2 = (jd_x + jd_b) / 2

            ts_x1 = ts.tt_jd(jd_x1)
            ts_x2 = ts.tt_jd(jd_x2)
            y_x1 = f(ts_x1)
            y_x2 = f(ts_x2)

            # a --- x1 --- x --- x2 --- b

            if (y_x1 - y_a) * (y_x - y_x1) < 0:
                jd_b, y_b = jd_x, y_x
                jd_x, y_x = jd_x1, y_x1
            elif (y_x - y_x1) * (y_x2 - y_x) < 0:
                jd_a, y_a = jd_x1, y_x1
                jd_b, y_b = jd_x2, y_x2
            else:
                jd_a, y_a = jd_x, y_x
                jd_x, y_x = jd_x2, y_x2

            """print(
                "\t",
                ts.tt_jd(jd_a).utc_iso(), "\t",
                ts.tt_jd(jd_x).utc_iso(), "\t",
                ts.tt_jd(jd_b).utc_iso(), "\t",
                y_a, y_x, y_b
            )"""

            dydt_a = (y_x - y_a) / (jd_x - jd_a)
            dydt_b = (y_b - y_x) / (jd_b - jd_x)

        if abs(dydt_a + dydt_b) / 2 < epsilon:
            founds.append((
                (ts.tt_jd(jd_a), ts.tt_jd(jd_x), ts.tt_jd(jd_b)),
                (y_a, y_x, y_b)
            ))
        #else:
            #print(dydt_a, dydt_b)

    return founds






def root_finder(
    start_time, end_time, f,
    num=12,
    epsilon=1e-6,      # in julian days
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

        if abs(y_i0) < epsilon * yrange: # almost zero, treat as zero
            founds.append((ts_i0, y_n[ts_i0]))
            continue
        if y_i0 * y_i1 > 0: continue # same sign, continue

        # find between ts_i0 and ts_i1
        jd_a, jd_b = ts_i0.tt, ts_i1.tt
        y_a, y_b = y_i0, y_i1
        
        while jd_b - jd_a > epsilon:
            jd_x = (jd_a + jd_b) / 2
            ts_x = ts.tt_jd(jd_x)
            y_x = f(ts_x)

            if y_x * y_a < 0:
                y_b = y_x
                jd_b = jd_x
            else:
                y_a = y_x
                jd_a = jd_x

        if abs(y_a - y_b) < epsilon * yrange:
            founds.append((ts_x, y_x))

    return founds 

            


    


if __name__ == "__main__":
    from _constants import *

    def f(t):   # conjunction sun - mercury
        t._nutation_angles = iau2000b(t.tt)
        sunApparent = Earth.at(t).observe(Sun).apparent()
        starApparent = Earth.at(t).observe(Mercury).apparent()
        sunL = sunApparent.ecliptic_latlon('date')[1].degrees
        starL = starApparent.ecliptic_latlon('date')[1].degrees
        return np.sin((sunL - starL) / 180.0 * np.pi * 2)
    f.rough_period = 30

    roots = root_finder(
        start_time=timescale.utc(2019, 1, 1),
        end_time=timescale.utc(2019, 12, 31, 23, 59, 59),
        f=f
    )

    for t, y in roots:
        print(t.utc_iso(), "\t", y)

    exit()

    from _spheric_dist import spherical_distance
    planet =  Uranus 

    

    def g(t):
        t._nutation_angles = iau2000b(t.tt)
        mLat, mLng = Earth.at(t).observe(planet).radec()[:2]
        sLat, sLng = Earth.at(t).observe(Sun).radec()[:2]
        return spherical_distance(
            (mLat._degrees, mLng.degrees),
            (sLat._degrees, sLng.degrees)
        )

    def g(t):
        t._nutation_angles = iau2000b(t.tt)
        ra1 = Earth.at(t).observe(planet).radec()[0].hours
        ra2 = 24 - ra1
        return np.amin(np.array([ra1, ra2]), axis=0)

    g.rough_period = 20 
    critical_points = critical_point_finder(
        start_time=timescale.utc(2019, 1, 1),
        end_time=timescale.utc(2019, 12, 31, 23, 59, 59),
        f=g
    )
    for t, y in critical_points:
        print(t[1].utc_iso(), "\t", y[1]-y[0], "\t", y[1], "\t", y[2]-y[1])
