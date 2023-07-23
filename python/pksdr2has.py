#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pksdr2has.py: Pocket SDR log to Galileo HAS message
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] Europe Union Agency for the Space Programme,
#     Galileo High Accuracy Service Signal-in-Space Interface Control
#     Document (HAS SIS ICD), Issue 1.0 May 2022.

import argparse
import sys
import libgale6


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Pocket SDR E6B log to HAS message converter')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-e', '--e6b', action='store_true',
        help='send E6B messages to stdout (it also turns off display message.')
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
    fp_rtcm = None
    fp_disp = sys.stdout
    fp_e6b = None
    t_level = 0
    force_ansi_color = False
    stat = False
    if 0 < args.trace:
        t_level = args.trace
    if args.e6b:
        fp_disp = None
        fp_e6b = sys.stdout
    if args.message:  # show HAS message to stderr
        fp_disp = sys.stderr
    if args.statistics:  # show HAS statistics
        stat = True
    if args.color:
        force_ansi_color = True
    gale6 = libgale6.GalE6(fp_rtcm, fp_disp, t_level, force_ansi_color, stat)
    while gale6.read_from_pocketsdr():
        if not gale6.ready_decoding_has():  # we continue reading HAS pages
            continue
        has_msg = gale6.obtain_has_message()
        gale6.decode_has_message(has_msg)
        if fp_e6b:
            fp_e6b.buffer.write(has_msg.tobytes())
            fp_e6b.flush()

# EOF

