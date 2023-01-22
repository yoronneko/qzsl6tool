#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# showrtcm.py: RTCM message dump
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import argparse
import sys
import libcolor
import librtcm

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Quasi-zenith satellite (QZS) L6 message to RTCM message converter')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=subtype detail, 2=subtype and bit image.')
    args = parser.parse_args()
    fp_disp = sys.stdout       # message display file pointer
    force_ansi_color = False   # force ANSI escape sequence
    trace_level = 0            # trace level
    if args.color:
        force_ansi_color = True
    if 0 < args.trace:
        trace_level = args.trace
    rtcm = librtcm.Rtcm(fp_disp, trace_level, force_ansi_color)
    while rtcm.read_rtcm_msg():
        rtcm.decode_rtcm_msg()

# EOF
