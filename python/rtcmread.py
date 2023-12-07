#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# rtcmread.py: RTCM message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libcolor
import librtcm

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='RTCM message read')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=subtype detail, 2=subtype and bit image.')
    args = parser.parse_args()
    fp_disp = sys.stdout       # message display file pointer
    if args.trace < 0:
        print(libcolor.Color().fg('red') + 'trace level should be positive ({args.trace}).' + libcolor.Color().fg(), file=sys.stderr)
        sys.exit(1)
    if 'showrtcm.py' in sys.argv[0]:
        print(libcolor.Color().fg('yellow') + 'Notice: please use "rtcmread.py", instead of "showrtcm.py" that will be removed.' + libcolor.Color().fg(), file=sys.stderr)
    rtcm = librtcm.Rtcm(fp_disp, args.trace, args.color)
    try:
        while rtcm.read():
            rtcm.decode_rtcm_msg()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        print(libcolor.Color().fg('yellow') + "User break - terminated" + \
            libcolor.Color().fg(), file=sys.stderr)
        sys.exit()

# EOF

