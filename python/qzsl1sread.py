#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# qzsl1sread.py: quasi-zenith satellite (QZS) L1S message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023-2024 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office, Government of Japan, Submeter-level augentation
#     service archive, https://sys.qzss.go.jp/dod/archives/slas.html
# [2] Cabinet Office, Government of Japan, Quasi-zenith satellite system
#     interface specification DC report service, IS-QZSS-DCR-011,
#     Oct. 18 2023.
# [3] Cabinet Office, Government of Japan, Quasi-zenith satellite system
#     interface specification Sub-meter level augmentation service,
#     IS-QZSS-L1S-006, Oct. 25, 2023

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libgnsstime
from   librtcm import rtk_crc24q
import libtrace

try:
    import bitstring
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

L_L1S = 250  # length of L1S and SBAS in bits
L_PAB =   8  # length of preamble in bits
L_MT  =   6  # length of message type in bits
L_DF  = 212  # length data field in bits, ref.[3], pp.13, Fig.4.1.1.-1
L_CRC =  24  # length of CRC in bits
GMS2NAME = {  # GMS code, ref.[3], Table 4.1.2-4
    #  station       lat   lon    height
     0: "Sapporo"    , # 43.15 141.22  50
     1: "Sendai"     , # 38.27 140.74 200
     3: "Hitachiota" , # 36.58 140.55 150
     5: "Komatsu"    , # 36.40 136.41  50
     6: "Kobe"       , # 34.71 135.04 200
     7: "Hiroshima"  , # 34.35 132.45  50
     8: "Fukuoka"    , # 33.60 130.23  50
     9: "Tanegashima", # 30.55 130.94 100
    10: "Amami"      , # 28.42 129.69  50
    11: "Itoman"     , # 26.15 127.69 100
    12: "Miyako"     , # 24.73 125.35 100
    13: "Ishigaki"   , # 24.37 124.13 100
    14: "Chichijima" , # 27.09 142.19 100
    63: "(unavail.)" , # (unavailable)
}
UNDEF = -1  # undefined value for IODP and IODI


