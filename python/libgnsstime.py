#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libgnsstime.py: GNSS time and universal coordinated time (UTC) conversion
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2025 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import datetime
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libqzsl6tool

FORMAT_DT = "%Y-%m-%d %H:%M:%S"

def epoch_info(gsys):
    ''' returns epoch leapsec, and rollover from GNSS's epoch
        gsys (GNSS system) is either GPS, GAL, or BDS'''
    if gsys == 'GPS':
        epoch    = datetime.datetime.strptime("1980-01-06 00:00:00", FORMAT_DT)
        leapsec  = 18
        rollover = 0
    elif gsys == 'GAL':
        epoch    = datetime.datetime.strptime("1999-08-22 00:00:00", FORMAT_DT)
        leapsec  = 13
        rollover = 0
    elif gsys == 'BDS':
        epoch    = datetime.datetime.strptime("2006-01-01 00:00:00", FORMAT_DT)
        leapsec  = 4
        rollover = 0
    else:
        raise Exception(f'unknown satellite system: {gsys}')
    return epoch, leapsec, rollover

def gps2utc(weekno, tow, gsys='GPS'):
    epoch, leapsec, rollover = epoch_info(gsys)
    elapsed = datetime.timedelta(
        weeks   = weekno + rollover * 1024,
        seconds = tow - leapsec)
    return datetime.datetime.strftime(epoch + elapsed, FORMAT_DT)

def utc2gps(current, gsys='GPS'):
    epoch, leapsec, rollover = epoch_info(gsys)
    elapsed = current - epoch + datetime.timedelta(seconds=leapsec)
    weekno  = elapsed.days // 7 - rollover * 1024
    tow     = elapsed.seconds + (elapsed.days - weekno * 7) * 24 * 60 * 60
    return f'{weekno} {tow}'


if __name__ == '__main__':
    if 'utc2gps.py' in sys.argv[0]:
        if len(sys.argv) < 3:
            print(f"UTC to GNSS time conversion, QZS L6 Tool ver.{libqzsl6tool.VERSION}")
            print(f"Usage: {sys.argv[0]} YYYY-MM-DD hh:mm:ss")
            print("Current GNSS time (week number, time of week):")
            current = datetime.datetime.now()
        else:
            date    = sys.argv[1]
            time    = sys.argv[2]
            current = datetime.datetime.strptime(f'{date} {time}', FORMAT_DT)
        print(f'GPS {utc2gps(current)}')
        print(f'GST {utc2gps(current, "GAL")}')
        print(f'BDT {utc2gps(current, "BDS")}')
    elif 'gps2utc.py' in sys.argv[0]:
        if len(sys.argv) < 3:
            print(f"GNSS time to UTC conversion, QZS L6 Tool ver.{libqzsl6tool.VERSION}")
            print(f"Usage: {sys.argv[0]} week_no time_of_week")
            sys.exit()
        weekno = int(sys.argv[1])
        tow    = int(sys.argv[2])
        print(f'GPS {gps2utc(weekno, tow)}')
        print(f'GST {gps2utc(weekno, tow, "GAL")}')
        print(f'BDT {gps2utc(weekno, tow, "BDS")}')

# EOF
