#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# gale6read.py: Galileo E6B message reader
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

LEN_CNAV_PAGE = 62  # C/NAV page size is 492 bit (61.5 byte)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Galileo E6B message dump')
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
    if args.trace < 0:
        print(libcolor.Color().fg('red') + 'trace level should be positive ({args.trace}).' + libcolor.Color().fg(), file=sys.stderr)
        sys.exit(1)
    if args.rtcm:  # RTCM message output to stdout
        fp_rtcm = sys.stdout
        fp_disp = None
    if args.message:  # show HAS message to stderr
        fp_disp = sys.stderr
    gale6 = libgale6.GalE6(fp_rtcm, fp_disp, args.trace, args.color, args.statistics)
    raw = sys.stdin.buffer.read(LEN_CNAV_PAGE + 1)
    while raw:
        satid = int.from_bytes(raw[0:1], 'little')
        cnav = raw[1:]
        if not gale6.ready_decoding_has(satid, cnav):
            raw = sys.stdin.buffer.read(LEN_CNAV_PAGE + 1)
            continue
        gale6.decode_has_message()

# EOF