class QzsL1s:
    iodp     = UNDEF  # PRN mask update number
    iodi     = UNDEF  # IOD updating number
    mask_prn = []     # satellite mask defined by MT48 (PRN mask)
    mask_sv  = []     # mask info for selected satellite defined by MT49 (data issue number)
    mask_uh  = []     # mask info for unhealthy satellite defined by MT51 (satellite health)
    iod      = [0 for _ in range(23)]  # data issue number

    def __init__(self, trace):
        self.trace = trace

    def decode_test_mode(self, df):  # ref.[3], sect.4.1.2.3, MT0
        ''' test mode messages solicit deleting previous messages stored in the receiver '''
        self.iodp     = UNDEF  # clear PRN mask update number
        self.iodi     = UNDEF  # clear IOD updating number
        self.mask_prn = []  # clear satellite mask defined by MT48 (PRN mask)
        self.mask_sv  = []  # clear selected satellite by MT49 (data issue number)
        self.mask_uh  = []  # clear unhealthy satellite by MT51 (satellite health)
        self.iod      = [0 for _ in range(23)]  # data issue number
        df.pos += L_DF
        return ''

    def decode_monitoring_station_info(self, df):  # ref.[3], sect.4.1.2.6, MT47
        ''' returns decoded message '''
        msg = self.trace.msg(1, "\nLocation    Lat[deg]   Lon[deg] Hgt[m]")
        for i in range(5):
            gms_code = df.read( 'u6')
            gms_lat  = df.read('i15')
            gms_lon  = df.read('i15')
            gms_hgt  = df.read( 'u6')
            if gms_code == 63: continue
            msg += self.trace.msg(1, f"\n{GMS2NAME.get(gms_code, 'undefined'):11s}   {gms_lat*0.005:6.3f}    {gms_lon*0.005+115.00:7.3f}   {gms_hgt*50-100:4d}")
        df.pos += 2  # spare
        return msg

    def decode_prn_mask(self, df):  # ref.[3], sect.4.1.2.7, MT48
        ''' returns decoded message '''
        self.mask_prn = []         # clear satellite mask
        self.mask_sv  = []         # clear selected satellite
        self.mask_uh  = []         # clear unhealthy satellite
        self.iodp = df.read('u2')  # PRN mask update number
        for i in range(64):        # for GPS
            if df.read('u1'): self.mask_prn.append(f'G{i+1:02d}')
        for i in range( 9):        # for QZSS
            if df.read('u1'): self.mask_prn.append(f'J{i+1:02d}')
        for i in range(36):        # for GLONASS
            if df.read('u1'): self.mask_prn.append(f'R{i+1:02d}')
        for i in range(36):        # for Galileo
            if df.read('u1'): self.mask_prn.append(f'E{i+1:02d}')
        for i in range(36):        # for BeiDou
            if df.read('u1'): self.mask_prn.append(f'C{i+1:02d}')
        df.pos += 29               # spare
        msg = f": selected sats:"
        for sat in self.mask_prn:
            msg += " " + sat
        msg += f" ({len(self.mask_prn)} sats, IODP={self.iodp})"
        return msg

    def decode_satellite_health(self, df):  # ref.[3], sect.4.1.2.10, MT51
        ''' returns decoded message '''
        self.mask_uh = []    # clear unhealthy satellite
        df.pos += 2          # spare
        for i in range(64):  # for GPS
            if not df.read('u1'): self.mask_uh.append(f'G{i:02d}')
        for i in range( 9):  # for QZSS
            if not df.read('u1'): self.mask_uh.append(f'J{i:02d}')
        for i in range(36):  # for GLONASS
            if not df.read('u1'): self.mask_uh.append(f'R{i:02d}')
        for i in range(36):  # for Galileo
            if not df.read('u1'): self.mask_uh.append(f'E{i:02d}')
        for i in range(36):  # for BeiDou
            if not df.read('u1'): self.mask_uh.append(f'C{i:02d}')
        df.pos += 29         # spare
        msg = ": lockout sats:"
        for sat in self.mask_uh:
            msg += " " + sat
        msg += f" ({len(self.mask_uh)} sats)"
        return msg

    def decode_data_issue_number(self, df):  # ref.[3], sect.4.1.2.8, MT49
        ''' returns decoded message '''
        mask_sv   = [0 for _ in range(23)]  # selected satellite
        iod       = [0 for _ in range(23)]  # data issue number
        iodi = df.read('u2')                # IOD updating number
        for i in range(23):
            mask_sv[i] = df.read('u1')
        for i in range(23):
            iod[i] = df.read('u8')
        iodp = df.read('u2')
        df.pos += 1  # spare
        if iodp != self.iodp:
            return self.trace.msg(0, f": IODP mismatch {iodp} != {self.iodp}", dec='dark')
        msg = f': IODI={iodi} IODP={self.iodp}'
        msg += self.trace.msg(1, "\nPRN IOD")
        count = 0
        self.mask_sv = []
        for i, sat in enumerate(self.mask_prn):
            if mask_sv[i]:
                self.mask_sv.append(sat)
                msg += self.trace.msg(1, f"\n{sat} {iod[i]:3d}")
                count += 1
        self.iodi = iodi
        self.iod  = iod
        msg += self.trace.msg(1, "\n")
        msg += self.trace.msg(0, f" ({count} sats)")

        return msg

    def decode_dgps_correction(self, df):  # ref.[3], sect.4.1.2.9, MT50
        ''' returns decoded message '''
        iodp       = df.read('u2')  # PRN mask updating number
        iodi       = df.read('u2')  # IOD updating number
        gms_code   = df.read('u6')  # monitoring station code
        gms_health = df.read('u1')  # monitoring station health
        mask_dgps  = [False for _ in range(23)]  # mask selected satellite
        for i in range(23):
            mask_dgps[i] = df.read('u1')  # mask selected satellite
        prc = [0 for _ in range(14)]      # pseudorange correcion
        for i in range(14):
            prc[i] = df.read('i12')       # pseudorange correction
        df.pos += 10                      # spare
        if self.iodp == UNDEF:
            return self.trace.msg(0, " (waiting for PRN mask, MT48)", dec='dark')
        if self.iodi == UNDEF:
            return self.trace.msg(0, " (waiting for data issue number, MT49)", dec='dark')
        if iodp != self.iodp:
            return self.trace.msg(0, f" (IODP mismatch: mask {self.iodp} != DGPS {iodp})", dec='dark')
        if iodi != self.iodi:
            return self.trace.msg(0, f" (IODI mismatch: mask {self.iodi} != DGPS {iodi})", dec='dark')
        msg = f": {GMS2NAME.get(gms_code, f'(unknown GMS code: {gms_code})')}"
        if gms_health:
           msg += self.trace.msg(0, " (unhealthy)", fg='red')   
        msg += self.trace.msg(1, "\nPRN PRC[m]")
        count = 0
        for i, sat in enumerate(self.mask_sv):
            if not mask_dgps[i]:
                continue
            msg += self.trace.msg(1, f"\n{sat} {prc[count]*0.04:6.2f}")
            if sat in self.mask_uh:
                msg += self.trace.msg(1, f"(unhealthy)", fg='red')
            count += 1
        msg += self.trace.msg(1, "\n")
        msg += self.trace.msg(0, f" ({count} sats)")
        return msg

    RC2NAME_EN = {     # report classification, ref.[2]
        1: "MaxPri",   # maximum priority
        2: "Priority", # priority
        3: "Normal",   # normal priority
        7: "Test",     # test
    }
    RC2NAME_JP = {
        1: "最優先",
        2: "優先",
        3: "通常",
        7: "訓練",
    }
    DC2NAME_EN = {  # disaster category, ref.[2]
         1: "Earthquake Early Warning",
         2: "Hypocenter",
         3: "Seismic Intensity",
         4: "Nankai Trough Earthquake",
         5: "Tsunami",
         6: "Northwest Pacific Tsunami",
         8: "Volcano",
         9: "Ash Fall",
        10: "Weather",
        11: "Flood",
        12: "Typhoon",
        14: "Marine",
    }
    DC2NAME_JP = {
         1: "緊急地震速報",
         2: "震源",
         3: "震度",
         4: "震南海トラフ地震",
         5: "津波",
         6: "北西太平洋津波",
         8: "火山",
         9: "降灰",
        10: "気象",
        11: "洪水",
        12: "台風",
        14: "海上",
    }
    IT2NAME_EN = {  # information type, ref.[2]
        0: "issue",
        1: "correction",
        2: "cancel",
    }
    IT2NAME_JP = {
        0: "発表",
        1: "訂正",
        2: "取消",
    }

    def decode_dcr (self, df):
        ''' returns decoded message
            Japan Meteorological Agency Disaster and Crisis Management Report
            ref.[2]
        '''
        rc   = df.read('u3')  # report classification, ref.[2], pp.12, Fig 4.1.2-1
        dc   = df.read('u4')  # disaster classification
        atmo = df.read('u4')  # month
        atda = df.read('u5')  # day
        atho = df.read('u5')  # hour
        atmi = df.read('u6')  # minute
        it   = df.read('u2')  # information type
        data = df.read( 171)  # data that depends on the disaster
        vn   = df.read('u6')  # version
        if vn != 1:
            raise Exception(f"\nversion number should be 1 ({vn})")
        msg = f": {self.DC2NAME_EN.get(dc, 'undefined classification')}" + \
              f" ({self.RC2NAME_EN.get(rc, 'undefined priority')})"
        if it != 0:
            msg += f" {self.IT2NAME_EN.get(it, 'undefined information type')}"
        msg += f" {atmo:02d}-{atda:02d} {atho:02d}:{atmi:02d} UTC"
        return msg

    MT2NAME = {
         0: 'Test mode',
         1: 'PRN mask',
         2: 'Fast corrections 1',
         3: 'Fast corrections 2',
         4: 'Fast corrections 3',
         5: 'Fast corrections 4',
         6: 'Integrity information',
         7: 'Fast correction degradation factor',
         9: 'GEO ranging function parameters',
        10: 'Degradation parameters',
        12: 'SBAS network time/UTC offset parameters',
        17: 'GEO satellite almanacs',
        18: 'Ionospheric grid point masks',
        24: 'Mixed fast/long-term satellite corrections',
        25: 'Long-term satellite error corrections',
        26: 'Ionospheric delay corrections',
        27: 'SBAS service message',
        28: 'Clock-ephemeris covariance matrix',
        43: 'DCR',
        44: 'DCX',
        47: 'Monitoring station information',
        48: 'PRN mask',
        49: 'Data issue number',
        50: 'DGPS correction',
        51: 'Satellite health',
        63: 'Null message',
    }

    def decode_l1s (self, l1s):
        ''' returns decoded message '''
        pab = l1s.read(L_PAB)  # preamble (8 bit), ref.[3], Fig.4.1.1-1
        mt  = l1s.read(L_MT)   # message type (6 bit)
        df  = l1s.read(L_DF)   # data field (212 bit)
        crc = l1s.read(L_CRC)  # crc24, ref.[3] pp., sect.4.1.1.3
        pad = bitstring.Bits('uint6=0')  # padding for byte alignment
        frame = (pad + pab + mt + df).tobytes()
        crc_test = rtk_crc24q(frame, len(frame))
        if crc.tobytes() != crc_test:
            msg = self.trace.msg(0, f"CRC error {crc_test.hex()} != {crc.hex}", fg='red')
            return msg
        mt_name = self.MT2NAME.get(mt.u, f"MT {mt.u}")
        msg = self.trace.msg(0, mt_name, fg='cyan')
        if   mt_name == 'Test mode':                       # MT0
            msg += self.decode_test_mode(df)
        elif mt_name == 'DCR':                             # MT43
            msg += self.decode_dcr(df)
        elif mt_name == 'Monitoring station information':  # MT47
            msg += self.decode_monitoring_station_info(df)
        elif mt_name == 'PRN mask':                        # MT48
            msg += self.decode_prn_mask(df)
        elif mt_name == 'Data issue number':               # MT49
            msg += self.decode_data_issue_number(df)
        elif mt_name == 'DGPS correction':                 # MT50
            msg += self.decode_dgps_correction(df)
        elif mt_name == 'Satellite health':                # MT51
            msg += self.decode_satellite_health(df)
        return msg

