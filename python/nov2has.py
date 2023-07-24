#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# nov2has.py: NovAtel binary to Galileo HAS message
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
# [2] NovAtel, OEM7 commands and logs reference manual, v23, May 2023.

import argparse
import sys
import libgale6


class NovCnav:
    def read(self):
        sync = [b'0x00' for i in range(3)]
        ok = False
        try:
            while not ok:
                b = sys.stdin.buffer.read(1)
                if not b:
                    return False
                sync = sync[1:3] + [b]
                if sync == [b'\xaa', b'\x44', b'\x12']:
                    ok = True
            b = sys.stdin.buffer.read(1)
            if not b:
                return False
            head_len = int.from_bytes(b, 'little')
            head = sys.stdin.buffer.read(head_len-4)
            if not head:
                return False
            self.parse_head(head)
            payload = sys.stdin.buffer.read(self.msg_len)
            if not payload:
                return False
            self.payload = payload
            crc = sys.stdin.buffer.read(4)
            if not crc:
                return False
        except KeyboardInterrupt:
            sys.exit()
        return True

    def parse_head(self, head):
        pos = 0
        if len(head) != 24:
            print(f'head len: {len(head)} != 24')
        self.msg_id   = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.msg_type = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.port     = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.msg_len  = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.seq      = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.t_idle   = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.t_stat   = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.gpsw     = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.gpst     = int.from_bytes(head[pos:pos+4], 'little')/1e3; pos += 4
        self.stat     = int.from_bytes(head[pos:pos+4], 'little'); pos += 4
        self.reserved = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.ver      = int.from_bytes(head[pos:pos+2], 'little'); pos += 2

    def galcnavrawpage(self):
        '''[1] p.589 3.40 GALCNAVRAWPAGE'''
        payload = self.payload
        if len(payload) != 4+4+2+2+58:
            print(f"length mismatch: {len(payload)} != {4+4+2+2+58}")
            return False
        pos = 0
        sig_ch  = int.from_bytes(payload[pos:pos+4], 'little'); pos += 4
        prn     = int.from_bytes(payload[pos:pos+4], 'little'); pos += 4
        msg_id  = int.from_bytes(payload[pos:pos+2], 'little'); pos += 2
        page_id = int.from_bytes(payload[pos:pos+2], 'little'); pos += 2
        e6b     = payload[pos:pos+ 58]; pos += 58
        self.satid = prn
        self.e6b = e6b + b'\x00\x00\x00\x00'
        self.e6b = e6b + b'\x00\x00\x00'
# NovAtel C/NAV data excludes 24-bit CRC and 6-bit tail bits (as mentioned),
# Three bytes (24 bit) are added for CRC, tail, and padding

NOV_MSG_NAME = {
8: 'IONUTC',
41: 'RAWEPHEM',
43: 'RANGE',
140: 'RANGECMP',
287: 'RAWWAASFRAME',
723: 'GLOEPHEMERIS',
973: 'RAWSBASFRAME',
1121: 'GALCLOCK',
1122: 'GALEPHEMERIS',
1127: 'GALIONO',
1330: 'QZSSRAWSUBFRAME',
1331: 'QZSSRAWEPHEM',
1347: 'QZSSIONUTC',
1696: 'BDSEPHEMERIS',
2123: 'NAVICEPHEMERIS',
2239: 'GALCNAVRAWPAGE',
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='NovAtel receiver binary to HAS message converter')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-e', '--e6b', action='store_true',
        help='send E6B messages to stdout, and also turns off display message.')
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
    nov = NovCnav()
    while nov.read():
        #print(f'{nov.gpsw:4d} {nov.gpst:8.2f} MT{nov.msg_id:<4d} {NOV_MSG_NAME.get(nov.msg_id,"unknown")} ({nov.msg_len} bytes)')
        if nov.msg_id != 2239:  # message ID of 2239 represents GALCNAVRAWPAGE
            continue
        nov.galcnavrawpage()
        if not gale6.ready_decoding_has(nov.satid, nov.e6b):
            continue
        has_msg = gale6.obtain_has_message()
        gale6.decode_has_message(has_msg)
        if fp_e6b:
            fp_e6b.buffer.write(has_msg.tobytes())
            fp_e6b.flush()

# EOF

