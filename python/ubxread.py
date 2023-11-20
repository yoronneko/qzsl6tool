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
from alstread import checksum
from septread import u4perm

try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    QZS L6 Tool needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)

LEN_L1S = 250   # message length of L1S and SBAS
SIGNAME_TBL = [ # signal name table: (gnssid, signae) -> signal name
    ['L1CA', '', '', 'L2CL', 'L2CM', '', 'L5I', 'L5Q'],             # GPS
    ['L1CA'],                                                       # SBAS
    ['E1C', 'E1B', '', 'E5aI', 'E5aQ', 'E5bI', 'E5bQ'],             # GAL
    ['B1I', 'B1I', 'B2I', 'B2I', '', 'B1C', '', 'B2a'],             # BDS
    [],                                                             # undefined
    ['L1CA', 'L1S', '', '', 'L2CM', 'L2CL', '', '', 'L5I', 'L5Q'],  # QZS
    ['L1OF', '', 'L2OF'],                                           # GLO
    ['L5'],                                                         # IRN
]

class UbxReceiver:
    gpstime  = 18  # GPS time
    gpsweek  =  0  # GPS week
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
        #if   gnssid == 0:  # GPS
        #    signame = ['L1CA', '', '', 'L2CL', 'L2CM', '', 'L5I', 'L5Q'][sigid]
        #elif gnssid == 1:  # SBAS
        #    signame = 'L1CA'
        #elif gnssid == 2:  # GAL
        #    signame = ['E1C', 'E1B', '', 'E5aI', 'E5aQ', 'E5bI', 'E5bQ'][sigid]
        #elif gnssid == 3:  # BDS
        #    signame = ['B1I', 'B1I', 'B2I', 'B2I', '', 'B1C', '', 'B2a'][sigid]
        #elif gnssid == 5:  # QZS
        #    signame = ['L1CA', 'L1S', '', '', 'L2CM', 'L2CL', '', '', 'L5I', 'L5Q'][sigid]
        #elif gnssid == 6:  # GLO
        #    signame = ['L1OF', '', 'L2OF'][sigid]
        #elif gnssid == 7:  # IRN
        #    signame = 'L5'
        #else:
        #    signame = f'ID{sigid}'
        try:
            signame = SIGNAME_TBL[gnssid][sigid]
        except:
            signame = f'ID{sigid}'
        payload_perm = bytearray(n_word * 4)
        u4perm(payload, payload_perm)
        self.svid     = svid
        self.gnssname = gnssname
        self.signame  = signame
        self.satname  = f'{gnssname}{svid:02d}'
        self.payload  = bitstring.ConstBitStream(payload_perm)
        self.msg      = \
            self.msg_color.fg('green')  + f'{self.satname:4s} ' + \
            self.msg_color.fg('yellow') + f'{self.signame:4s} ' + \
            self.msg_color.fg() + f'{rcv.payload.hex}'
        return True

    def decode_qzsl1s(self):
        prn = self.svid
        if self.signame == 'L1S':
            prn = self.svid + 182
        l1s = bitstring.BitStream()
        if not self.prn_prev:
            l1s += bitstring.Bits(uint=prn, length=8)
            self.prn_prev = prn
        l1s += bitstring.Bits(uint=self.gpsweek, length=12)
        l1s += bitstring.Bits(uint=self.gpstime, length=20)
        l1s += self.payload[:LEN_L1S]
        self.l1s = l1s.tobytes()

    def decode_qzsl1s_qzqsm(self):
        l1s = self.payload
        l1s.bytealign()
        prn = self.svid + 182
        sentence = f'QZQSM,{prn-128},{l1s.hex}'
        cksum = functools.reduce(operator.xor, (ord(s) for s in sentence), 0)
        self.qzqsm = f'${sentence}*{cksum:02x}' 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='u-blox message read')
    parser.add_argument('--l1s',
        help='send QZS L1S messages to stdout', action='store_true')
    parser.add_argument('--sbas',
        help='send SBAS messages to stdout', action='store_true')
    parser.add_argument('--qzqsm',
        help='send NMEA messages of QZS L1S DCR to stdout', action='store_true')
    parser.add_argument('--duplicate',
        help='allow duplicate NMEA sentences of QZS L1S DCR (all QZS sats send the same DCR messages)', action='store_true')
    #parser.add_argument('-s', '--sbas',
    #    help='SBAS', action='store_true')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    args = parser.parse_args()
    fp_disp, fp_raw = sys.stdout, None
    if args.qzqsm or args.l1s or args.sbas:
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
    except (BrokenPipeError, IOError):
        sys.exit()
    except KeyboardInterrupt:
        print(rcv.msg_color.fg('yellow') + "User break - terminated" + \
            rcv.msg_color.fg(), file=fp_disp)
        sys.exit()

# EOF