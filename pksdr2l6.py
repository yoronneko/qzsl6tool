#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pksdr2l6.py: PocketSDR log message to quasi-zenith satellite (QZS) L6 raw converter
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import sys

line = sys.stdin.readline().strip()
while (line):
    if line[0:6] != "$L6FRM":
        line = sys.stdin.readline().strip()
        continue
    t_data = line.split(',')[5]
    sys.stdout.buffer.write(bytes.fromhex(t_data))
    sys.stdout.flush()
    line = sys.stdin.readline().strip()

# EOF
