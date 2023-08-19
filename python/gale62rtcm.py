#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# gale62rtcm.py: Pocket SDR log to RTCM message
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libgale6

try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    QZS L6 Tool needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)


LEN_HASPAGE = 56  # HAS page size is 448 bit, or 56 byte

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Galileo E6B message to RTCM message')
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
        help='show HAS statistics in display messages.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=detail, 2=bit image.')
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
    if args.message:  # show HAS message to stderr
        fp_disp = sys.stderr
    if args.statistics:  # show HAS statistics
        stat = True
    if args.color:
        force_ansi_color = True
    gale6 = libgale6.GalE6(fp_rtcm, fp_disp, t_level, force_ansi_color, stat)
    e6msg = sys.stdin.buffer.read(LEN_HASPAGE)
    while e6msg:
        has_msg=bitstring.BitArray(e6msg)
        gale6.decode_has_message(has_msg)
        e6msg = sys.stdin.buffer.read(LEN_HASPAGE)

# EOF

