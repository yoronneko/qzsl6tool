#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# qzsl1sread.py: quasi-zenith satellite (QZS) L1S message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023-2026 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office, Government of Japan, Submeter-level augentation service archive, https://sys.qzss.go.jp/dod/archives/slas.html
# [2] Cabinet Office, Government of Japan, Quasi-zenith satellite system interface specification DC report service, IS-QZSS-DCR-011, Oct. 18 2023.
# [3] Cabinet Office, Government of Japan, Quasi-zenith satellite system interface specification Sub-meter level augmentation service, IS-QZSS-L1S-006, Oct. 25, 2023
# [4] Electric Navigation Research Institute, SBAS/L1-SAIF message specification, https://www.enri.go.jp/jp/research/organization/nav/program/message.html, in Japanese.
# [5] Cabinet Office, Government of Japan, Quasi-zenith satellite system interface specification DCX report service, IS-QZSS-DCX-004, May 2026.
# [6] Jiangyao Song, Ting Liu, Xiao Chen, Zhongwang Wu, "Satellite navigation message authentication in GNSS: research on message scheduler for SBAS L1," Sensors (Basel). 2024 Jan, https://pmc.ncbi.nlm.nih.gov/articles/PMC11154249/, doi: 10.3390/s24020360.

import argparse
import os
import sys
from typing import TextIO

sys.path.append(os.path.dirname(__file__))
import libgnsstime
import libqzsl6tool
import libtrace

try:
    from bitstring import BitStream
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