def read_from_l1s_file(qzsl1s, l1s_file, fp_disp):
    ''' reads and interprets L1S file, and displays the contents
        format: [PRN(8)]
                [GPS week(12)][GPS tow(20)][L1S RAW(250)][padding(6)]...
    '''
    with open(l1s_file, 'r') as f:
        prn = int.from_bytes (f.buffer.read(1), 'big')
        if not prn:
            sys.exit(0)
        if fp_disp:
            print (f"PRN {prn}", file=fp_disp)
        raw = f.buffer.read(36)
        while raw:
            payload = bitstring.ConstBitStream(raw)
            gpsweek = payload.read('u12')
            gpstow  = payload.read('u20')
            l1s     = payload.read(L_L1S)
            payload.pos += 6  # spare
            msg = qzsl1s.trace.msg(0, libgnsstime.gps2utc(gpsweek, gpstow), fg='green') + \
                ': ' + qzsl1s.decode_l1s(l1s)
            qzsl1s.trace.show(0, msg)
            raw = f.buffer.read(36)

def read_from_stdin(qzsl1s,  fp_disp):
    ''' reads and interprets stdin data, and displays the contents
        format: [PRN(8)][L1S RAW(250)][padding(6)]...
    '''
    raw = sys.stdin.buffer.read(33)
    while raw:
        payload = bitstring.ConstBitStream(raw)
        prn = payload.read('u8')
        l1s = payload.read(L_L1S)
        payload.pos += 6  # spare
        msg = qzsl1s.trace.msg(0, f'PRN{prn:3d}', fg='green') + \
            ': ' + qzsl1s.decode_l1s(l1s)
        qzsl1s.trace.show(0, msg)
        raw = sys.stdin.buffer.read(33)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Quasi-zenith satellite (QZS) L1S message read')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=subtype detail, 2=subtype and bit image.')
    parser.add_argument(
        'l1s_files', metavar='file', nargs='*', default=None,
        help='L1S file(s) obtained from the QZS archive, https://sys.qzss.go.jp/dod/archives/slas.html')
    args = parser.parse_args()
    fp_disp = sys.stdout
    trace = libtrace.Trace(fp_disp, args.trace, args.color)
    qzsl1s = QzsL1s(trace)
    try:
        if args.l1s_files:  # read from file(s)
            for l1s_file in args.l1s_files:
                read_from_l1s_file(qzsl1s, l1s_file, fp_disp)
        else:               # read from stdin
            read_from_stdin(qzsl1s, fp_disp)
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
