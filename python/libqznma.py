#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libqznma.py: library for decoding QZNMA
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Signal Authentication Service,
#     IS-QZSS-SAS-001 Draft-002, Jan. 24, 2023.

import sys

try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    QZS L6 Tool needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)

sys.path.append(__file__)
import libcolor
import libssr

class Qznma:
    "Quasi-Zenith Satellite navigation authentication  message process class"
    def __init__(self, fp_disp, t_level, msg_color):
        self.fp_disp = fp_disp
        self.t_level = t_level
        self.msg_color = msg_color
        self.rds1 = bitstring.ConstBitStream()
        self.rds2 = bitstring.ConstBitStream()

    def decode(self, payload):
        '''decode reformat digital signature (RDS) in L6E
        [1] p.67 Fig.6-52, 6-53, and 6-54'''
        if len(payload) != 1695:
            raise Exception(f"QZNMA size error: {len(payload)} != 1695.")
        rds1     = payload.read(576)
        rds2     = payload.read(576)
        reserved = payload.read(543)
        if reserved.any(1):
            self.trace(2, f"QZNMA reserved dump: {reserved.bin}")
        message = '      '
        message += self.decode_rds(rds1)
        message += self.decode_rds(rds2)
        return message

    def trace(self, level, *args):
        if self.t_level < level or not self.fp_disp:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_disp)
            except (BrokenPipeError, IOError):
                sys.exit()

    def decode_rds(self, rds):
        '''decodes reformat digital signature
        [1] p.43 Table 6-2 GPS LNAV RDS Message
        '''
        pos = 0
        nma_id = rds.read( 'b4')
        rtow   = rds.read('u20')
        svid   = rds.read( 'u8')
        mt     = rds.read( 'u4')
        reph   = rds.read( 'u4')
        keyid  = rds.read( 'u8')
        signat = rds.read( 512 )
        salt   = rds.read('u16')
        message = ''
        if nma_id != '0000':
            message = self.msg_color.dec('dark') + '(inactive) ' + \
                self.msg_color.dec()
            if rds[4:].any(1):
                self.trace(2,f'NMA_ID={nma_id}: {rds[4:]}\n')
            return message
        satsig = ''
        if svid == 0:
            message += self.msg_color.dec('dark') + '(null) ' + \
                self.msg_color.dec()
            return message
        elif   1 <= svid and svid <=  63: satsig += f'G{svid    :02d}'
        elif  65 <= svid and svid <= 127: satsig += f'E{svid-64 :02d}'
        elif 129 <= svid and svid <= 191: satsig += f'S{svid    :03d}'
        elif 193 <= svid and svid <= 202: satsig += f'J{svid-192:02d}'
        else:
            raise Exception(f'unknown SVID{svid}')
        if   mt == 0b0001: satsig += '(LNAV) '
        elif mt == 0b0010: satsig += '(CNAV) '
        elif mt == 0b0011: satsig += '(CNAV2) '
        elif mt == 0b0100: satsig += '(F/NAV) '
        elif mt == 0b0101: satsig += '(I/NAV) '
        else:
            raise Exception(f'unknown message_type={mt}')
        message += satsig
        self.trace(1, f'QZNMA {satsig}',
                      f'TOW={rtow} Eph={reph} KeyID={keyid} salt={salt}\n')
        self.trace(2, f'{signat.bin}\n')
        return message

# EOF
