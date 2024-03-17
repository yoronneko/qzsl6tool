#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# gale6read.py: Galileo E6B message read
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
import libtrace

LEN_CNAV_PAGE = 62  # C/NAV page size is 492 bit (61.5 byte)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Galileo E6B message read')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    parser.add_argument(
        '-s', '--statistics', action='store_true',
        help='show HAS statistics in display messages.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=detail, 2=bit image.')
    args = parser.parse_args()
    fp_disp = sys.stdout
    if args.trace < 0:
        libtrace.err(f'trace level should be positive ({args.trace}).')
        sys.exit(1)
    if args.message:  # show HAS message to stderr
        fp_disp = sys.stderr
    trace = libtrace.Trace(fp_disp, args.trace, args.color)
    gale6 = libgale6.GalE6(trace, args.statistics)
    try:
        while True:
            raw = sys.stdin.buffer.read(LEN_CNAV_PAGE + 1)
            if not raw:
                break
            satid = int.from_bytes(raw[0:1], 'little')
            cnav  = raw[1:]
            if not gale6.ready_decoding_has(satid, cnav):
                continue
            gale6.decode_has_message()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
