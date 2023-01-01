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
import librtcm

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Quasi-zenith satellite (QZS) L6 message to RTCM converter')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='allow ANSI escape sequences for text color decoration')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='trace level for debug: 1=subtype detail, 2=subtype and bit image')
    args = parser.parse_args()
    rtcm = librtcm.Rtcm()
    if args.color:
        rtcm.ansi_color = True
    if 0 < args.trace:
        rtcm.t_level = args.trace
    while rtcm.read_rtcm_msg():
        rtcm.decode_rtcm_msg()

# EOF
