#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# gps2utc.py: GPS time to universal coordinated time (UTC) conversion
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import sys
import datetime


def gps2utc(gpsweek, gpssec):
    leapsec = 18
    rollover = 0
    datetimefmt = "%Y-%m-%d %H:%M:%S"
    epoch = datetime.datetime.strptime("1980-01-06 00:00:00", datetimefmt)
    elapsed = datetime.timedelta(
        weeks=gpsweek + rollover * 1024,
        seconds=gpssec - leapsec)
    return datetime.datetime.strftime(epoch + elapsed, datetimefmt)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("GPS time to UTC")
        print(f"Usage: {sys.argv[0]} GPSweek GPSsecond")
        sys.exit()
    gpsweek = int(sys.argv[1])
    gpssec = int(sys.argv[2])
    print(gps2utc(gpsweek, gpssec))

# EOF
