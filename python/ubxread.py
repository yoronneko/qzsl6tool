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
# [2] Tomoji Takasu, RTKLIB, http://github.com/tomojitakasu/RTKLIB,
#     rev.2.4.3 b34, Dec 2020.

import argparse
import datetime
import functools
import operator
import os
import sys

sys.path.append(os.path.dirname(__file__))
from   alstread import checksum
from   septread import u4perm
from   librtcm  import rtk_crc24q
import libtrace

try:
    import bitstring
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

LEN_L1CA = 300  # message length of GPS & QZS L1C/A, L2C, L5
LEN_L1OF =  85  # message length of GLO L1OF, L2OF
LEN_L1S  = 250  # message length of QZS L1S & SBAS L1C/A
LEN_B1I  = 300  # message length of BDS B1I, B2I

class UbxReceiver:
    payload_prev = bitstring.BitStream()  # previous payload

    def __init__(self, trace):
        self.trace = trace

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
                libtrace.err(f'ubx sfrbx version should be 2 ({ver})')
                continue
            if (msg_len-8)/4 != n_word:
                libtrace.err(f'numWord mismatch: {(msg_len-8)/4} != {n_word}')
                continue
            payload = sys.stdin.buffer.read(n_word * 4)
            csum    = sys.stdin.buffer.read(2)
            if not payload or not csum:
                return False
            csum1, csum2 = checksum(b'\x02\x13' + head + payload)
            if csum[0] != csum1 or csum[1] != csum2:
                libtrace.err(f'checksum error: {csum.hex()}!={csum1:02x}{csum2:02x}')
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
        self.prn      = svid + 182 if signame == 'L1S' else svid
        self.gnssname = gnssname
        self.signame  = signame
        self.satname  = f'{gnssname}{svid:02d}'
        if   signame == 'L1S' or gnssname == 'S':     # QZS L1S or SBAS L1C/A
            self.payload = bitstring.BitStream(payload_perm)[:LEN_L1S+6]
        elif signame == 'E1B' or signame == 'E5bI':   # GAL I/NAV
            inav = bitstring.BitStream(payload_perm)
            # undocumented u-blox I/NAV raw data structure solved in
            # ref.[2], src/rcv/ublox.c:785 (int decode_enav(.))
            inav = inav[:120-6] + inav[128:128+120-6]  # tail 6-bit are removed
            # CRC is calculated with 4-bit padding and 196-bit I/NAV
            inav_crc = (bitstring.Bits('uint4=0') + inav[:196]).tobytes()
            crc = inav[196:196+24].tobytes()
            crc_calc = rtk_crc24q(inav_crc, len(inav_crc))
            if crc != crc_calc:
                libtrace.err(f"CRC error {crc_calc.hex()} != {crc.hex()}")
            self.payload = inav + bitstring.Bits('uint4=0')
        elif signame == 'L1CA' or signame == 'L2CM':  # GPS or QZS L1C/A
            self.payload = bitstring.BitStream(payload_perm)[:LEN_L1CA+4]
        elif signame == 'L1OF' or signame == 'L2OF':  # GLO L1OF and L2OF
            self.payload = bitstring.BitStream(payload_perm)[:LEN_L1OF+3]
        elif signame == 'B1I' or signame == 'B2I':    # BDS B1I and B2I
            self.payload = bitstring.BitStream(payload_perm)[:LEN_B1I+4]
        else:
            raise Exception(f'unknown signal: {signame}')
        self.msg = \
            self.trace.msg(0, f'{self.satname:4s} ', fg='green') + \
            self.trace.msg(0, f'{self.signame:4s} ', fg='yellow') + \
            f'{self.payload.hex}'
        return True

    def decode_qzsl1s(self, args):
        ''' retruns decoded raww
            format: [PRN(8)][RAW(250)][padding(6)]...
        '''
        if (self.signame != 'L1S' and self.gnssname != 'S') or \
           (not args.duplicate and self.payload == self.payload_prev):
            return
        l1s = bitstring.BitStream(uint=self.prn, length=8) + self.payload
        self.payload_prev = self.payload
        return l1s.tobytes()

    def decode_qzsl1s_qzqsm(self, args):
        ''' returns decoded nmea text
            format: $QZQSM, [hex][hex]...[hex]*[checksum]
        '''
        if self.signame != 'L1S' or \
           (not args.duplicate and rcv.payload == payload_prev):
            return
        mt = self.payload[8:8+6].uint
        if mt != 43 and mt != 44:
            return
        self.payload_prev = self.payload
        sentence = f'QZQSM,{self.prn-128},{self.payload.hex}'
        cksum = functools.reduce(operator.xor, (ord(s) for s in sentence), 0)
        return bytes(f'${sentence}*{cksum:02x}\n', 'utf-8')

    def decode_galinav(self):
        ''' returns decoded raw (E1B only)
            format: [SVID(8)][I/NAV RAW(114x2)][padding(4)]...
        '''
        if self.signame != 'E1B':
            return
        inav = bitstring.BitStream(uint=self.svid, length=8) + self.payload
        return inav.tobytes()

    def decode_gnsslnav(self):
        ''' returns decoded raw
            format: [SVID(8)][L1C/A RAW(300)][padding(4)]...
        '''
        if self.signame != 'L1CA' or self.gnssname == 'S':
            return
        l1ca = bitstring.BitStream(uint=self.svid, length=8) + self.payload
        return l1ca.tobytes()

    def decode_glol1of(self):
        ''' returns decoded raw
            format: [SVID(8)][L1OF/L2OF RAW(300)][padding(3)]...
        '''
        if self.signame != 'L1OF' or self.signame != 'L2OF':
            return
        l1of = bitstring.BitStream(uint=self.svid, length=8) + self.payload
        return l1of.tobytes()

    def decode_bdsb1i(self):
        ''' returns decoded raw
            format: [SVID(8)][B1I/B2I RAW(300)][padding(4)]...
        '''
        if self.signame != 'B1I' or self.signame != 'B2I':
            return
        b1i = bitstring.BitStream(uint=self.svid, length=8) + self.payload
        return b1i.tobytes()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='u-blox message read')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--l1s', action='store_true',
        help='send QZS L1S messages to stdout')
    group.add_argument('--qzqsm', action='store_true',
        help='send QZS L1S DCR NMEA messages to stdout')
    group.add_argument('--sbas', action='store_true',
        help='send SBAS messages to stdout')
    group.add_argument('-l', '--lnav', action='store_true',
        help='send GNSS LNAV messages to stdout')
    group.add_argument('-i', '--inav', action='store_true',
        help='send GAL I/NAV messages to stdout')
    parser.add_argument('-d', '--duplicate', action='store_true',
        help='allow duplicate QZS L1S DCR NMEA sentences (currently, all QZS sats send the same DCR messages)')
    parser.add_argument('-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument('-m', '--message', action='store_true',
        help='show display messages to stderr')
    parser.add_argument('-p', '--prn', type=int, default=0,
        help='specify satellite PRN (PRN=0 means all sats)')
    args = parser.parse_args()
    fp_disp, fp_raw = sys.stdout, None
    if args.qzqsm or args.l1s or args.sbas or args.inav:
        fp_disp, fp_raw = None, sys.stdout
        payload_prev = bitstring.BitStream()
    if args.message:
        fp_disp = sys.stderr
    if args.prn < 0:
        libtrace.err(f"PRN must be positive ({args.prn})")
        sys.exit(1)
    trace = libtrace.Trace(fp_disp, 0, args.color)
    rcv = UbxReceiver(trace)
    try:
        while rcv.read():
            if args.prn != 0 and rcv.prn != args.prn: continue
            rcv.trace.show(0, rcv.msg)
            if fp_raw:
                if   args.l1s  : raw = rcv.decode_qzsl1s(args)
                elif args.qzqsm: raw = rcv.decode_qzsl1s_qzqsm(args)
                elif args.lnav : raw = rcv.decode_gnsslnav()
                elif args.inav : raw = rcv.decode_galinav()
                if raw:
                    fp_raw.buffer.write(raw)
                    fp_raw.flush()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
