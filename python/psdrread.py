#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# psdrread.py: Pocket SDR log reader
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libcolor

LEN_CNAV_PAGE = 62  # C/NAV   page  size is 492 bit (61.5  byte)
LEN_BCNAV3    = 61  # B-CNAV3 frame size is 486 bit (60.75 byte)

class PocketSdr:
    def __init__(self, fp_disp, ansi_color):
        self.fp_disp = fp_disp
        self.msg_color = libcolor.Color(fp_disp, ansi_color)

    def read(self):
        ''' returns True when L6D, L6E, E6B, or B2b signal log is read,
            returns False when EOF is encounterd '''
        self.satid = 0
        self.e6b   = b''
        self.l6    = b''
        while True:
            line = sys.stdin.readline().strip()
            if not line:  # end of file
                return False
            if   line[0:6] == "$L6FRM":
                self.l6 = bytes.fromhex(line.split(',')[5])
                break
            elif line[0:5] == '$CNAV':
                self.satid = int(line.split(',')[3])
                self.e6b   = bytes.fromhex(line.split(',')[4]) + \
                    bytes(LEN_CNAV_PAGE - 61)
                break
            elif line[0:7] == '$BCNAV3':
                self.satid = int(line.split(',')[3])
                self.b2b   = bytes.fromhex(line.split(',')[4])
                break
        return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Pocket SDR E6B log to HAS message converter')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-b', '--b2b', action='store_true',
        help='send B2b messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-e', '--e6b', action='store_true',
        help='send E6B messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-l', '--l6', action='store_true',
        help='send L6 messages to stdout, and also turns off display message.')
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
    fp_b2b  = None
    fp_e6b  = None
    fp_l6   = None
    has_decode = False
    if args.trace < 0:
        print(libcolor.Color().fg('red') + 'trace level should be positive ({args.trace}).' + libcolor.Color().fg(), file=sys.stderr)
        sys.exit(1)
    if args.b2b:
        fp_disp, fp_b2b, fp_e6b, fp_l6 = None, sys.stdout, None, None
    if args.e6b:
        fp_disp, fp_b2b, fp_e6b, fp_l6 = None, None, sys.stdout, None
    if args.l6:
        fp_disp, fp_b2b, fp_e6b, fp_l6 = None, None, None, sys.stdout
    if args.message:  # show HAS message to stderr
        fp_disp = sys.stderr
    if 'pksdr2qzsl6.py' in sys.argv[0]:
        print(libcolor.Color().fg('yellow') + 'Notice: please use "psdrread.py -l" (psdrread.py needs -l option then), instead of "pksdr2qzsl6.py" that will be removed.' + libcolor.Color().fg(), file=sys.stderr)
        fp_disp, fp_b2b, fp_e6b, fp_l6 = None, None, None, sys.stdout
    if 'pksdr2has.py' in sys.argv[0]:  # for compatibility of pksdr2has.py
        print(libcolor.Color().fg('yellow') + 'Notice: please use "psdrread.py -e | gale6read.py (pksdrread.py needs -e option then)", instead of "pksdr2has.py" that will be removed.' + libcolor.Color().fg(), file=sys.stderr)
        has_decode = True
        import libgale6
        gale6 = libgale6.GalE6(fp_rtcm, fp_disp, args.trace, args.color, args.statistics)
    rcv = PocketSdr(fp_disp, args.color)
    try:
        while rcv.read():
            if fp_l6 and rcv.l6:
                fp_l6.buffer.write(rcv.l6)
                fp_l6.flush()
            if fp_e6b and rcv.e6b:
                fp_e6b.buffer.write(rcv.satid.to_bytes(1, byteorder='little'))
                fp_e6b.buffer.write(rcv.e6b)
                fp_e6b.flush()
            if fp_b2b and rcv.b2b:
                fp_b2b.buffer.write(rcv.satid.to_bytes(1, byteorder='little'))
                fp_b2b.buffer.write(rcv.b2b)
                fp_b2b.flush()
            if has_decode and rcv.e6b:  # for compatibility of pksdr2has.py
                if gale6.ready_decoding_has(rcv.satid, rcv.e6b):
                    gale6.decode_has_message()
    except (BrokenPipeError, IOError):
        sys.exit()
    except KeyboardInterrupt:
        print(libcolor.Color().fg('yellow') + "User break - terminated" + \
            libcolor.Color().fg(), file=sys.stderr)
        sys.exit()

# EOF
