#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# utc2gps.py: universal coordinated time (UTC) to GPS time conversion
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import sys
import datetime


def utc2gps(date, time):
    leapsec = 18
    rollover = 0
    datetimefmt = "%Y-%m-%d %H:%M:%S"
    utc = date + " " + time
    epoch = datetime.datetime.strptime("1980-01-06 00:00:00", datetimefmt)
    current = datetime.datetime.strptime(utc, datetimefmt)
    leap = datetime.timedelta(seconds=leapsec)
    elapsed = current - epoch + leap
    week = int(elapsed.days / 7)
    sec = elapsed.seconds + (elapsed.days - week * 7) * 24 * 60 * 60
    week = week - rollover * 1024
    return f'{week} {sec}'


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("UTC to GPS time")
        print(f"Usage: {sys.argv[0]} YYYY-MM-DD hh:mm:ss")
        sys.exit()
    date = sys.argv[1]
    time = sys.argv[2]
    print(utc2gps(date, time))

# EOF
