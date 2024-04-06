#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# bdsb2read.py: BeiDou B2b message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2024 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libbdsb2
import libtrace

LEN_BCNAV3 = 125  # BDS CNAV3 page size is 1000 sym (125 byte)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='BeiDou B2b message read')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    parser.add_argument(
        '-p', '--prn', type=int, default=0,
        help='show B2b message for specified PRN only.')
    parser.add_argument(
        '-s', '--statistics', action='store_true',
        help='show B2b statistics in display messages.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=detail, 2=bit image.')
    args = parser.parse_args()
    fp_disp = sys.stdout
    if args.message:  # show B2b message to stderr
        fp_disp = sys.stderr
    if args.trace < 0:
        libtrace.err(f'trace level should be positive ({args.trace}).')
        sys.exit(1)
    if args.prn < 0:
        libtrace.err(f'PRN should be positive ({args.trace}).')
        sys.exit(1)
    trace = libtrace.Trace(fp_disp, args.trace, args.color)
    bdsb2 = libbdsb2.BdsB2(trace, args.statistics)
    try:
        raw = sys.stdin.buffer.read(LEN_BCNAV3)
        while raw:
            bdsb2.decode(raw, args.prn)
            raw = sys.stdin.buffer.read(LEN_BCNAV3)
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit()
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
