#!/usr/bin/env python3

import numpy as np

def spherical_distance(latlng1, latlng2):
    """Input and output are all in degrees."""

    lat1, lng1 = latlng1
    lat2, lng2 = latlng2
    degrees_to_radians = np.pi/180.0

    phi_1 = (90 - lat1) * degrees_to_radians
    phi_2 = (90 - lat2) * degrees_to_radians
    theta_diff = (lng1 - lng2) * degrees_to_radians

    return np.arccos(
        (np.sin(phi_1) * np.sin(phi_2) * np.cos(theta_diff) + 
           np.cos(phi_1) * np.cos(phi_2))
    ) / degrees_to_radians
