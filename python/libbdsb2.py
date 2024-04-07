#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libbsdb2.py: library for BeiDou B2b message processing
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
# [3] Tomoji Takasu, Pocket SDR -An Open-Source GNSS SDR, ver. 0.11,
#     https://github.com/tomojitakasu/PocketSDR

# change this to 1 if you use 64-ary LDPC function of Pocket SDR (ref.[3])
POCKET_SDR_LDPC = 0

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libssr
import libtrace
import libgnsstime

try:
    import bitstring
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

try:
    if POCKET_SDR_LDPC:
        import sdr_ldpc
        import numpy as np
except ModuleNotFoundError:
    POCKET_SDR_LDPC = 0

PREAMBLE_BCNAV3 = b'\xeb\x90'  # preamble for BDS B2b message
LEN_BCNAV3      = 125          # BDS CNAV3 page size is 1000 sym (125 byte)

def rtk_crc24(data):
    ''' calculate CRC24 for BDS B2b message
        g(x) = x^24 + x^23 + x^18 + x^17 + x^14 + x^11 + x^10 + x^7 + x^6 + x^5 + x^4 + x^3 + x + 1
        data:   data to be calculated
    '''
    crc = 0
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            if crc & 0x800000:
                crc = (crc << 1) ^ 0x864cfb
            else:
                crc = crc << 1
            crc &= 0xffffff
    return crc.to_bytes(3, 'big')

def slot2satname(slot):
    ''' returns satellite name from mask slot
        slot: satellite slot position
            slot   1- 63: BDS
            slot  64-100: GPS
            slot 101-137: GAL
            slot 138-174: GLO
            slot 175-255: reserved
    '''
    if   1 <= slot and slot <=  63:  # BDS has 63 satellites
        return f'C{slot:02d}'
    if  64 <= slot and slot <= 100:  # GPS has 37 satellites
        return f'G{slot-63:02d}'
    if 100 <= slot and slot <= 137:  # GAL has 37 satellites
        return f'E{slot-99:02d}'
    if 138 <= slot and slot <= 174:  # GLO has 37 satellites
        return f'R{slot-137:02d}'
    raise Exception(f"mask position should be 1-174 (actual {slot}).")