L_L1S : int = 250  # length of L1S and SBAS in bits
L_PAB : int =   8  # length of preamble in bits
L_MT  : int =   6  # length of message type in bits
L_DF  : int = 212  # length data field in bits, ref.[3], pp.13, Fig.4.1.1.-1
L_CRC : int =  24  # length of CRC in bits
UNDEF : int = -1   # undefined value for IODP and IODI
GMS2NAME: dict[int, str] = {  # GMS code, ref.[3], Table 4.1.2-4
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

class QzsL1s:
    def reset_all_variables(self) -> None:
        self.iodp_l1s      : int       = UNDEF  # PRN mask update number
        self.iodi_l1s      : int       = UNDEF  # IOD updating number
        self.mask_prn_l1s  : list[str] = []     # satellite mask defined by MT48 (PRN mask)
        self.mask_sv_l1s   : list[str] = []     # mask info for selected satellite defined by MT49 (data issue number)
        self.mask_uh_l1s   : list[str] = []     # mask info for unhealthy satellite defined by MT51 (satellite health)
        self.iod_l1s       : list[int] = [0 for _ in range(23)]  # data issue number
        self.iodp_sbas     : int       = UNDEF  # PRN mask update number
        self.iodp_sbas_prev: int       = UNDEF  # PRN mask update number
        self.iodi_sbas     : int       = UNDEF  # IOD updating number
        self.mask_prn_sbas : list[str] = []     # mask info for SBAS satellites defined by MT1 (PRN mask)
        self.mask_prn_sbas_prev: list[str] = [] # previous mask info for SBAS satellites defined by MT1 (PRN mask)
        self.total_igp     : int       = UNDEF   # The total number of IGP bands by MT18
        self.igp_mask      : list[BitStream] = [BitStream(201) for _ in range(11)]  # IGP mask for each band by MT18
        self.igp_mask_pat  : int       = UNDEF   # IGP mask pattern by MT18

    def __init__(self, trace: libtrace.Trace, jp: bool = False) -> None:
        self.trace = trace
        self.jp    = jp  # display DCR messages in Japanese
        self.reset_all_variables()  # initialize all variables

    def decode_test_mode(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.3, MT0
        ''' test mode messages solicit deleting previous messages stored in the receiver '''
        self.reset_all_variables()  # clear all variables
        df.pos += L_DF
        return ''

    def decode_monitoring_station_info(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.6, MT47
        ''' returns decoded message '''
        msg: str = self.trace.msg(1, "\nLocation    Lat[deg]   Lon[deg] Hgt[m]")
        for _ in range(5):
            gms_code = df.read( 6).u
            gms_lat  = df.read(15).i
            gms_lon  = df.read(15).i
            gms_hgt  = df.read( 6).u
            if gms_code == 63: continue
            msg += self.trace.msg(1, f"\n{GMS2NAME.get(gms_code, 'undefined'):11s}   {gms_lat*0.005:6.3f}    {gms_lon*0.005+115.00:7.3f}   {gms_hgt*50-100:4d}")
        df.pos += 2  # spare
        return msg

    def decode_prn_mask(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.7, MT48
        ''' returns decoded message '''
        self.mask_prn_l1s = []         # clear satellite mask
        self.mask_sv_l1s  = []         # clear selected satellite
        self.mask_uh_l1s  = []         # clear unhealthy satellite
        self.iodp_l1s = df.read(2).u   # PRN mask update number
        for i in range(64):        # for GPS
            if df.read(1).u: self.mask_prn_l1s.append(f'G{i+1:02d}')
        for i in range( 9):        # for QZSS
            if df.read(1).u: self.mask_prn_l1s.append(f'J{i+1:02d}')
        for i in range(36):        # for GLONASS
            if df.read(1).u: self.mask_prn_l1s.append(f'R{i+1:02d}')
        for i in range(36):        # for Galileo
            if df.read(1).u: self.mask_prn_l1s.append(f'E{i+1:02d}')
        for i in range(36):        # for BeiDou
            if df.read(1).u: self.mask_prn_l1s.append(f'C{i+1:02d}')
        df.pos += 29               # spare
        msg: str = f": selected sats:"
        for sat in self.mask_prn_l1s:
            msg += " " + sat
        msg += f" ({len(self.mask_prn_l1s)} sats, IODP={self.iodp_l1s})"
        return msg

    def decode_satellite_health(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.10, MT51
        ''' returns decoded message '''
        self.mask_uh_l1s = []    # clear unhealthy satellite
        df.pos += 2          # spare
        for i in range(64):  # for GPS
            if not df.read(1).u: self.mask_uh_l1s.append(f'G{i+1:02d}')
        for i in range( 9):  # for QZSS
            if not df.read(1).u: self.mask_uh_l1s.append(f'J{i+1:02d}')
        for i in range(36):  # for GLONASS
            if not df.read(1).u: self.mask_uh_l1s.append(f'R{i+1:02d}')
        for i in range(36):  # for Galileo
            if not df.read(1).u: self.mask_uh_l1s.append(f'E{i+1:02d}')
        for i in range(36):  # for BeiDou
            if not df.read(1).u: self.mask_uh_l1s.append(f'C{i+1:02d}')
        df.pos += 29         # spare
        msg: str = ": lockout sats:"
        for sat in self.mask_uh_l1s:
            msg += " " + sat
        msg += f" ({len(self.mask_uh_l1s)} sats)"
        return msg

    def decode_data_issue_number(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.8, MT49
        ''' returns decoded message '''
        mask_sv_l1s = [0 for _ in range(23)]  # selected satellite
        iod_l1s     = [0 for _ in range(23)]  # data issue number
        iodi_l1s    = df.read(2).u                 # IOD updating number
        for i in range(23):
            mask_sv_l1s[i] = df.read(1).u
        for i in range(23):
            iod_l1s[i] = df.read(8).u
        iodp_l1s = df.read(2).u
        df.pos += 1  # spare
        if iodp_l1s != self.iodp_l1s:
            return self.trace.msg(0, f": IODP mismatch: current {self.iodp_l1s} != received {iodp_l1s}", dec='dark')
        msg: str = f': IODI={iodi_l1s} IODP={self.iodp_l1s}'
        msg += self.trace.msg(1, "\nPRN IOD")
        count = 0
        self.mask_sv_l1s = []
        for i, sat in enumerate(self.mask_prn_l1s):
            if mask_sv_l1s[i]:
                self.mask_sv_l1s.append(sat)
                msg += self.trace.msg(1, f"\n{sat} {iod_l1s[i]:3d}")
                count += 1
        self.iodi_l1s = iodi_l1s
        self.iod_l1s  = iod_l1s
        msg += self.trace.msg(1, "\n")
        msg += self.trace.msg(0, f" ({count} sats)")
        return msg

    def decode_dgps_correction(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.9, MT50
        ''' returns decoded message '''
        iodp_l1s   = df.read(2).u  # PRN mask updating number
        iodi_l1s   = df.read(2).u  # IOD updating number
        gms_code   = df.read(6).u  # monitoring station code
        gms_health = df.read(1).u  # monitoring station health
        mask_dgps  = [False for _ in range(23)]  # mask selected satellite
        for i in range(23):
            mask_dgps[i] = bool(df.read(1).u)  # mask selected satellite
        prc = [0 for _ in range(14)]     # pseudorange correcion
        for i in range(14):
            prc[i] = df.read(12).i       # pseudorange correction
        df.pos += 10                     # spare
        if self.iodp_l1s == UNDEF:
            return self.trace.msg(0, " (waiting for PRN mask, MT48)", dec='dark')
        if self.iodi_l1s == UNDEF:
            return self.trace.msg(0, " (waiting for IODI, MT49)", dec='dark')
        if iodp_l1s != self.iodp_l1s:
            return self.trace.msg(0, f" (IODP mismatch: current {self.iodp_l1s} != received {iodp_l1s})", dec='dark')
        if iodi_l1s != self.iodi_l1s:
            return self.trace.msg(0, f" (IODI mismatch: current {self.iodi_l1s} != received {iodi_l1s})", dec='dark')
        msg: str = f": {GMS2NAME.get(gms_code, f'(unknown GMS code: {gms_code})')}"
        if gms_health:
           msg += self.trace.msg(0, " (unhealthy)", fg='red')   
        msg += self.trace.msg(1, "\nPRN PRC[m]")
        count = 0
        for i, sat in enumerate(self.mask_sv_l1s):
            if not mask_dgps[i]:
                continue
            msg += self.trace.msg(1, f"\n{sat} {prc[count]*0.04:6.2f}")
            if sat in self.mask_uh_l1s:
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

    def decode_dcr (self, df: BitStream) -> str:
        ''' returns decoded message
            Japan Meteorological Agency Disaster and Crisis Management Report (JMA DCR)
            ref.[2]
        '''
        rc   = df.read(  3).u  # report classification, ref.[2], pp.12, Fig 4.1.2-1
        dc   = df.read(  4).u  # disaster classification
        atmo = df.read(  4).u  # month
        atda = df.read(  5).u  # day
        atho = df.read(  5).u  # hour
        atmi = df.read(  6).u  # minute
        it   = df.read(  2).u  # information type
        data = df.read(171)    # data that depends on the disaster
        vn   = df.read(  6).u  # version
        dc2name = self.DC2NAME_JP if self.jp else self.DC2NAME_EN
        rc2name = self.RC2NAME_JP if self.jp else self.RC2NAME_EN
        it2name = self.IT2NAME_JP if self.jp else self.IT2NAME_EN
        msg = f": {dc2name.get(dc, 'undefined classification')}" + \
              f" ({rc2name.get(rc, 'undefined priority')})"
        if it != 0:
            msg += f" {it2name.get(it, 'undefined information type')}"
        msg += f" {atmo:02d}-{atda:02d} {atho:02d}:{atmi:02d} UTC"
        if vn != 1:
            msg += self.trace.msg(0, f"\nversion number should be 1 ({vn})", fg='red')
        return msg

    def decode_dcx(self, df: BitStream) -> str:  # ref.[4]
        ''' returns decoded message
            Disaster and Crisis Management Report - Extended (DCX)
            ref.[5]
        '''
        # Implementation for decoding DCX report goes here
        return ''

    def decode_sbas_prn_mask(self, df: BitStream) -> str:  # ref.[4]
        ''' returns decoded SBAS PRN mask message '''
        self.mask_prn_sbas_prev = self.mask_prn_sbas.copy()  # update satellite mask
        self.iodp_sbas_prev = self.iodp_sbas  # update previous IODP for SBAS
        self.mask_prn_sbas = []  # clear current satellite mask
        bitmask: BitStream = df.read(210)
        self.iodp_sbas     = df.read(2).u   # Issue of Data, PRN mask
        for i in range(37):  # for GPS
            if bitmask[i]:
                self.mask_prn_sbas.append(f'G{i+1:02d}')
        for i in range(24):  # for GLONASS
            if bitmask[37 + i]:
                self.mask_prn_sbas.append(f'R{i+1:02d}')
        for i in range(18):  # for SBAS
            if bitmask[119 + i]:
                self.mask_prn_sbas.append(f'S{i+120:02d}')
        msg: str = self.trace.msg(1, f"\nselected sats:")
        for sat in self.mask_prn_sbas:
            msg += self.trace.msg(1, " " + sat)
        msg += self.trace.msg(1, f" ({len(self.mask_prn_sbas)} sats, IODP={self.iodp_sbas})")
        return msg

    def decode_fast_correction(self, df: BitStream, id: int) -> str:  # ref.[4]
        ''' returns decoded Fast correction 2 message '''
        fc        = [0 for _ in range(13)]
        udrei     = [0 for _ in range(13)]
        iodf_sbas = df.read(2).u  # Issue of Data, Fast correction 1
        iodp_sbas = df.read(2).u  # Issue of Data, PRN mask
        for i in range(13):
            fc[i] = df.read(12).i
        for i in range(13):
            udrei[i] = df.read(4).u
        if iodp_sbas == self.iodp_sbas:
            prn_mask = self.mask_prn_sbas
        elif iodp_sbas == self.iodp_sbas_prev:
            prn_mask = self.mask_prn_sbas_prev
        elif self.iodp_sbas == UNDEF:
            return self.trace.msg(0, f" (waiting for PRN mask, MT1)", dec='dark')
        else:
            return self.trace.msg(0, f" (IODP mismatch: current {self.iodp_sbas} != received {iodp_sbas})", dec='dark')
        if len(prn_mask) < 13 * (id-1) + 1:
            return self.trace.msg(0, f" (PRN mask too short: {len(prn_mask)} < {13*(id-1)+1})", dec='dark')
        msg: str = self.trace.msg(1, f'\nSAT correction[m] (IODF={iodf_sbas})')
        for i, sat in enumerate(prn_mask[13*(id-1):13*id]):
            if fc[i] != 2047:
                msg += self.trace.msg(1, f"\n{sat:<4}: {fc[i]*0.125:8.3f}, UDREI={udrei[i]}")
            else:
                msg += self.trace.msg(1, f"\n{sat:<4}: {'VOID':>8s}, UDREI={udrei[i]}", dec='dark')
        return msg

    def decode_geo_ranging_function_parameters(self, df: BitStream) -> str:  # ref.[4]
        ''' returns decoded GEO ranging function parameters message '''
        df.pos += 8  # Skip 8 bits for reserved
        t0   = df.read(13).u  # Reference time for GEO ranging function
        ura  = df.read( 4).u  # User range accuracy
        xg   = df.read(30).i  # Xg
        yg   = df.read(30).i  # Yg
        zg   = df.read(25).i  # Zg
        dgx  = df.read(17).i  # first  derivative of Xg
        dgy  = df.read(17).i  # first  derivative of Yg
        dgz  = df.read(18).i  # first  derivative of Zg
        ddgx = df.read(10).i  # second derivative of Xg
        ddgy = df.read(10).i  # second derivative of Yg
        ddgz = df.read(10).i  # second derivative of Zg
        agf0 = df.read(12).i  # a_Gf0
        agf1 = df.read( 8).i  # a_Gf1
        msg =  f'\n  t0={t0*16}[s] URA={ura} a_Gf0={agf0*pow(2,-31)}[s] a_Gf1={agf1*pow(2,-40):10.3e}[s/s]' + \
               f'\n  Xg={xg*0.08e-3:10.3e}[km]       Yg={yg*0.08e-3:10.3e}[km]       Zg={zg*0.4e-3:10.3e}[km]' + \
               f'\n dXg={dgx*0.625e-3:10.3e}[m/s]     dYg={dgy*0.625e-3:10.3e}[m/s]     dZg={dgz*4e-3:10.3e}[mm/s^2]' + \
               f'\nddXg={ddgx*0.0125e-3:10.3e}[mm/s^2] ddYg={ddgy*0.0125e-3:10.3e}[mm/s^2] ddZg={ddgz*0.0625e-3:10.3e}[mm/s^2]'
        return self.trace.msg(1, msg)

    def decode_sbas_network_time_utc_offset_parameters(self, df: BitStream) -> str:  # ref.[4]
        ''' returns decoded SBAS network time/UTC offset parameters message '''
        df.pos += 137           # Skip 137 bits
        f_glo  = df.read( 1).u  # GLO time offset flag
        da_glo = df.read(24).i  # GLO time offset value
        df.pos += 50            # Skip 50 bits
        msg: str = ''
        if f_glo:
            msg = f'GLO time offset value: {da_glo*pow(2,-31)}[s]'
        return msg

    def decode_ionospheric_grid_point_masks(self, df: BitStream) -> str:  # ref.[4]
        ''' returns decoded Ionospheric grid point masks message '''
        self.total_igp          = df.read(  4).u  # The total number of IGP bands, max. 11
        igp_band                = df.read(  4).u  # IGP number, 0-10
        self.iodi_sbas          = df.read(  2).u  # IODI
        self.igp_mask[igp_band] = df.read(201)    # IGP mask
        self.igp_mask_pat       = df.read(  1).u  # IGP mask pattern
        return self.trace.msg(1, f'\nTotal_IGP={self.total_igp} IODI={self.iodi_sbas} IGP_mask_pattern={self.igp_mask_pat}')

    def decode_mt25sub(self, mt25sub: BitStream) -> str:
        ''' returns decoded MT25 submessage '''
        rate_code = mt25sub.read(1).u
        msg = ''
        if rate_code == 0:
            for _ in range(2):
                prn = mt25sub.read( 6).u  # PRN mask number
                iod = mt25sub.read( 8).u  # IOD of the satellite
                dx  = mt25sub.read( 9).i  # x correction
                dy  = mt25sub.read( 9).i  # y correction
                dz  = mt25sub.read( 9).i  # z correction
                daf0 = mt25sub.read(10).i  # clock correction
                iodp_sbas = mt25sub.read(2).u  # IODP of the SBAS satellite
                mt25sub.pos += 1  # Skip 1 reserved bit
                if iodp_sbas == self.iodp_sbas:
                    prn_mask = self.mask_prn_sbas
                elif iodp_sbas == self.iodp_sbas_prev:
                    prn_mask = self.mask_prn_sbas_prev
                elif self.iodp_sbas == UNDEF:
                    return self.trace.msg(0, f" (waiting for PRN mask, MT1)", dec='dark')
                else:
                    return self.trace.msg(0, f" (IODP mismatch: current {self.iodp_sbas} != received {iodp_sbas})", dec='dark')
                msg += self.trace.msg(1, f'\n{prn_mask[prn]:<4s} IOD={iod} dx={dx*0.125}[m] dy={dy*0.125}[m] dz={dz*0.125}[m] daf0={daf0*pow(2,-31)}[s]')
        else:
            prn  = mt25sub.read( 6).u  # PRN mask number
            iod  = mt25sub.read( 8).u  # IOD of the satellite
            dx   = mt25sub.read(11).i  # x correction
            dy   = mt25sub.read(11).i  # y correction
            dz   = mt25sub.read(11).i  # z correction
            daf0 = mt25sub.read(11).i  # ai correction
            ddx  = mt25sub.read( 8).i  # first derivative of x correction
            ddy  = mt25sub.read( 8).i  # first derivative of y correction
            ddz  = mt25sub.read( 8).i  # first derivative of z correction
            daf1 = mt25sub.read( 8).i  # first derivative of ai correction
            ti   = mt25sub.read(13).u
            iodp_sbas = mt25sub.read(2).u  # IODP of the SBAS satellite
            if iodp_sbas == self.iodp_sbas:
                prn_mask = self.mask_prn_sbas
            elif iodp_sbas == self.iodp_sbas_prev:
                prn_mask = self.mask_prn_sbas_prev
            elif self.iodp_sbas == UNDEF:
                return self.trace.msg(0, f" (waiting for PRN mask, MT1)", dec='dark')
            else:
                return self.trace.msg(0, f" (IODP mismatch: current {self.iodp_sbas} != received {iodp_sbas})", dec='dark')
            msg += self.trace.msg(1, f'\n{prn_mask[prn]:<4s} IOD={iod} daf0={daf0*pow(2,-31):10.3e}[s] daf1={daf1*pow(2,-39):10.3e}[s] ti={ti*16}[s]'
                    f'\n{"":<4s}  dx={dx*0.125:10.3e}[m]    dy={dy*0.125:10.3e}[m]    dz={dz*0.125:10.3e}[m]'
                    f'\n{"":<4s} ddx={ddx*0.0625:10.3e}[m/s] ddy={ddy*0.0625:10.3e}[m/s] ddz={ddz*0.0625:10.3e}[m/s]'
                    )
        return msg

    def decode_mixed_fast_long_term_satellite_corrections(self, df: BitStream) -> str:  # ref.[4]
        ''' returns decoded Mixed fast/long-term satellite corrections message '''
        fc    = [0 for _ in range(6)]
        udrei = [0 for _ in range(6)]
        for i in range(6):
            fc[i]    = df.read(12).i  # Fast correction
        for i in range(6):
            udrei[i] = df.read( 4).u  # UDREI
        iodp_sbas = df.read(2).u      # IODP
        id        = df.read(2).u + 1  # fast correction ID, 1-4
        iodf      = df.read(2).u      # IODF
        df.pos    += 4  # reserved
        mt25sub   = df.read(106)
        if iodp_sbas == self.iodp_sbas:
            prn_mask = self.mask_prn_sbas
        elif iodp_sbas == self.iodp_sbas_prev:
            prn_mask = self.mask_prn_sbas_prev
        elif self.iodp_sbas == UNDEF:
            return self.trace.msg(0, f" (waiting for PRN mask, MT1)", dec='dark')
        else:
            return self.trace.msg(0, f" (IODP mismatch: current {self.iodp_sbas} != received {iodp_sbas})", dec='dark')
        if len(prn_mask) < 13 * (id-1) + 1:
            return self.trace.msg(0, f" (PRN mask too short for fast correction ID {id}: {len(prn_mask)} < {13 * (id-1) + 1})", dec='dark')
        msg: str = self.trace.msg(1, f'\nSAT correction[m] (IODF={iodf})')
        for i, sat in enumerate(prn_mask[13*(id-1):13*(id-1)+6]):
            if fc[i] != 2047:
                msg += self.trace.msg(1, f"\n{sat:<4}: {fc[i]*0.125:8.3f}, UDREI={udrei[i]}")
            else:
                msg += self.trace.msg(1, f"\n{sat:<4}: {'VOID':>8s}, UDREI={udrei[i]}", dec='dark')
        msg += self.decode_mt25sub(mt25sub)
        return msg

    def decode_long_term_satellite_error_corrections(self, df: BitStream) -> str:  # ref.[4]
        ''' returns decoded Long-term satellite error corrections message '''
        mt25sub1 = df.read(106)
        mt25sub2 = df.read(106)
        return self.decode_mt25sub(mt25sub1) + self.decode_mt25sub(mt25sub2)

    def decode_ionospheric_delay_corrections(self, df: BitStream) -> str:  # ref.[4]
        ''' returns decoded Ionospheric delay corrections message '''
        tau  = [0 for _ in range(15)]
        give = [0 for _ in range(15)]
        igp_band  = df.read(4).u  # IGP band number
        igp_block = df.read(4).u  # IGP block number
        for i in range(15):
            tau [i] = df.read(9).i  # Ionospheric delay correction for the ith grid point
            give[i] = df.read(4).u
        iodi_sbas = df.read(2).u  # IODI
        if self.iodi_sbas == UNDEF:
            return self.trace.msg(0, f" (waiting for IGP masks, MT18)", dec='dark')
        elif iodi_sbas != self.iodi_sbas:
            return self.trace.msg(0, f" (IODI mismatch: current {self.iodi_sbas} != received {iodi_sbas})", dec='dark')
        df.pos += 7  # reserved
        return self.trace.msg(1, f'\nIGP_band={igp_band} IGP_block={igp_block}')
    
    MT2NAME = {  # asterisk (*) indicates unknown message structure
         0: 'Test mode',  # ref.[2]
         1: 'SBAS PRN mask',  # ref.[4]
         2: 'Fast corrections 1',  # ref.[4]
         3: 'Fast corrections 2',  # ref.[4]
         4: 'Fast corrections 3',  # ref.[4]
         5: 'Fast corrections 4',  # ref.[4]
         6: 'Integrity information(*)',  # ref.[6]
         7: 'Fast correction degradation factor(*)',  # ref.[6
         9: 'GEO ranging function parameters',  # ref.[4]
        10: 'Degradation factors(*)',  # ref.[6]
        12: 'SBAS network time/UTC offset parameters',  # ref.[4]
        17: 'GEO satellite almanacs(*)',  # ref.[6]
        18: 'Ionospheric grid point masks',  # ref.[4]
        20: 'SBAS L1 authentication message(*)',  # ref.[6]
        21: 'SBAS over the air air rekeying (OTAR)(*)',  # ref.[6]
        24: 'Mixed fast/long-term satellite corrections',  # ref.[4]
        25: 'Long-term satellite error corrections',  # ref.[4]
        26: 'Ionospheric delay corrections',  # ref.[4]
        27: 'SBAS service message(*)',  # ref.[6]
        28: 'Clock-ephemeris covariance matrix(*)',  # ref.[6]
        43: 'DCR',  # ref.[2]
        44: 'DCX',  # ref.[5]
        47: 'Monitoring station information',  # ref.[4]
        48: 'PRN mask',  # ref.[4]
        49: 'Data issue number',  # ref.[4]
        50: 'DGPS correction',  # ref.[4]
        51: 'Satellite health',  # ref.[4]
        58: 'QZS ephemeris',  # ref.[4]
        62: 'Reserved',  # ref.[6]
        63: 'Null message',  # ref.[2]
    }

    def decode_l1s (self, l1s: BitStream) -> str:
        ''' returns decoded message '''
        pab = l1s.read(L_PAB)  # preamble (8 bit), ref.[3], Fig.4.1.1-1
        mt  = l1s.read(L_MT)   # message type (6 bit)
        df  = l1s.read(L_DF)   # data field (212 bit)
        crc = l1s.read(L_CRC)  # crc24, ref.[3] pp., sect.4.1.1.3
        pad = BitStream('uint6=0')  # padding for byte alignment
        frame = (pad + pab + mt + df).tobytes()
        crc_test = libqzsl6tool.rtk_crc24q(frame, len(frame))
        if crc.tobytes() != crc_test:
            msg = self.trace.msg(0, f" CRC error {crc_test.hex()} != {crc.hex}", fg='red')  # crc_test is bytes (.hex() method); crc is a BitStream (.hex property)
            return msg
        mt_name = self.MT2NAME.get(mt.u, f"MT {mt.u}")
        msg = self.trace.msg(0, f'MT{mt.u:02d}: ', fg='yellow') + self.trace.msg(0, mt_name, fg='cyan')
        if   mt_name == 'Test mode':                        # MT0 (L1S and SBAS)
            msg += self.decode_test_mode(df)
        elif mt_name == 'DCR':                              # MT43 (L1S)
            msg += self.decode_dcr(df)
        elif mt_name == 'DCX':                              # MT44 (L1S)
            msg += self.decode_dcx(df)
        elif mt_name == 'Monitoring station information':   # MT47 (L1S)
            msg += self.decode_monitoring_station_info(df)
        elif mt_name == 'PRN mask':                         # MT48 (L1S)
            msg += self.decode_prn_mask(df)
        elif mt_name == 'Data issue number':                # MT49 (L1S)
            msg += self.decode_data_issue_number(df)
        elif mt_name == 'DGPS correction':                  # MT50 (L1S)
            msg += self.decode_dgps_correction(df)
        elif mt_name == 'Satellite health':                 # MT51 (L1S)
            msg += self.decode_satellite_health(df)
        elif mt_name == 'SBAS PRN mask':                    # MT1  (SBAS)
            msg += self.decode_sbas_prn_mask(df)
        elif 'Fast corrections' in mt_name:                  # MT2-5 (SBAS)
            id = int(mt_name[-1])  # Extract the fast correction number from the mt_name
            if id < 1 or 4 < id:
                raise ValueError(f"Invalid fast correction ID: {id}")
            msg += self.decode_fast_correction(df, id)
        elif mt_name == 'GEO ranging function parameters':  # MT9 (SBAS)
            msg += self.decode_geo_ranging_function_parameters(df)
        elif mt_name == 'SBAS network time/UTC offset parameters':  # MT12 (SBAS)
            msg += self.decode_sbas_network_time_utc_offset_parameters(df)
        elif mt_name == 'Ionospheric grid point masks':     # MT18 (SBAS)
            msg += self.decode_ionospheric_grid_point_masks(df)
        elif mt_name == 'Mixed fast/long-term satellite corrections':  # MT24 (SBAS)
            msg += self.decode_mixed_fast_long_term_satellite_corrections(df)
        elif mt_name =='Long-term satellite error corrections':  # MT25 (SBAS)
            msg += self.decode_long_term_satellite_error_corrections(df)
        elif mt_name == 'Ionospheric delay corrections':    # MT26 (SBAS)
            msg += self.decode_ionospheric_delay_corrections(df)
        return msg

def read_from_l1s_file(qzsl1s: QzsL1s, l1s_file: str, fp_disp: TextIO | None) -> None:
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
            payload = BitStream(raw)
            gpsweek = payload.read(12).u
            gpstow  = payload.read(20).u
            l1s     = payload.read(L_L1S)
            payload.pos += 6  # spare
            msg = qzsl1s.trace.msg(0, libgnsstime.gps2utc(gpsweek, gpstow), fg='green') + ':' + qzsl1s.decode_l1s(l1s)
            qzsl1s.trace.show(0, msg)
            raw = f.buffer.read(36)

def read_from_stdin(qzsl1s: QzsL1s,  fp_disp: TextIO | None) -> None:
    ''' reads and interprets stdin data, and displays the contents
        format: [PRN(8)][L1S RAW(250)][padding(6)]...
    '''
    raw = sys.stdin.buffer.read(33)
    while raw:
        payload = BitStream(raw)
        prn = payload.read(8).u
        l1s = payload.read(L_L1S)
        payload.pos += 6  # spare
        msg = qzsl1s.trace.msg(0, f'PRN{prn:3d}', fg='green') + ':' + qzsl1s.decode_l1s(l1s)
        qzsl1s.trace.show(0, msg)
        raw = sys.stdin.buffer.read(33)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=f'Quasi-zenith satellite (QZS) L1S message read, QZS L6 Tool ver.{libqzsl6tool.VERSION}')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=subtype detail, 2=subtype and bit image.')
    parser.add_argument(
        '--jp', action='store_true',
        help='show DCR (disaster and crisis management report) in Japanese.')
    parser.add_argument(
        'l1s_files', metavar='file', nargs='*', default=None,
        help='L1S file(s) obtained from the QZS archive, https://sys.qzss.go.jp/dod/archives/slas.html')
    args = parser.parse_args()
    fp_disp = sys.stdout
    trace = libtrace.Trace(fp_disp, args.trace, args.color)
    qzsl1s = QzsL1s(trace, args.jp)
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
