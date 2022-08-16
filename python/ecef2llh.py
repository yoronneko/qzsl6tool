#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ecef2llh.py: coordinate conversion from earth-centered earth-fixed (ECEF) to
#              latitude, longitude, and elliptical height
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import math
import sys


def ecef2llh(px, py, pz):
    wgs84er = 6378137.
    wgs84ef = 1. / 298.257223563
    rad2deg = 180. / math.pi
    e2 = wgs84ef * (2. - wgs84ef)
    r2 = px * px + py * py
    v = wgs84er
    z = pz
    zk = 0.
    while 1e-4 < math.fabs(z - zk):
        zk = z
        sinp = z / math.sqrt(r2 + z * z)
        v = wgs84er / math.sqrt(1. - e2 * sinp * sinp)
        z = pz + v * e2 * sinp
    if 1e-12 < r2:
        lat = math.atan(z / math.sqrt(r2)) * rad2deg
        lon = math.atan2(py, px) * rad2deg
    else:
        lat = 90. if 0 < pz else -90.
        lon = 0.
    height = math.sqrt(r2 + z * z) - v
    return lat, lon, height


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("ECEF to Latitude Longitude and Height")
        print(f"Usage: {sys.argv[0]} x y z")
        sys.exit()
    x = float(sys.argv[1])
    y = float(sys.argv[2])
    z = float(sys.argv[3])
    lat, lon, height = ecef2llh(x, y, z)
    print(f"{lat:.7f} {lon:.7f} {height:.3f}")

# EOF
