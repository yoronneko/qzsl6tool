#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libecef.py: coordinate conversion between earth-centered earth-fixed (ECEF)
#             and latitude, longitude, elliptical height (LLH)
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2025 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import math
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libqzsl6tool

RAD2DEG = 180. / math.pi
WGS84EF = 1. / 298.257223563
WGS84ER = 6378137.
E2      = WGS84EF * (2. - WGS84EF)

def ecef2llh(px, py, pz):
    r2 = px * px + py * py
    v = WGS84ER
    z = pz
    zk = 0.
    while 1e-4 < math.fabs(z - zk):
        zk = z
        sinp = z / math.sqrt(r2 + z * z)
        v = WGS84ER / math.sqrt(1. - E2 * sinp * sinp)
        z = pz + v * E2 * sinp
    if 1e-12 < r2:
        lat = math.atan(z / math.sqrt(r2)) * RAD2DEG
        lon = math.atan2(py, px) * RAD2DEG
    else:
        lat = 90. if 0 < pz else -90.
        lon = 0.
    height = math.sqrt(r2 + z * z) - v
    return lat, lon, height

def llh2ecef(lat, lon, height):
    sinp = math.sin(lat / RAD2DEG)
    cosp = math.cos(lat / RAD2DEG)
    sinl = math.sin(lon / RAD2DEG)
    cosl = math.cos(lon / RAD2DEG)
    v = WGS84ER / math.sqrt(1. - E2 * sinp * sinp)
    x = (v + height) * cosp * cosl
    y = (v + height) * cosp * sinl
    z = (v * (1. - E2) + height) * sinp
    return x, y, z

if __name__ == '__main__':
    if 'ecef2llh.py' in sys.argv[0]:
        if len(sys.argv) < 3:
            print(f"ECEF to LLH conversion, QZS L6 Tool ver.{libqzsl6tool.VERSION}")
            print(f"Usage: {sys.argv[0]} x y z")
            sys.exit()
        x = float(sys.argv[1])
        y = float(sys.argv[2])
        z = float(sys.argv[3])
        lat, lon, height = ecef2llh(x, y, z)
        print(f"{lat:.7f} {lon:.7f} {height:.3f}")
    elif 'llh2ecef.py' in sys.argv[0]:
        if len(sys.argv) < 3:
            print(f"LLH to ECEF conversion, QZS L6 Tool ver.{libqzsl6tool.VERSION}")
            print(f"Usage: {sys.argv[0]} lat lon height")
            sys.exit()
        lat    = float(sys.argv[1])
        lon    = float(sys.argv[2])
        height = float(sys.argv[3])
        x, y, z = llh2ecef(lat, lon, height)
        print(f"{x:.3f} {y:.3f} {z:.3f}")

# EOF
