#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# psdrread.py: Pocket SDR log read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
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
        self.satid   = 0
        self.signame = None
        self.msg     = ''
        while True:
            line = sys.stdin.readline().strip()
            if not line:  # end of file
                return False
            if   line[0:6] == "$L6FRM":
                self.signame = 'l6'
                self.satid = int(line.split(',')[3])
                self.raw = bytes.fromhex(line.split(',')[5])
                self.msg = self.trace.msg(0, f"J{self.satid-192:02d} L6: ", fg='green') + \
                    self.trace.msg(0, line.split(',')[5], fg='yellow')
                break
            elif line[0:5] == '$CNAV':
                self.signame = 'e6b'
                self.satid = int(line.split(',')[3])
                self.raw = self.satid.to_bytes(1, byteorder='little') + \
                    bytes.fromhex(line.split(',')[4]) + \
                    bytes(LEN_CNAV_PAGE - 61)
                self.msg = self.trace.msg(0, f"E{self.satid:02d} E6B: ", fg='green') + \
                    self.trace.msg(0, line.split(',')[4], fg='yellow')
                break
            elif line[0:5] == '$INAV':
                self.signame = 'inav'
                self.satid = int(line.split(',')[3])
                self.raw = satid.to_bytes(1, byteorder='little') + \
                    bytes.fromhex(line.split(',')[4])
                self.msg = self.trace.msg(0, f"E{self.satid:02d} I/NAV: ", fg='green') + \
                    self.trace.msg(0, line.split(',')[4], fg='yellow')
                break
            elif line[0:7] == '$BCNAV3':
                self.signame = 'b2b'
                self.satid = int(line.split(',')[3])
                self.raw = bytes.fromhex(line.split(',')[4])
                self.msg = self.trace.msg(0, f"C{self.satid:02d} B2b: ", fg='green') + \
                    self.trace.msg(0, line.split(',')[4], fg='yellow')
                break
        return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Pocket SDR message read')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-b', '--b2b', action='store_true',
        help='send BDS B2b messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-i', '--inav', action='store_true',
        help='send GAL I/NAV messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-e', '--e6b', action='store_true',
        help='send GAL E6B messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-l', '--l6', action='store_true',
        help='send QZS L6 messages to stdout, and also turns off display message.')
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
