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
# [7] RTCA, Minimum operational performance standards for global positioning system/satellite-based augmentation system airborne equipment, DO-229D, Dec. 2006.
# [8] Ken Alexander, Todd Walter, Andrew Neish, Jason Anderson, "SBAS authentication standards," Proc. ION GNSS+ 2024, Sept. 2024, https://web.stanford.edu/group/scpnt/gpslab/pubs/papers/Dennis_ION_GNSS_2024_SBAS_Authentication_Standards.pdf (draft ICAO SARPs, subject to change).
# [9] European Union, Emergency warning satellite service common alert message format specification, Issue 1.0, Jan. 2024.

import argparse
import os
import sys
from typing import TextIO

sys.path.append(os.path.dirname(__file__))
import libcamf
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

L_L1S: int = 250  # length of L1S and SBAS in bits
L_DF : int = 212  # length data field in bits, ref.[3], pp.13, Fig.4.1.1.-1
UNDEF: int = -1   # undefined value for IODP and IODI

MT2NAME: dict[int, str] = {  # asterisk (*) indicates unknown message structure
     0: 'Test mode',  # ref.[2]
     1: 'SBAS PRN mask',  # ref.[4]
     2: 'Fast corrections 1',  # ref.[4]
     3: 'Fast corrections 2',  # ref.[4]
     4: 'Fast corrections 3',  # ref.[4]
     5: 'Fast corrections 4',  # ref.[4]
     6: 'Integrity information',  # ref.[6]
     7: 'Fast correction degradation factor',  # ref.[7]
     9: 'GEO ranging function parameters',  # ref.[4]
    10: 'Degradation factors',  # ref.[7]
    12: 'SBAS network time/UTC offset parameters',  # ref.[4]
    17: 'GEO satellite almanacs',  # ref.[7]
    18: 'Ionospheric grid point masks',  # ref.[4]
    20: 'SBAS L1 authentication message',  # ref.[8]
    21: 'SBAS over the air rekeying (OTAR)',  # ref.[8]
    24: 'Mixed fast/long-term satellite corrections',  # ref.[4]
    25: 'Long-term satellite error corrections',  # ref.[4]
    26: 'Ionospheric delay corrections',  # ref.[4]
    27: 'SBAS service message(*)',  # ref.[6]
    28: 'Clock-ephemeris covariance matrix',  # ref.[7]
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

# IGP (ionospheric grid point) definitions, ref.[7], Table A-14 (band 0-8) and Table A-15 (band 9-10)
IGP_LAT_A: list[int] = [-75, -65] + list(range(-55, 60, 5)) + [65, 75, 85]  # 28 pts, with 85N
IGP_LAT_B: list[int] = list(range(-55, 60, 5))                                # 23 pts
IGP_LAT_C: list[int] = [-75, -65] + list(range(-55, 60, 5)) + [65, 75]      # 27 pts
IGP_LAT_D: list[int] = [-85, -75, -65] + list(range(-55, 60, 5)) + [65, 75]  # 28 pts, with 85S
IGP_LON_A: list[int] = list(range(-180, 180,  5))  # 72 pts
IGP_LON_B: list[int] = list(range(-180, 180, 10))  # 36 pts
IGP_LON_C: list[int] = list(range(-180, 180, 30))  # 12 pts
IGP_LON_D: list[int] = list(range(-170, 190, 30))  # 12 pts

def igp_table() -> list[list[tuple[int, int]]]:
    '''
    returns IGP position table: IGP_TABLE[band][index] = (lat, lon) in degrees
    index is 0-origin (IGP number - 1)
    '''
    table: list[list[tuple[int, int]]] = []
    for band in range(9):  # vertical bands, 201 IGPs each
        lon0 = -180 + 40 * band
        lat_first = IGP_LAT_A if band % 2 == 0 else IGP_LAT_D
        lats = [lat_first, IGP_LAT_B, IGP_LAT_C, IGP_LAT_B, IGP_LAT_C, IGP_LAT_B, IGP_LAT_C, IGP_LAT_B]
        igps: list[tuple[int, int]] = []
        for col, lat_list in enumerate(lats):
            igps += [(lat, lon0 + 5 * col) for lat in lat_list]
        table.append(igps)
    for sign in (1, -1):  # horizontal bands 9 (north) and 10 (south), 192 IGPs each
        igps = [(sign * 60, lon) for lon in IGP_LON_A]
        for lat in (65, 70, 75):
            igps += [(sign * lat, lon) for lon in IGP_LON_B]
        igps += [(sign * 85, lon) for lon in (IGP_LON_C if sign == 1 else IGP_LON_D)]
        table.append(igps)
    return table

IGP_TABLE: list[list[tuple[int, int]]] = igp_table()

AI2DEGRADATION: dict[int, tuple[float, int, int, int]] = {  # ref.[7], Table A-8
    # ai: (degradation factor [m/s^2], timeout en route/terminal [s], timeout precision approach [s], max update interval [s])
     0: (0.00000, 180, 120, 60),
     1: (0.00005, 180, 120, 60),
     2: (0.00009, 153, 102, 51),
     3: (0.00012, 135,  90, 45),
     4: (0.00015, 135,  90, 45),
     5: (0.00020, 117,  78, 39),
     6: (0.00030,  99,  66, 33),
     7: (0.00045,  81,  54, 27),
     8: (0.00060,  63,  42, 21),
     9: (0.00090,  45,  30, 15),
    10: (0.00150,  45,  30, 15),
    11: (0.00210,  27,  18,  9),
    12: (0.00270,  27,  18,  9),
    13: (0.00330,  27,  18,  9),
    14: (0.00460,  18,  12,  6),
    15: (0.00580,  18,  12,  6),
}

SPID2NAME: dict[int, str] = {  # SBAS service provider ID, ref.[7], sect.A.4.4.12
     0: 'WAAS',   1: 'EGNOS',  2: 'MSAS',   3: 'GAGAN',  4: 'SDCM',
     5: 'BDSBAS', 6: 'KASS',   7: 'A-SBAS', 8: 'SouthPAN',
    14: 'GBAS',  15: 'unallocated',
}

L3KEY_APPLICABILITY: dict[int, str] = {  # ref.[8], Table B-y3
    0: 'signal', 1: 'satellite', 2: 'SBAS system', 3: 'reserved',
}
CRYPTO_TECHNIQUE: dict[int, str] = {  # ref.[8], Table B-y3
    1: 'TESLA',
}
TESLA_HASH_FUNCTION: dict[int, str] = {  # ref.[8], Table B-y3, note 2 (tentative)
    0: 'SHA-256', 1: 'SHA3-256', 2: 'reserved', 3: 'reserved',
}

GIVEI2GIVE: dict[int, float] = {  # GIVEI to GIVE [m], ref.[7], Table A-17
     0: 0.3,  1: 0.6,  2: 0.9,  3: 1.2,  4: 1.5,  5: 1.8,  6: 2.1,  7: 2.4,
     8: 2.7,  9: 3.0, 10: 3.6, 11: 4.5, 12: 6.0, 13: 15.0, 14: 45.0,
}

# DCX (MT44) tables, ref.[5]; CAMF tables are in libcamf.py, ref.[9]
DCX_SDM2PRN: dict[int, str] = {  # satellite designation mask bit -> PRN, ref.[5], Table 5.6-3
    0: 'PRN183', 1: 'PRN184', 2: 'PRN185', 3: 'PRN186', 6: 'PRN189',
}
DCX_PROVIDER_JP: dict[int, str] = {  # A3, Table 4.2-6 (Japan)
    0: 'not used', 1: 'FMMC (L-Alert)', 2: 'FDMA (J-Alert)', 3: 'Related Ministries (J-Alert)',
    4: 'Local Government',
}
DCX_BASIC_INSTRUCTION: dict[int, str] = {  # A11 bits 1-2, Table 4.2-14
    0: '', 1: 'Stay.', 2: 'Move to/toward', 3: 'Keep away from',
}
DCX_BASIC_INSTRUCTION_INFO: dict[int, str] = {  # A11 bits 3-10, Table 4.2-14
    0: '', 1: 'Under/inside a solid structure.', 2: '3rd floor or higher.', 3: 'Underground.',
    4: 'Mountain.', 5: 'Water area.', 6: 'Building where chemicals are handled, such as a factory.',
    7: 'Cliffs and areas at risk of collapse.',
}
DCX_INSTRUCTION_A11: dict[int, str] = {  # A11 with bits 1-2 = 00, Table 4.2-15
      0: '',
      1: 'Take the best immediate action to save your life.',
    126: 'This is a test message for DCX.',
    127: 'Take the best immediate action to save your life.',
    128: 'Missile launched, missile launched. It is believed that a missile was launched. Please take shelter inside buildings or underground.',
    129: 'Missile passed, missile passed. It is believed that the previous missile has passed over the area. The call for evacuation will be canceled.',
    130: 'It is believed that the previous missile has dropped in the sea. The call for evacuation will be canceled.',
    131: 'It is believed that the previous missile will not come to Japan. The call for evacuation will be canceled.',
    132: 'Take shelter immediately, take shelter immediately. Please take shelter inside buildings or underground. It is believed that a missile will drop around this area.',
    133: 'The previous missile has been intercepted and destroyed. There is a possibility of pieces of the destroyed missile dropping. Please stay indoors for shelter.',
    134: 'Missile dropped, missile dropped. It is believed that a missile has dropped around this area. Please stay indoors for shelter.',
    135: 'It is believed that the previous missile will not drop in Japan. The call for evacuation will be canceled.',
    136: 'This is a test message for J-Alert.',
    255: 'Take immediate action to save your life.',
}
DCX_PREFECTURE: list[str] = [  # J-Alert EX9 prefecture code, bit position 47 (Hokkaido) to 1 (Okinawa), Table 4.2-25
    'Hokkaido', 'Aomori', 'Iwate', 'Miyagi', 'Akita', 'Yamagata', 'Fukushima', 'Ibaraki', 'Tochigi',
    'Gunma', 'Saitama', 'Chiba', 'Tokyo', 'Kanagawa', 'Niigata', 'Toyama', 'Ishikawa', 'Fukui',
    'Yamanashi', 'Nagano', 'Gifu', 'Shizuoka', 'Aichi', 'Mie', 'Shiga', 'Kyoto', 'Osaka', 'Hyogo',
    'Nara', 'Wakayama', 'Tottori', 'Shimane', 'Okayama', 'Hiroshima', 'Yamaguchi', 'Tokushima',
    'Kagawa', 'Ehime', 'Kochi', 'Fukuoka', 'Saga', 'Nagasaki', 'Kumamoto', 'Oita', 'Miyazaki',
    'Kagoshima', 'Okinawa',
]

class QzsL1s:
    def reset_all_variables(self) -> None:
        self.iodp_l1s: int                 = UNDEF  # PRN mask update number
        self.iodi_l1s: int                 = UNDEF  # IOD updating number
        self.mask_prn_l1s: list[str]       = []     # satellite mask defined by MT48 (PRN mask)
        self.mask_sv_l1s: list[str]        = []     # mask info for selected satellite defined by MT49 (data issue number)
        self.mask_uh_l1s: list[str]        = []     # mask info for unhealthy satellite defined by MT51 (satellite health)
        self.iod_l1s: list[int]            = [UNDEF for _ in range(23)]  # data issue number
        self.iodp_sbas: int                = UNDEF  # PRN mask update number
        self.iodp_sbas_prev: int           = UNDEF  # PRN mask update number
        self.iodf_sbas: list[int]          = [UNDEF for _ in range(4)]  # Issue of Data, Fast correction
        self.iodi_sbas: int                = UNDEF  # IOD updating number
        self.mask_prn_sbas: list[str]      = []     # mask info for SBAS satellites defined by MT1 (PRN mask)
        self.mask_prn_sbas_prev: list[str] = []     # previous mask info for SBAS satellites defined by MT1 (PRN mask)
        self.total_igp: int                = UNDEF  # The total number of IGP bands by MT18
        self.igp_mask: list[BitStream]     = [BitStream(201) for _ in range(len(IGP_TABLE))]  # IGP mask for each band by MT18
        self.igp_mask_pat: int             = UNDEF  # IGP mask pattern by MT18

    def __init__(self, trace: libtrace.Trace, jp: bool = False) -> None:
        self.trace = trace
        self.jp    = jp  # display DCR messages in English or Japanese
        self.reset_all_variables()  # initialize all variables

    def decode_test_mode(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.3, MT0 (both L1S and SBAS)
        '''
        MT0: test mode messages, solicit deleting previous messages stored in the receiver
        returns empty status string
        '''
        self.reset_all_variables()  # clear all variables
        df.pos += L_DF
        return ''

    def decode_sbas_prn_mask(self, df: BitStream) -> str:  # ref.[4], MT1 (SBAS)
        '''
        MT1: SBAS PRN mask
        returns status string
        '''
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
        for i in range(19):  # for SBAS, PRN 120-138
            if bitmask[119 + i]:
                self.mask_prn_sbas.append(f'S{i+120:02d}')
        msg: str = self.trace.msg(1, f"\nselected sats:")
        for sat in self.mask_prn_sbas:
            msg += self.trace.msg(1, " " + sat)
        msg += self.trace.msg(1, f" ({len(self.mask_prn_sbas)} sats, IODP={self.iodp_sbas})")
        return msg

    def select_prn_mask_sbas(self, iodp_sbas: int) -> tuple[list[str] | None, str]:
        '''
        selects the SBAS PRN mask matching the received IODP
        inputs  received IODP
        returns (PRN mask or None, status string)
        '''
        if iodp_sbas == self.iodp_sbas:
            return self.mask_prn_sbas, ''
        if iodp_sbas == self.iodp_sbas_prev:
            return self.mask_prn_sbas_prev, self.trace.msg(1, f' (using previous PRN mask: IODP={iodp_sbas})')
        if self.iodp_sbas == UNDEF:
            return None, self.trace.msg(0, " (waiting for PRN mask, MT1)", dec='dark')
        return None, self.trace.msg(0, f" (IODP mismatch: current {self.iodp_sbas} != received {iodp_sbas})", dec='dark')

    def decode_fast_correction(self, df: BitStream, msg_id: int) -> str:  # ref.[4], MT2-5 (SBAS)
        '''
        MT2-5: Fast correction message
        inputs  correction message number, 1-4
        returns status string
        '''
        fc    = [0 for _ in range(13)]
        udrei = [0 for _ in range(13)]
        self.iodf_sbas[msg_id-1] = df.read(2).u  # Issue of Data, Fast correction
        iodp_sbas                = df.read(2).u  # Issue of Data, PRN mask
        for i in range(13):
            fc[i] = df.read(12).i
        for i in range(13):
            udrei[i] = df.read(4).u
        prn_mask, msg = self.select_prn_mask_sbas(iodp_sbas)
        if prn_mask is None:
            return msg
        if len(prn_mask) < 13 * (msg_id-1) + 1:
            return msg + self.trace.msg(0, f" (PRN mask too short: {len(prn_mask)} < {13*(msg_id-1)+1})", dec='dark')
        msg += self.trace.msg(1, f'\nSAT correction[m] (IODF={self.iodf_sbas[msg_id-1]}), IODP={iodp_sbas}')
        for i, sat in enumerate(prn_mask[13*(msg_id-1):13*msg_id]):
            if fc[i] != 2047:
                msg += self.trace.msg(1, f"\n{sat:<4}: {fc[i]*0.125:8.3f}, UDREI={udrei[i]}")
            else:
                msg += self.trace.msg(1, f"\n{sat:<4}: {'VOID':>8s}, UDREI={udrei[i]}", dec='dark')
        return msg

    def decode_integrity_information(self, df: BitStream) -> str:  # ref.[6], MT6 
        '''
        MT6: Integrity information message
        inputs  data field (212 bit),
        returns status string
        '''
        iodf_sbas  = [UNDEF for _ in range(4)]
        udrei_sbas = [UNDEF for _ in range(4*13-1)]
        for id in range(4):  # SBAS fast correction message number (1-4)
            iodf_sbas[id] = df.read(2).u  # IODF
        for i in range(4*13-1):
            udrei_sbas[i] = df.read(4).u  # UDREI
        if self.iodp_sbas == UNDEF:
            return self.trace.msg(0, " (waiting for PRN mask, MT1)", dec='dark')
        msg = self.trace.msg(1, f'\nIODF={iodf_sbas}')
        for i, sat in enumerate(self.mask_prn_sbas[:4*13-1]):
            msg += self.trace.msg(1, f'\n{sat:<4}: UDREI={udrei_sbas[i]}')
        return msg

    def decode_fast_correction_degradation_factor(self, df: BitStream) -> str:  # ref.[7], sect.A.4.4.5, MT7 (SBAS)
        '''
        MT7: Fast correction degradation factor
        returns status string
        '''
        t_lat     = df.read(4).u  # system latency [s]
        iodp_sbas = df.read(2).u  # IODP
        df.pos += 2  # spare
        ai = [0 for _ in range(51)]
        for i in range(51):
            ai[i] = df.read(4).u  # degradation factor indicator
        prn_mask, msg = self.select_prn_mask_sbas(iodp_sbas)
        if prn_mask is None:
            return msg
        msg += self.trace.msg(1, f'\nt_lat={t_lat}[s] IODP={iodp_sbas}')
        msg += self.trace.msg(1, '\nSAT  ai  a[m/s^2] timeout_ET[s] timeout_PA[s] max_interval[s]')
        for i, sat in enumerate(prn_mask[:51]):
            a, t_et, t_pa, t_max = AI2DEGRADATION[ai[i]]
            msg += self.trace.msg(1, f'\n{sat:<4s} {ai[i]:2d} {a:9.5f} {t_et:13d} {t_pa:13d} {t_max:15d}')
        return msg

    def decode_geo_ranging_function_parameters(self, df: BitStream) -> str:  # ref.[4], MT9 (SBAS)
        '''
        MT9: GEO ranging function parameters message
        returns status string
        '''
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
               f'\n dXg={dgx*0.625e-3:10.3e}[m/s]     dYg={dgy*0.625e-3:10.3e}[m/s]     dZg={dgz*4e-3:10.3e}[m/s]' + \
               f'\nddXg={ddgx*0.0125e-3:10.3e}[m/s^2]  ddYg={ddgy*0.0125e-3:10.3e}[m/s^2]  ddZg={ddgz*0.0625e-3:10.3e}[m/s^2]'
        return self.trace.msg(1, msg)

    def decode_degradation_factors(self, df: BitStream) -> str:  # ref.[7], sect.A.4.4.6, MT10 (SBAS)
        '''
        MT10: Degradation factors
        returns status string
        '''
        b_rrc      = df.read(10).u * 0.002     # [m]   range-rate correction degradation
        c_ltc_lsb  = df.read(10).u * 0.002     # [m]   long-term correction, max round-off error
        c_ltc_v1   = df.read(10).u * 0.00005   # [m/s] long-term correction, velocity code 1
        i_ltc_v1   = df.read( 9).u             # [s]   update interval, velocity code 1
        c_ltc_v0   = df.read(10).u * 0.002     # [m]   long-term correction, velocity code 0
        i_ltc_v0   = df.read( 9).u             # [s]   update interval, velocity code 0
        c_geo_lsb  = df.read(10).u * 0.0005    # [m]   GEO navigation, max round-off error
        c_geo_v    = df.read(10).u * 0.00005   # [m/s] GEO navigation, velocity
        i_geo      = df.read( 9).u             # [s]   GEO navigation update interval
        c_er       = df.read( 6).u * 0.5       # [m]   degradation when corrections have timed out
        c_iono_stp = df.read(10).u * 0.001     # [m]   ionospheric step
        i_iono     = df.read( 9).u             # [s]   ionospheric update interval
        c_iono_rmp = df.read(10).u * 0.000005  # [m/s] ionospheric ramp
        rss_udre   = df.read( 1).u             # root-sum-square flag for UDRE
        rss_iono   = df.read( 1).u             # root-sum-square flag for iono
        c_cov      = df.read( 7).u * 0.1       # covariance degradation
        df.pos += 81  # spare
        msg = self.trace.msg(1, f'\nB_rrc={b_rrc:.3f}[m] C_ltc_lsb={c_ltc_lsb:.3f}[m] C_ltc_v1={c_ltc_v1:.5f}[m/s] I_ltc_v1={i_ltc_v1}[s] C_ltc_v0={c_ltc_v0:.3f}[m] I_ltc_v0={i_ltc_v0}[s]')
        msg += self.trace.msg(1, f'\nC_geo_lsb={c_geo_lsb:.4f}[m] C_geo_v={c_geo_v:.5f}[m/s] I_geo={i_geo}[s] C_er={c_er:.1f}[m]')
        msg += self.trace.msg(1, f'\nC_iono_step={c_iono_stp:.3f}[m] I_iono={i_iono}[s] C_iono_ramp={c_iono_rmp:.6f}[m/s] RSS_UDRE={rss_udre} RSS_iono={rss_iono} C_covariance={c_cov:.1f}')
        return msg

    def decode_sbas_network_time_utc_offset_parameters(self, df: BitStream) -> str:  # ref.[4], MT12 (SBAS)
        '''
        MT12: SBAS network time/UTC offset parameters message
        returns status string
        '''
        df.pos += 137           # Skip 137 bits
        f_glo  = df.read( 1).u  # GLO time offset flag
        da_glo = df.read(24).i  # GLO time offset value
        df.pos += 50            # Skip 50 bits
        msg: str = ''
        if f_glo:
            msg = self.trace.msg(1, f'\nGLO time offset value: {da_glo*pow(2,-31)}[s]')
        return msg

    def decode_geo_satellite_almanacs(self, df: BitStream) -> str:  # ref.[7], sect.A.4.4.12, MT17 (SBAS)
        '''
        MT17: GEO satellite almanacs
        returns status string
        '''
        msg = ''
        for _ in range(3):  # three almanacs per message
            data_id = df.read( 2).u  # data ID
            prn     = df.read( 8).u  # PRN number, 0 = unused slot
            spid    = df.read( 4).u  # health and status: service provider ID
            f_rng   = df.read( 1).u  # ranging off
            f_cor   = df.read( 1).u  # corrections off
            f_int   = df.read( 1).u  # broadcast integrity off
            df.pos += 1              # reserved
            xg      = df.read(15).i  # Xg, LSB 2600 m
            yg      = df.read(15).i  # Yg, LSB 2600 m
            zg      = df.read( 9).i  # Zg, LSB 26000 m
            dxg     = df.read( 3).i  # Xg rate, LSB 10 m/s
            dyg     = df.read( 3).i  # Yg rate, LSB 10 m/s
            dzg     = df.read( 4).i  # Zg rate, LSB 40.96 m/s
            if prn == 0:
                continue
            status = ''
            status += ' ranging'     if not f_rng else ''
            status += ' corrections' if not f_cor else ''
            status += ' integrity'   if not f_int else ''
            msg += self.trace.msg(1, f'\nS{prn:03d} data_ID={data_id} provider={SPID2NAME.get(spid, f"unknown({spid})")} service:{status if status else " none"}')
            msg += self.trace.msg(1, f'\n     Xg={xg*2.6:9.1f}[km] Yg={yg*2.6:9.1f}[km] Zg={zg*26:9.1f}[km]'
                    f' dXg={dxg*10:4d}[m/s] dYg={dyg*10:4d}[m/s] dZg={dzg*40.96:7.2f}[m/s]')
        t0 = df.read(11).u  # time of day, LSB 64 s
        msg += self.trace.msg(1, f'\n     t0={t0*64}[s]')
        return msg

    def decode_ionospheric_grid_point_masks(self, df: BitStream) -> str:  # ref.[4], MT18 
        '''
        MT18: Ionospheric grid point masks message
        returns status string
        '''
        self.total_igp          = df.read(  4).u  # The total number of IGP bands, max. 11
        igp_band                = df.read(  4).u  # IGP number, 0-10
        iodi_sbas               = df.read(  2).u  # IODI
        igp_mask                = df.read(201)    # IGP mask
        igp_mask_pat            = df.read(  1).u  # IGP mask pattern
        if len(IGP_TABLE) <= igp_band:
            return self.trace.msg(0, f" (invalid IGP band number: {igp_band})", dec='dark')
        if iodi_sbas != self.iodi_sbas:  # new IODI, clear all band masks
            self.igp_mask = [BitStream(201) for _ in range(len(IGP_TABLE))]
        self.iodi_sbas          = iodi_sbas
        self.igp_mask[igp_band] = igp_mask
        self.igp_mask_pat       = igp_mask_pat
        n_igp = sum(1 for b in igp_mask if b)
        msg = self.trace.msg(1, f'\nTotal_IGP={self.total_igp} IGP_band={igp_band} IODI={self.iodi_sbas} IGP_mask_pattern={self.igp_mask_pat} ({n_igp} IGPs)')
        msg += self.trace.msg(2, '\nIGP lat[deg] lon[deg]')
        for i in range(len(IGP_TABLE[igp_band])):
            if igp_mask[i]:
                lat, lon = IGP_TABLE[igp_band][i]
                msg += self.trace.msg(2, f'\n{i+1:3d} {lat:8d} {lon:8d}')
        return msg

    def decode_mt25sub(self, mt25sub: BitStream) -> str: # for SBAS MT24 and MT25
        '''
        inputs  raw MT25 submessage (106 bit)
        returns decoded message
        '''
        def sat_name(prn_mask: list[str], prn: int) -> str:
            # PRN mask number is 1-origin; 0 means no data
            if prn == 0 or len(prn_mask) < prn:
                return ''
            return prn_mask[prn-1]
        rate_code = mt25sub.read(1).u  # velocity code
        msg = ''
        if rate_code == 0:
            prn  = [0 for _ in range(2)]
            iod  = [0 for _ in range(2)]
            dx   = [0 for _ in range(2)]
            dy   = [0 for _ in range(2)]
            dz   = [0 for _ in range(2)]
            daf0 = [0 for _ in range(2)]
            for i in range(2):
                prn [i] = mt25sub.read( 6).u  # PRN mask number
                iod [i] = mt25sub.read( 8).u  # IOD of the satellite
                dx  [i] = mt25sub.read( 9).i  # x correction
                dy  [i] = mt25sub.read( 9).i  # y correction
                dz  [i] = mt25sub.read( 9).i  # z correction
                daf0[i] = mt25sub.read(10).i  # clock correction
            iodp_sbas = mt25sub.read(2).u  # IODP
            mt25sub.pos += 1  # spare
            if all(p == 0 for p in prn):
                return msg
            prn_mask, msg = self.select_prn_mask_sbas(iodp_sbas)
            if prn_mask is None:
                return msg
            for i in range(2):
                sat = sat_name(prn_mask, prn[i])
                if not sat:
                    continue
                msg += self.trace.msg(1, f'\n{sat:<4s} IOD={iod[i]} daf0={daf0[i]*pow(2,-31):10.3e}[s]'
                        f'\n{"":<4s}  dx={dx[i]*0.125:10.3e}[m]    dy={dy[i]*0.125:10.3e}[m]    dz={dz[i]*0.125:10.3e}[m]')
        else:
            prn  = mt25sub.read( 6).u  # PRN mask number
            iod  = mt25sub.read( 8).u  # IOD of the satellite
            dx   = mt25sub.read(11).i  # x correction
            dy   = mt25sub.read(11).i  # y correction
            dz   = mt25sub.read(11).i  # z correction
            daf0 = mt25sub.read(11).i  # clock correction
            ddx  = mt25sub.read( 8).i  # x velocity correction
            ddy  = mt25sub.read( 8).i  # y velocity correction
            ddz  = mt25sub.read( 8).i  # z velocity correction
            daf1 = mt25sub.read( 8).i  # clock drift correction
            ti   = mt25sub.read(13).u  # time of applicability
            iodp_sbas = mt25sub.read(2).u  # IODP
            if prn == 0:
                return msg
            prn_mask, msg = self.select_prn_mask_sbas(iodp_sbas)
            if prn_mask is None:
                return msg
            sat = sat_name(prn_mask, prn)
            if not sat:
                return msg + self.trace.msg(0, f" (PRN mask number out of range: {prn} > {len(prn_mask)})", dec='dark')
            msg += self.trace.msg(1, f'\n{sat:<4s} IOD={iod} daf0={daf0*pow(2,-31):10.3e}[s] daf1={daf1*pow(2,-39):10.3e}[s/s] ti={ti*16}[s]'
                    f'\n{"":<4s}  dx={dx*0.125:10.3e}[m]    dy={dy*0.125:10.3e}[m]    dz={dz*0.125:10.3e}[m]'
                    f'\n{"":<4s} ddx={ddx*pow(2,-11):10.3e}[m/s] ddy={ddy*pow(2,-11):10.3e}[m/s] ddz={ddz*pow(2,-11):10.3e}[m/s]'
                    )
        return msg

    def decode_sbas_l1_authentication_message(self, df: BitStream) -> str:  # ref.[8], Table B-x1, MT20 (SBAS)
        '''
        MT20: SBAS L1 authentication message (TESLA)
        returns status string
        '''
        bemac1 = df.read( 28)  # block erasure MAC 1
        bemac2 = df.read( 28)  # block erasure MAC 2
        amac   = df.read( 28)  # aggregated message authentication code
        hp     = df.read(128)  # TESLA hash point of the previous authentication frame
        msg  = self.trace.msg(1, f'\nbeMAC1={bemac1.hex} beMAC2={bemac2.hex} aMAC={amac.hex}')
        msg += self.trace.msg(1, f'\nTESLA hash point={hp.hex}')
        return msg

    def decode_sbas_otar(self, df: BitStream) -> str:  # ref.[8], Table B-y1 and B-y3, MT21 (SBAS)
        '''
        MT21: SBAS over the air rekeying (OTAR), level 3 signature (confirmed hash point) message
        returns status string
        '''
        f_sig   = df.read(1).u  # 0: level 3 key material, 1: level 2 signature of level 3 key material
        iodk3   = df.read(3).u  # issue of data, key, level 3
        page    = df.read(3).u  # page number 0-7 (payload number = page + 1)
        payload = df.read(205)
        msg = self.trace.msg(1, f'\nIODK_lvl3={iodk3} page={page} ')
        if f_sig:
            msg += self.trace.msg(1, f'level 2 signature part {page+1}:\n{payload.u:052x}')
            return msg
        msg += self.trace.msg(1, f'level 3 key material, payload {page+1}:')
        if page == 0:
            iodk2    = payload.read( 3).u  # IODK of level 2 signing key
            slot     = payload.read( 3).u  # MT20 message slot, 0-5
            wn_start = payload.read(13).u  # level 3 validity start time, week number
            fr_start = payload.read(17).u  # level 3 validity start time, frame
            wn_dur   = payload.read( 3).u  # level 3 validity duration, weeks
            fr_dur   = payload.read(17).u  # level 3 validity duration, frames
            appl     = payload.read( 2).u  # level 3 key applicability
            crypto   = payload.read( 4).u  # cryptographic technique
            hashf    = payload.read( 2).u  # TESLA hash function
            chp      = payload.read(128)   # TESLA confirmed hash point
            valid    = payload.read( 8)    # IODK validity flags for IODK 0-7
            payload.pos += 5  # reserved
            valid_iodk = [str(i) for i in range(8) if valid[i]]
            msg += self.trace.msg(1, f'\nIODK_lvl2={iodk2} MT20_slot={slot}'
                    f' validity: start WN={wn_start} frame={fr_start}, duration {wn_dur}[week] + {fr_dur}[frame]')
            msg += self.trace.msg(1, f'\napplicability={L3KEY_APPLICABILITY.get(appl, appl)}'
                    f' technique={CRYPTO_TECHNIQUE.get(crypto, f"undefined({crypto})")}'
                    f' hash={TESLA_HASH_FUNCTION.get(hashf, hashf)}'
                    f' valid IODK_lvl3: {" ".join(valid_iodk) if valid_iodk else "none"}')
            msg += self.trace.msg(1, f'\nTESLA confirmed hash point={chp.hex}')
        elif page == 1:
            salt = payload.read(128)  # TESLA hash path salt
            payload.pos += 77  # reserved
            msg += self.trace.msg(1, f'\nTESLA hash path salt={salt.hex}')
        else:
            msg += self.trace.msg(1, f'\n(undefined payload) {payload.u:052x}')
        return msg

    def decode_mixed_fast_long_term_satellite_corrections(self, df: BitStream) -> str:  # ref.[4], MT24 (SBAS)
        '''
        MT24: Mixed fast/long-term satellite corrections
        returns status string
        '''
        fc    = [0 for _ in range(6)]
        udrei = [0 for _ in range(6)]
        for i in range(6):
            fc[i]    = df.read(12).i  # Fast correction
        for i in range(6):
            udrei[i] = df.read( 4).u  # UDREI
        iodp_sbas = df.read(2).u      # IODP
        msg_id    = df.read(2).u + 1  # fast correction ID, 1-4
        iodf      = df.read(2).u      # IODF
        df.pos    += 4  # reserved
        mt25sub   = df.read(106)
        prn_mask, msg = self.select_prn_mask_sbas(iodp_sbas)
        if prn_mask is None:
            msg25 = self.decode_mt25sub(mt25sub)
            return msg if msg25 == msg else msg + msg25  # avoid repeating the same status
        if len(prn_mask) < 13 * (msg_id-1) + 1:
            return msg + self.trace.msg(0, f" (PRN mask too short for fast correction ID {msg_id}: {len(prn_mask)} < {13 * (msg_id-1) + 1})", dec='dark')
        msg += self.trace.msg(1, f'\nSAT correction[m] (IODF={iodf})')
        for i, sat in enumerate(prn_mask[13*(msg_id-1):13*(msg_id-1)+6]):
            if fc[i] != 2047:
                msg += self.trace.msg(1, f"\n{sat:<4}: {fc[i]*0.125:8.3f}, UDREI={udrei[i]}")
            else:
                msg += self.trace.msg(1, f"\n{sat:<4}: {'VOID':>8s}, UDREI={udrei[i]}", dec='dark')
        msg += self.decode_mt25sub(mt25sub)
        return msg

    def decode_long_term_satellite_error_corrections(self, df: BitStream) -> str:  # ref.[4], MT25 (SBAS)
        '''
        MT25: Long-term satellite error corrections
        returns status string
        '''
        mt25sub1 = df.read(106)
        mt25sub2 = df.read(106)
        msg1 = self.decode_mt25sub(mt25sub1)
        msg2 = self.decode_mt25sub(mt25sub2)
        if msg1 == msg2:  # both halves return the same status (e.g. waiting for PRN mask); show it once
            return msg1
        return msg1 + msg2

    def decode_clock_ephemeris_covariance_matrix(self, df: BitStream) -> str:  # ref.[7], sect.A.4.4.16, MT28 (SBAS)
        '''
        MT28: Clock-ephemeris covariance matrix
        returns status string
        '''
        iodp_sbas = df.read(2).u  # IODP
        prn_mask, msg = self.select_prn_mask_sbas(iodp_sbas)
        for _ in range(2):  # two satellites per message
            prn = df.read(6).u  # PRN mask number, 0 = no data
            sfe = df.read(3).u  # scale exponent
            e11 = df.read(9).u  # E1,1
            e22 = df.read(9).u  # E2,2
            e33 = df.read(9).u  # E3,3
            e44 = df.read(9).u  # E4,4
            e12 = df.read(10).i  # E1,2
            e13 = df.read(10).i  # E1,3
            e14 = df.read(10).i  # E1,4
            e23 = df.read(10).i  # E2,3
            e24 = df.read(10).i  # E2,4
            e34 = df.read(10).i  # E3,4
            if prn == 0 or prn_mask is None:
                continue
            if len(prn_mask) < prn:
                msg += self.trace.msg(0, f" (PRN mask number out of range: {prn} > {len(prn_mask)})", dec='dark')
                continue
            sf = pow(2, sfe - 5)  # scale factor
            # relative covariance matrix C = SF^2 * R^T R, where R is upper triangular
            r = [[e11, e12, e13, e14],
                 [  0, e22, e23, e24],
                 [  0,   0, e33, e34],
                 [  0,   0,   0, e44]]
            c = [[sf * sf * sum(r[k][i] * r[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
            msg += self.trace.msg(1, f'\n{prn_mask[prn-1]:<4s} scale_exp={sfe} (SF=2^{sfe-5})'
                    f' E11={e11} E22={e22} E33={e33} E44={e44}'
                    f' E12={e12} E13={e13} E14={e14} E23={e23} E24={e24} E34={e34}')
            msg += self.trace.msg(2, '\n     relative covariance matrix (x, y, z, clock):')
            for i in range(4):
                msg += self.trace.msg(2, '\n    ' + ''.join(f' {c[i][j]:12.5e}' for j in range(4)))
        return msg

    def decode_ionospheric_delay_corrections(self, df: BitStream) -> str:  # ref.[4], MT26 (SBAS)
        '''
        MT26: Ionospheric delay corrections
        returns status string
        '''
        tau   = [0 for _ in range(15)]
        givei = [0 for _ in range(15)]
        igp_band  = df.read(4).u  # IGP band number, 0-10
        igp_block = df.read(4).u  # IGP block number, 0-13
        for i in range(15):
            tau  [i] = df.read(9).u  # IGP vertical delay estimate, LSB 0.125 m, 511 = not monitored
            givei[i] = df.read(4).u  # grid ionospheric vertical error indicator, 15 = not monitored
        iodi_sbas = df.read(2).u  # IODI
        df.pos += 7  # spare
        if self.iodi_sbas == UNDEF:
            return self.trace.msg(0, " (waiting for IGP masks, MT18)", dec='dark')
        if iodi_sbas != self.iodi_sbas:
            return self.trace.msg(0, f" (IODI mismatch: current {self.iodi_sbas} != received {iodi_sbas})", dec='dark')
        if len(IGP_TABLE) <= igp_band:
            return self.trace.msg(0, f" (invalid IGP band number: {igp_band})", dec='dark')
        mask = self.igp_mask[igp_band]
        if not mask.any(1):
            return self.trace.msg(0, f" (waiting for IGP mask of band {igp_band}, MT18)", dec='dark')
        # IGP block covers the 15 IGPs selected by the mask, counted from the block start
        igp_idx = [i for i in range(len(IGP_TABLE[igp_band])) if mask[i]][15*igp_block:15*igp_block+15]
        if not igp_idx:
            return self.trace.msg(0, f" (IGP block {igp_block} exceeds mask of band {igp_band}: {sum(1 for b in mask if b)} IGPs)", dec='dark')
        msg = self.trace.msg(1, f'\nIGP_band={igp_band} IGP_block={igp_block} IODI={iodi_sbas} ({len(igp_idx)} IGPs)')
        msg += self.trace.msg(1, '\nIGP lat[deg] lon[deg] delay[m] GIVE[m]')
        for i, idx in enumerate(igp_idx):
            lat, lon = IGP_TABLE[igp_band][idx]
            line = f'\n{idx+1:3d} {lat:8d} {lon:8d}'
            if tau[i] == 511 or givei[i] == 15:
                msg += self.trace.msg(1, line + f' {"n/a":>8s} {"n/a":>7s}', dec='dark')
            else:
                msg += self.trace.msg(1, line + f' {tau[i]*0.125:8.3f} {GIVEI2GIVE[givei[i]]:7.1f}')
        return msg

    RC2NAME_EN = {  # report classification (RC), ref.[2]
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
    DC2NAME_EN = {  # disaster category (DC), ref.[2]
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
    IT2NAME_EN = {  # information type (IT), ref.[2]
        0: "issue",
        1: "correction",
        2: "cancel",
    }
    IT2NAME_JP = {
        0: "発表",
        1: "訂正",
        2: "取消",
    }

    def decode_dcr (self, df: BitStream) -> str:  # ref.[2], MT43 (L1S)
        '''
        MT43: Japan Meteorological Agency Disaster and Crisis Management Report (JMA DCR)
        returns status string
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

    def decode_dcx(self, df: BitStream) -> str:  # ref.[5], sect.4.2, MT44 (L1S)
        '''
        MT44: Disaster and Crisis Management Report - Extended (DCX)
        returns status string
        '''
        # satellite designation (SD), 10 bits
        sdmt = df.read(1).u  # 0: service type, 1: MT44 transmission status
        sdm  = df.read(9)    # one bit per satellite
        # common alert message format (CAMF), 122 bits
        a1  = df.read( 2).u  # message type
        a2  = df.read( 9).u  # country/region
        a3  = df.read( 5).u  # provider identifier
        a4  = df.read( 7).u  # hazard category and type
        a5  = df.read( 2).u  # severity
        a6  = df.read( 1).u  # hazard onset: week number (0: current, 1: next)
        a7  = df.read(14).u  # hazard onset: time of the week [min], 0: not used
        a8  = df.read( 2).u  # hazard duration
        a9  = df.read( 1).u  # type of library (0: international, 1: country/region)
        a10 = df.read( 3).u  # version of library
        a11 = df.read(10)    # instruction library
        a12 = df.read(16).u  # ellipse centre latitude
        a13 = df.read(17).u  # ellipse centre longitude
        a14 = df.read( 5).u  # ellipse semi-major axis
        a15 = df.read( 5).u  # ellipse semi-minor axis
        a16 = df.read( 6).u  # ellipse azimuth
        a17 = df.read( 2).u  # type of specific settings
        a18 = df.read(15)    # specific settings
        ext = df.read(74)    # extended message
        df.pos += 6          # reserved
        # satellite designation
        sd_name = 'MT44 transmission' if sdmt else 'service type'
        sats = []
        for i, prn in DCX_SDM2PRN.items():
            if sdmt:
                sats.append(f'{prn}:{"on" if sdm[i] else "off"}')
            else:
                sats.append(f'{prn}:{"abroad" if sdm[i] else "Japan"}')
        sd_msg = self.trace.msg(2, f'\nSD ({sd_name}): ' + ' '.join(sats))
        if a1 == 0 and a3 == 0 and a4 == 0 and not ext.any(1):  # NULL message, ref.[5], Table 4.3-1
            return self.trace.msg(0, ' (NULL message)', dec='dark') + sd_msg
        # CAMF
        country  = libcamf.COUNTRY.get(a2, f'country {a2}')
        provider = DCX_PROVIDER_JP.get(a3, f'provider {a3}') if a2 == 111 else f'provider {a3}'
        msg = f': {libcamf.MSG_TYPE[a1]} {libcamf.HAZARD.get(a4, f"hazard {a4}")} ({libcamf.SEVERITY[a5]})'
        msg += sd_msg
        msg += self.trace.msg(1, f'\n{country}, {provider}')
        msg += self.trace.msg(1, f'\nonset: {libcamf.onset_str(a6, a7)}, duration {libcamf.DURATION[a8]}')
        lib = 'country/region' if a9 else 'international'
        msg += self.trace.msg(1, f'\nlibrary: {lib} #{a10+1}')
        if a9 == 0:  # international library, list A and list B, ref.[9] Annex C.11
            ic_a = a11.read(5).u
            ic_b = a11.read(5).u
            msg += self.trace.msg(1, f'\ninstruction: IC-A-{ic_a+1:02d} "{libcamf.LIST_A.get(ic_a, "")}"')
            msg += self.trace.msg(1, f'\n             IC-B-{ic_b+1:02d} "{libcamf.LIST_B.get(ic_b, "")}"')
        else:        # country/region library (Japan), Table 4.2-14 and 4.2-15
            basic = a11.read(2).u
            info  = a11.read(8).u
            if basic == 0:
                msg += self.trace.msg(1, f'\ninstruction: "{DCX_INSTRUCTION_A11.get(info, f"code {info}")}"')
            else:
                msg += self.trace.msg(1, f'\ninstruction: "{DCX_BASIC_INSTRUCTION[basic]} {DCX_BASIC_INSTRUCTION_INFO.get(info, f"code {info}")}"'.replace('. "', '."'))
        lat = -90 + 180 * a12 / (pow(2, 16) - 1)
        lon = -180 + 360 * a13 / (pow(2, 17) - 1)
        az  = -90 + 180 * a16 / pow(2, 6)
        if a12 or a13 or a14 or a15 or a16:
            msg += self.trace.msg(1, f'\nellipse: centre {lat:.3f} {lon:.3f}, semi-major {libcamf.RADIUS_KM[a14]:.3f}[km], semi-minor {libcamf.RADIUS_KM[a15]:.3f}[km], azimuth {az:.2f}[deg]')
        msg += self.trace.msg(2, f'\nspecific settings: {libcamf.SPECIFIC_SETTINGS[a17]} {a18.bin}')
        for line in libcamf.decode_specific_settings(a17, a18, a4, lat, lon, a14, a15, az):
            msg += self.trace.msg(1, '\n' + line)
        # extended message
        if a2 != 111:  # organizations outside Japan, Table 4.2-26
            ex11 = ext.read(68)
            vn   = ext.read( 6).u
            msg += self.trace.msg(2, f'\nextended (outside Japan): {ex11.bin} version {vn}')
        elif a3 in (2, 3):  # J-Alert, Table 4.2-23
            ex8 = ext.read( 1).u  # 0: prefecture code, 1: cities, towns and villages code
            ex9 = ext.read(64)
            ext.pos += 3  # reserved
            vn  = ext.read( 6).u
            if ex8 == 0:
                pref = ex9.read(47)
                names = [DCX_PREFECTURE[46 - i] for i in reversed(range(47)) if pref[i]]  # last bit is Hokkaido
                msg += self.trace.msg(1, f'\ntarget prefectures: {" ".join(names) if names else "(none)"}')
            else:
                codes = [ex9.read(16).u for _ in range(4)]
                msg += self.trace.msg(1, f'\ntarget area codes: ' + ' '.join(f'{c:05d}' for c in codes if c))
            msg += self.trace.msg(2, f'\nextended message version {vn}')  # not fixed to 1 in actual broadcasts
        else:  # L-Alert and local government, Table 4.2-20
            ex1 = ext.read(16).u  # target area code
            ex2 = ext.read( 1).u  # evacuate direction type
            ex3 = ext.read(17).u  # additional ellipse centre latitude
            ex4 = ext.read(17).u  # additional ellipse centre longitude
            ex5 = ext.read( 5).u  # additional ellipse semi-major axis
            ex6 = ext.read( 5).u  # additional ellipse semi-minor axis
            ex7 = ext.read( 7).u  # additional ellipse azimuth
            vn  = ext.read( 6).u  # version number
            if ex1:
                msg += self.trace.msg(1, f'\ntarget area code: {ex1:05d}')
            if ex3 or ex4 or ex5 or ex6 or ex7:
                lat = -90 + 180 * ex3 / (pow(2, 17) - 1)
                lon =  45 + 180 * ex4 / (pow(2, 17) - 1)
                az  = -90 + 180 * ex7 / pow(2, 7)
                direction = 'head to' if ex2 else 'leave'
                msg += self.trace.msg(1, f'\nadditional ellipse ({direction}): centre {lat:.3f} {lon:.3f}, semi-major {libcamf.RADIUS_KM[ex5]:.3f}[km], semi-minor {libcamf.RADIUS_KM[ex6]:.3f}[km], azimuth {az:.2f}[deg]')
            msg += self.trace.msg(2, f'\nextended message version {vn}')  # not fixed to 1 in actual broadcasts
        return msg

    def decode_monitoring_station_info(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.6, MT47 (L1S)
        '''
        MT47: monitoring station information
        returns status string
        '''
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

    def decode_prn_mask(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.7, MT48 (L1S)
        '''
        MT48: PRN mask
        returns decoded message
        '''
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

    def decode_data_issue_number(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.8, MT49 (L1S)
        '''
        MT49: data issue number
        returns status string
        '''
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

    def decode_dgps_correction(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.9, MT50 (L1S)
        '''
        MT50: DGPS correction message
        returns status string
        '''
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

    def decode_satellite_health(self, df: BitStream) -> str:  # ref.[3], sect.4.1.2.10, MT51 (L1S)
        '''
        MT51: satellite health
        returns status string
        '''
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

    def decode_l1s (self, l1s: BitStream) -> str:
        ''' returns decoded message '''
        L_PAB: int =   8  # length of preamble in bits
        L_MT : int =   6  # length of message type in bits
        L_CRC: int =  24  # length of CRC in bits
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
        mt_name = MT2NAME.get(mt.u, f"MT {mt.u}")
        msg = self.trace.msg(0, f'MT{mt.u:02d}: ', fg='yellow') + self.trace.msg(0, mt_name, fg='cyan')
        if   mt_name == 'Test mode':                        # MT0 (L1S and SBAS)
            msg += self.decode_test_mode(df)
        elif mt_name == 'SBAS PRN mask':                    # MT1  (SBAS)
            msg += self.decode_sbas_prn_mask(df)
        elif mt_name.startswith('Fast corrections'):        # MT2-5 (SBAS)
            msg += self.decode_fast_correction(df, mt.u - 1)  # message number 1-4
        elif mt_name == 'Integrity information':            # MT6 (SBAS)
            msg += self.decode_integrity_information(df)
        elif mt_name == 'Fast correction degradation factor':  # MT7 (SBAS)
            msg += self.decode_fast_correction_degradation_factor(df)
        elif mt_name == 'GEO ranging function parameters':  # MT9 (SBAS)
            msg += self.decode_geo_ranging_function_parameters(df)
        elif mt_name == 'Degradation factors':              # MT10 (SBAS)
            msg += self.decode_degradation_factors(df)
        elif mt_name == 'SBAS network time/UTC offset parameters':  # MT12 (SBAS)
            msg += self.decode_sbas_network_time_utc_offset_parameters(df)
        elif mt_name == 'GEO satellite almanacs':           # MT17 (SBAS)
            msg += self.decode_geo_satellite_almanacs(df)
        elif mt_name == 'Ionospheric grid point masks':     # MT18 (SBAS)
            msg += self.decode_ionospheric_grid_point_masks(df)
        elif mt_name == 'SBAS L1 authentication message':   # MT20 (SBAS)
            msg += self.decode_sbas_l1_authentication_message(df)
        elif mt_name == 'SBAS over the air rekeying (OTAR)':  # MT21 (SBAS)
            msg += self.decode_sbas_otar(df)
        elif mt_name == 'Mixed fast/long-term satellite corrections':  # MT24 (SBAS)
            msg += self.decode_mixed_fast_long_term_satellite_corrections(df)
        elif mt_name == 'Long-term satellite error corrections':  # MT25 (SBAS)
            msg += self.decode_long_term_satellite_error_corrections(df)
        elif mt_name == 'Ionospheric delay corrections':    # MT26 (SBAS)
            msg += self.decode_ionospheric_delay_corrections(df)
        elif mt_name == 'Clock-ephemeris covariance matrix':  # MT28 (SBAS)
            msg += self.decode_clock_ephemeris_covariance_matrix(df)
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
        elif mt_name == 'Null message':                     # MT63 (SBAS)
            pass  # do nothing for null message
        else:
            msg += self.trace.msg(1, f'\n(not implemented)')
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
