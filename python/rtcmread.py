#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# rtcmread.py: RTCM message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
# Copyright (c) 2007-2020 by T.TAKASU
#
# The function of rtk_crc24q () is from rtkcmn.c of RTKLIB 2.4.3b34,
# https://github.com/tomojitakasu/RTKLIB
#
# Released under BSD 2-clause license.
#
# References:
# [1] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.
# [2] Global Positioning Augmentation Service Corporation (GPAS),
#     Quasi-Zenith Satellite System Correction Data on Centimeter Level
#     Augmentation Service for Experiment Data Format Specification,
#     1st ed., Nov. 2017, in Japanese.
#     http://file.gpas.co.jp/L6E_MADOCA_DataFormat.pdf
# [3] Global Positioning Augmentation Service Corporation (GPAS),
#     Interface specification for GPAS-MADOCA Product
#     https://www.gpas.co.jp/data/GPAS-MADOCA_Interface_Specification_en.pdf
# [4] Tomoji Takasu, RTKLIB: An Open Source Program Package for GNSS Positioning,
#     v.2.4.3b34, Apr. 2020.
#     https://github.com/tomojitakasu/RTKLIB

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import ecef2llh
import libeph
import libssr
import libtrace

try:
    import bitstring
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

class Rtcm:
    '''RTCM message process class'''

    readbuf = b''  # read buffer, used as static variable
    payload = bitstring.ConstBitStream()

    def __init__(self, trace):
        self.trace = trace
        self.eph   = libeph.Eph(trace)
        self.ssr   = libssr.Ssr(trace)

    def read(self):
        '''returns true if successfully reading an RTCM message'''
        BUFMAX = 1000  # maximum length of buffering RTCM message
        BUFADD =   20  # length of buffering additional RTCM message
        while True:
            if BUFMAX < len(self.readbuf):
                libtrace.err("RTCM buffer exhausted")
                return False
            b = sys.stdin.buffer.read(BUFADD)
            if not b:
                return False
            self.readbuf += b
            len_readbuf = len(self.readbuf)
            pos = 0
            found_sync = False
            while pos != len_readbuf and not found_sync:
                if self.readbuf[pos:pos+1] == b'\xd3':
                    found_sync = True
                else:
                    pos += 1
            if not found_sync:
                self.readbuf = b''
                continue
            if len_readbuf < pos + 3:
                self.readbuf = self.readbuf[pos:]
                continue
            bl = self.readbuf[pos+1:pos+3]              # possible message len
            mlen = int.from_bytes(bl, 'big') & 0x3ff
            if len_readbuf < pos + 3 + mlen + 3:
                self.readbuf = self.readbuf[pos:]
                continue
            bp = self.readbuf[pos+3:pos+3+mlen]         # possible payload
            bc = self.readbuf[pos+3+mlen:pos+3+mlen+3]  # possible CRC
            frame = b'\xd3' + bl + bp
            if bc != rtk_crc24q(frame, len(frame)):     # CRC error
                libtrace.err("CRC error")
                self.readbuf = self.readbuf[pos+1:]
                continue
            else:  # read properly
                self.readbuf = self.readbuf[pos+3+mlen+3:]
                break
        self.payload = bitstring.ConstBitStream(bp)
        return True

    def decode(self):
        msgnum = self.payload.read('u12')  # message number
        satsys = msgnum2satsys(msgnum)
        mtype  = msgnum2mtype(msgnum)
        msg = self.trace.msg(0, f'RTCM {msgnum} ', fg='green') + self.trace.msg(0, f'{satsys:1} {mtype:14}', fg='yellow')
        if mtype == 'Ant Rcv info':
            msg += self.decode_ant_info(self.payload, msgnum)
        elif mtype == 'Position':
            msg += self.decode_antenna_position(self.payload, msgnum)
        elif mtype == 'Code bias':
            msg += self.decode_code_phase_bias(self.payload)
        elif 'Obs' in mtype:
            msg += self.decode_obs(self.payload, satsys, mtype)
        elif 'MSM' in mtype:
            msg += self.decode_msm(self.payload, satsys, mtype)
        elif 'NAV' in mtype:
            msg += self.eph.decode_ephemerides(self.payload, satsys, mtype)
        elif mtype == 'CSSR':
            # determine CSSR before SSR, otherwise CSSR is never selected
            self.payload.pos = 0  # reset bit position
            msg += self.ssr.decode_cssr(self.payload)  # needs message type info
        elif mtype == 'Raw CSSR':
            self.payload.pos = len(self.payload.bin)  # cannot decode raw CSSR, skip it
        elif 'SSR' in mtype:
            self.ssr.ssr_decode_head(self.payload, satsys, mtype)
            if mtype == 'SSR orbit':
                msg += self.ssr.ssr_decode_orbit(self.payload, satsys)
            elif mtype == 'SSR clock':
                msg += self.ssr.ssr_decode_clock(self.payload, satsys)
            elif mtype == 'SSR code bias':
                msg += self.ssr.ssr_decode_code_bias(self.payload, satsys)
            elif mtype == 'SSR URA':
                msg += self.ssr.ssr_decode_ura(self.payload, satsys)
            elif mtype == 'SSR hr clock':
                msg += self.ssr.ssr_decode_hr_clock(self.payload, satsys)
            else:
                msg += f'unknown SSR message: {msgnum} {mtype}'
        else:
            msg += f'unknown message: {mtype}'
            self.payload.pos = len(self.payload.bin)  # skip unknown message
        if self.payload.pos % 8 != 0:  # byte align
            self.payload.pos += 8 - (self.payload.pos % 8)
        if self.payload.pos != len(self.payload.bin):
            msg += self.trace.msg(0, f' packet size mismatch: expected {len(self.payload.bin)}, actual {self.payload.pos}', fg='red')
        self.trace.show(0, msg)

    def decode_antenna_position(self, payload, msgnum):
        ''' returns decoded position and antenna height if available '''
        stid  = payload.read(12).u  # station id, DF003
        payload.pos +=  6            # reserved ITRF year, DF921
        payload.pos +=  1            # GPS indicator, DF022
        payload.pos +=  1            # GLO indicator, DF023
        payload.pos +=  1            # reserved GAL indicator, DF024
        payload.pos +=  1            # reference station ind, DF141
        px  = payload.read(38).i    # ARP ECEF-X, DF025
        payload.pos +=  1            # single receiver osc ind, DF142
        payload.pos +=  1            # reserved, DF001
        py  = payload.read(38).i    # ARP ECEF-Y, DF026
        payload.pos +=  2            # quarter cycle indicator, DF364
        pz  = payload.read(38).i    # ARP ECEF-Z, DF027
        ahgt =  0
        if msgnum == 1006:  # antenna height for RTCM 1006
            ahgt = payload.read(16).u  # antenna height, DF028
        msg = ''
        if stid != 0:
            msg += f'{stid} '
        lat, lon, height = ecef2llh.ecef2llh(px*1e-4, py*1e-4, pz*1e-4)
        msg += f'{lat:.7f} {lon:.7f} {height:.3f}'
        if ahgt != 0:
            msg += f'(+{ahgt*1e-4:.3f})'
        return msg

    def decode_ant_info(self, payload, msgnum):
        '''returns decoded antenna and receiver information '''
        str_ant = ''
        str_ser = ''
        str_rcv = ''
        str_ver = ''
        str_rsn = ''
        stid = payload.read(12).u      # station id, DF0003
        cnt  = payload.read( 8).u      # antenna descriptor counter, DF029
        for _ in range(cnt):
            str_ant += chr(payload.read(8).u)  # antenna descriptor, DF030
        ant_setup = payload.read(8).u          # antenna setup id, DF031
        if msgnum == 1008 or msgnum == 1033:
            cnt = payload.read(8).u    # antenna serial number couner, DF032
            for _ in range(cnt): str_ser += chr(payload.read(8).u)  # antenna ser num, DF033
        if msgnum == 1033:
            cnt = payload.read(8).u    # receiver type descriptor counter, DF227
            for _ in range(cnt): str_rcv += chr(payload.read(8).u)  # rec. type. desc., DF228
            cnt = payload.read(8).u    # receiver firmware counter, DF229
            for _ in range(cnt): str_ver += chr(payload.read(8).u)  # receier firmware, DF230
            cnt = payload.read(8).u    # receiver serial number counter, DF231
            for _ in range(cnt): str_rsn += chr(payload.read(8).u)  # antenna serial number, DF232
        msg = ''
        if stid      !=  0: disp_msg += f'{stid} '
        msg += f'{str_ant}'
        if ant_setup !=  0: msg += f' {ant_setup}'
        if str_ser   != '': msg += f' s/n {str_ser}'
        if str_rcv   != '': msg += f' rcv "{str_rcv}"'
        if str_ver   != '': msg += f' ver {str_ver}'
        if str_rsn   != '': msg += f' s/n {str_rsn}'
        return msg

    def decode_code_phase_bias(self, payload):
        '''decodes code-and-phase bias for GLONASS'''
        sid  = payload.read(12).u  # reference station id, DF003
        cpbi = payload.read( 1).u  # code-phase bias ind, DF421
        payload.pos += 3            # reserved, DF001
        mask = payload.read( 4).u  # FDMA signal mask, DF422
        l1ca = payload.read(16).i  # L1 C/A code-phase bias, DF423
        l1p  = payload.read(16).i  # L1 P code-phase bias, DF424
        l2ca = payload.read(16).i  # L2 C/A code-phase bias, DF425
        l2p  = payload.read(16).i  # L2 P  code-phase bias, DF426
        return f'L1CA={l1ca*0.02} L1P={l1p*0.02} L2CA={l2ca*0.02} L2P={l2p*0.02}'

    def decode_obs(self, payload, satsys, mtype):
        ''' decodes observation message and returns message '''
        be = 30 if satsys != 'R' else 27  # bit format of epoch time
        bp = 24 if satsys != 'R' else 25  # bit format of pseudorange
        bi =  8 if satsys != 'R' else  7  # bit format of pseudorange mod ambiguity
        sid   = payload.read(12).u  # reference station id, DF003
        tow   = payload.read(be).u  # epoch time, DF004 (GPS), DF034 (GLONASS)
        sync  = payload.read( 1).u  # synchronous flag, DF005
        nsat  = payload.read( 5).u  # number of signals, DF006 (GPS)
        smind = payload.read( 1).u  # divrgence-free smoothing ind, DF007
        smint = payload.read( 3).u  # smoothing interval, DF008
        msg = ''
        for _ in range(nsat):
            satid     = payload.read( 6).u  # satellite id, DF009, DF038
            cind1     = payload.read( 1).u  # L1 code indicator, DF010, DF039
            if satsys == 'R':
                fc    = payload.read( 5).u  # freq. channel number, DF040
            pr1       = payload.read(bp).u  # L1 pseudorange, DF011, DF041
            phpr1     = payload.read(20).i  # L1 phaserange-pseudorange, DF012, DF042
            lti1      = payload.read( 7).u  # L1 locktime ind, DF013, DF043
            if 'Full' in mtype:
                pma1  = payload.read(bi).u  # L1 pseudorange modulus ambiguity, DF014, DF044
                cnr1  = payload.read( 8).u  # L1 CNR, DF015, DF045
            if 'L2' in mtype:
                cind2 = payload.read( 2).u  # L2 code indicator, DF016, DF046
                prd   = payload.read(14).i  # L2-L1 pseudorange difference, DF017, DF047
                phpr2 = payload.read(20).i  # L2 phaserange-L1 pseudorange, DF018, DF048
                lti2  = payload.read( 7).u  # L2 locktime ind, DF019, DF049
                if mtype in 'Full':
                    cnr2  = payload.read( 8).u  # L2 CNR, DF020, DF050
            if satsys != 'S':
                msg += f'{satsys}{satid:02} '
            else:
                msg += f'{satsys}{satid+119:3} '
        return msg

    def decode_msm(self, payload, satsys, mtype):
        ''' decodes MSM message and returns message '''
        sid    = payload.read(12).u  # reference station id, DF003
        epoch  = payload.read(30).u  # GNSS epoch time, DF004
        mm     = payload.read( 1).u  # multiple message bit, DF393
        iods   = payload.read( 3).u  # issue of data station, DF409
        payload.pos += 7              # reserved, DF001
        csi    = payload.read( 2).u  # clock steering ind, DF411
        eci    = payload.read( 2).u  # external clock ind, DF412
        smind  = payload.read( 1).u  # divergence-free smoothing ind, DF417
        smint  = payload.read( 3).u  # smoothing interval, DF418
        sat_mask = [0 for _ in range(64)]
        nsat = 0
        for satid in range(64):
            mask = payload.read(1).u  # satellite mask, DF394
            if mask:
                sat_mask[nsat] = satid
                nsat += 1
        sig_mask = [0 for _ in range(32)]
        nsig = 0
        for sigid in range(32):
            mask = payload.read(1).u  # signal mask, DF395
            if mask:
                sig_mask[nsig] = sigid
                nsig += 1
        cell_mask = [0 for _ in range(nsat * nsig)]
        n_cell_mask = 0
        for maskpos in range(nsat * nsig):
            mask = payload.read(1).u  # cell mask, DF396
            cell_mask[maskpos] = mask
            if mask:
                n_cell_mask += 1
        if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
            for _ in range(nsat):
                rng  = payload.read(8).u   # rough ranges, DF398
        if '5' in mtype or '7' in mtype:
            for _ in range(nsat):
                einf = payload.read(4).u   # sat specific extended info
        for _ in range(nsat):
            rng_m    = payload.read(10).u  # range mod 1 ms, DF398
        if '5' in mtype or '7' in mtype:
            for _ in range(nsat):
                prr  = payload.read(14).i  # phase range rates, DF399
        for maskpos in range(nsat * nsig):
            if not cell_mask[maskpos]:
                continue
            bfpsr = 15  # bit length of fine pseudorange
            bfphr = 22  # bit length of fine phaserange
            blti  =  4  # bit length of lock time indicator
            bcnr  =  6  # bit length of CNR
            if '6' in mtype or '7' in mtype:
                bfpsr = 20  # extended bit length for fine pseudorange
                bfphr = 24  # extended bit length for fine phaserange
                blti  = 10  # extended bit length for lock time indicator
                bcnr  = 10  # extended bit length for CNR
            if '1' in mtype or '3' in mtype or '4' in mtype or \
               '5' in mtype or '6' in mtype or '7' in mtype:
                fpsr = payload.read(bfpsr).i  # fine pseudorange, DF400, DF405
            if '2' in mtype or '3' in mtype or '4' in mtype or \
               '5' in mtype or '6' in mtype or '7' in mtype:
                fphr = payload.read(bfphr).i  # fine phaserange, DF401, DF406
                lti  = payload.read( blti).u  # lock time ind, DF402, DF407
                hai  = payload.read(    1).u  # half-cycle ambiguity, DF420
            if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
                cnr  = payload.read( bcnr).u  # CNR, DF403, 408
            if '5' in mtype or '7' in mtype:
                fphr = payload.read(15).i  # fine phaserange rate, DF404
        msg = ''
        if satsys != 'S':
            for satid in range(nsat):
                msg += f'{satsys}{sat_mask[satid]+1:02} '
        else:
            for satid in range(nsat):
                msg += f'{satsys}{sat_mask[satid]+119:3} '
        return msg