def sigmask2signame(satsys, sigmask):
    ''' convert satellite system and signal mask to signal name '''
    signame = f'satsys={satsys} sigmask={sigmask}'
    if   satsys == 'C':
        signame = ["B1I", "B1C(D)", "B1C(P)", "Reserved", "B2a(D)", "B2a(P)", "Reserved", "B2b-I", "B2b-Q", "Reserved", "Reserved", "Reserved", "B3 I", "Reserved", "Reserved", "Reserved"][sigmask]
    elif satsys == 'G':
        signame = ["L1 C/A", "L1 P", "Reserved", "Reserved", "L1C(P)", "L1C(D+P)", "Reserved", "L2C(L)", "L2C(M+L)", "Reserved", "Reserved", "L5 I", "L5 Q", "L5 I+Q", "Reserved", "Reserved"][sigmask]
    elif satsys == 'R':
        signame = ["G1 C/A", "G1 P", "G2 C/A", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved"][sigmask]
    elif satsys == 'E':
        signame = ["Reserved", "E1 B", "E1 C", "Reserved", "E5a Q", "E5a I", "Reserved", "E5b I", "E5b Q", "Reserved", "Reserved", "E6 C", "Reserved", "Reserved", "Reserved", "Reserved"][sigmask]
    else:
        raise Exception(
            f'unassigned signal name for satsys={satsys} and sigmask={sigmask}')
    return signame

class BdsB2():
    epoch  = 0  # epoch in second within one BDT day
    iodssr = 0  # issue of data indicating configuration change of data generation
    iodp   = 0  # issue of data indicating the PRN mask change
    mask   = bitstring.BitStream(255)  # satellite mask

    def __init__(self, trace, stat):
        self.trace = trace
        self.stat  = stat
        self.ssr   = libssr.Ssr(trace)

    def __del__(self):
        if self.stat:
            self.ssr.show_cssr_stat()

    def decode(self, raw, prn_s):
        rawb = bitstring.ConstBitStream(raw)
        preamble   = rawb.read( 16)
        prn        = rawb.read(  6).u
        rawb.pos   += 6  # reserved
        b2b_data   = rawb.read(486)
        b2b_parity = rawb.read(486)
        mestype = b2b_data.read(  6)
        mesdata = b2b_data.read(456)
        crc     = b2b_data.read( 24)
        if prn_s != 0 and prn_s != prn:
            return ''
        msg = self.trace.msg(0, f'C{prn:02d}', fg='green') + \
              self.trace.msg(0, f' MT{mestype.u:<2d}', fg='yellow') + ' '
        if preamble != PREAMBLE_BCNAV3:
            msg += self.trace.msg(0, f"Preamble error {preamble.hex} != {PREAMBLE_BCNAV3.hex()}", fg='red')
            self.trace.show(0, msg)
            self.trace.show(2, mesdata.hex)
            return
        if POCKET_SDR_LDPC:  # if Pocket SDR (ref.[3]) LDPC python module is available
            syms = np.fromstring((b2b_data + b2b_parity).bin, 'u1') - ord('0')
            bits, _ = sdr_ldpc.decode_LDPC_BCNV3(syms)
            b2b_data = bitstring.Bits(bits)[:486]
        pad = bitstring.Bits('uint2=0')  # padding for byte alignment
        frame = (pad + mestype + mesdata).tobytes()
        crc_test = rtk_crc24(frame)
        if crc.tobytes() != crc_test:
            msg += self.trace.msg(0, f"CRC error {crc_test.hex()} != {crc.hex}", fg='red')
            self.trace.show(0, msg)
            self.trace.show(2, mesdata.hex)
            return
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
            msg += self.trace.msg(0, "(unknown message type) ", fg='yellow')
        self.trace.show(0, msg)
        # self.trace.show(2,  mesdata.hex)

    def decode_b2b_1(self, mesdata):
        ''' decode B2b message type 1
            satellite mask
        '''
        self.epoch  = mesdata.read( 17).u
        mesdata.pos += 4  # reserved
        self.iodssr = mesdata.read(  2).u
        iodp        = mesdata.read(  4).u
        self.mask   = mesdata.read(255)
        mesdata.pos += 174  # reserved
        msg = self.trace.msg(0, f'MASK  {libssr.epoch2time(self.epoch)} IODSSR={self.iodssr} IODP={iodp}', fg='cyan')
        if iodp != self.iodp:
            msg += self.trace.msg(0, ' (updated)', fg='yellow')
            self.iodp = iodp
        msg += self.trace.msg(1, '\n')
        for maskpos in range(174):
            if self.mask[maskpos]:
                msg += self.trace.msg(1, f' {slot2satname(maskpos+1)}')
        msg += self.trace.msg(2, f'\nMask: {self.mask.bin}')
        return msg

    def decode_b2b_2(self, mesdata):
        ''' decode B2b message type 2
            satellite orbit correction and user range accuracy index
        '''
        epoch     = mesdata.read(17).u
        mesdata.pos += 4  # reserved
        iodssr    = mesdata.read( 2).u
        msg = self.trace.msg(0, f'ORBIT {libssr.epoch2time(epoch)} IODSSR={iodssr}', fg='cyan')
        if iodssr != self.iodssr:
            msg += self.trace.msg(0, ' IODSSR mismatch', dec='dark')
            return msg
        msg += self.trace.msg(1, '\nSAT IODN IODCorr radial[m] along[m] cross[m] URA[mm]')
        for _ in range(6):
            slot    = mesdata.read( 9).u
            iodn    = mesdata.read(10).u
            iodcorr = mesdata.read( 3).u
            radial  = mesdata.read(15).i
            along   = mesdata.read(13).i
            cross   = mesdata.read(13).i
            urai    = mesdata.read( 6)
            if slot == 0:
                continue
            msg += self.trace.msg(1, f'\n{slot2satname(slot)} {iodn:{libssr.FMT_IODE}} {iodcorr:7d}   {radial*0.0016:{libssr.FMT_ORB}}  {along*0.0064:{libssr.FMT_ORB}}  {cross*0.0064:{libssr.FMT_ORB}} {libssr.ura2dist(urai):{libssr.FMT_URA}}')
        mesdata.pos += 19  # reserved
        return msg

    def decode_b2b_3(self, mesdata):
        ''' decode B2b message type 3
            differential code bias
        '''
        epoch     = mesdata.read(17).u
        mesdata.pos += 4  # reserved
        iodssr    = mesdata.read( 2).u
        numsat    = mesdata.read( 5).u
        msg = self.trace.msg(0, f'CODE  {libssr.epoch2time(epoch)} IODSSR={iodssr} numsat={numsat}', fg='cyan')
        if iodssr != self.iodssr:
            msg += self.trace.msg(0, ' IODSSR mismatch', dec='dark')
            return msg
        msg += self.trace.msg(1, f'\nSAT {"Signal Code":{libssr.FMT_GSIG}} Code Bias[m]')
        for _ in range(numsat):
            slot  = mesdata.read( 9).u
            numcb = mesdata.read( 4).u
            satname = slot2satname(slot)
            satsys = satname[0]
            for _ in range(numcb):
                sigcode = mesdata.read( 4).u
                cb      = mesdata.read(12).i
                msg += self.trace.msg(1, f'\n{satname} {sigmask2signame(satsys, sigcode):{libssr.FMT_GSIG}}      {cb*0.017:{libssr.FMT_CB}}')
        return msg

    def decode_b2b_4(self, mesdata):
        ''' decode B2b message type 4
            satellite clock correction
        '''
        msg = ''
        epoch    = mesdata.read(17).u
        mesdata.pos += 4  # reserved
        iodssr   = mesdata.read( 2).u
        iodp     = mesdata.read( 4).u
        st1      = mesdata.read( 5).u
        msg = self.trace.msg(0, f'CLOCK {libssr.epoch2time(epoch)} IODSSR={iodssr} IODP={iodp}', fg='cyan')
        if iodssr != self.iodssr:
            msg += self.trace.msg(0, ' IODSSR mismatch', dec='dark')
            return msg
        if iodp != self.iodp:
            msg += self.trace.msg(0, ' IODP mismatch', dec='dark')
            return msg
        if 11 < st1:
            msg += self.trace.msg(0, f' ST1={st1} out of range', dec='dark')
            return msg
        msg += self.trace.msg(1, '\nSAT IODCorr clock[m]')
        maskpos = st1 * 23
        for _ in range(23):
            iodcorr = mesdata.read( 3).u
            c0      = mesdata.read(15).i
            if self.mask[maskpos] and c0 != -16383:
                msg += self.trace.msg(1, f'\n{slot2satname(maskpos+1)} {iodcorr:7d}  {c0*0.0016:{libssr.FMT_CLK}}')
            maskpos += 1
        mesdata.pos += 10  # reserved
        return msg

    def decode_b2b_5(self, mesdata):
        ''' decode B2b message type 5
            user range accuracy index
        '''
        epoch   = mesdata.read(17).u
        mesdata.pos += 4  # reserved
        iodssr  = mesdata.read( 2).u
        iodp    = mesdata.read( 4).u
        st2     = mesdata.read( 3).u
        msg = self.trace.msg(0, f'URA   {libssr.epoch2time(epoch)} IODSSR={iodssr} IODP={iodp}', fg='cyan')
        if iodssr != self.iodssr:
            msg += self.trace.msg(0, ' IODSSR mismatch', dec='dark')
            return msg
        if iodp != self.iodp:
            msg += self.trace.msg(0, ' IODP mismatch', dec='dark')
            return msg
        if 3 < st2:
            msg += self.trace.msg(0, f' ST2={st2} out of range', dec='dark')
            return msg
        msg += self.trace.msg(1, '\nSAT URA[mm]')
        maskpos = st2 * 70
        for _ in range(70):
            urai = mesdata.read( 6)
            if self.mask[maskpos]:
                continue
            msg += self.trace.msg(1, f'\n{slot2satname(maskpos+1)} {libssr.ura2dist(urai):{libssr.FMT_URA}}')
        mesdata.pos += 6  # reserved
        return msg

    def decode_b2b_6(self, mesdata):
        ''' decode B2b message type 6
            clock coreection and orbit correction - combination 1
        '''
        numc   = mesdata.read( 5).u
        numo   = mesdata.read( 3).u
        msg    = self.trace.msg(0, f'CLK&ORB1 numc={numc} numo={numo}', fg='cyan')
        cepoch = mesdata.read(17).u
        mesdata.pos += 4  # reserved
        iodssr = mesdata.read( 2).u
        iodp   = mesdata.read( 4).u
        slot_s = mesdata.read( 9).u
        msg += self.trace.msg(1, f'\nCLOCK  {libssr.epoch2time(cepoch)} IODSSR={iodssr}', fg='cyan')
        if iodssr != self.iodssr:
            msg += self.trace.msg(0, ' IODSSR mismatch', dec='dark')
            return msg
        if iodp != self.iodp:
            msg += self.trace.msg(0, ' IODP mismatch', dec='dark')
            return msg
        msg += self.trace.msg(1, '\nSAT IODCorr clock[m]')
        for _ in range(numc):
            iodcorr = mesdata.read( 3).u
            c0      = mesdata.read(15).i
            msg += self.trace.msg(1, f'\n{slot2satname(slot_s)} {iodcorr} {c0*0.0016:{libssr.FMT_CLK}}m')
            slot_s += 1
        oepoch = mesdata.read(17).u
        mesdata.pos += 4  # reserved
        iodssr = mesdata.read( 2).u
        msg += self.trace.msg(0, f'\nORBIT {libssr.epoch2time(oepoch)} IODSSR={iodssr}', fg='cyan')
        if iodssr != self.iodssr:
            msg += self.trace.msg(0, ' IODSSR mismatch', dec='dark')
            return msg
        msg += self.trace.msg(1, '\nSAT IODN IODCorr radial[m] along[m] cross[m] URA[mm]')
        for _ in range(numo):
            slot    = mesdata.read( 9).u
            iodn    = mesdata.read(10).u
            iodcorr = mesdata.read( 3).u
            radial  = mesdata.read(15).i
            along   = mesdata.read(13).i
            cross   = mesdata.read(13).i
            urai    = mesdata.read( 6)
            if slot == 0:
                continue
            msg += self.trace.msg(1, f'\n{slot2satname(slot)} {iodn:{libssr.FMT_IODE}} {iodcorr:7d} {radial*0.0016:{libssr.FMT_ORB}} {along*0.0064:{libssr.FMT_ORB}} {cross*0.0064:{libssr.FMT_ORB}}')
            accuracy = libssr.ura2dist(urai)
            if accuracy != libssr.URA_INVALID:
                msg += self.trace.msg(1, f'{accuracy:{libssr.FMT_URA}}')
        return msg

    def decode_b2b_7(self, mesdata):
        ''' decode B2b message type 7
            clock coreection and orbit correction - combination 2
        '''
        numc   = mesdata.read( 5).u
        numo   = mesdata.read( 3).u
        msg    = self.trace.msg(0, f'CLK&ORB2 numc={numc} numo={numo}', fg='cyan')
        cepoch = mesdata.read(17).u
        mesdata.pos += 4
        iodssr = mesdata.read( 2).u
        msg    = self.trace.msg(1, f'\nCLOCK  {libssr.epoch2time(cepoch)} IODSSR={iodssr}', fg='cyan')
        if iodssr != self.iodssr:
            msg += self.trace.msg(0, ' IODSSR mismatch', dec='dark')
            return msg
        msg += self.trace.msg(1, '\nSAT IODCorr clock[m]')
        for _ in range(numc):
            slot    = mesdata.read( 9).u
            iodcorr = mesdata.read( 3).u
            c0      = mesdata.read(15).i
            if slot == 0:
                continue
            msg += self.trace.msg(1, f'\n{slot2satname(slot)} {iodcorr:7d} {c0*0.0016:{libssr.FMT_CLK}}')
        oepoch = mesdata.read(17).u
        mesdata.pos += 4
        iodssr = mesdata.read( 2).u
        msg += self.trace.msg(0, f'\nORBIT {libssr.epoch2time(oepoch)} IODSSR={iodssr}', fg='cyan')
        if iodssr != self.iodssr:
            msg += self.trace.msg(0, ' IODSSR mismatch', dec='dark')
            return msg
        msg += self.trace.msg(1, '\nSAT IODN IODCorr radial[m] along[m] cross[m] URA[mm]')
        for _ in range(numo):
            slot    = mesdata.read( 9).u
            iodn    = mesdata.read(10).u
            iodcorr = mesdata.read( 3).u
            radial  = mesdata.read(15).i
            along   = mesdata.read(13).i
            cross   = mesdata.read(13).i
            urai    = mesdata.read( 6)
            if slot == 0:
                continue
            msg += self.trace.msg(1, f'\n{slot2satname(slot)} {iodn:{libssr.FMT_IODE}} {iodcorr} {radial*0.0016:{libssr.FMT_ORB}} {along*0.0064:{libssr.FMT_ORB}} {cross*0.0064:{libssr.FMT_ORB}} {libssr.ura2dist(urai):{libssr.FMT_URA}}')
        return msg

    def decode_b2b_10(self, mesdata):
        ''' decode B2b message type 10
            ephemeris, DIF1, SIF1, AIF1, SISMA
        '''
        sow          = mesdata.read(20).u
        mesdata.pos += 4  # reserved
        # ephemeris 1 (203 bit)
        toe          = mesdata.read(11).u
        sattype      = mesdata.read( 2).u
        delta_a      = mesdata.read(26).i
        dot_a        = mesdata.read(25).i
        delta_n0     = mesdata.read(17).i
        delta_dot_n0 = mesdata.read(23).i
        M0           = mesdata.read(33).i
        e            = mesdata.read(33).i
        omega        = mesdata.read(33).i
        # ephemeris 2 (222 bit)
        Omega_0      = mesdata.read(33).i
        delta_i0     = mesdata.read(33).i
        dot_Omega    = mesdata.read(19).i
        dot_i0       = mesdata.read(15).i
        Cis          = mesdata.read(16).i
        Cic          = mesdata.read(16).i
        Crs          = mesdata.read(24).i
        Crc          = mesdata.read(24).i
        Cus          = mesdata.read(21).i
        Cuc          = mesdata.read(21).i 
        # parameters
        dif1         = mesdata.read( 1).u
        sif1         = mesdata.read( 1).u
        aif1         = mesdata.read( 1).u
        sisma        = mesdata.read( 1).u
        msg = self.trace.msg(0, f'EPH  {libssr.epoch2timedate(sow)} TOE={toe} sattype={sattype}', fg='cyan')
        return msg

    def decode_b2b_30(self, mesdata):
        ''' decode B2b message type 30
            Clock, TGD, Ionosphere, BDT-UTC, EOP, SISA, HS
        '''
        sow = mesdata.read(20).u
        wn  = mesdata.read(13).u
        mesdata.pos += 4  # reserved
        # clock correction parameters (69 bit)
        toc = mesdata.read(11).u
        a0  = mesdata.read(25).i
        a1  = mesdata.read(22).i
        a2  = mesdata.read(11).i
        # TGD
        tgd = mesdata.read(12).i
        # ionospheric delay correction model parameters (74 bit)
        alpha1 = mesdata.read(10).i
        alpha2 = mesdata.read( 8).i
        alpha3 = mesdata.read( 8).i
        alpha4 = mesdata.read( 8).i
        alpha5 = mesdata.read( 8).i
        alpha6 = mesdata.read( 8).i
        alpha7 = mesdata.read( 8).i
        alpha8 = mesdata.read( 8).i
        alpha9 = mesdata.read( 8).i
        # BDT-UTC parameters (97 bit)
        a0_utc     = mesdata.read(16).i
        a1_utc     = mesdata.read(13).i
        a2_utc     = mesdata.read( 7).i
        delta_tls  = mesdata.read( 8).i
        tot        = mesdata.read(16).i
        wnot       = mesdata.read(13).i
        wnlsf      = mesdata.read(13).i
        dn         = mesdata.read( 3).i
        delta_tlsf = mesdata.read( 8).i
        # EOP (earth orientation parameters) (138 bit)
        t_eop         = mesdata.read(16).u
        pm_x          = mesdata.read(21).i
        pm_x_dot      = mesdata.read(15).i
        pm_y          = mesdata.read(21).i
        pm_y_dot      = mesdata.read(15).i
        delta_ut1     = mesdata.read(31).i
        delta_ut1_dot = mesdata.read(19).i
        # SISAIoc (22 bit)
        top      = mesdata.read(11).u
        sisaiocb = mesdata.read( 5).u
        sisaioc1 = mesdata.read( 3).u
        sisaioc2 = mesdata.read( 3).u
        # SISAIoe & HS
        sisaioe  = mesdata.read( 5).u
        hs       = mesdata.read( 2).u
        msg = self.trace.msg(0, f'CLK  {libgnsstime.gps2utc(wn, sow, "BDS")}', fg='cyan')
        return msg

    def decode_b2b_40(self, mesdata):
        ''' decode B2b message type 40
            BGT0, MidiAlmana, WNa
        '''
        sow = mesdata.read(20).u
        # BGT0 (68 bit)
        gnssid  = mesdata.read( 3).u
        wn0bgto = mesdata.read(13).u
        t0bgto  = mesdata.read(16).u
        a0bgto  = mesdata.read(16).i
        a1bgto  = mesdata.read(13).i
        a2bgto  = mesdata.read( 7).i
        # MidiAlmanac (156 bit)
        prn_a     = mesdata.read( 6).u
        sattype   = mesdata.read( 2).u
        wna       = mesdata.read(13).u
        toa       = mesdata.read( 8).u
        e         = mesdata.read(11).i
        delta_i   = mesdata.read(11).i
        sqrt_a    = mesdata.read(17).i
        Omega0    = mesdata.read(16).i
        dot_Omega = mesdata.read(11).i
        omega     = mesdata.read(16).i
        M0        = mesdata.read(16).i
        af0       = mesdata.read(11).i
        af1       = mesdata.read(10).i
        health    = mesdata.read( 8).u
        # WNa (13 bit)
        wna = mesdata.read(13).u
        # toa (8 bit)
        toa = mesdata.read( 8).u
        # Reduced Almanac (38 bit) x 5
        for _ in range(5):
            prn_a   = mesdata.read(6).u
            sattype = mesdata.read(2).u
            deltaA  = mesdata.read(8).i
            Omega0  = mesdata.read(7).i
            Phi0    = mesdata.read(7).i
            health  = mesdata.read(8).u
        msg = self.trace.msg(0, f'ALM  {libgnsstime.gps2utc(wn0bgto, t0bgto, "BDS")}', fg='cyan')
        return msg

    def decode_b2b_63(self, mesdata):
        ''' decode B2b null message type 63
            null message
        '''
        msg = self.trace.msg(0, 'NULL', fg='cyan')
        return msg

# EOF
