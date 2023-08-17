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
import libcolor

def crc32(data):
    polynomial = 0xedb88320
    crc = 0
    for byte in data:
        tmp2 = (crc ^ byte) & 0xff
        for _ in range(8):
            if tmp2 & 1:
                tmp2 = (tmp2 >> 1) ^ polynomial
            else:
                tmp2 = tmp2 >> 1
        tmp1 = (crc >> 8) & 0x00ffffff
        crc = tmp1 ^ tmp2
    return crc.to_bytes(4,'little')

class NovCnav:
    def __init__(self, fp_disp, ansi_color):
        self.fp_disp   = fp_disp
        self.msg_color = libcolor.Color(fp_disp, ansi_color)

    def read(self):
        sync = bytes(3)
        ok = False
        try:
            while not ok:
                b = sys.stdin.buffer.read(1)
                if not b:
                    return False
                sync = sync[1:3] + b
                if sync == b'\xaa\x44\x12':
                    ok = True
            head_len = sys.stdin.buffer.read(1)
            if not head_len:
                return False
            u_head_len = int.from_bytes(head_len, 'little')
            head = sys.stdin.buffer.read(u_head_len-4)
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
            crc_cal = crc32(sync + head_len + head + payload)
            if crc != crc_cal:
                print(self.msg_color.fg('red'), end='', file=self.fp_disp)
                print(f'CRC error: {crc.hex()} != {crc_cal.hex()}', file=self.fp_disp)
                print(self.msg_color.fg(), end='', file=self.fp_disp)
                return False
        except KeyboardInterrupt:
            sys.exit()
        return True

    def parse_head(self, head):
        pos = 0
        if len(head) != 24:
            print(self.msg_color.fg('red'), end='', file=self.fp_disp)
            print(f'head len: {len(head)} != 24', file=self.fp_disp)
            print(self.msg_color.fg(), end='', file=self.fp_disp)
        self.msg_id   = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.msg_type = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.port     = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.msg_len  = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.seq      = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.t_idle   = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.t_stat   = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.gpsw     = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.gpst     = int.from_bytes(head[pos:pos+4], 'little'); pos += 4
        self.stat     = int.from_bytes(head[pos:pos+4], 'little'); pos += 4
        self.reserved = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.ver      = int.from_bytes(head[pos:pos+2], 'little'); pos += 2

    def galcnavrawpage(self):
        '''[1] p.589 3.40 GALCNAVRAWPAGE'''
        payload = self.payload
        if len(payload) != 4+4+2+2+58:
            print(self.msg_color.fg('red'), end='', file=self.fp_disp)
            print(f"length mismatch: {len(payload)} != {4+4+2+2+58}", file=self.fp_disp)
            print(self.msg_color.fg(), end='', file=self.fp_disp)
            return False
        pos = 0
        sig_ch  = int.from_bytes(payload[pos:pos+4], 'little'); pos += 4
        prn     = int.from_bytes(payload[pos:pos+4], 'little'); pos += 4
        msg_id  = int.from_bytes(payload[pos:pos+2], 'little'); pos += 2
        page_id = int.from_bytes(payload[pos:pos+2], 'little'); pos += 2
        e6b     = payload[pos:pos+ 58]; pos += 58
        self.satid = prn
        self.e6b = e6b + b'\x00\x00\x00'
# NovAtel C/NAV data excludes 24-bit CRC and 6-bit tail bits (as mentioned),
# Three bytes (24 bit) are added for CRC, tail, and padding


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
    nov = NovCnav(fp_disp, force_ansi_color)
    while nov.read():
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

