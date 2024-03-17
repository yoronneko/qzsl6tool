#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libbsdb2.py: library for BeiDou B2B message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2024 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] China Satellite Navigation Office, BeiDou Navigation Satellite
#     System Signal In Space Interface Control Document, Precise Point
#     Positioning Service Signal PPP-B2b (Version 1.0),
#     BDS-SIS-ICD-PPP-B2b-1.0, July 2020.
# [2] China Satellite Navigation Office, BeiDou Navigation Satellite
#     System Signal In Space Interface Control Document, Open Service
#     Signal B2b (Version 1.0), BDS-SIS-ICD-OS-B2b-1.0, July 2020.

import argparse
import os
import sys

try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)

sys.path.append(os.path.dirname(__file__))
import libcolor
import libssr
from   librtcm import rtk_crc24q

PREAMBLE_BCNAV3 = b'\xeb\x90'  # preamble for BDS B2b message
LEN_BCNAV3      = 125  # BDS CNAV3 page size is 1000 sym (125 byte)

class BdsB2():
    def __init__(self, fp_disp, t_level, color, stat):
        self.fp_disp   = fp_disp
        self.t_level   = t_level
        self.msg_color = libcolor.Color(fp_disp, color)
        self.stat      = stat
        self.ssr       = libssr.Ssr(fp_disp, t_level, self.msg_color)

    def __del__(self):
        if self.stat:
            self.ssr.show_cssr_stat()

    def trace(self, level, *args):
        if self.t_level < level or not self.fp_disp:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_disp)
            except (BrokenPipeError, IOError):
                sys.exit()

    def decode(self, raw, prn_s):
        rawb = bitstring.ConstBitStream(raw)
        preamble   = rawb.read( 16)
        prn        = rawb.read(  6)
        rev        = rawb.read(  6)
        b2b_data   = rawb.read(486)
        b2b_parity = rawb.read(486 )
        mestype  = b2b_data.read(   6)
        mesdata  = b2b_data.read( 456)
        crc      = b2b_data.read(  24)
        if preamble != PREAMBLE_BCNAV3:
            return self.msg_color.fg('red') + "Preamble error" + self.msg_color.fg()
        if prn_s != 0 and prn_s != prn.u:
            return ''
        msg = self.msg_color.fg('green') + f'C{prn.u:02d}' + \
            self.msg_color.fg('yellow') + f' MT{mestype.u:<2d}' + \
            self.msg_color.fg() + ' '
        if   mestype.u ==  1: msg += self.decode_b2b_1 (mesdata)  # ref.[1], p.15, sect.6.2.2
        elif mestype.u ==  2: msg += self.decode_b2b_2 (mesdata)  # ref.[1], p.17, sect.6.2.3
        elif mestype.u ==  3: msg += self.decode_b2b_3 (mesdata)  # ref.[1], p.20, sect.6.2.4
        elif mestype.u ==  4: msg += self.decode_b2b_4 (mesdata)  # ref.[1], p.22, sect.6.2.5
        elif mestype.u ==  5: msg += self.decode_b2b_5 (mesdata)  # ref.[1], p.25, sect.6.2.6
        elif mestype.u ==  6: msg += self.decode_b2b_6 (mesdata)  # ref.[1], p.27, sect.6.2.7
        elif mestype.u ==  7: msg += self.decode_b2b_7 (mesdata)  # ref.[1], p.29, sect.6.2.8
        elif mestype.u == 10: msg += self.decode_b2b_10(mesdata)  # ref.[2], p.14, Fig.6-3
        elif mestype.u == 30: msg += self.decode_b2b_30(mesdata)  # ref.[2], p.14, Fig.6-4
        elif mestype.u == 40: msg += self.decode_b2b_40(mesdata)  # ref.[2], p.15, Fig.6-5
        elif mestype.u == 63: msg += self.decode_b2b_63(mesdata)  # ref.[1], p.31, sect.6.2.9
        else:
            msg += self.msg_color.fg('yellow') + f"Reserved message type {mestype.u}" + \
                self.msg_color.fg()
        pad = bitstring.Bits('uint2=0')  # padding for byte alignment
        frame = pad + mestype + mesdata
        crc_test = rtk_crc24q(frame, len(frame))
        if crc.tobytes() != crc_test:
            msg += self.msg_color.fg('red') + \
                f" CRC error {crc_test.hex()} != {crc.hex}" + \
                self.msg_color.fg()
        return msg

    def decode_b2b_1(self, mesdata):
        ''' decode B2b message type 1
            satellite mask
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_2(self, mesdata):
        ''' decode B2b message type 2
            satellite orbit correction and user range accuracy index
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_3(self, mesdata):
        ''' decode B2b message type 3
            differential code bias
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_4(self, mesdata):
        ''' decode B2b message type 4
            satellite clock correction
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_5(self, mesdata):
        ''' decode B2b message type 5
            user range accuracy index
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_6(self, mesdata):
        ''' decode B2b message type 6
            clock coreection and orbit correction - combination 1
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_7(self, mesdata):
        ''' decode B2b message type 7
            clock coreection and orbit correction - combination 2
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_10(self, mesdata):
        ''' decode B2b message type 10
            ephemeris, DIF1, SIF1, AIF1, SISMA
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_30(self, mesdata):
        ''' decode B2b message type 30
            Clock, TGD, Ionosphere, BDT-UTC, EOP, SISA, HS
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_40(self, mesdata):
        ''' decode B2b message type 40
            BGT0, MidiAlmana, WNa
        '''
        return mesdata.hex    # return as hex string

    def decode_b2b_63(self, mesdata):
        ''' decode B2b null message type 63
            null message
        '''
        return mesdata.hex    # return as hex string

# EOF
