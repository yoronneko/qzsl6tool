#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# septdump.py: Septentrio receiver raw message dump
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2023 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# [1] Septentrio, mosaic-X5 Firmware v4.14.0 Release Note, 2023.
# [2] Septentrio, mosaic-CLAS Firmware v4.14.0 Release Note, 2023.

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import gps2utc
import libcolor


def crc16_ccitt(data):
    crc = 0
    polynomial = 0x1021
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial
            else:
                crc = crc << 1
            crc &= 0xffff
    return crc.to_bytes(2,'little')

class SeptReceiver:
    def __init__(self, fp_disp, ansi_color):
        self.fp_disp = fp_disp
        self.msg_color = libcolor.Color(fp_disp, ansi_color)

    def read(self):
        ''' reads standard input as SBF raw, [1]
            and returns true if successful '''
        sync = bytes(2)
        try:
            while True:
                while sync != b'\x24\x40':
                    b = sys.stdin.buffer.read(1)
                    if not b:
                        return False
                    sync = sync[1:2] + b
                head = sys.stdin.buffer.read(6)
                if not head:
                    return False
                crc     = head[0:2]
                msg_id  = int.from_bytes(head[2:4], 'little')
                msg_len = int.from_bytes(head[4:6], 'little')
                if msg_len % 4 != 0:
                    # the message length should be multiple of 4 as in [1].
                    msg = self.msg_color.fg('red') + \
                        f'message length {msg_len} should be multiple of 4' + \
                        self.msg_color.fg()
                    print(msg, file=self.fp_disp)
                    return False
                payload = sys.stdin.buffer.read(msg_len - 8)
                if not payload:
                    return False
                crc_cal = crc16_ccitt(head[2:6] + payload)
                if crc_cal == crc:
                    break
                else:
                    msg = self.msg_color.fg('red') + \
                        f'CRC Error: {crc.hex()} != {crc_cal.hex()}' + \
                        self.msg_color.fg()
                    print(msg, file=self.fp_disp)
                    continue
            self.msg_id   = msg_id
            self.msg_name = self.SEPT_MSG_NAME.get(msg_id, f"MT{msg_id}")
            self.payload  = payload
        except KeyboardInterrupt:
            msg = self.msg_color.fg('yellow') + "User break - terminated" + \
                  self.msg_color.fg()
            print(msg, file=sys.stderr)
            sys.exit()
        return True

    def galrawcnav(self):
        ''' returns hex-decoded messages
            GALRawCNAV (4024) ref.[1], p.282
        '''
        payload = self.payload
        pos = 0
        tow         = int.from_bytes(payload[pos:pos+4], 'little'); pos += 4
        wnc         = int.from_bytes(payload[pos:pos+2], 'little'); pos += 2
        svid        = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        crc_passed  = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        viterbi_cnt = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        source      = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        pos +=  1
        rx_channel  = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        self.cnav   = payload[pos:pos+64]; pos +=  64
        self.satid = svid - 70
        msg = self.msg_color.fg('green') + \
            gps2utc.gps2utc(wnc, tow//1000) + ' ' + \
            self.msg_color.fg('cyan') + self.msg_name + \
            self.msg_color.fg('yellow') + f' E{self.satid:02d} ' + \
            self.msg_color.fg() + self.cnav.hex()
            # see ref.[1] p.259 for converting from svid to sat code.
        return msg

    def qzsrawl6(self):
        ''' returns hex-decoded message
            QZSRawL6 (4096) ref.[2], p.267
        '''
        payload = self.payload
        pos = 0
        tow        = int.from_bytes(payload[pos:pos+4], 'little'); pos += 4
        wnc        = int.from_bytes(payload[pos:pos+2], 'little'); pos += 2
        svid       = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        parity     = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        rs_cnt     = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        source     = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        pos +=  1
        rx_channel = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        self.l6    = payload[pos:pos+252]; pos += 252
        self.satid = svid - 180
        msg = self.msg_color.fg('green') + \
            gps2utc.gps2utc(wnc, tow//1000) + ' ' + \
            self.msg_color.fg('cyan') + self.msg_name + \
            self.msg_color.fg('yellow') + \
            f' J{self.satid:02d}({"L6D" if source == 1 else "L6E"}) ' + \
            self.msg_color.fg() + self.l6.hex()
            # see ref.[2] p.243 for converting from svid to sat code, and see ref.[2] p.267 for determining signal name.
        return msg

    def bdsrawb2b(self):
        ''' returns hex-decoded message
            BDSRawB2b (4242) ref.[1], p.288
        '''
        payload = self.payload
        pos = 0
        tow         = int.from_bytes(payload[pos:pos+4], 'little'); pos += 4
        wnc         = int.from_bytes(payload[pos:pos+2], 'little'); pos += 2
        svid        = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        crc_passed  = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        pos +=  1
        source      = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        pos +=  1
        rx_channel  = int.from_bytes(payload[pos:pos+1], 'little'); pos += 1
        self.b2b    = payload[pos:pos+ 124]; pos += 124
        self.satid = (svid - 140) if svid <= 180 else (svid - 182)
        msg = self.msg_color.fg('green') + \
            gps2utc.gps2utc(wnc, tow//1000) + ' ' + \
            self.msg_color.fg('cyan') + self.msg_name + \
            self.msg_color.fg('yellow') + f' C{self.satid:02d} ' + \
            self.msg_color.fg() + self.b2b.hex()
            # see ref.[1] p.259 for converting from svid to sat code.
        return msg

    SEPT_MSG_NAME = {    # dictionary for obtaining message name from ID
        4024: 'GALRawCNAV',  # ref.[1] p.282
        4069: 'QZSRawL6'  ,  # ref.[2] p.267
        4242: 'BDSRawB2b' ,  # ref.[1] p.288
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Septentrio message dump')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    args = parser.parse_args()
    fp_disp = sys.stdout
    force_ansi_color = False
    if args.color:  # force ANSI color escape sequences
        force_ansi_color = True
    sept = SeptReceiver(fp_disp, force_ansi_color)
    while sept.read():
        # print(sept.msg_name, file=fp_disp)
        msg = ''
        try:
            if   sept.msg_name == 'GALRawCNAV': msg += sept.galrawcnav()
            elif sept.msg_name == 'QZSRawL6'  : msg += sept.qzsrawl6()
            elif sept.msg_name == 'BDSRawB2b' : msg += sept.bdsrawb2b()
            else:
                msg += sept.msg_color.dec('dark') + msg_name + \
                       sept.msg_color.dec()
            print(msg, file=fp_disp)

        except (BrokenPipeError, IOError):
            sys.exit()
# EOF
