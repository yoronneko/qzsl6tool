#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# septread.py: Septentrio receiver raw message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2023 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] Septentrio, mosaic-X5 Firmware v4.14.0 Release Note, 2023.
# [2] Septentrio, mosaic-CLAS Firmware v4.14.0 Release Note, 2023.

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import gps2utc
import libcolor

LEN_CNAV_PAGE = 62  # C/NAV page size is 492 bit (61.5 byte)

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

def u4perm(inblk, outblk):
    ''' permutation of endian for decode raw message '''
    if len(inblk) % 4 != 0:
        raise Exception(f"Septentrio raw u32 should be multiple of 4 (actual {len(inblk)}).")
    outblk[0::4] = inblk[3::4]
    outblk[1::4] = inblk[2::4]
    outblk[2::4] = inblk[1::4]
    outblk[3::4] = inblk[0::4]


class SeptReceiver:
    def __init__(self, fp_disp, ansi_color):
        self.fp_disp   = fp_disp
        self.msg_color = libcolor.Color(fp_disp, ansi_color)
        self.l6        = b''
        self.e6b       = b''
        self.b2b       = b''

    def read(self):
        ''' reads standard input as SBF raw, [1]
            and returns true if successful '''
        while True:
            sync = bytes(2)
            while sync != b'\x24\x40':
                b = sys.stdin.buffer.read(1)
                if not b:
                    return False
                sync = sync[1:2] + b
            head = sys.stdin.buffer.read(6)
            if not head:
                return False
            crc     =                head[0:2]
            msg_id  = int.from_bytes(head[2:4], 'little')
            msg_len = int.from_bytes(head[4:6], 'little')
            if msg_len % 4 != 0:
                # the message length should be multiple of 4 as in [1].
                print(self.msg_color.fg('red') + \
                    f'message length {msg_len} should be multiple of 4' + \
                    self.msg_color.fg(), file=self.fp_disp)
                return False
            payload = sys.stdin.buffer.read(msg_len - 8)
            if not payload:
                return False
            crc_cal = crc16_ccitt(head[2:6] + payload)
            if crc_cal == crc:
                break
            else:
                print(self.msg_color.fg('red') + \
                    f'CRC Error: {crc.hex()} != {crc_cal.hex()}' + \
                    self.msg_color.fg(), file=self.fp_disp)
                continue
        self.msg_id   = msg_id
        self.msg_name = self.SEPT_MSG_NAME.get(msg_id, f"MT{msg_id}")
        self.payload  = payload
        return True

    def galrawcnav(self):
        ''' returns hex-decoded messages
            GALRawCNAV (4024) ref.[1], p.282
        '''
        payload = self.payload
        pos = 0
        tow         = int.from_bytes(payload[pos:pos+ 4], 'little'); pos +=  4
        wnc         = int.from_bytes(payload[pos:pos+ 2], 'little'); pos +=  2
        svid        = int.from_bytes(payload[pos:pos+ 1], 'little'); pos +=  1
        crc_passed  = int.from_bytes(payload[pos:pos+ 1], 'little'); pos +=  1
        viterbi_cnt = int.from_bytes(payload[pos:pos+ 1], 'little'); pos +=  1
        source      = int.from_bytes(payload[pos:pos+ 1], 'little'); pos +=  1
        pos +=  1
        rx_channel  = int.from_bytes(payload[pos:pos+ 1], 'little'); pos +=  1
        nav_bits    =                payload[pos:pos+64]           ; pos += 64
        e6b = bytearray(64)
        u4perm(nav_bits, e6b)
        # see ref.[1] p.259 for converting from svid to sat code.
        self.satid = svid - 70
        self.e6b   = e6b[:LEN_CNAV_PAGE]
        msg = self.msg_color.fg('green') + \
            gps2utc.gps2utc(wnc, tow // 1000) + ' ' + \
            self.msg_color.fg('cyan') + self.msg_name + \
            self.msg_color.fg('yellow') + f' E{self.satid:02d} ' + \
            self.msg_color.fg() + self.e6b.hex()
        return msg

    def qzsrawl6(self):
        ''' returns hex-decoded message
            QZSRawL6 (4096) ref.[2], p.267
        '''
        payload = self.payload
        pos = 0
        tow        = int.from_bytes(payload[pos:pos+  4], 'little'); pos +=   4
        wnc        = int.from_bytes(payload[pos:pos+  2], 'little'); pos +=   2
        svid       = int.from_bytes(payload[pos:pos+  1], 'little'); pos +=   1
        parity     = int.from_bytes(payload[pos:pos+  1], 'little'); pos +=   1
        rs_cnt     = int.from_bytes(payload[pos:pos+  1], 'little'); pos +=   1
        source     = int.from_bytes(payload[pos:pos+  1], 'little'); pos +=   1
        pos +=  1  # reserved
        rx_channel = int.from_bytes(payload[pos:pos+  1], 'little'); pos +=   1
        nav_bits   =                payload[pos:pos+252]           ; pos += 252
        self.satid = svid - 180
        self.l6    = bytearray(252)
        u4perm(nav_bits, self.l6)
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
        tow        = int.from_bytes(payload[pos:pos+  4], 'little'); pos +=   4
        wnc        = int.from_bytes(payload[pos:pos+  2], 'little'); pos +=   2
        svid       = int.from_bytes(payload[pos:pos+  1], 'little'); pos +=   1
        crc_passed = int.from_bytes(payload[pos:pos+  1], 'little'); pos +=   1
        pos += 1  # reserved
        source     = int.from_bytes(payload[pos:pos+  1], 'little'); pos +=   1
        pos += 1  # reserved
        rx_channel = int.from_bytes(payload[pos:pos+  1], 'little'); pos +=   1
        nav_bits   =                payload[pos:pos+124]           ; pos += 124
        self.satid = (svid - 140) if svid <= 180 else (svid - 182)
        self.b2b   = bytearray(124)
        u4perm(nav_bits, self.b2b)
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
    parser = argparse.ArgumentParser(description='Septentrio message read')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-e', '--e6b', action='store_true',
        help='send E6B messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-l', '--l6', action='store_true',
        help='send QZS L6 messages to stdout (it also turns off Septentrio messages)..')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    args = parser.parse_args()
    fp_e6b, fp_l6, fp_disp = None, None, sys.stdout
    if args.e6b:
        fp_disp, fp_e6b, fp_l6 = None, sys.stdout, None
    if args.l6:
        fp_disp, fp_e6b, fp_l6 = None, None, sys.stdout
    if args.message:  # show HAS message to stderr
        fp_disp = sys.stderr
    rcv = SeptReceiver(fp_disp, args.color)
    try:
        while rcv.read():
            # print(rcv.msg_name, file=fp_disp)
            msg = ''
            if   rcv.msg_name == 'GALRawCNAV':
                msg += rcv.galrawcnav()
                if fp_e6b and rcv.e6b:
                    fp_e6b.buffer.write(
                        rcv.satid.to_bytes(1, byteorder='little'))
                    fp_e6b.buffer.write(rcv.e6b)
                    fp_e6b.flush()
            elif rcv.msg_name == 'QZSRawL6':
                msg += rcv.qzsrawl6()
                if fp_l6 and rcv.l6:
                    fp_l6.buffer.write(rcv.l6)
                    fp_l6.flush()
            elif rcv.msg_name == 'BDSRawB2b':
                msg += rcv.bdsrawb2b()
            else:
                msg += rcv.msg_color.dec('dark') + rcv.msg_name + \
                    rcv.msg_color.dec()
            if fp_disp:
                print(msg, file=fp_disp)
                fp_disp.flush()
    except (BrokenPipeError, IOError):
        sys.exit()
    except KeyboardInterrupt:
        print(rcv.msg_color.fg('yellow') + "User break - terminated" + \
            rcv.msg_color.fg(), file=sys.stderr)
        sys.exit()

# EOF

