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
import librtcm
import libtrace

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
        libtrace.err(f'trace level should be positive ({args.trace}).')
        sys.exit(1)
    trace = libtrace.Trace(fp_disp, args.trace, args.color)
    rtcm = librtcm.Rtcm(trace)
    try:
        while rtcm.read():
            rtcm.decode()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
