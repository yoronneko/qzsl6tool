#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libecef.py: coordinate conversion between earth-centered earth-fixed (ECEF)
#             and latitude, longitude, elliptical height (LLH)
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2026 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import math
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libqzsl6tool

RAD2DEG: float = 180. / math.pi
WGS84EF: float = 1. / 298.257223563
WGS84ER: float = 6378137.
E2     : float = WGS84EF * (2. - WGS84EF)

def ecef2llh(px: float, py: float, pz: float) -> tuple[float, float, float]:
    r2: float = px * px + py * py
    v: float = WGS84ER
    z: float = pz
    zk: float = 0.
    while 1e-4 < math.fabs(z - zk):
        zk = z
        sinp: float = z / math.sqrt(r2 + z * z)
        v = WGS84ER / math.sqrt(1. - E2 * sinp * sinp)
        z = pz + v * E2 * sinp
    lat: float = 90. if 0 < pz else -90.
    lon: float = 0.
    if 1e-12 < r2:
        lat = math.atan(z / math.sqrt(r2)) * RAD2DEG
        lon = math.atan2(py, px) * RAD2DEG
    height: float = math.sqrt(r2 + z * z) - v
    return lat, lon, height

def llh2ecef(lat: float, lon: float, height: float) -> tuple[float, float, float]:
    sinp: float = math.sin(lat / RAD2DEG)
    cosp: float = math.cos(lat / RAD2DEG)
    sinl: float = math.sin(lon / RAD2DEG)
    cosl: float = math.cos(lon / RAD2DEG)
    v   : float = WGS84ER / math.sqrt(1. - E2 * sinp * sinp)
    x   : float = (v + height) * cosp * cosl
    y   : float = (v + height) * cosp * sinl
    z   : float = (v * (1. - E2) + height) * sinp
    return x, y, z

if __name__ == '__main__':
    if 'ecef2llh.py' in sys.argv[0]:
        if len(sys.argv) < 4:
            print(f"ECEF to LLH conversion, QZS L6 Tool ver.{libqzsl6tool.VERSION}")
            print(f"Usage: {sys.argv[0]} x y z")
            sys.exit()
        x: float = float(sys.argv[1])
        y: float = float(sys.argv[2])
        z: float = float(sys.argv[3])
        lat, lon, height = ecef2llh(x, y, z)
        print(f"{lat:.7f} {lon:.7f} {height:.3f}")
    elif 'llh2ecef.py' in sys.argv[0]:
        if len(sys.argv) < 4:
            print(f"LLH to ECEF conversion, QZS L6 Tool ver.{libqzsl6tool.VERSION}")
            print(f"Usage: {sys.argv[0]} lat lon height")
            sys.exit()
        lat   : float = float(sys.argv[1])
        lon   : float = float(sys.argv[2])
        height: float = float(sys.argv[3])
        x, y, z = llh2ecef(lat, lon, height)
        print(f"{x:.3f} {y:.3f} {z:.3f}")

# EOF