def send_rtcm(fp, rtcm_payload):
    if not fp:
        return
    r = rtcm_payload.tobytes()
    rtcm = b'\xd3' + len(r).to_bytes(2, 'big') + r
    rtcm_crc = rtk_crc24q(rtcm, len(rtcm))
    fp.buffer.write(rtcm)
    fp.buffer.write(rtcm_crc)
    fp.flush()

def msgnum2satsys(msgnum):  # message number to satellite system
    satsys = ''
    if   msgnum in {1001, 1002, 1003, 1004, 1019, 1071, 1072, 1073, 1074,
             1075, 1076, 1077, 1057, 1058, 1059, 1060, 1061, 1062, 11}:
        satsys = 'G'
    elif msgnum in {1009, 1010, 1011, 1012, 1020, 1081, 1081, 1082, 1083,
            1084, 1085, 1086, 1087, 1063, 1064, 1065, 1066, 1067,
            1068, 1230}:
        satsys = 'R'
    elif msgnum in {1045, 1046, 1091, 1092, 1093, 1094, 1095, 1096, 1097,
            1240, 1241, 1242, 1243, 1244, 1245, 12}:
        satsys = 'E'
    elif msgnum in {1044, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1246,
            1247, 1248, 1249, 1250, 1251, 13}:
        satsys = 'J'
    elif msgnum in {1042, 63, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1258,
            1259, 1260, 1261, 1262, 1263, 14}:
        satsys = 'C'
    elif msgnum in {1101, 1102, 1103, 1104, 1105, 1106, 1107}:
        satsys = 'S'
    elif msgnum in {1041, 1131, 1132, 1133, 1134, 1135, 1136, 1137}:
        satsys = 'I'
    return satsys

