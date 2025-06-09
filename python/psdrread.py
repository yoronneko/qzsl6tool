#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# psdrread.py: Pocket SDR log read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023-2025 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libqzsl6tool
import libtrace

LEN_BCNAV3    = 125  # BDS CNAV3 page size is 1000 sym (125 byte)
LEN_L6_FRM    = 250  # QZS L6 frame size is 2000 bit (250 byte)
LEN_CNAV_PAGE =  62  # GAL C/NAV page size is 492 bit (61.5 byte)

class PocketSdr:
    def __init__(self, trace):
        self.trace = trace

    def read(self):
        ''' returns True when L6D, L6E, E6B, or B2b signal log is read,
            returns False when EOF is encountered '''
        while True:
            self.prn     = 0
            self.signame = ''
            self.msg     = ''
            line = sys.stdin.readline().strip()
            if not line:  # end of file
                return False
            cols = line.split(',')
            if   line[0:6] == "$L6FRM":  # L6D or L6E (old format)
                self.prn = int(cols[3])
                self.signame = 'l6'
                self.raw = bytes.fromhex(cols[5])
                satid    = self.prn - 192 if self.prn <= 202 else self.prn - 202
                self.msg = self.trace.msg(0, f"J{satid:02d} L6: ", fg='green') + \
                    self.trace.msg(0, cols[5], fg='yellow')
                return True
            elif line[0:5] == '$CNAV':  # E6B (old format)
                self.signame = 'e6b'
                self.prn = int(cols[3])
                self.raw = self.prn.to_bytes(1, byteorder='little') + \
                    bytes.fromhex(cols[4]) + \
                    bytes(LEN_CNAV_PAGE - 61)
                self.msg = self.trace.msg(0, f"E{self.prn:02d} E6B: ", fg='green') + \
                    self.trace.msg(0, cols[4], fg='yellow')
                return True
            elif line[0:5] == '$INAV':  # E1B or E5b (old format)
                self.signame = 'inav'
                self.prn = int(cols[3])
                self.raw = self.prn.to_bytes(1, byteorder='little') + \
                    bytes.fromhex(cols[4])
                self.msg = self.trace.msg(0, f"E{self.prn:02d} I/NAV: ", fg='green') + \
                    self.trace.msg(0, cols[4], fg='yellow')
                return True
            elif line[0:7] == '$BCNAV3':  # B2b (old format)
                self.signame = 'b2b'
                self.prn = int(cols[3])
                self.raw = bytes.fromhex(cols[4])
                self.msg = self.trace.msg(0, f"C{self.prn:02d} B2b: ", fg='green') + \
                    self.trace.msg(0, cols[4], fg='yellow')
                return True
            elif line[0:4] == '$NAV':
                # new Pocket SDR format
                # ex.: $NAV,5.963,E04,E1B,4,0,128,02555555555555555555555554108FDD
                #       [0]   [1] [2] [3][4][5][6][7]
                self.prn = int(cols[4])
                if cols[3] == 'L6D' or cols[3] == 'L6E':
                    self.signame = 'l6'
                    self.raw = bytes.fromhex(cols[7])
                    self.msg = self.trace.msg(0, f"{cols[2]} L6: ", fg='green') + \
                        self.trace.msg(0, cols[7], fg='yellow')
                    return True
                elif cols[3] == 'E6B':
                    self.signame = 'e6b'
                    self.raw = self.prn.to_bytes(1, byteorder='little') + \
                        bytes.fromhex(cols[7]) + \
                        bytes(LEN_CNAV_PAGE - 61)
                    self.msg = self.trace.msg(0, f"{cols[2]} E6B: ", fg='green') + \
                        self.trace.msg(0, cols[7], fg='yellow')
                    return True
                elif cols[3] == 'E1B' or cols[3] == 'E5A':
                    self.signame = 'inav'
                    self.raw = self.prn.to_bytes(1, byteorder='little') + \
                        bytes.fromhex(cols[7])
                    self.msg = self.trace.msg(0, f"{cols[2]} I/NAV: ", fg='green') + \
                        self.trace.msg(0, cols[7], fg='yellow')
                    return True
                elif cols[3] == 'B2B':
                    self.signame = 'b2b'
                    self.raw = bytes.fromhex(cols[7])
                    self.msg = self.trace.msg(0, f"{cols[2]} B2b: ", fg='green') + \
                        self.trace.msg(0, cols[7], fg='yellow')
                    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=f'Pocket SDR message read, QZS L6 Tool ver.{libqzsl6tool.VERSION}')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-b', '--b2b', action='store_true',
        help='send BDS B2b messages to stdout, and also turns off display message.')
    group.add_argument(
        '-i', '--inav', action='store_true',
        help='send GAL I/NAV messages to stdout, and also turns off display message.')
    group.add_argument(
        '-e', '--e6b', action='store_true',
        help='send GAL E6B messages to stdout, and also turns off display message.')
    group.add_argument(
        '-l', '--l6', action='store_true',
        help='send QZS L6 messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    args = parser.parse_args()
    fp_disp, fp_raw = sys.stdout, None
    if args.b2b or args.e6b or args.inav or args.l6:
        fp_disp, fp_raw = None, sys.stdout
    trace = libtrace.Trace(fp_disp, 0, args.color)
    rcv = PocketSdr(trace)
    try:
        while rcv.read():
            rcv.trace.show(0, rcv.msg)
            if (args.b2b  and rcv.signame == 'b2b' ) or \
               (args.e6b  and rcv.signame == 'e6b' ) or \
               (args.inav and rcv.signame == 'inav') or \
               (args.l6   and rcv.signame == 'l6'  ):
                if fp_raw:
                    fp_raw.buffer.write(rcv.raw)
                    fp_raw.flush()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
