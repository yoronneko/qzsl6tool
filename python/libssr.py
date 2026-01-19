#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libssr.py: library for SSR and compact SSR message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2026 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office, Government of Japan, Quasi-Zenith Satellite System
#     Interface Specification Centimeter Level Augmentation Service,
#     IS-QZSS-L6-005, Sept. 21, 2022.
# [2] Global Positioning Augmentation Service Corporation (GPAS),
#     Quasi-Zenith Satellite System Correction Data on Centimeter Level
#     Augmentation Service for Experiment Data Format Specification,
#     1st ed., Nov. 2017.
# [3] Cabinet Office, Government of Japan, Quasi-Zenith Satellite System
#     Interface Specification Multi-GNSS Advanced Orbit and Clock Augmentation
#     - Precise Point Positioning, IS-QZSS-MDC-002, Nov., 2023.
# [4] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.
# [5] European Union Agency for the Space Programme,
#     Galileo High Accuracy Service Signal-in-Space Interface Control
#     Document (HAS SIS ICD), Issue 1.0 May 2022.
# [6] Cabinet Office, Government of Japan, Quasi-Zenith Satellite System
#     Interface Specification Multi-GNSS Advanced Orbit and Clock Augmentation
#     - Precise Point Positioning, IS-QZSS-MDC-004-Draft, May 2025.

import sys

import libtrace

try:
    from bitstring import BitStream
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

URA_INVALID = 0    # invalid user range accuracy
CSSR_UI = [        # CSSR update interval in second, ref.[3], Table 4.2.2-6
    1, 2, 5, 10, 15, 30, 60, 120, 240, 300, 600, 900, 1800, 3600, 7200, 10800
]
HAS_VI = [         # HAS validity interval in second
    5, 10, 15, 20, 30, 60, 90, 120, 180, 240, 300, 600, 900, 1800, 3600, 0
]
FMT_ORB    = '7.4f'  # format string for orbit
FMT_CLK    = '7.3f'  # format string for clock
FMT_CB     = '7.3f'  # format string for code bias
FMT_PB     = '7.3f'  # format string for phase bias
FMT_TROP   = '7.3f'  # format string for troposphere residual
FMT_TECU   = '6.2f'  # format string for TECU
FMT_IODE   = '4d'    # format string for issue of data ephemeris
FMT_IODSSR = '<2d'   # format string for issue of data SSR
FMT_GSIG   = '13s'   # format string for GNSS signal name
FMT_URA    = '7.2f'  # format string for URA
N_NID      = 19      # number of compact network ID, = len(CLASGRID)
CLASGRID   = [       # CLAS grid, [location, number of grid, ([lat, lon]), ..., see ref[1] and https://s-taka.org/en/clasgrid/
["ISHIGAKI", 8, [
(24.75, 125.37), (24.83, 125.17), (24.64, 124.69), (24.54, 124.30), (24.34, 124.17), (24.06, 123.80), (24.43, 123.79), (24.45, 122.94),],],
["OKINAWA", 11, [
(26.42, 126.87), (26.15, 127.53), (26.69, 127.53), (26.69, 128.18), (27.23, 128.18), (27.23, 128.84), (27.77, 128.51), (27.77, 129.17), (28.30, 129.17), (28.30, 129.83), (25.83, 131.23),],],
["KYUSYU", 32, [
(33.16, 129.50), (33.70, 129.50), (34.23, 129.50), (34.77, 129.50), (34.23, 128.84), (32.62, 128.84), (33.16, 128.84), (31.81, 129.50), (31.00, 130.49), (31.00, 131.14), (30.46, 130.49), (30.46, 131.14), (31.54, 130.16), (32.08, 130.16), (32.62, 130.16), (33.16, 130.16), (33.70, 130.16), (31.54, 130.82), (32.08, 130.82), (32.62, 130.82), (33.16, 130.82), (33.70, 130.82), (31.54, 131.47), (32.08, 131.47), (32.62, 131.47), (33.16, 131.47), (33.70, 131.47), (28.84, 128.84), (28.84, 129.50), (29.38, 129.50), (29.92, 129.50), (29.92, 130.16),],],
["SHIKOKU", 15, [
(32.62, 132.13), (33.16, 132.13), (33.70, 132.13), (32.62, 132.79), (33.16, 132.79), (33.70, 132.79), (34.23, 132.79), (33.16, 133.45), (33.70, 133.45), (34.23, 133.45), (33.16, 134.11), (33.70, 134.11), (34.23, 134.11), (33.70, 134.76), (34.23, 134.76),],],
["CHUGOKU", 15, [
(34.23, 130.82), (34.23, 131.47), (34.77, 131.47), (34.23, 132.13), (34.77, 132.13), (34.77, 132.79), (35.31, 132.79), (34.77, 133.45), (35.31, 133.45), (35.85, 132.79), (35.85, 133.45), (36.39, 133.45), (34.77, 134.11), (35.31, 134.11), (35.85, 134.11),],],
["KANSAI", 27, [
(34.77, 134.76), (35.31, 134.76), (35.85, 134.76), (33.70, 135.42), (34.23, 135.42), (34.77, 135.42), (35.31, 135.42), (35.85, 135.42), (33.70, 136.08), (34.23, 136.08), (34.77, 136.08), (35.31, 136.08), (35.85, 136.08), (36.39, 136.08), (34.23, 136.74), (34.77, 136.74), (35.31, 136.74), (35.85, 136.74), (36.39, 136.74), (36.93, 136.74), (37.47, 136.74), (34.77, 137.40), (35.31, 137.40), (35.85, 137.40), (36.39, 137.40), (36.93, 137.40), (37.47, 137.40),],],
["KANTO", 22, [
(34.77, 138.05), (35.31, 138.05), (35.85, 138.05), (36.39, 138.05), (34.77, 138.71), (35.31, 138.71), (35.85, 138.71), (36.39, 138.71), (34.23, 139.04), (34.23, 139.70), (34.77, 139.37), (35.31, 139.37), (35.85, 139.37), (36.39, 139.37), (34.77, 140.03), (35.31, 140.03), (35.85, 140.03), (36.39, 140.03), (35.31, 140.69), (35.85, 140.69), (36.39, 140.69), (33.11, 139.79),], ],
["TOHOKU-SOUTH", 20, [
(36.93, 138.05), (36.93, 138.71), (37.47, 138.71), (37.74, 138.05), (38.28, 138.05), (38.01, 138.71), (36.93, 139.37), (37.47, 139.37), (38.01, 139.37), (38.55, 139.37), (36.93, 140.03), (37.47, 140.03), (38.01, 140.03), (38.55, 140.03), (36.93, 140.69), (37.47, 140.69), (38.01, 140.69), (38.55, 140.69), (37.47, 141.34), (38.55, 141.34),],],
["TOHOKU-NORTH", 18, [
(39.09, 140.03), (39.62, 140.03), (40.16, 140.03), (40.70, 140.03), (41.24, 140.03), (39.09, 140.69), (39.62, 140.69), (40.16, 140.69), (40.70, 140.69), (41.24, 140.69), (39.09, 141.34), (39.62, 141.34), (40.16, 141.34), (40.70, 141.34), (41.24, 141.34), (39.09, 142.00), (39.62, 142.00), (40.16, 142.00),],],
["HOKKAIDO-WEST", 23, [
(42.32, 139.37), (41.78, 140.03), (42.32, 140.03), (42.86, 140.03), (41.78, 140.69), (42.32, 140.69), (42.86, 140.69), (43.40, 140.69), (41.78, 141.34), (42.32, 141.34), (42.86, 141.34), (43.40, 141.34), (43.94, 141.34), (42.32, 142.00), (42.86, 142.00), (43.40, 142.00), (43.94, 142.00), (42.32, 142.66), (42.86, 142.66), (43.40, 142.66), (41.78, 143.32), (42.32, 143.32), (42.86, 143.32),],],
["HOKKAIDO-EAST", 19, [
(45.28, 141.34), (44.48, 142.00), (45.01, 142.00), (45.55, 142.00), (43.94, 142.66), (44.48, 142.66), (45.01, 142.66), (43.40, 143.32), (43.94, 143.32), (44.48, 143.32), (42.86, 143.98), (43.40, 143.98), (43.94, 143.98), (42.86, 144.63), (43.40, 144.63), (43.94, 144.63), (43.40, 145.29), (43.94, 145.29), (44.48, 145.29),],],
["OGASAWARA", 2, [
(27.07, 142.20), (26.64, 142.16),],],
["HOKKAIDO-ISLAND", 13, [
(43.40, 145.95), (43.94, 145.95), (44.48, 145.95), (43.94, 146.61), (44.48, 146.61), (45.01, 146.61), (44.48, 147.27), (45.01, 147.27), (45.01, 147.92), (45.55, 147.92), (45.01, 148.58), (45.55, 148.58), (45.55, 149.24),],],
["ISLAND (TAKESHIMA)", 1, [ (37.24, 131.87),],],
["ISLAND (KITA-DAITO)", 1, [(25.96, 131.31),],],
["ISLAND (UOTSURI)", 1, [(25.73, 123.54),],],
["ISLAND (IOU)", 1, [(24.77, 141.34),],],
["ISLAND (MINAMI-TORISHIMA)", 1, [(24.28, 153.99),],],
["ISLAND (OKINOSHIMA)", 1, [(20.44, 136.09),],],
]

