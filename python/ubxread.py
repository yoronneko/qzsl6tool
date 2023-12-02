#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ubxread.py: u-blox receiver raw message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2023 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] u-blox, F9 high precision GNSS receiver interface description,
#     F9 HPG 1.30, UBX-21046737, Dec. 2021.

import argparse
import datetime
import functools
import operator
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libcolor
from   alstread import checksum
from   septread import u4perm

try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    QZS L6 Tool needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)

LEN_L1CA = 300  # message length of GPS & QZS L1C/A, L2C, L5
LEN_L1OF =  85  # message length of GLO L1OF, L2OF
LEN_L1S  = 250  # message length of QZS L1S & SBAS L1C/A
LEN_INAV = 240  # message length of GAL I/NAV
LEN_B1I  = 300  # message length of BDS B1I, B2I

class UbxReceiver:
    prn_prev =  0  # previous PRN

    def __init__(self, fp_disp, ansi_color):
        self.fp_disp   = fp_disp
        self.msg_color = libcolor.Color(fp_disp, ansi_color)

    def read(self):
        ''' reads from standard input as u-blox raw message,
            and returns true if successful '''
        while True:
            sync = bytes(4)
            while sync != b'\xb5\x62\x02\x13':  # ubx-rxm-sfrbx ([1], 3.17.9)
                b = sys.stdin.buffer.read(1)
                if not b:
                    return False
                sync = sync[1:4] + b
            head = sys.stdin.buffer.read(10)
            if not head:
                return False
            msg_len = int.from_bytes(head[0: 2], 'little')
            gnssid  = int.from_bytes(head[2: 3], 'little')
            svid    = int.from_bytes(head[3: 4], 'little')
            sigid   = int.from_bytes(head[4: 5], 'little')
            freqid  = int.from_bytes(head[5: 6], 'little')
            n_word  = int.from_bytes(head[6: 7], 'little')
            chn     = int.from_bytes(head[7: 8], 'little')
            ver     = int.from_bytes(head[8: 9], 'little')
            res     = int.from_bytes(head[9:10], 'little')
            if ver != 0x02:  # [1], sect.3.17.9
                print(self.msg_color.fg('red') + \
                    f'ubx sfrbx version should be 2 ({ver})' +
                    self.msg_color.fg(), file=sys.stderr)
                continue
            if (msg_len-8)/4 != n_word:
                print(self.msg_color.fg('red') + \
                    f'numWord mismatch: {(msg_len-8)/4} != {n_word}' +
                    self.msg_color.fg(), file=sys.stderr)
                continue
            payload = sys.stdin.buffer.read(n_word * 4)
            csum    = sys.stdin.buffer.read(2)
            if not payload or not csum:
                return False
            csum1, csum2 = checksum(b'\x02\x13' + head + payload)
            if csum[0] != csum1 or csum[1] != csum2:
                print(self.msg_color.fg('red') + \
                    f'checksum error: {csum.hex()}!={csum1:02x}{csum2:02x}' + \
                    self.msg_color.fg(), file=sys.stderr)
                continue
            break
        # [1] 1.5.2 GNSS identifiers
        gnssname = ['G', 'S', 'E', 'B', 'IMES', 'J', 'R', 'I'][gnssid]
        # [1] 1.5.4 Signal identifiers
        signame = [ # signal name table: (gnssid, signae) -> signal name
        ['L1CA', '', '', 'L2CL', 'L2CM', '', 'L5I', 'L5Q'],             # GPS
        ['L1CA'],                                                       # SBAS
        ['E1C', 'E1B', '', 'E5aI', 'E5aQ', 'E5bI', 'E5bQ'],             # GAL
        ['B1I', 'B1I', 'B2I', 'B2I', '', 'B1C', '', 'B2a'],             # BDS
        [],                                                             # undef
        ['L1CA', 'L1S', '', '', 'L2CM', 'L2CL', '', '', 'L5I', 'L5Q'],  # QZS
        ['L1OF', '', 'L2OF'],                                           # GLO
        ['L5'],                                                         # IRN
        ][gnssid][sigid]
        payload_perm = bytearray(n_word * 4)
        u4perm(payload, payload_perm)
        self.svid     = svid
        self.gnssname = gnssname
        self.signame  = signame
        self.satname  = f'{gnssname}{svid:02d}'
        if signame == 'L1S' or gnssname == 'S':
            self.payload = bitstring.ConstBitStream(payload_perm)[:LEN_L1S+2]
            paylast = bitstring.ConstBitStream(payload_perm)[LEN_L1S:]
        elif   signame == 'L1CA' or signame == 'L2CM':
            self.payload = bitstring.ConstBitStream(payload_perm)[:LEN_L1CA+4]
            paylast = bitstring.ConstBitStream(payload_perm)[LEN_L1CA:]
        elif signame == 'E1B' or signame == 'E5bI':
            self.payload = bitstring.ConstBitStream(payload_perm)[:LEN_INAV+4]
            paylast = bitstring.ConstBitStream(payload_perm)[LEN_INAV:]
        elif signame == 'L1OF' or signame == 'L2OF':
            self.payload = bitstring.ConstBitStream(payload_perm)[:LEN_L1OF+3]
            paylast = bitstring.ConstBitStream(payload_perm)[LEN_L1OF:]
        elif signame == 'B1I' or signame == 'B2I':
            self.payload = bitstring.ConstBitStream(payload_perm)[:LEN_B1I+4]
            paylast = bitstring.ConstBitStream(payload_perm)[LEN_B1I:]
        else:
            raise Exception(f'unknown signal: {signame}')
        #print(signame, paylast.bin)
        self.msg = \
            self.msg_color.fg('green')  + f'{self.satname:4s} ' + \
            self.msg_color.fg('yellow') + f'{self.signame:4s} ' + \
            self.msg_color.fg() + f'{self.payload.hex}'
        return True

    def decode_qzsl1s(self):
        prn = self.svid
        if self.signame == 'L1S':
            prn = self.svid + 182
        l1s = bitstring.BitStream()
        if not self.prn_prev:
            l1s += bitstring.Bits(uint=prn, length=8)
            self.prn_prev = prn
        l1s += bitstring.Bits(uint= 0, length=12)  # GPS week
        l1s += bitstring.Bits(uint=18, length=20)  # GPS time
        l1s += self.payload[:LEN_L1S]
        self.l1s = l1s.tobytes()

    def decode_qzsl1s_qzqsm(self):
        l1s = self.payload
        l1s.bytealign()
        prn = self.svid + 182
        sentence = f'QZQSM,{prn-128},{l1s.hex}'
        cksum = functools.reduce(operator.xor, (ord(s) for s in sentence), 0)
        self.qzqsm = f'${sentence}*{cksum:02x}' 

    def decode_galinav(self):
        inav = bitstring.BitStream(uint=self.svid, length=8)
        inav += self.payload[:LEN_INAV]
        self.inav = inav.tobytes()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='u-blox message read')
    parser.add_argument('--l1s',
        help='send QZS L1S messages to stdout', action='store_true')
    parser.add_argument('--qzqsm',
        help='send QZS L1S DCR NMEA messages to stdout', action='store_true')
    parser.add_argument('--sbas',
        help='send SBAS messages to stdout', action='store_true')
    parser.add_argument('--duplicate',
        help='allow duplicate QZS L1S DCR NMEA sentences (currently, all QZS sats send the same DCR messages)', action='store_true')
    parser.add_argument('--inav',
        help='send GAL I/NAV messages to stdout', action='store_true')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    args = parser.parse_args()
    fp_disp, fp_raw = sys.stdout, None
    if args.qzqsm or args.l1s or args.sbas or args.inav:
        fp_disp, fp_raw = None, sys.stdout
        payload_prev = bitstring.ConstBitStream()
    if args.message:
        fp_disp = sys.stderr
    rcv = UbxReceiver(fp_disp, args.color)
    try:
        while rcv.read():
            if fp_disp:
                print(rcv.msg, file=fp_disp)
                fp_disp.flush()
            if (args.l1s  and rcv.signame=='L1S') or \
               (args.sbas and rcv.signame=='L1CA' and rcv.gnssname=='S'):
                if rcv.payload == payload_prev and not args.duplicate: continue
                payload_prev = rcv.payload
                rcv.decode_qzsl1s()
                if fp_raw and rcv.l1s:
                    fp_raw.buffer.write(rcv.l1s)
                    fp_raw.flush()
            elif args.qzqsm and rcv.signame=='L1S':
                mt = rcv.payload[8:8+6].uint
                if mt != 43 and mt != 44: continue
                if rcv.payload == payload_prev and not args.duplicate: continue
                payload_prev = rcv.payload
                rcv.decode_qzsl1s_qzqsm()
                if fp_raw:
                    print(rcv.qzqsm, file=fp_raw)
                    fp_raw.flush()
            elif args.inav and rcv.signame=='E1B':
                rcv.decode_galinav()
                if fp_raw and rcv.inav:
                    fp_raw.buffer.write(rcv.inav)
                    fp_raw.flush()
    except (BrokenPipeError, IOError):
        sys.exit()
    except KeyboardInterrupt:
        print(rcv.msg_color.fg('yellow') + "User break - terminated" + \
            rcv.msg_color.fg(), file=fp_disp)
        sys.exit()

# EOF
