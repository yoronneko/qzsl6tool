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
import libcolor
import libqzsl6

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Quasi-zenith satellite (QZS) L6 message to RTCM message converter')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    parser.add_argument(
        '-r', '--rtcm', action='store_true',
        help='send RTCM messages to stdout (it also turns off display messages unless -m is specified).')
    parser.add_argument(
        '-s', '--statistics', action='store_true',
        help='show CSSR statistics in display messages.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=subtype detail, 2=subtype and bit image.')
    args = parser.parse_args()
    fp_rtcm = None
    fp_disp = sys.stdout
    t_level = 0
    force_ansi_color = False
    stat = False
    if 0 < args.trace:
        t_level = args.trace
    if args.rtcm:  # RTCM message output to stdout
        fp_rtcm = sys.stdout
        fp_disp = None
    if args.message:  # show QZS message to stderr
        fp_disp = sys.stderr
    if args.statistics:  # show CLAS statistics
        stat = True
    if args.color:
        force_ansi_color = True
    qzsl6 = libqzsl6.QzsL6(fp_rtcm, fp_disp, t_level, force_ansi_color, stat)
    while qzsl6.read_l6_msg():
        qzsl6.show_l6_msg()

# EOF