def msgnum2mtype(msgnum):  # message number to message type
    mtype = f'MT{msgnum:<4d}'
    if   msgnum in {1001, 1009}                  : mtype = 'Obs L1'
    elif msgnum in {1002, 1010}                  : mtype = 'Obs Full L1'
    elif msgnum in {1003, 1011}                  : mtype = 'Obs L1L2'
    elif msgnum in {1004, 1012}                  : mtype = 'Obs Full L1L2'
    elif msgnum in {1019, 1020, 1044, 1042, 1041, 63}: mtype = 'NAV'
    elif msgnum == 1230                          : mtype = 'Code bias'
    elif msgnum == 1045                          : mtype = 'F/NAV'
    elif msgnum == 1046                          : mtype = 'I/NAV'
    elif (1071 <= msgnum and msgnum <= 1077) or \
       (1081 <= msgnum and msgnum <= 1087) or \
       (1091 <= msgnum and msgnum <= 1097) or \
       (1101 <= msgnum and msgnum <= 1137)       : mtype = f'MSM{msgnum % 10}'
    elif msgnum in {1057, 1063, 1240, 1246, 1258}: mtype = 'SSR orbit'
    elif msgnum in {1058, 1064, 1241, 1247, 1259}: mtype = 'SSR clock'
    elif msgnum in {1059, 1065, 1242, 1248, 1260}: mtype = 'SSR code bias'
    elif msgnum in {1060, 1066, 1243, 1249, 1261}: mtype = 'SSR obt/clk'
    elif msgnum in {1061, 1067, 1244, 1250, 1262}: mtype = 'SSR URA'
    elif msgnum in {1062, 1068, 1245, 1251, 1263}: mtype = 'SSR hr clock'
    elif msgnum in {11, 12, 13, 14}              : mtype = 'SSR phase bias'
    elif msgnum in {1007, 1008, 1033}            : mtype = 'Ant Rcv info'
    elif msgnum in {1005, 1006}                  : mtype = 'Position'
    elif msgnum == 4073                          : mtype = 'CSSR'
    elif msgnum == 4050                          : mtype = 'Raw CSSR'
    return mtype

