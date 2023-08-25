#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# nov2has.py: NovAtel binary to Galileo HAS message
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libgale6
import libcolor
import novdump


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='NovAtel receiver binary to HAS message converter')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-e', '--cnav', action='store_true',
        help='send E6B C/NAV messages to stdout, and also turns off display message.')
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
    fp_cnav = None
    t_level = 0
    force_ansi_color = False
    stat = False
    if 0 < args.trace:
        t_level = args.trace
    if args.cnav:
        fp_disp = None
        fp_cnav = sys.stdout
    if args.message:  # show HAS message to stderr
        fp_disp = sys.stderr
    if args.statistics:  # show HAS statistics
        stat = True
    if args.color:
        force_ansi_color = True
    gale6 = libgale6.GalE6(fp_rtcm, fp_disp, t_level, force_ansi_color, stat)
    nov = novdump.NovReceiver(fp_disp, force_ansi_color)
    while nov.read():
        msg_name = nov.NOV_MSG_NAME.get(nov.msg_id, f"MT{nov.msg_id}")
        if msg_name != 'GALCNAVRAWPAGE':
            continue
        nov.galcnavrawpage()
        if fp_cnav:
            fp_cnav.buffer.write(nov.satid.to_bytes(1, byteorder='little'))
            fp_cnav.buffer.write(nov.cnav)
            fp_cnav.buffer.write((0).to_bytes(1, byteorder='little')) # dummy for tail
            fp_cnav.flush()
        if not gale6.ready_decoding_has(nov.satid, nov.cnav):
            continue
        has_msg = gale6.obtain_has_message()
        gale6.decode_has_message(has_msg)

# EOF

