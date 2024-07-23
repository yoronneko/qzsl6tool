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
import libgnsstime
import libtrace

LEN_BCNAV3      = 125  # BDS CNAV3 page size is 1000 sym (125 byte)
LEN_L6_FRM      = 250  # QZS L6 frame size is 2000 bit (250 byte)
LEN_CNAV_PAGE   = 62   # GAL C/NAV page size is 492 bit (61.5 byte)
PREAMBLE_BCNAV3 = b'\xeb\x90'  # preamble for BDS B2b message
SEPT_MSG_NAME = {      # dictionary for obtaining message name from ID
        4024: 'GALRawCNAV',  # ref.[1] p.282
        4069: 'QZSRawL6'  ,  # ref.[2] p.267
        4242: 'BDSRawB2b' ,  # ref.[1] p.288
}

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
    raw = b''

    def __init__(self, trace):
        self.trace = trace

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
            msg_id  = int.from_bytes(head[2:4], 'little') & 0x1fff
            msg_len = int.from_bytes(head[4:6], 'little')
            if msg_len % 4 != 0:
                # the message length should be multiple of 4 as in [1].
                libtrace.err(f'message length {msg_len} should be multiple of 4')
                return False
            payload = sys.stdin.buffer.read(msg_len - 8)
            if not payload:
                return False
            crc_cal = crc16_ccitt(head[2:6] + payload)
            if crc_cal == crc:
                break
            else:
                libtrace.err(f'CRC Error: {crc.hex()} != {crc_cal.hex()}')
                continue
        self.msg_id   = msg_id
        self.msg_name = SEPT_MSG_NAME.get(msg_id, f"MT{msg_id}")
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
        # see ref.[1] p.259 for converting from svid to sat code.
        self.satid = svid - 70
        msg = self.trace.msg(0, libgnsstime.gps2utc(wnc, tow // 1000), fg='green') + ' ' + \
            self.trace.msg(0, self.msg_name, fg='cyan') + \
            self.trace.msg(0, f' E{self.satid:02d} ', fg='yellow')
        if crc_passed != 1:  # CRC check failed
            return msg + self.trace.msg(0, 'CRC Error', fg='red') + ' ' + self.raw.hex()
        e6b = bytearray(64)
        u4perm(nav_bits, e6b)
        self.raw   = self.satid.to_bytes(1, byteorder='little') + e6b[:LEN_CNAV_PAGE]
        return msg + self.raw.hex()

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
            # see ref.[2] p.243 for converting from svid to sat code, and see ref.[2] p.267 for determining signal name.
        msg = self.trace.msg(0, libgnsstime.gps2utc(wnc, tow//1000), fg='green') + ' ' + \
            self.trace.msg(0, self.msg_name, fg='cyan') + \
            self.trace.msg(0, f' J{self.satid:02d}({"L6D" if source == 1 else "L6E"}) ', fg='yellow')
        if parity == 0:  # parity check failed
            return msg + self.trace.msg(0, 'Parity Error', fg='red') + ' ' + self.raw.hex()
        l6         = bytearray(252)
        u4perm(nav_bits, l6)
        self.raw   = l6[:LEN_L6_FRM]
        return msg + self.raw.hex()

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
        msg = self.trace.msg(0, libgnsstime.gps2utc(wnc, tow//1000), fg='green') + ' ' + \
            self.trace.msg(0, self.msg_name, fg='cyan') + \
            self.trace.msg(0, f' C{self.satid:02d} ', fg='yellow')
        # see ref.[1] p.259 for converting from svid to sat code.
        if crc_passed != 1:  # CRC check failed
            return msg + self.trace.msg(0, 'CRC Error', fg='red') + ' ' + self.raw.hex()
        b2b   = bytearray(124)
        u4perm(nav_bits, b2b)
        self.raw = (PREAMBLE_BCNAV3 + b2b)[:LEN_BCNAV3]
        return msg + self.raw.hex()

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
        help='send QZS L6 messages to stdout (it also turns off Septentrio messages).')
    parser.add_argument(
        '-b', '--b2b', action='store_true',
        help='send BDS B2b messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    args = parser.parse_args()
    fp_disp, fp_raw = sys.stdout, None
    if args.e6b or args.l6 or args.b2b:
        fp_disp, fp_raw = None, sys.stdout
    if args.message:  # send display messages to stderr
        fp_disp = sys.stderr
    trace = libtrace.Trace(fp_disp, 0, args.color)
    rcv = SeptReceiver(trace)
    try:
        while rcv.read():
            # print(rcv.msg_name, file=fp_disp)
            if   rcv.msg_name == 'GALRawCNAV':
                msg = rcv.galrawcnav()
            elif rcv.msg_name == 'QZSRawL6':
                msg = rcv.qzsrawl6()
            elif rcv.msg_name == 'BDSRawB2b':
                msg = rcv.bdsrawb2b()
            else:
                msg = rcv.trace.msg(0, rcv.msg_name, dec='dark')
                rcv.raw = bytearray()
            rcv.trace.show(0, msg)
            if (args.e6b and rcv.msg_name == 'GALRawCNAV') or \
               (args.l6  and rcv.msg_name == 'QZSRawL6'  ) or \
               (args.b2b and rcv.msg_name == 'BDSRawB2b' ):
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
