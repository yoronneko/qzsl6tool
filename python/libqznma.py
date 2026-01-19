#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libqznma.py: library for decoding QZNMA
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023-2026 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office, Government of Japan, Quasi-Zenith Satellite System
#     Interface Specification Signal Authentication Service,
#     IS-QZSS-SAS-001 Draft-002, Jan. 24, 2023.

import sys

sys.path.append(__file__)
import libtrace

try:
    from bitstring import BitStream
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

L_RDS      = 576  # length of RDS in bits
L_RESERVED = 543  # length of reserved bits in bits
L_SIGNAT   = 512  # length of signature in bits
class Qznma:
    "Quasi-Zenith Satellite navigation authentication  message process class"
    def __init__(self, trace: libtrace.Trace) -> None:
        self.trace = trace
        self.rds1 = BitStream()
        self.rds2 = BitStream()

    def decode(self, payload: BitStream) -> str:
        '''decode reformat digital signature (RDS) in L6E
        [1] p.67 Fig.6-52, 6-53, and 6-54'''
        if len(payload) != 1695:
            raise Exception(f"QZNMA size error: {len(payload)} != 1695.")
        rds1     = payload.read(L_RDS)
        rds2     = payload.read(L_RDS)
        reserved = payload.read(L_RESERVED)
        if reserved.any(1):
            self.trace.show(2, f"QZNMA reserved dump: {reserved.bin}")
        message = ' ' + self.decode_rds(rds1) + self.decode_rds(rds2)
        return message

    def decode_rds(self, rds: BitStream) -> str:
        '''decodes reformat digital signature
        [1] p.43 Table 6-2 GPS LNAV RDS Message
        '''
        nma_id = rds.read( 4).b      # navigation message authentication ID
        rtow   = rds.read(20).u      # reference time of week
        svid   = rds.read( 8).u      # space vehicle ID
        mt     = rds.read( 4).u      # message type
        reph   = rds.read( 4).u      # reference ephemeris
        keyid  = rds.read( 8).u      # key ID
        signat = rds.read(L_SIGNAT)  # digital signature
        salt   = rds.read(16).u      # salt (true random number)
        message = ''
        if nma_id != '0000':         # NMA is not used
            message = self.trace.msg(0, '(inactive) ', dec='dark')
            if rds[4:].any(1):       # RDS field should be all zero
                self.trace.show(2,f'NMA_ID={nma_id}: {rds[4:]}\n')
            return message
        satsig = ''
        if svid == 0:
            message += self.trace.msg(0, '(null) ', dec='dark')
            return message
        elif   1 <= svid and svid <=  63: satsig += f'G{svid    :02d}'
        elif  65 <= svid and svid <= 127: satsig += f'E{svid-64 :02d}'
        elif 129 <= svid and svid <= 191: satsig += f'S{svid    :03d}'
        elif 193 <= svid and svid <= 202: satsig += f'J{svid-192:02d}'
        else:
            satsig += f'(unknown SVID{svid})'
        if   mt == 0b0001: satsig += '(LNAV) '
        elif mt == 0b0010: satsig += '(CNAV) '
        elif mt == 0b0011: satsig += '(CNAV2) '
        elif mt == 0b0100: satsig += '(F/NAV) '
        elif mt == 0b0101: satsig += '(I/NAV) '
        elif mt == 0: satsig += '(inactive)'
        else:
            satsig += f'(unknown message_type={mt}) '
        message += satsig
        self.trace.show(1, f'QZNMA {satsig}TOW={rtow} Eph={reph} KeyID={keyid} salt={salt}')
        self.trace.show(2, f'{signat.bin}')
        return message

# EOF