# following code is from RTKLIB 2.4.3b34 [4], rtkcmn.c

tbl_CRC24Q = [
0x000000,0x864CFB,0x8AD50D,0x0C99F6,0x93E6E1,0x15AA1A,0x1933EC,0x9F7F17,
0xA18139,0x27CDC2,0x2B5434,0xAD18CF,0x3267D8,0xB42B23,0xB8B2D5,0x3EFE2E,
0xC54E89,0x430272,0x4F9B84,0xC9D77F,0x56A868,0xD0E493,0xDC7D65,0x5A319E,
0x64CFB0,0xE2834B,0xEE1ABD,0x685646,0xF72951,0x7165AA,0x7DFC5C,0xFBB0A7,
0x0CD1E9,0x8A9D12,0x8604E4,0x00481F,0x9F3708,0x197BF3,0x15E205,0x93AEFE,
0xAD50D0,0x2B1C2B,0x2785DD,0xA1C926,0x3EB631,0xB8FACA,0xB4633C,0x322FC7,
0xC99F60,0x4FD39B,0x434A6D,0xC50696,0x5A7981,0xDC357A,0xD0AC8C,0x56E077,
0x681E59,0xEE52A2,0xE2CB54,0x6487AF,0xFBF8B8,0x7DB443,0x712DB5,0xF7614E,
0x19A3D2,0x9FEF29,0x9376DF,0x153A24,0x8A4533,0x0C09C8,0x00903E,0x86DCC5,
0xB822EB,0x3E6E10,0x32F7E6,0xB4BB1D,0x2BC40A,0xAD88F1,0xA11107,0x275DFC,
0xDCED5B,0x5AA1A0,0x563856,0xD074AD,0x4F0BBA,0xC94741,0xC5DEB7,0x43924C,
0x7D6C62,0xFB2099,0xF7B96F,0x71F594,0xEE8A83,0x68C678,0x645F8E,0xE21375,
0x15723B,0x933EC0,0x9FA736,0x19EBCD,0x8694DA,0x00D821,0x0C41D7,0x8A0D2C,
0xB4F302,0x32BFF9,0x3E260F,0xB86AF4,0x2715E3,0xA15918,0xADC0EE,0x2B8C15,
0xD03CB2,0x567049,0x5AE9BF,0xDCA544,0x43DA53,0xC596A8,0xC90F5E,0x4F43A5,
0x71BD8B,0xF7F170,0xFB6886,0x7D247D,0xE25B6A,0x641791,0x688E67,0xEEC29C,
0x3347A4,0xB50B5F,0xB992A9,0x3FDE52,0xA0A145,0x26EDBE,0x2A7448,0xAC38B3,
0x92C69D,0x148A66,0x181390,0x9E5F6B,0x01207C,0x876C87,0x8BF571,0x0DB98A,
0xF6092D,0x7045D6,0x7CDC20,0xFA90DB,0x65EFCC,0xE3A337,0xEF3AC1,0x69763A,
0x578814,0xD1C4EF,0xDD5D19,0x5B11E2,0xC46EF5,0x42220E,0x4EBBF8,0xC8F703,
0x3F964D,0xB9DAB6,0xB54340,0x330FBB,0xAC70AC,0x2A3C57,0x26A5A1,0xA0E95A,
0x9E1774,0x185B8F,0x14C279,0x928E82,0x0DF195,0x8BBD6E,0x872498,0x016863,
0xFAD8C4,0x7C943F,0x700DC9,0xF64132,0x693E25,0xEF72DE,0xE3EB28,0x65A7D3,
0x5B59FD,0xDD1506,0xD18CF0,0x57C00B,0xC8BF1C,0x4EF3E7,0x426A11,0xC426EA,
0x2AE476,0xACA88D,0xA0317B,0x267D80,0xB90297,0x3F4E6C,0x33D79A,0xB59B61,
0x8B654F,0x0D29B4,0x01B042,0x87FCB9,0x1883AE,0x9ECF55,0x9256A3,0x141A58,
0xEFAAFF,0x69E604,0x657FF2,0xE33309,0x7C4C1E,0xFA00E5,0xF69913,0x70D5E8,
0x4E2BC6,0xC8673D,0xC4FECB,0x42B230,0xDDCD27,0x5B81DC,0x57182A,0xD154D1,
0x26359F,0xA07964,0xACE092,0x2AAC69,0xB5D37E,0x339F85,0x3F0673,0xB94A88,
0x87B4A6,0x01F85D,0x0D61AB,0x8B2D50,0x145247,0x921EBC,0x9E874A,0x18CBB1,
0xE37B16,0x6537ED,0x69AE1B,0xEFE2E0,0x709DF7,0xF6D10C,0xFA48FA,0x7C0401,
0x42FA2F,0xC4B6D4,0xC82F22,0x4E63D9,0xD11CCE,0x575035,0x5BC9C3,0xDD8538
]

# CRC24Q for RTCM3, (1+x)(x^23+x^17+x^13+x^12+x^11+x^9+x^8+x^7+x^5+x^3+1)

def rtk_crc24q(buff, length):
    crc = 0
    for i in range(length):
        crc = ((crc << 8) & 0xffffff) ^ tbl_CRC24Q[(crc >> 16) ^ buff[i]]
    return crc.to_bytes(3, 'big')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='RTCM message read')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=subtype detail, 2=subtype and bit image.')
    args = parser.parse_args()
    fp_disp = sys.stdout       # message display file pointer
    if args.trace < 0:
        libtrace.err(f'trace level should be positive ({args.trace}).')
        sys.exit(1)
    trace = libtrace.Trace(fp_disp, args.trace, args.color)
    rtcm = Rtcm(trace)
    try:
        while rtcm.read():
            rtcm.decode()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
