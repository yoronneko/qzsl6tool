#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# qzsl62rtcm.py: quasi-zenith satellite (QZS) L6 message to RTCM message converter
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import argparse
import sys
import libqzsl6tool

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Quasi-zenith satellite (QZS) L6 message to RTCM converter')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='trace level for debug: 1=subtype detail, 2=subtype and bit image')
    parser.add_argument(
        '-r', '--rtcm', action='store_true',
        help='RTCM message output, supress QZS messages (unless -m is specified)')
    parser.add_argument(
        '-s', '--statistics', action='store_true',
        help='show CSSR statistics')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show QZS messages and statistics to stderr')
    args = parser.parse_args()
    qzsl6 = libqzsl6tool.QzsL6()
    if 0 < args.trace:
        qzsl6.t_level = args.trace
    if args.rtcm:  # RTCM message output to stdout
        qzsl6.fp_rtcm = sys.stdout
        qzsl6.fp_msg = None
        qzsl6.fp_trace = sys.stderr
    if args.message:  # show QZS message to stderr
        qzsl6.fp_msg = sys.stderr
        qzsl6.fp_trace = sys.stderr
    if args.statistics:  # show CLAS statistics
        qzsl6.stat = True
    while qzsl6.receive_l6_msg():
        qzsl6.show_l6_msg()

# EOF