def epoch2time(epoch: int) -> str:
    ''' convert epoch to time
        epoch: epoch in second (0-86400)
    '''
    hour = epoch // 3600
    min  = (epoch % 3600) // 60
    sec  = epoch % 60
    return f'{hour:02d}:{min:02d}:{sec:02d}'
    # return f'{hour:02d}:{min:02d}:{sec:02d} ({epoch})'

def epoch2timedate(epoch: int) -> str:
    ''' convert epoch to time plus date'''
    return f'{epoch2time(epoch%86400)}+{epoch//86400}'

def gnssid2satsys(gnssid: int) -> str:
    ''' convert gnss id to satellite system '''
    if   gnssid == 0: satsys = 'G'  # GPS
    elif gnssid == 1: satsys = 'R'  # GLONASS
    elif gnssid == 2: satsys = 'E'  # Galileo
    elif gnssid == 3: satsys = 'C'  # BeiDou
    elif gnssid == 4: satsys = 'J'  # QZSS
    elif gnssid == 5: satsys = 'S'  # SBAS in ref.[1]
    elif gnssid == 7: satsys = 'D'  # BDS3 in ref.[6], MADOCA-PPP workaround (D01 stand for C19, D02 for C20, ...)
    else            : satsys = '?'  # reserved
    return satsys

def sigmask2signame(satsys: str, sigmask: int) -> str:
    ''' convert satellite system and signal mask to signal name '''
    signame = f'satsys={satsys} sigmask={sigmask}'
    if satsys == 'G':
        signame = [ "L1C/A", "L1P", "L1Z-tracking", "L1C(D)", "L1C(P)", "L1C(D+P)", "L2CM", "L2CL", "L2CM+L", "L2P", "L2Z-tracking", "L5I", "L5Q", "L5I+Q", "", ""][sigmask]
    elif satsys == 'R':
        signame = [ "G1C/A", "G1P", "G2C/A", "G2P", "G1a(D)", "G1a(P)", "G1a(D+P)", "G2a(D)", "G2a(P)", "G2a(D+P)", "G3I", "G3Q", "G3I+Q", "", "", "", ""][sigmask]
    elif satsys == 'E':
        signame = [ "E1B", "E1C", "E1B+C", "E5aI", "E5aQ", "E5aI+Q", "E5bI", "E5bQ", "E5bI+Q", "E5I", "E5Q", "E5I+Q", "E6B", "E6C", "E6B+C", ""][sigmask]
    elif satsys == 'C':
        signame = [ "B1I", "B1Q", "B1I+Q", "B3I", "B3Q", "B3I+Q", "B2I", "B2Q", "B2I+Q", "", "", "", "", "", "", ""][sigmask]
    elif satsys == 'D':  # MADOCA-PPP workaround for ref.[6]
        signame = [ "B1I", "B1Q", "B1I+Q", "B3I", "B3Q", "B3I+Q", "B2bI", "B2bQ", "B2bI+Q", "B1C(D)", "B1C(P)", "B1C(D+P)", "B2a(D)", "B2a(P)", "B2a(D+P)", ""][sigmask]
    elif satsys == 'J':
        signame = [ "L1C/A", "L1C(D)", "L1C(P)", "L1C(D+P)", "L2CM", "L2CL", "L2CM+L", "L5I", "L5Q", "L5I+Q", "", "", "", "", "", ""][sigmask]
    elif satsys == 'S':
        signame = [
            "L1C/A", "L5I", "L5Q", "L5I+Q", "", "", "", "", "", "", "", "", "", "", "", "", ""][sigmask]
    else:
        raise Exception(
            f'unassigned signal name for satsys={satsys} and sigmask={sigmask}')
    return signame

def sigmask2signame_b2b(satsys: str, sigmask: int) -> str:
    ''' convert satellite system and signal mask to signal name '''
    signame = f'satsys={satsys} sigmask={sigmask}'
    if satsys == 'G':
        signame = ["L1C/A", "L1P", "", "", "L1C(P)", "L1C(D+P)", "", "L2CL", "L2CM+L", "", "", "L5I", "L5Q", "L5I+Q", "", ""][sigmask]
    elif satsys == 'R':
        signame = ["G1C/A", "G1P", "G2C/A", "", "", "", "", "", "", "", "", "", "", "", "", ""][sigmask]
    elif satsys == 'E':
        signame = ["", "E1B", "E1C", "", "E5aQ", "E5aI", "", "E5bI", "E5bQ", "", "", "E6C", "", "", "", ""][sigmask]
    elif satsys == 'C':
        signame = ["B1I", "B1C(D)", "B1C(P)", "", "B2a(D)", "B2a(P)", "", "B2bI", "B2bQ", "", "", "", "B3I", "", "", ""][sigmask]
    else:
        raise Exception(
            f'unassigned signal name for satsys={satsys} and sigmask={sigmask}')
    return signame

def ura2dist(ura: BitStream) -> float:
    ''' converts user range accuracy (URA) code to accuracy in distance [mm] '''
    dist = 0.0
    if   ura.b == '000000':   # undefined or unknown
        dist = URA_INVALID
    elif ura.b == '111111':   # URA more than 5466.5 mm
        dist = 5466.5
    else:
        cls  = ura[4:7].u
        val  = ura[0:4].u
        dist = 3 ** cls * (1 + val / 4) - 1
    return dist


