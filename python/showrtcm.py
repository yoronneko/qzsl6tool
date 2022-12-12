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
from libqzsl6tool import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Quasi-zenith satellite (QZS) L6 message to RTCM converter')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='trace level for debug: 1=subtype detail, 2=subtype and bit image')
    args = parser.parse_args()
    rtcm = Rtcm()
    if 0 < args.trace:
        rtcm.t_level = args.trace
    while rtcm.receive():
        rtcm.decode_message()

# EOF
