#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# llh2ecef.py: coordinate conversion from latitude, longitude, and elliptical
#              height to earth-centered earth-fixed (ECEF)
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import math
import sys

def llh2ecef(lat, lon, height):
    wgs84er = 6378137.
    wgs84ef = 1. / 298.257223563
    rad2deg = 180. / math.pi
    sinp = math.sin(lat / rad2deg)
    cosp = math.cos(lat / rad2deg)
    sinl = math.sin(lon / rad2deg)
    cosl = math.cos(lon / rad2deg)
    e2 = wgs84ef * (2. - wgs84ef)
    v = wgs84er / math.sqrt(1. - e2 * sinp * sinp)
    x = (v + height) * cosp * cosl
    y = (v + height) * cosp * sinl
    z = (v * (1. - e2) + height) * sinp
    return x, y, z


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Latitude Longitude and Height to ECEF")
        print(f"Usage: {sys.argv[0]} lat lon height")
        sys.exit()
    lat = float(sys.argv[1])
    lon = float(sys.argv[2])
    height = float(sys.argv[3])
    x, y, z = llh2ecef(lat, lon, height)
    print(f"{x:.3f} {y:.3f} {z:.3f}")

# EOF