class Ssr:
    """class of state space representation (SSR) and compact SSR process"""
    subtype    = 0      # subtype number
    ssr_nsat   = 0      # number of satellites
    ssr_mmi    = 0      # multiple message indicator
    ssr_iod    = 0      # iod ssr
    epoch      = 0      # epoch
    hepoch     = 0      # hourly epoch
    interval   = 0      # update interval
    mmi        = 0      # multiple message indication
    satsys     = []     # array of satellite system
    nsatmask   = []     # array of number of satellite mask
    nsigmask   = []     # array of number of signal mask
    cellmask   = []     # array of cell mask
    gsys       = {}     # dict of sat    name from system name
    gsig       = {}     # dict of signal name from system name
    stat       = False  # statistics output
    stat_nsat  = 0      # stat: number of satellites
    stat_nsig  = 0      # stat: number of signals
    stat_bsat  = 0      # stat: bit number of satellites
    stat_bsig  = 0      # stat: bit number of signals
    stat_both  = 0      # stat: bit number of other information
    stat_bnull = 0      # stat: bit number of null

    def __init__(self, trace: libtrace.Trace) -> None:
        self.trace = trace

    def ssr_decode_head(self, payload: BitStream, satsys: str, mtype: str) -> str:
        ''' stores ssr_epoch, ssr_interval, ssr_mmi, ssr_iod, ssr_nsat'''
        # bit format of ssr_epoch changes according to satellite system
        bw = 20 if satsys != 'R' else 17
        self.ssr_epoch     = payload.read(bw).u  # epoch time
        self.ssr_interval  = payload.read( 4).u  # SSR update interval
        self.ssr_mmi       = payload.read( 1).u  # multiple message indication
        if mtype == 'SSR orbit' or mtype == 'SSR obt/clk':
            self.ssr_sdat  = payload.read( 1).u  # sat ref datum
        self.ssr_iod       = payload.read( 4).u  # IOD SSR
        self.ssr_pid       = payload.read(16).u  # SSR provider ID
        self.ssr_sid       = payload.read( 4).u  # SSR solution ID
        # bit format of nsat changes with satsys
        bw = 6 if satsys != 'J' else 4
        self.ssr_nsat      = payload.read(bw).u
        msg = f'\nEpoch={epoch2timedate(self.ssr_epoch)} UI={CSSR_UI[self.ssr_interval]} MMI={self.ssr_mmi}'
        if mtype == 'SSR orbit' or mtype == 'SSR obt/clk':
            msg += f' Datum={self.ssr_sdat}'
        msg += f' IODSSR={self.ssr_iod:{FMT_IODSSR}} Provider={self.ssr_pid} Solution={self.ssr_sid}'
        return self.trace.msg(2, msg)

    def ssr_decode_orbit(self, payload: BitStream, satsys: str) -> str:
        ''' decodes SSR orbit correction and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 4  # ref. [2]
        elif satsys == 'R': bw = 5  # ref. [1]
        else:               bw = 6  # ref. [1]
        msg1 = self.trace.msg(1, '\nSAT IODE radial[m] along[m] cross[m] d_radial[m/s] d_along[m/s] d_cross[m/s]')
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid   = payload.read(bw).u  # satellite ID, DF068
            iode    = payload.read( 8).u  # IODE, DF071
            radial  = payload.read(22).i  # radial, DF365
            along   = payload.read(20).i  # along track, DF366
            cross   = payload.read(20).i  # cross track, DF367
            dradial = payload.read(21).i  # dot_radial, DF368
            dalong  = payload.read(19).i  # dot_along track, DF369
            dcross  = payload.read(19).i  # dot_cross track, DF370
            strsat += f"{satsys}{satid:02} "
            msg1 += self.trace.msg(1, f'\n{satsys}{satid:02d} {iode:{FMT_IODE}}   {radial*1e-4:{FMT_ORB}}  {along*4e-4:{FMT_ORB}}  {cross*4e-5:{FMT_ORB}}       {dradial*1e-6:{FMT_ORB}}      {dalong*4e-6:{FMT_ORB}}      {dcross*4e-6:{FMT_ORB}}')
        msg = self.trace.msg(0, f"{strsat}(IOD={self.ssr_iod} nsat={self.ssr_nsat}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def ssr_decode_clock(self, payload: BitStream, satsys: str) -> str:
        ''' decodes SSR clock correction and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 4  # ref. [2]
        elif satsys == 'R': bw = 5  # ref. [1]
        else              : bw = 6  # ref. [1]
        msg1 = self.trace.msg(1, '\nSAT   c0[m] c1[m/s] c2[m/s^2]')
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid = payload.read(bw).u  # satellite ID
            c0    = payload.read(22).i  # delta clock c0, DF376
            c1    = payload.read(21).i  # delta clock c1, DF377
            c2    = payload.read(27).i  # delta clock c2, DF378
            strsat += f"{satsys}{satid:02d} "
            msg1 += self.trace.msg(1, f'\n{satsys}{satid:02d} {c0*1e-4:{FMT_CLK}} {c1*1e-6:{FMT_CLK}}   {c2*2e-8:{FMT_CLK}}')
        msg = self.trace.msg(0, f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def ssr_decode_code_bias(self, payload: BitStream, satsys: str) -> str:
        ''' decodes SSR code bias and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 4   # ref. [2]
        elif satsys == 'R': bw = 5   # ref. [1]
        else              : bw = 6   # ref. [1]
        msg1 = self.trace.msg(1, '\nSAT signal_name code_bias[m]')
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid = payload.read(bw).u  # satellite ID, DF068, ...
            ncb   = payload.read( 5).u  # code bias number, DF383
            strsat += f"{satsys}{satid:02d} "
            for j in range(ncb):
                stmi  = payload.read( 5).u  # sig&trk mode ind, DF380
                cb    = payload.read(14).i  # code bias, DF383
                sstmi = sigmask2signame(satsys, stmi)
                msg1 += self.trace.msg(1, f'\n{satsys}{satid:02d} {sstmi:{FMT_GSIG}}    {cb*1e-2:{FMT_CB}}')
        msg = self.trace.msg(0, f"{strsat}(IOD={self.ssr_iod} nsat={self.ssr_nsat}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def ssr_decode_ura(self, payload: BitStream, satsys: str) -> str:
        ''' decodes SSR user range accuracy and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 4  # ref. [2]
        elif satsys == 'R': bw = 5  # ref. [1]
        else              : bw = 6  # ref. [1]
        msg1 = self.trace.msg(1, '\nSAT URA[mm]')
        strsat = ''
        for i in range(self.ssr_nsat):
            satid = payload.read(bw).u  # satellite ID, DF068
            ura   = payload.read( 6)  # user range accuracy, DF389
            accuracy = ura2dist(ura)
            if accuracy != URA_INVALID:
                msg1 += self.trace.msg(1, f'\n{satsys}{satid:02d} {accuracy:{FMT_URA}}')
                strsat += f"{satsys}{satid:02} "
        msg = self.trace.msg(0, f"{strsat}(IOD={self.ssr_iod} nsat={self.ssr_nsat}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def ssr_decode_hr_clock(self, payload: BitStream, satsys: str) -> str:
        '''decodes SSR high rate clock and returns string'''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 4
        elif satsys == 'R': bw = 5
        else              : bw = 6
        msg1 = self.trace.msg(1, '\nSAT high_rate_clock[m]')
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid = payload.read(bw).u  # satellite ID
            hrc   = payload.read(22).i  # high rate clock, DF390
            strsat += f"{satsys}{satid:02} "
            msg1 += self.trace.msg(1, f'\n{satsys}{satid:02}            {hrc*1e-4:{FMT_CLK}}')
        msg = self.trace.msg(0, f"{strsat}(IOD={self.ssr_iod} nsat={self.ssr_nsat}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def decode_cssr(self, payload: BitStream) -> str:
        ''' calls cssr decode functions and returns decoded string '''
        if not self.decode_cssr_head(payload):
            return 'Could not decode CSSR header'
        if   self.subtype ==  1: self.decode_cssr_st1 (payload)
        elif self.subtype ==  2: self.decode_cssr_st2 (payload)
        elif self.subtype ==  3: self.decode_cssr_st3 (payload)
        elif self.subtype ==  4: self.decode_cssr_st4 (payload)
        elif self.subtype ==  5: self.decode_cssr_st5 (payload)
        elif self.subtype ==  6: self.decode_cssr_st6 (payload)
        elif self.subtype ==  7: self.decode_cssr_st7 (payload)
        elif self.subtype ==  8: self.decode_cssr_st8 (payload)
        elif self.subtype ==  9: self.decode_cssr_st9 (payload)
        elif self.subtype == 10: self.decode_cssr_st10(payload)
        elif self.subtype == 11: self.decode_cssr_st11(payload)
        elif self.subtype == 12: self.decode_cssr_st12(payload)
        else:
            raise Exception(f"unknown CSSR subtype: {self.subtype}")
        msg = f'ST{self.subtype:<2d}'
        if self.subtype == 1:
            msg += f' Epoch={epoch2timedate(self.epoch)} ({self.epoch}) UI={CSSR_UI[self.ui]:2d}s ({self.ui}) IODSSR={self.iodssr} {"cont." if self.mmi else ""}'
        else:
            etime=f'{self.hepoch//60:02d}:{self.hepoch%60:02d}'
            msg += f' Epoch={etime} ({self.hepoch}) UI={CSSR_UI[self.ui]:2d}s ({self.ui}) IODSSR={self.iodssr}{" cont." if self.mmi else ""}'
        return msg

    def show_cssr_stat(self) -> None:
        bit_total = self.stat_bsat + self.stat_bsig + self.stat_both + \
                self.stat_bnull
        msg = f'stat n_sat {self.stat_nsat} n_sig {self.stat_nsig} ' + \
              f'bit_sat {self.stat_bsat} bit_sig {self.stat_bsig} ' + \
              f'bit_other {self.stat_both} bit_null {self.stat_bnull} ' + \
              f'bit_total {bit_total}'
        self.trace.show(0, msg)

    def decode_cssr_head(self, payload: BitStream) -> bool:
        ''' decode CSSR header and returns True if success '''
        self.msgnum  = 0
        self.subtype = 0
        len_payload = len(payload)
        if payload.all(0):  # payload is zero padded
            self.trace.show(2, f"CSSR null data {len(payload.bin)} bits", fg='green')
            return False
        if len_payload < payload.pos + 12:
            return False
        self.msgnum  = payload.read(12).u
        if self.msgnum == 4073:  # for CLAS and MADOCA-PPP clock & orbit corrections (ref. [1])
            if len_payload < payload.pos + 4:
                return False
            self.subtype = payload.read(4).u  # subtype
            if self.subtype == 1:  # Mask message
                if len_payload < payload.pos + 20:  # could not retrieve the epoch
                    return False
                self.epoch = payload.read(20).u  # GPS epoch time 1s
            elif self.subtype == 10:  # Service Information
                return True
            else:
                if len_payload < payload.pos + 12:  # could not retrieve hourly epoch
                    return False
                self.hepoch = payload.read(12).u  # GNSS hourly epoch
            if len_payload < payload.pos + 4 + 1 + 4:
                return False
            self.ui     = payload.read(4).u  # update interval
            self.mmi    = payload.read(1).u  # multiple message indication
            self.iodssr = payload.read(4).u  # IOD SSR
            return True
        self.trace.show(0, f"CSSR msgnum should be 4073 ({self.msgnum}), size {len(payload.bin)} bits\nCSSR dump: {payload.bin}", fg='red')
        return False

    def _decode_mask(self, payload: BitStream, ssr_type: str) -> bool:
        ''' decode mask information and returns True if success
            ssr_type: cssr or has
        '''
        if ssr_type not in {'cssr', 'has'}:
            raise Exception(f'unknown ssr_type: {ssr_type}')
        len_payload = len(payload)
        if len_payload < payload.pos + 4:
            return False
        ngnss = payload.read(4).u  # number of GNSS
        if len_payload < payload.pos + 61 * ngnss:
            return False
        satsys   = [''               for _ in range(ngnss)]
        nsatmask = [0                for _ in range(ngnss)]
        nsigmask = [0                for _ in range(ngnss)]
        cellmask = [BitStream() for _ in range(ngnss)]
        navmsg   = [0                for _ in range(ngnss)]
        gsys     = {}
        gsig     = {}
        for ignss in range(ngnss):
            ugnssid   = payload.read( 4).u
            bsatmask  = payload.read(40)
            bsigmask  = payload.read(16)
            cmavail   = payload.read( 1).u
            t_satsys  = gnssid2satsys(ugnssid)
            t_satmask = 0
            t_sigmask = 0
            t_gsys = []
            t_gsig = []
            for i, val in enumerate(bsatmask):
                if val:
                    t_satmask += 1
                    if t_satsys == 'D':  # MADOCA-PPP gnssid workaround, ref[6]
                        t_gsys.append(f'C{i + 18:02d}') # D01->C19, D02->C20, ...
                    else:
                        t_gsys.append(f'{t_satsys}{i + 1:02d}')
            for i, val in enumerate(bsigmask):
                if val:
                    t_sigmask += 1
                    t_gsig.append(sigmask2signame(t_satsys, i))
            ncell = t_satmask * t_sigmask
            if cmavail:
                bcellmask = payload.read(ncell)
            else:
                bcellmask = BitStream('0b1') * ncell
            nm = 0  # navigation message (HAS)
            if ssr_type == 'has':
                nm = payload.read(3).u
            cellmask[ignss]    = bcellmask  # cell mask
            satsys  [ignss]    = t_satsys   # satellite system
            nsatmask[ignss]    = t_satmask  # satellite mask
            nsigmask[ignss]    = t_sigmask  # signal mask
            gsys    [t_satsys] = t_gsys     # GNSS system
            gsig    [t_satsys] = t_gsig     # GNSS signal
            navmsg  [ignss]    = nm         # navigation message (HAS)
        if ssr_type == 'has':
            payload.pos += 6       # reserved
        self.satsys    = satsys    # satellite system
        self.nsatmask  = nsatmask  # number of satellite mask
        self.nsigmask  = nsigmask  # number of signal mask
        self.cellmask  = cellmask  # cell mask
        self.gsys      = gsys      # dict of sat    name from system name
        self.gsig      = gsig      # dict of signal name from system name
        self.stat_nsat = 0
        self.stat_nsig = 0
        msg1 = ''
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                self.stat_nsat += 1
                if ssr_type == 'cssr':
                    msg1 += 'ST1 ' + gsys
                else:
                    msg1 += 'MASK ' + gsys
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    msg1 += ' ' + gsig
                    self.stat_nsig += 1
                msg1 += '\n'
            if ssr_type == 'has' and navmsg[i] != 0:
                msg1 += '\n' + self.trace.msg(1, '{satsys}: HAS NavMsg should be zero.', fg='red')
        self.trace.show(1, msg1, end='')
        if self.stat:
            self.show_cssr_stat()
        self.stat_bsat  = 0
        self.stat_bsig  = 0
        self.stat_both  = payload.pos
        self.stat_bnull = 0
        return True

    def decode_cssr_st1(self, payload: BitStream) -> bool:
        ''' decode CSSR ST1 mask message and returns True if success '''
        return self._decode_mask(payload, 'cssr')

    def decode_has_mask(self, has_msg: BitStream) -> bool:
        ''' decode HAS mask message and returns True if success '''
        return self._decode_mask(has_msg, 'has')

    def decode_cssr_st2(self, payload: BitStream) -> bool:
        ''' decode CSSR ST2 orbit message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg1  = 'ST2 SAT IODE radial[m] along[m] cross[m]'
        for satsys in self.satsys:
            bw = 10 if satsys == 'E' else 8  # IODE bit width
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + bw + 15 + 13 + 13:
                    return False
                iode   = payload.read(bw).u
                radial = payload.read(15).i
                along  = payload.read(13).i
                cross  = payload.read(13).i
                if radial != -16384 and along != -4096 and cross != -4096:
                    msg1 += f'\nST2 {gsys} {iode:{FMT_IODE}}   {radial*0.0016:{FMT_ORB}}  {along*0.0064:{FMT_ORB}}  {cross*0.0064:{FMT_ORB}}'
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_has_orbit(self, payload: BitStream) -> bool:
        ''' decode HAS orbit message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4:
            return False
        vi = payload.read('u4')
        msg1 = f'ORBIT SAT IODE radial[m] along[m] cross[m] validity_interval={HAS_VI[vi]}s ({vi})'
        for satsys in self.satsys:
            bw = 10 if satsys == 'E' else 8
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + bw + 13 + 12 + 12:
                    return False
                iode   = payload.read(bw).u
                radial = payload.read(13)
                along  = payload.read(12)
                cross  = payload.read(12)
                if radial.b != '1000000000000' and along.b != '100000000000' and cross.b != '100000000000':
                    msg1 += f'\nORBIT {gsys} {iode:{FMT_IODE}}   {radial.i*0.0025:{FMT_ORB}}  {along.i*0.0080:{FMT_ORB}}  {cross.i*0.0080:{FMT_ORB}}'
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_cssr_st3(self, payload: BitStream) -> bool:
        ''' decode CSSR ST3 clock message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg1 = 'ST3 SAT   c0[m]'
        for satsys in self.satsys:
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + 15:
                    return False
                c0 = payload.read(15).i
                if c0 != -16384:
                    msg1 += f"\nST3 {gsys} {c0*1.6e-3:{FMT_CLK}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_has_ckful(self, payload: BitStream) -> bool:
        ''' decode HAS clock full message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4:
            return False
        vi = payload.read(4).u
        msg1 = f'CKFUL SAT   c0[m] validity_interval={HAS_VI[vi]}[s] ({vi})'
        if len_payload < payload.pos + 2 * len(self.satsys):
            return False
        multiplier = [1 for i in range(len(self.satsys))]
        for i, satsys in enumerate(self.satsys):
            multiplier[i] = payload.read(2).u + 1
        for i, satsys in enumerate(self.satsys):
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + 13:
                    return False
                c0 = payload.read(13)
                if c0.b != '1000000000000' and c0.b != '0111111111111':
                    msg1 += f"\nCKFUL {gsys} {c0.i*2.5e-3*multiplier[i]:{FMT_CLK}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_has_cksub(self, payload: BitStream) -> bool:
        ''' decode HAS clock subset message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4 + 2:
            return False
        vi = payload.read(4).u
        ns = payload.read(2).u  # GNSS subset number
        msg1 = f'CKSUB SAT   c0[m] validity_interval={HAS_VI[vi]}[s] ({vi}), gnss_subset_number={ns}'
        multiplier = [1 for i in range(len(self.satsys))]
        for i in range(ns):
            if len_payload < payload.pos + 4 + 2:
                return False
            satsys     = payload.read(4).u
            multiplier = payload.read(2).u + 1
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    if len_payload < payload.pos + 13:
                        return False
                    c0 = payload.read(13)
                    if c0.b != '1000000000000' and c0.b == '0111111111111':
                        msg1 += f"\nCKSUB {gsys} {c0.i*2.5e-3*multiplier:{FMT_CLK}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def _decode_code_bias(self, payload: BitStream, ssr_type: str) -> bool:
        ''' decode code bias information and returns True if success
            ssr_type: cssr or has
        '''
        if ssr_type not in {'cssr', 'has'}:
            raise Exception(f'unknow ssr_type: {ssr_type}')
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg1 = 'ST4 SAT sinal_name      code_bias[m]'
        if ssr_type == 'has':
            if len_payload < payload.pos + 4:
                return False
            vi = payload.read(4).u
            msg1 = f'CBIAS SAT signal_name     code_bias[m] validity_interval={HAS_VI[vi]}s ({vi})'
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    if len_payload < payload.pos + 11:
                        return False
                    cb = payload.read(11).i
                    if cb != -1024:
                        if ssr_type == "cssr": msg1 += "\nST4"
                        else                 : msg1 += "\nCBIAS"
                        msg1 += f" {gsys} {gsig:{FMT_GSIG}}        {cb*0.02:{FMT_CB}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsig += payload.pos - stat_pos
        return True

    def decode_cssr_st4(self, payload: BitStream) -> bool:
        ''' decode CSSR ST4 code bias message and returns True if success '''
        return self._decode_code_bias(payload, 'cssr')

    def decode_has_cbias(self, payload: BitStream) -> bool:
        ''' decode HAS code bias message and returns True if success '''
        return self._decode_code_bias(payload, 'has')

    def decode_cssr_st5(self, payload: BitStream) -> bool:
        ''' decode CSSR ST5 phase bias message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg1  = 'ST5 SAT signal_name phase_bias[m]       discontinuity'
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    if len_payload < payload.pos + 15 + 2:
                        return False
                    pb  = payload.read(15).i
                    di  = payload.read( 2).u
                    if pb != -16384:
                        msg1 += f'\nST5 {gsys} {gsig:{FMT_GSIG}}     {pb*0.001:{FMT_PB}}       {di}'
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsig += payload.pos - stat_pos
        return True

    def decode_has_pbias(self, payload: BitStream) -> bool:
        ''' decode HAS phase bias message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4:
            return False
        vi = payload.read(4).u
        msg1 = f'PBIAS SAT signal_name phase_bias[cycle] discontinuity validity_interval={HAS_VI[vi]}[s] ({vi})'
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    if len_payload < payload.pos + 11 + 2:
                        return False
                    pb  = payload.read(11).i
                    di  = payload.read( 2).u
                    if pb != -1024:
                        msg1 += f'\nPBIAS {gsys} {gsig:{FMT_GSIG}}     {pb*0.01:{FMT_PB}}       {di}'
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsig += payload.pos - stat_pos
        return True

    def decode_cssr_st6(self, payload: BitStream) -> bool:
        ''' decode CSSR ST6 network bias message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 3:
            return False
        f_cb = payload.read(1).u  # code    bias existing flag
        f_pb = payload.read(1).u  # phase   bias existing flag
        f_nb = payload.read(1).u  # network bias existing flag
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            svmask[satsys] = BitStream('0b1')*ngsys
        msg1 = f"ST6 code_bias={'on' if f_cb else 'off'} phase_bias={'on' if f_pb else 'off'} network_bias={'on' if f_nb else 'off'}"
        msg1 += "\nST6 SAT signal_name    "
        if f_cb:
            msg1 += " code_bias[m]"
        if f_pb:
            msg1 += " phase_bias[m] discontinuity"
        if f_nb:
            if len_payload < payload.pos + 5:
                return False
            cnid = payload.read('u5')  # compact network ID
            if cnid < 1 or N_NID < cnid:
                raise Exception(f"invalid compact network ID: {cnid}")
            msg1 += f" NID={cnid} ({CLASGRID[cnid-1][0]})"
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if len_payload < payload.pos + ngsys:
                    return False
                svmask[satsys] = payload.read(ngsys)
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask or not svmask[satsys][j]:
                        continue
                    msg1 += f"\nST6 {gsys} {gsig:{FMT_GSIG}}"
                    if f_cb:
                        if len_payload < payload.pos + 11:
                            return False
                        cb  = payload.read(11).i  # code bias
                        if cb != -1024:
                            msg1 += f" {cb*0.02:{FMT_CB}}"
                    if f_pb:
                        if len_payload < payload.pos + 15 + 2:
                            return False
                        pb = payload.read(15).i  # phase bias
                        di = payload.read( 2).u  # disc ind
                        if pb != -16384:
                            msg1 += f"         {pb*0.001:{FMT_PB}}     {di}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos + 3
        self.stat_bsig += payload.pos - stat_pos - 3
        return True

    def decode_cssr_st7(self, payload: BitStream) -> bool:
        ''' decode CSSR ST7 user range accuracy message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg1 = 'ST7 SAT URA[mm]'
        for satsys in self.satsys:
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + 6:
                    return False
                ura = payload.read(6)  # [3], Sect.4.2.2.7
                accuracy = ura2dist(ura)
                if accuracy != URA_INVALID:
                    msg1 += f"\nST7 {gsys} {accuracy:{FMT_URA}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_cssr_st8(self, payload: BitStream) -> bool:
        ''' decode CSSR ST8 STEC message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 2 + 5:
            return False
        stec_type = payload.read(2).u  # STEC correction type
        cnid      = payload.read(5).u  # compact network ID
        if cnid < 1 or N_NID < cnid:
            raise Exception(f"invalid compact network ID: {cnid}")
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if len_payload < payload.pos + ngsys:
                return False
            svmask[satsys] = payload.read(ngsys)
        msg1 = "ST8 SAT qual[TECU] c00[TECU]"
        if 1 <= stec_type:
            msg1 += " c01[TECU/deg] c10[TECU/deg]"
        if 2 <= stec_type:
            msg1 += " c11[TECU/deg^2]"
        if 3 <= stec_type:
            msg1 += " c02[TECU/deg^2] c20[TECU/deg^2]"
        msg1 += f" NID={cnid} ({CLASGRID[cnid-1][0]})"
        for satsys in self.satsys:
            for maskpos, gsys in enumerate(self.gsys[satsys]):
                if not svmask[satsys][maskpos]:
                    continue
                if len_payload < payload.pos + 6 + 14:
                    return False
                qi  = payload.read( 6)  # quality indicator
                c00 = payload.read(14).i
                if c00 != -8192:
                    msg1 += f"\nST8 {gsys}     {ura2dist(qi):{FMT_TECU}}    {c00*0.05:{FMT_TECU}}"
                if 1 <= stec_type:
                    if len_payload < payload.pos + 12 + 12:
                        return False
                    c01 = payload.read(12).i
                    c10 = payload.read(12).i
                    if c01 != -2048 and c10 != -2048:
                        msg1 += f"        {c01*0.02:{FMT_TECU}}        {c10*0.02:{FMT_TECU}}"
                if 2 <= stec_type:
                    if len_payload < payload.pos + 10:
                        return False
                    c11  = payload.read(10).i
                    if c11 != -512:
                        msg1 += f"          {c11*0.02:{FMT_TECU}}"
                if 3 <= stec_type:
                    if len_payload < payload.pos + 8 + 8:
                        return False
                    c02  = payload.read(8).i
                    c20  = payload.read(8).i
                    if c02 != -128 and c20 != -128:
                        msg1 += f"          {c02*0.005:{FMT_TECU}}          {c20*0.005:{FMT_TECU}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos + 7
        self.stat_bsat += payload.pos - stat_pos - 7
        return True

    def decode_cssr_st9(self, payload: BitStream) -> bool:
        ''' decode CSSR ST9 trop correction message and returns True if success '''
        len_payload = len(payload)
        if len_payload < payload.pos + 2 + 1 + 5:
            return False
        tctype = payload.read(2).u  # Trop correction type
        srange = payload.read(1).u  # STEC correction range
        cnid   = payload.read(5).u  # compact network ID
        if cnid < 1 or N_NID < cnid:
            raise Exception(f"invalid compact network ID: {cnid}")
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if len_payload < payload.pos + ngsys:
                return False
            svmask[satsys] = payload.read(ngsys)
        if len_payload < payload.pos + 6 + 6:
            return False
        tqi   = payload.read(6)    # tropo quality indicator
        ngrid = payload.read(6).u  # number of grids
        if CLASGRID[cnid-1][1] != ngrid:
            raise Exception(f"cnid={cnid}, ngrid={ngrid} != {CLASGRID[cnid-1][1]}")
        bw = 16 if srange else 7    # bit width of residual correction
        CSSR_TROP_CORR_TYPE = ['Not included', 'Neill mapping function', 'Reserved', 'Reserved',]
        msg1 = f"ST9 Trop Type: {CSSR_TROP_CORR_TYPE[tctype]} ({tctype}), resolution={bw}[bit] ({srange}), NID={cnid} ({CLASGRID[cnid-1][0]}), qual={ura2dist(tqi):{FMT_URA}}[mm], ngrid={ngrid}"
        if tctype != 1:
            self.trace.show(1, msg1)
            raise Exception(f"tctype={tctype}: we implicitly assume the tropospheric correction type (tctype) is 1. if tctype=0 (no topospheric correction), we don't know whether we read the following tropospheric correction data or not. Others are reserved.")
        for grid in range(ngrid):
            if len_payload < payload.pos + 9 + 8:
                return False
            msg1 += '\nST9 SAT  Lat.   Lon. residual[TECU]'
            vd_h = payload.read(9).i  # hydrostatic vertical delay
            vd_w = payload.read(8).i  # wet         vertical delay
            if vd_h != -256 and vd_w != -128:
                msg1 += f' hydro_delay={2.3+vd_h*0.004:6.3f}[m] wet_delay={0.252+vd_w*0.004:6.3f}[m]'
            for satsys in self.satsys:
                for maskpos, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][maskpos]:
                        continue
                    if len_payload < payload.pos + bw:
                        return False
                    res  = payload.read(f'i{bw}')  # residual
                    if (srange == 1 and res != -32768) or \
                       (srange == 0 and res != -64):
                        lat, lon = CLASGRID[cnid-1][2][grid]
                        msg1 += f'\nST9 {gsys} {lat:5.2f} {lon:6.2f}         {res*0.04:{FMT_TECU}}'
        self.trace.show(1, msg1)
        self.stat_both += payload.pos
        return True

    def decode_cssr_st10(self, payload: BitStream) -> bool:
        ''' decode CSSR ST10 auxiliary message and returns True if success '''
        len_payload = len(payload)
        if len_payload < payload.pos + 5:
            return False
        counter = payload.read(3).u  # info message counter
        dsize   = payload.read(2).u  # data size
        size  = (dsize + 1) * 40
        if len_payload < payload.pos + size:
            return False
        aux_frame_data = payload.read(size)
        self.trace.show(1, f'ST10 {counter}:{aux_frame_data.hex}')
        self.stat_both += payload.pos
        return True

    def decode_cssr_st11(self, payload: BitStream) -> bool:
        ''' decode CSSR ST11 network correction message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < 40:
            return False
        f_o = payload.read(1).u  # orbit existing flag
        f_c = payload.read(1).u  # clock existing flag
        f_n = payload.read(1).u  # network correction
        msg1 = f"ST11 orbit_correction={'on' if f_o else 'off'} clock_correction={'on' if f_c else 'off'} network_correction={'on' if f_n else 'off'}"
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            svmask[satsys] = BitStream('0b1')*ngsys
        if f_n:
            if len_payload < payload.pos + 5:
                return False
            cnid = payload.read(5).u  # compact network ID
            if cnid < 1 or N_NID < cnid:
                raise Exception(f"invalid compact network ID: {cnid}")
            msg1 += f"\nST11 NID={cnid} ({CLASGRID[cnid-1][0]})"
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if len_payload < payload.pos + ngsys:
                    return False
                svmask[satsys] = payload.read(ngsys)
        msg1 += "\nST11 SAT"
        if f_o:
            msg1 += " IODE radial[m] along[m] cross[m]"
        if f_c:
            msg1 += "   c0[m]"
        for satsys in self.satsys:
            for i, gsys in enumerate(self.gsys[satsys]):
                if not svmask[satsys][i]:
                    continue
                f_o_disp = f_o
                f_c_disp = f_c
                iode     = 0
                radial   = 0
                along    = 0
                cross    = 0
                c0       = 0
                if f_o:
                    bw = 10 if satsys == 'E' else 8  # IODE bit width
                    if len_payload < payload.pos + bw + 15 + 13 + 13:
                        return False
                    iode   = payload.read(bw).u  # IODE
                    radial = payload.read(15).i  # radial
                    along  = payload.read(13).i  # along
                    cross  = payload.read(13).i  # cross
                    if radial == -16384 or along == -4096 or cross == -4096:
                        f_o_disp = False
                if f_c:
                    if len_payload < payload.pos + 15:
                        return False
                    c0  = payload.read(15).i
                    if c0 == -16384:
                        f_c_disp = False
                if f_o_disp or f_c_disp:
                    msg1 += f"\nST11 {gsys}"
                if f_o_disp:
                    msg1 += f' {iode:{FMT_IODE}}   {radial*0.0016:{FMT_ORB}}  {along*0.0064:{FMT_ORB}}  {cross*0.0064:{FMT_ORB}}'
                if f_c_disp:
                    msg1 += f" {c0*1.6e-3:{FMT_CLK}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos + 3
        self.stat_bsat += payload.pos - stat_pos - 3
        if f_n:  # correct bit number because because we count up bsat as NID
            self.stat_both += 5
            self.stat_bsat -= 5
        return True

    def decode_cssr_st12(self, payload: BitStream) -> bool:
        ''' decode CSSR ST12 network and troposphere corrections message and returns True if success '''
        len_payload = len(payload)
        if len_payload < payload.pos + 2 + 2 + 5 + 6:
            return False
        tavail = payload.read(2)    # troposhpere correction availability
        savail = payload.read(2)    # STEC        correction availability
        cnid   = payload.read(5).u  # compact network ID
        ngrid  = payload.read(6).u  # number of grids
        if cnid < 1 or N_NID < cnid:
            raise Exception(f"invalid compact network ID: {cnid}")
        if CLASGRID[cnid-1][1] != ngrid:
            raise Exception(f"cnid={cnid}, ngrid={ngrid} != {CLASGRID[cnid-1][1]}")
        msg1 = f"ST12 Trop NID={cnid} ({CLASGRID[cnid-1][0]})"
        if tavail[0]:  # bool object
            # 0 <= ttype (forward reference)
            if len_payload < payload.pos + 6 + 2 + 9:
                return False
            tqi   = payload.read(6)    # tropo quality indication
            ttype = payload.read(2).u  # tropo correction type
            t00   = payload.read(9).i  # tropo poly coeff
            msg1 += f" qual={ura2dist(tqi)}[mm]"
            if t00 != -256:
                msg1 += f" t00={t00*0.004:.3f}[m]"
            if 1 <= ttype:
                if len_payload < payload.pos + 7 + 7:
                    return False
                t01  = payload.read(7).i
                t10  = payload.read(7).i
                if t01 != -64 and t10 != -64:
                    msg1 += f" t01={t01*0.002:.3f}[m/deg] t10={t10*0.002:.3f}[m/deg]"
            if 2 <= ttype:
                if len_payload < payload.pos + 7:
                    return False
                t11  = payload.read(7).i
                if t11 != -64:
                    msg1 += f" t11={t11*0.001:.3f}[m/deg^2]"
        if tavail[1]:  # bool object
            if len_payload < payload.pos + 1 + 4:
                return False
            trs  = payload.read(1).u  # tropo residual size
            tro  = payload.read(4).u  # tropo residual offset
            bw   = 8 if trs else 6
            msg1 += f" offset={tro*0.02:.3f}[m]"
            if len_payload < payload.pos + bw * ngrid:
                return False
            msg1 += "\nST12 Trop  Lat.   Lon. residual[m]"
            for grid in range(ngrid):
                tr = payload.read(bw).i  # tropo residual
                if (bw == 6 and tr != -32) or (bw == 8 and tr != -128):
                    lat, lon = CLASGRID[cnid-1][2][grid]
                    msg1 += f"\nST12 Trop {lat:5.2f} {lon:6.2f}     {tr*0.004:{FMT_TROP}}"
        stat_pos = payload.pos
        if savail[0]:  # bool object
            svmask = {}
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if len_payload < payload.pos + ngsys:
                    return False
                svmask[satsys] = payload.read(ngsys)
            for satsys in self.satsys:
                for maskpos, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][maskpos]:
                        continue
                    if len_payload < payload.pos + 6 + 2 + 14:
                        return False
                    sqi = payload.read( 6)    # STEC quality indication
                    sct = payload.read( 2).u  # STEC correct type
                    c00 = payload.read(14).i
                    msg1 += f"\nST12 STEC {gsys}  Lat.   Lon. residual[TECU] qual={ura2dist(sqi):.3f}[TECU]"
                    if c00 != -8192:
                        msg1 += f" c00={c00*0.05:.3f}[TECU]"
                    if 1 <= sct:
                        if len_payload < payload.pos + 12 + 12:
                            return False
                        c01 = payload.read(12).i
                        c10 = payload.read(12).i
                        if c01 != -2048 and c10 != -2048:
                            msg1 += f" c01={c01*0.02:.3f}[TECU/deg] c10={c10*0.02:.3f}[TECU/deg]"
                    if 2 <= sct:
                        if len_payload < payload.pos + 10:
                            return False
                        c11 = payload.read(10).i
                        if c11 != -512:
                            msg1 += f" c11={c11* 0.02:.3f}[TECU/deg^2]"
                    if 3 <= sct:
                        if len_payload < payload.pos + 8 + 8:
                            return False
                        c02 = payload.read(8).i
                        c20 = payload.read(8).i
                        if c02 != -128 and c20 != -128:
                            msg1 += f" c02={c02*0.005:.3f}[TECU/deg^2] c20={c20*0.005:.3f}[TECU/deg^2]"
                    if len_payload < payload.pos + 2:
                        return False
                    srs = payload.read(2).u  # STEC residual size
                    bw  = [   4,    4,    5,    7][srs]
                    lsb = [0.04, 0.12, 0.16, 0.24][srs]
                    if len_payload < payload.pos + bw * ngrid:
                        return False
                    for grid in range(ngrid):
                        sr  = payload.read(bw).i  # STEC residual
                        lat, lon = CLASGRID[cnid-1][2][grid]
                        if (bw == 4 and sr !=  -8) or \
                           (bw == 5 and sr != -16) or \
                           (bw == 7 and sr != -64):
                            msg1 += f"\nST12 STEC {gsys} {lat:5.2f} {lon:6.2f}         {sr*lsb:{FMT_TECU}}"
        if savail[1]:  # bool object
            pass  # the use of this bit is not defined in ref.[1]
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_mdcppp_iono_head(self, payload: BitStream) -> bool:
        ''' decode MADOCA-PPP ionosphere correction header and returns True if success '''
        self.msgnum  = 0
        self.subtype = 0
        len_payload  = len(payload)
        if payload.all(0):  # payload is zero padded
            self.trace.show(2, f"null {len(payload.bin)} bits", dec='dark')
            return False
        if len_payload < payload.pos + 12 + 4:
            return False
        self.msgnum  = payload.read(12).u  # nessage number
        self.subtype = payload.read( 4).u  # subtype ID
        if self.subtype != 0:
            self.trace.show(0, f"Subtype should be 0 ({self.subtype})", fg='red')
        if self.msgnum == 1:  # for MADOCA-PPP STEC coverage message (ref. [3])
            if len_payload < payload.pos + 20 + 4 + 1 + 4 + 8 + 1 + 16 + 5:
                return False
            self.epoch        = payload.read(20).u  # epoch time, 1s, 0-604799
            self.ui           = payload.read( 4).u  # update interval
            self.mmi          = payload.read( 1).u  # multiple message indicator
            self.iodssr       = payload.read( 4).u  # IOD SSR
            self.region_id    = payload.read( 8).u  # region ID
            self.region_alert = payload.read( 1).u  # region alert
            self.len_msg      = payload.read(16).u  # message length in bits
            self.n_areas      = payload.read( 5).u  # number of areas
            return True
        elif self.msgnum == 2:  # for MADOCA-PPP STEC correction message (ref. [3])
            if len_payload < payload.pos + 12 + 4 + 1 + 4 + 8 + 5 + 2 + 5 + 5 + 5 + 5 + 5:
                return False
            self.epoch        = payload.read(12).u  # epoch time, 1s, 0-3599
            self.ui           = payload.read( 4).u  # update interval
            self.mmi          = payload.read( 1).u  # multiple message indicator
            iodssr            = payload.read( 4).u  # IOD SSR
            self.region_id    = payload.read( 8).u  # STEC region ID
            self.area         = payload.read( 5).u  # STEC area number
            self.stec_type    = payload.read( 2).u  # correction type
            self.n_gps        = payload.read( 5).u  # number of GPS satellites
            self.n_glo        = payload.read( 5).u  # number of GLONASS satellites
            self.n_gal        = payload.read( 5).u  # number of Galileo satellites
            self.n_bds        = payload.read( 5).u  # number of BeiDou satellites, 0 (not supported)
            self.n_qzs        = payload.read( 5).u  # number of QZSS satellites
            if iodssr != self.iodssr:
                self.trace.show(0, f"IOD SSR mismatch: {iodssr} != {iodssr}", fg='red')
                return False
            return True
        self.trace.show(0, f"MDCCPPP-Iono msgnum should be 1 or 2 ({self.msgnum}), ST{self.subtype}, size {len(payload.bin)} bits\nMDCPPP dump: {payload.bin}", fg='red')
        return False

    def decode_mdcppp_mt1(self, payload: BitStream) -> bool:  # ref. [3]
        ''' decodes MADOCA-PPP MT1 messages and returns True if success '''
        len_payload = len(payload)
        msg1 = f'MT1 Epoch={epoch2timedate(self.epoch)} UI={CSSR_UI[self.ui]:2d}s({self.ui}) MMI={self.mmi} IODSSR={self.iodssr} Region={self.region_id}{"*" if self.region_alert else" "} {self.len_msg}bit {"cont." if self.mmi else ""} NumAreas={self.n_areas}'
        msg1 += '\n # shape lat[deg] lon[deg] lats lons / radius[km]'
        for _ in range(self.n_areas):
            if len_payload < payload.pos + 5 + 1:
                return False
            area_no = payload.read(5).u
            shape   = payload.read(1).u
            if shape == 0:
                if len_payload < payload.pos + 11 + 12 + 8 + 8:
                    return False
                lat_ref  = payload.read(11).i  # center latitude  of rectangle area
                lon_ref  = payload.read(12).u  # center longitude of rectangle area
                lat_span = payload.read( 8).u  # span   latitude  of rectangle area
                lon_span = payload.read( 8).u  # span   longitude of rectangle area
                msg1 += f'\n{area_no:2d} RECT    {lat_ref*0.1:6.1f}  {lon_ref*0.1:7.1f} {lat_span*0.1:4.1f} {lon_span*0.1:4.1f}'
            else:  # shape == 1
                if len_payload < payload.pos + 15 + 16 + 8:
                    return False
                lat_ref  = payload.read(15).i  # center latitude  of circle area
                lon_ref  = payload.read(16).u  # center longitude of circle area
                radius   = payload.read( 8).u  # radius           of circle area
                msg1 += f'\n{area_no:2d} CIRCLE  {lat_ref*0.01:6.1f}  {lon_ref*0.01:7.1f} {radius*10:4d}'
        self.trace.show(1, msg1)
        return True

    def decode_mdcppp_mt2(self, payload: BitStream) -> bool:  # ref. [3]
        ''' decoding MADOCA-PPP MT2 messages and returns True if success '''
        len_payload = len(payload)
        bw = [                                  # bit width of a single STEC correction
            6 + 6 + 14                       ,  # STEC correction type = 0
            6 + 6 + 14 + 12 + 12             ,  # STEC correction type = 1
            6 + 6 + 14 + 12 + 12 + 10        ,  # STEC correction type = 2
            6 + 6 + 14 + 12 + 12 + 10 + 8 + 8,  # STEC correction type = 3
            ][self.stec_type]
        if len_payload < payload.pos + bw * (self.n_gps + self.n_glo + self.n_gal + self.n_bds + self.n_qzs):
            return False
        msg1 = f'MT2 Epoch={epoch2time(self.epoch)} IODSSR={self.iodssr} Region={self.region_id} Area={self.area} G={self.n_gps} R={self.n_glo} E={self.n_gal} C={self.n_bds} J={self.n_qzs}'
        msg1 += '\nSAT  qual[mm] c00[TECU]'
        if 1 <= self.stec_type:
            msg1 += " c01[TECU/deg] c10[TECU/deg]"
        if 2 <= self.stec_type:
            msg1 += " c11[TECU/deg^2]"
        if 3 <= self.stec_type:
            msg1 += " c02[TECU/deg^2] c20[TECU/deg^2]"
        for satsys in ["G", "R", "E", "C", "J"]:
            numsat = 0
            if   satsys == "G": numsat = self.n_gps
            elif satsys == "R": numsat = self.n_glo
            elif satsys == "E": numsat = self.n_gal
            elif satsys == "C": numsat = self.n_bds
            elif satsys == "J": numsat = self.n_qzs
            for _ in range(numsat):
                satid = payload.read( 6).u    # GNSS satellite ID
                qi    = payload.read( 6)    # quality indicator
                c00   = payload.read(14).i    # STEC correction coefficient C00
                if c00 != -8192:
                    msg1 += f'\n{satsys}{satid:02d}   {ura2dist(qi):7.2f}    {c00*0.05:{FMT_TECU}}'
                if 1 <= self.stec_type:
                    c01 = payload.read(12).i  # STEC correction coefficient C01
                    c10 = payload.read(12).i  # STEC correction coefficient C10
                    if c01 != -2048 and c10 != -2048:
                        msg1 += f'        {c01*0.02:{FMT_TECU}}        {c10*0.02:{FMT_TECU}}'
                if 2 <= self.stec_type:
                    c11 = payload.read(10).i  # STEC correction coefficient C11
                    if c11 != -512:
                        msg1 += f'          {c11*0.02:{FMT_TECU}}'
                if 3 <= self.stec_type:
                    c02 = payload.read(8).i  # STEC correction coefficient C02
                    c20 = payload.read(8).i  # STEC correction coefficient C20
                    if c02 != -128 and c20 != -128:
                        msg1 += f'          {c02*0.005:{FMT_TECU}}          {c20*0.005:{FMT_TECU}}'
        self.trace.show(1, msg1)
        return True

# EOF
