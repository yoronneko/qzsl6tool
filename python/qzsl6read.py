#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# qzsl6read.py: quasi-zenith satellite (QZS) L6 message reader
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
    if args.trace < 0:
        print(libcolor.Color().fg('red') + 'trace level should be positive ({args.trace}).' + libcolor.Color().fg(), file=sys.stderr)
        sys.exit(1)
    if args.rtcm:  # RTCM message output to stdout
        fp_rtcm = sys.stdout
        fp_disp = None
    if args.message:  # show QZS message to stderr
        fp_disp = sys.stderr
    if 'qzsl62rtcm.py' in sys.argv[0]:
        print(libcolor.Color().fg('yellow') + 'Notice: please use "qzsl6read.py", instead of "qzsl62rtcm.py" that will be removed.' + libcolor.Color().fg(), file=sys.stderr)
    qzsl6 = libqzsl6.QzsL6(fp_rtcm, fp_disp, args.trace, args.color, args.statistics)
    try:
        while qzsl6.read_l6_msg():
            qzsl6.show_l6_msg()
    except (BrokenPipeError, IOError):
        sys.exit()
    except KeyboardInterrupt:
        print(libcolor.Color().fg('yellow') + "User break - terminated" + \
            libcolor.Color().fg(), file=sys.stderr)
        sys.exit()

# EOF

