#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libssr.py: library for SSR and compact SSR message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2024 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Centimeter Level Augmentation Service,
#     IS-QZSS-L6-005, Sept. 21, 2022.
# [2] Global Positioning Augmentation Service Corporation (GPAS),
#     Quasi-Zenith Satellite System Correction Data on Centimeter Level
#     Augmentation Serice for Experiment Data Format Specification,
#     1st ed., Nov. 2017.
# [3] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Multi-GNSS Advanced Orbit and Clock Augmentation
#     - Precise Point Positioning, IS-QZSS-MDC-001, Feb., 2022.
# [4] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.
# [5] European Union Agency for the Space Programme,
#     Galileo High Accuracy Service Signal-in-Space Interface Control
#     Document (HAS SIS ICD), Issue 1.0 May 2022.

import sys

import libtrace

try:
    import bitstring
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
FMT_TECU   = '6.3f'  # format string for TECU
FMT_IODE   = '4d'    # format string for issue of data ephemeris
FMT_IODSSR = '<2d'   # format string for issue of data SSR
FMT_GSIG   = '13s'   # format string for GNSS signal name
FMT_URA    = '7.2f'  # format string for URA
CLASGRID   = [       # CLAS grid, [location, number of grid, ([lat, lon]), ..., see https://s-taka.org/en/clasgrid/
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
N_CLASGRID = 19         # = len(CLASGRID)

def epoch2time(epoch):
    ''' convert epoch to time
        epoch: epoch in second (0-86400)
    '''
    hour = epoch // 3600
    min  = (epoch % 3600) // 60
    sec  = epoch % 60
    return f'{hour:02d}:{min:02d}:{sec:02d}'
    # return f'{hour:02d}:{min:02d}:{sec:02d} ({epoch})'

def epoch2timedate(epoch):
    ''' convert epoch to time plus date'''
    return f'{epoch2time(epoch%86400)}+{epoch//86400}'

def gnssid2satsys(gnssid):
    ''' convert gnss id to satellite system '''
    if   gnssid == 0: satsys = 'G'
    elif gnssid == 1: satsys = 'R'
    elif gnssid == 2: satsys = 'E'
    elif gnssid == 3: satsys = 'C'
    elif gnssid == 4: satsys = 'J'
    elif gnssid == 5: satsys = 'S'
    else: raise Exception(f'undefined gnssid {gnssid}')
    return satsys

def sigmask2signame(satsys, sigmask):
    ''' convert satellite system and signal mask to signal name '''
    signame = f'satsys={satsys} sigmask={sigmask}'
    if satsys == 'G':
        signame = [ "L1 C/A", "L1 P", "L1 Z-tracking", "L1C(D)", "L1C(P)",
            "L1C(D+P)", "L2 CM", "L2 CL", "L2 CM+CL", "L2 P", "L2 Z-tracking",
            "L5 I", "L5 Q", "L5 I+Q", "", ""][sigmask]
    elif satsys == 'R':
        signame = [ "G1 C/A", "G1 P", "G2 C/A", "G2 P", "G1a(D)", "G1a(P)",
            "G1a(D+P)", "G2a(D)", "G2a(P)", "G2a(D+P)", "G3 I", "G3 Q",
            "G3 I+Q", "", "", "", ""][sigmask]
    elif satsys == 'E':
        signame = [ "E1 B", "E1 C", "E1 B+C", "E5a I", "E5a Q", "E5a I+Q",
            "E5b I", "E5b Q", "E5b I+Q", "E5 I", "E5 Q", "E5 I+Q",
            "E6 B", "E6 C", "E6 B+C", ""][sigmask]
    elif satsys == 'C':
        signame = [ "B1 I", "B1 Q", "B1 I+Q", "B3 I", "B3 Q", "B3 I+Q",
            "B2 I", "B2 Q", "B2 I+Q", "", "", "", "", "", "", "", ""][sigmask]
    elif satsys == 'J':
        signame = [ "L1 C/A", "L1 L1C(D)", "L1 L1C(P)", "L1 L1C(D+P)",
            "L2 L2C(M)", "L2 L2C(L)", "L2 L2C(M+L)", "L5 I", "L5 Q",
            "L5 I+Q", "", "", "", "", "", ""][sigmask]
    elif satsys == 'S':
        signame = [
            "L1 C/A", "L5 I", "L5 Q", "L5 I+Q", "", "", "", "", "", "",
            "", "", "", "", "", "", ""][sigmask]
    else:
        raise Exception(
            f'unassigned signal name for satsys={satsys} and sigmask={sigmask}')
    return signame

def ura2dist(ura):
    ''' converts user range accuracy (URA) code to accuracy in distance [mm] '''
    dist = 0.0
    if   ura.bin == 0b000000:   # undefined or unknown
        dist = URA_INVALID
    elif ura.bin == 0b111111:   # URA more than 5466.5 mm
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
    gsys       = {}     # dict of sat   name from system name
    gsig       = {}     # dict of sigal name from system name
    stat       = False  # statistics output
    stat_nsat  = 0      # stat: number of satellites
    stat_nsig  = 0      # stat: number of signals
    stat_bsat  = 0      # stat: bit number of satellites
    stat_bsig  = 0      # stat: bit number of signals
    stat_both  = 0      # stat: bit number of other information
    stat_bnull = 0      # stat: bit number of null

    def __init__(self, trace):
        self.trace = trace

    def ssr_decode_head(self, payload, satsys, mtype):
        ''' stores ssr_epoch, ssr_interval, ssr_mmi, ssr_iod, ssr_nsat'''
        # bit format of ssr_epoch changes according to satellite system
        bw = 'u20' if satsys != 'R' else 'u17'
        self.ssr_epoch     = payload.read(  bw )  # epoch time
        self.ssr_interval  = payload.read( 'u4')  # SSR update interval
        self.ssr_mmi       = payload.read( 'u1')  # multiple message indication
        if mtype == 'SSR orbit' or mtype == 'SSR obt/clk':
            self.ssr_sdat  = payload.read( 'u1')  # sat ref datum
        self.ssr_iod       = payload.read( 'u4')  # IOD SSR
        self.ssr_pid       = payload.read('u16')  # SSR provider ID
        self.ssr_sid       = payload.read( 'u4')  # SSR solution ID
        # bit format of nsat changes with satsys
        bw = 'u6' if satsys != 'J' else 'u4'
        self.ssr_nsat      = payload.read(  bw )

    def ssr_decode_orbit(self, payload, satsys):
        ''' decodes SSR orbit correction and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'  # ref. [2]
        elif satsys == 'R': bw = 'u5'  # ref. [1]
        else:               bw = 'u6'  # ref. [1]
        msg1 = self.trace.msg(1, '\nSAT radial[m] along[m] cross[m] d_radial[m/s] d_along[m/s] d_cross[m/s]')
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid   = payload.read(  bw )  # satellite ID, DF068
            iode    = payload.read( 'u8')  # IODE, DF071
            radial  = payload.read('i22')  # radial, DF365
            along   = payload.read('i20')  # along track, DF366
            cross   = payload.read('i20')  # cross track, DF367
            dradial = payload.read('i21')  # dot_radial, DF368
            dalong  = payload.read('i19')  # dot_along track, DF369
            dcross  = payload.read('i19')  # dot_cross track, DF370
            strsat += f"{satsys}{satid:02} "
            msg1 += self.trace.msg(1, f'\n{satsys}{satid:02d}   {radial*1e-4:{FMT_ORB}}  {along*4e-4:{FMT_ORB}}  {cross*4e-5:{FMT_ORB}}       {dradial*1e-6:{FMT_ORB}}      {dalong*4e-6:{FMT_ORB}}      {dcross*4e-6:{FMT_ORB}}')
        msg = self.trace.msg(0, f"{strsat}(IOD={self.ssr_iod} IODE={iode} nsat={self.ssr_nsat}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def ssr_decode_clock(self, payload, satsys):
        ''' decodes SSR clock correction and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'  # ref. [2]
        elif satsys == 'R': bw = 'u5'  # ref. [1]
        else              : bw = 'u6'  # ref. [1]
        msg1 = self.trace.msg(1, '\nSAT   c0[m] c1[m/s] c2[m/s^2]')
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid = payload.read(  bw )  # satellite ID
            c0    = payload.read('i22')  # delta clock c0, DF376
            c1    = payload.read('i21')  # delta clock c1, DF377
            c2    = payload.read('i27')  # delta clock c2, DF378
            strsat += f"{satsys}{satid:02d} "
            msg1 += self.trace.msg(1, f'\n{satsys}{satid:02d} {c0*1e-4:{FMT_CLK}} {c1*1e-6:{FMT_CLK}}   {c2*2e-8:{FMT_CLK}}')
        msg = self.trace.msg(0, f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def ssr_decode_code_bias(self, payload, satsys):
        ''' decodes SSR code bias and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'   # ref. [2]
        elif satsys == 'R': bw = 'u5'   # ref. [1]
        else              : bw = 'u6'   # ref. [1]
        msg1 = self.trace.msg(1, '\nSAT signal_name code_bias[m]')
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid = payload.read( bw )  # satellite ID, DF068, ...
            ncb   = payload.read('u5')  # code bias number, DF383
            strsat += f"{satsys}{satid:02d} "
            for j in range(ncb):
                stmi  = payload.read( 'u5')  # sig&trk mode ind, DF380
                cb    = payload.read('i14')  # code bias, DF383
                sstmi = sigmask2signame(satsys, stmi)
                msg1 += self.trace.msg(1, f'\n{satsys}{satid:02d} {sstmi:{FMT_GSIG}}    {cb*1e-2:{FMT_CB}}')
        msg = self.trace.msg(0, f"{strsat}(IOD={self.ssr_iod} nsat={self.ssr_nsat}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def ssr_decode_ura(self, payload, satsys):
        ''' decodes SSR user range accuracy and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'  # ref. [2]
        elif satsys == 'R': bw = 'u5'  # ref. [1]
        else              : bw = 'u6'  # ref. [1]
        msg1 = self.trace.msg(1, '\nSAT URA[mm]')
        strsat = ''
        for i in range(self.ssr_nsat):
            satid = payload.read(bw)  # satellite ID, DF068
            ura   = payload.read( 6)  # user range accuracy, DF389
            accuracy = ura2dist(ura)
            if accuracy != URA_INVALID:
                msg1 += self.trace.msg(1, f'\n{satsys}{satid:02d} {accuracy:{FMT_URA}}')
                strsat += f"{satsys}{satid:02} "
        msg = self.trace.msg(0, f"{strsat}(IOD={self.ssr_iod} nsat={self.ssr_nsat}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def ssr_decode_hr_clock(self, payload, satsys):
        '''decodes SSR high rate clock and returns string'''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'
        elif satsys == 'R': bw = 'u5'
        else              : bw = 'u6'
        msg1 = self.trace.msg(1, '\nSAT high_rate_clock[m]')
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid = payload.read(  bw )  # satellite ID
            hrc   = payload.read('i22')  # high rate clock, DF390
            strsat += f"{satsys}{satid:02} "
            msg1 += self.trace.msg(1, f'\n{satsys}{satid:02}            {hrc*1e-4:{FMT_CLK}}')
        msg = self.trace.msg(0, f"{strsat}(IOD={self.ssr_iod} nsat={self.ssr_nsat}{' cont.' if self.ssr_mmi else ''})") + msg1
        return msg

    def decode_cssr(self, payload):
        ''' calls cssr decode functions and returns True if success '''
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
        string = f'ST{self.subtype:<2d}'
        if self.subtype == 1:
            string += f' Epoch={epoch2timedate(self.epoch)} ({self.epoch}) UI={CSSR_UI[self.ui]:2d}s ({self.ui}) IODSSR={self.iodssr} {"cont." if self.mmi else ""}'
        else:
            etime=f'{self.hepoch//60:02d}:{self.hepoch%60:02d}'
            string += f' Epoch={etime} ({self.hepoch}) UI={CSSR_UI[self.ui]:2d}s ({self.ui}) IODSSR={self.iodssr}{" cont." if self.mmi else ""}'
        return string

    def show_cssr_stat(self):
        bit_total = self.stat_bsat + self.stat_bsig + self.stat_both + \
                self.stat_bnull
        msg = f'stat n_sat {self.stat_nsat} n_sig {self.stat_nsig} ' + \
              f'bit_sat {self.stat_bsat} bit_sig {self.stat_bsig} ' + \
              f'bit_other {self.stat_both} bit_null {self.stat_bnull} ' + \
              f'bit_total {bit_total}'
        self.trace.show(0, msg)

    def decode_cssr_head(self, payload):
        ''' decode CSSR header and returns True if success '''
        self.msgnum  = 0
        self.subtype = 0
        len_payload = len(payload)
        if payload.all(0) or not len_payload:  # payload is zero padded
            self.trace.show(2, f"CSSR null data {len(payload.bin)} bits", fg='green')
            return False
        if len_payload < 12 + 4:
            return False
        self.msgnum  = payload.read('u12')
        self.subtype = payload.read('u4')  # subtype
        if self.msgnum != 4073:  # CSSR message number should be 4073
            # raise Exception(f"CSSR msgnum should be 4073 ({self.msgnum}), size {len(payload.bin)} bits\nCSSR dump: {payload.bin}")
            self.trace.show(0, f"CSSR msgnum should be 4073 ({self.msgnum}), size {len(payload.bin)} bits\nCSSR dump: {payload.bin}", fg='red')
            return False
        if self.subtype == 1:  # Mask message
            if len_payload < payload.pos + 20:  # could not retreve the epoch
                return False
            self.epoch = payload.read('u20')  # GPS epoch time 1s
        elif self.subtype == 10:  # Service Information
            return True
        else:
            if len_payload < payload.pos + 12:  # could not retreve hourly epoch
                return False
            self.hepoch = payload.read('u12')  # GNSS hourly epoch
        if len_payload < payload.pos + 4 + 1 + 4:
            return False
        self.ui     = payload.read('u4')  # update interval
        self.mmi    = payload.read('u1')  # multiple message indication
        self.iodssr = payload.read('u4')  # IOD SSR
        return True

    def _decode_mask(self, payload, ssr_type):
        ''' decode mask information and returns True if success
            ssr_type: cssr or has
        '''
        if ssr_type not in {'cssr', 'has'}:
            raise Exception(f'unknown ssr_type: {ssr_type}')
        len_payload = len(payload)
        if len_payload < payload.pos + 4:
            return False
        ngnss = payload.read('u4')  # numer of GNSS
        if len_payload < payload.pos + 61 * ngnss:
            return False
        satsys   = [None for i in range(ngnss)]
        nsatmask = [None for i in range(ngnss)]
        nsigmask = [None for i in range(ngnss)]
        cellmask = [None for i in range(ngnss)]
        navmsg   = [None for i in range(ngnss)]
        gsys     = {}
        gsig     = {}
        for ignss in range(ngnss):
            ugnssid   = payload.read('u4')
            bsatmask  = payload.read( 40 )
            bsigmask  = payload.read( 16 )
            cmavail   = payload.read('u1')
            t_satsys  = gnssid2satsys(ugnssid)
            t_satmask = 0
            t_sigmask = 0
            t_gsys = []
            t_gsig = []
            for i, val in enumerate(bsatmask):
                if val:
                    t_satmask += 1
                    t_gsys.append(t_satsys + f'{i + 1:02d}')
            for i, val in enumerate(bsigmask):
                if val:
                    t_sigmask += 1
                    t_gsig.append(sigmask2signame(t_satsys, i))
            ncell = t_satmask * t_sigmask
            if cmavail:
                bcellmask = payload.read(ncell)
            else:
                bcellmask = bitstring.ConstBitStream('0b1') * ncell
            nm = 0  # navigation message (HAS)
            if ssr_type == 'has':
                nm = payload.read('u3')
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
        self.gsys      = gsys      # dict of sat   name from system name
        self.gsig      = gsig      # dict of sigal name from system name
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
                msg1 += '\n{satsys}: NavMsg should be zero.\n'
        self.trace.show(1, msg1, end='')
        if self.stat:
            self.show_cssr_stat()
        self.stat_bsat  = 0
        self.stat_bsig  = 0
        self.stat_both  = payload.pos
        self.stat_bnull = 0
        return True

    def decode_cssr_st1(self, payload):
        ''' decode CSSR ST1 mask message and returns True if success '''
        return self._decode_mask(payload, 'cssr')

    def decode_has_mask(self, has_msg):
        ''' decode HAS mask message and returns True if success '''
        return self._decode_mask(has_msg, 'has')

    def decode_cssr_st2(self, payload):
        ''' decode CSSR ST2 orbit message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg1  = 'ST2 SAT IODE radial[m] along[m] cross[m]'
        for satsys in self.satsys:
            bw = 10 if satsys == 'E' else 8  # IODE bit width
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + bw + 15 + 13 + 13:
                    return False
                iode   = payload.read(f'u{bw}')
                radial = payload.read('i15')
                along  = payload.read('i13')
                cross  = payload.read('i13')
                if radial != -16384 and along != -16384 and cross != -16384:
                    msg1 += f'\nST2 {gsys} {iode:{FMT_IODE}}   {radial*0.0016:{FMT_ORB}}  {along*0.0064:{FMT_ORB}}  {cross*0.0064:{FMT_ORB}}'
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_has_orbit(self, payload):
        ''' decode HAS orbit message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4:
            return False
        vi = payload.read('u4')
        msg1 = f'ORBIT SAT IODE radial[m] along[m] cross[m] validity_interval={HAS_VI[vi]}s ({vi})'
        for satsys in self.satsys:
            if satsys == 'E': bw = 10
            else            : bw =  8
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + bw + 13 + 12 + 12:
                    return False
                iode = payload.read(f'u{bw}')
                rad  = payload.read(13)
                alg  = payload.read(12)
                crs  = payload.read(12)
                if rad.bin != '1000000000000' and alg.bin != '100000000000' and crs.bin != '100000000000':
                    msg1 += f'\nORBIT {gsys} {iode:{FMT_IODE}}   {rad.i*0.0025:{FMT_ORB}}  {alg.i*0.0080:{FMT_ORB}}  {crs.i*0.0080:{FMT_ORB}}'
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_cssr_st3(self, payload):
        ''' decode CSSR ST3 clock message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg1 = 'ST3 SAT   c0[m]'
        for satsys in self.satsys:
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + 15:
                    return False
                c0 = payload.read('i15')
                if c0 != -16384:
                    msg1 += f"\nST3 {gsys} {c0*1.6e-3:{FMT_CLK}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_has_ckful(self, payload):
        ''' decode HAS clock full message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4:
            return False
        vi = payload.read('u4')
        msg1 = f'CKFUL SAT   c0[m] validity_interval={HAS_VI[vi]}[s] ({vi})'
        if len_payload < payload.pos + 2 * len(self.satsys):
            return False
        multiplier = [1 for i in range(len(self.satsys))]
        for i, satsys in enumerate(self.satsys):
            multiplier[i] = payload.read('u2') + 1
        for i, satsys in enumerate(self.satsys):
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + 13:
                    return False
                c0 = payload.read(13)
                if c0.bin != '1000000000000' and c0.bin != '0111111111111':
                    msg1 += f"\nCKFUL {gsys} {c0.i*2.5e-3*multiplier[i]:{FMT_CLK}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_has_cksub(self, payload):
        ''' decode HAS clock subset message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4 + 2:
            return False
        vi = payload.read('u4')
        ns = payload.read('u2')  # GNSS subset number
        msg1 = f'CKSUB SAT   c0[m] validity_interval={HAS_VI[vi]}[s] ({vi}), gnss_subset_number={ns}'
        multiplier = [1 for i in range(len(self.satsys))]
        for i in range(ns):
            if len_payload < payload.pos + 4 + 2:
                return False
            satsys     = payload.read('u4')
            multiplier = payload.read('u2') + 1
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    if len_payload < payload.pos + 13:
                        return False
                    c0 = payload.read(13)
                    if c0.bin != '1000000000000' and c0.bin == '0111111111111':
                        msg1 += f"\nCKSUB {gsys} {c0.i*2.5e-3*multiplier:{FMT_CLK}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def _decode_code_bias(self, payload, ssr_type):
        ''' decode code bias information and returns True if success
            ssr_type: cssr or has
        '''
        if ssr_type not in {'cssr', 'has'}:
            raise Exception(f'unknow ssr_type: {ssr_type}')
        nsigsat = 0  # Nsig * Nsat
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    nsigsat += 1
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg1 = 'ST4 SAT sinal_name      code_bias[m]'
        if ssr_type == 'has':
            if len_payload < payload.pos + 4:
                return False
            vi = payload.read('u4')
            msg1 = f'CBIAS SAT signal_name     code_bias[m] validity_interval={HAS_VI[vi]}s ({vi})'
        if len(payload) < payload.pos + 11 * nsigsat:
            return False
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                for k, gsig in enumerate(self.gsig[satsys]):
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    cb  = payload.read('i11')
                    if cb != -1024:
                        if ssr_type == "cssr": msg1 += "\nST4"
                        else                 : msg1 += "\nCBIAS"
                        msg1 += f" {gsys} {gsig:{FMT_GSIG}}        {cb*0.02:{FMT_CB}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsig += payload.pos - stat_pos
        return True

    def decode_cssr_st4(self, payload):
        ''' decode CSSR ST4 code bias message and returns True if success '''
        return self._decode_code_bias(payload, 'cssr')

    def decode_has_cbias(self, payload):
        ''' decode HAS code bias message and returns True if success '''
        return self._decode_code_bias(payload, 'has')

    def decode_cssr_st5(self, payload):
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
                    pb  = payload.read('i15')
                    di  = payload.read( 'u2')
                    if pb != -16384:
                        msg1 += f'\nST5 {gsys} {gsig:{FMT_GSIG}}     {pb*0.001:{FMT_PB}}       {di}'
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsig += payload.pos - stat_pos
        return True

    def decode_has_pbias(self, payload):
        ''' decode HAS phase bias message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4:
            return False
        vi = payload.read('u4')
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
                    pb  = payload.read('i11')
                    di  = payload.read( 'u2')
                    if pb != -1024:
                        msg1 += f'\nPBIAS {gsys} {gsig:{FMT_GSIG}}     {pb*0.01:{FMT_PB}}       {di}'
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsig += payload.pos - stat_pos
        return True

    def decode_cssr_st6(self, payload):
        ''' decode CSSR ST6 network bias message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < 45:
            return False
        f_cb = payload.read('u1')  # code    bias existing flag
        f_pb = payload.read('u1')  # phase   bias existing flag
        f_nb = payload.read('u1')  # network bias existing flag
        svmask = {}
        cnid = 0
        msg1 = f"ST6 code_bias={'on' if f_cb else 'off'} phase_bias={'on' if f_pb else 'off'} network_bias={'on' if f_nb else 'off'}"
        msg1 += "\nST6 SAT signal_name    "
        if f_cb:
            msg1 += " code_bias[m]"
        if f_pb:
            msg1 += " phase_bias[m] discontinuity"
        if f_nb:
            cnid = payload.read('u5')  # compact network ID
            if cnid < 1 or N_CLASGRID < cnid:
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
                    if not svmask[satsys][j] or not mask:
                        continue
                    msg1 += f"\nST6 {gsys} {gsig:{FMT_GSIG}}"
                    if f_cb:
                        if len_payload < payload.pos + 11:
                            return False
                        cb  = payload.read('i11')  # code bias
                        if cb != -1024:
                            msg1 += f" {cb*0.02:{FMT_CB}}"
                    if f_pb:
                        if len_payload < payload.pos + 15 + 2:
                            return False
                        pb = payload.read('i15')  # phase bias
                        di = payload.read( 'u2')  # disc ind
                        if pb != -16384:
                            msg1 += f"         {pb*0.001:{FMT_PB}}     {di}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos + 3
        self.stat_bsig += payload.pos - stat_pos - 3
        return True

    def decode_cssr_st7(self, payload):
        ''' decode CSSR ST7 user range accuracy message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < 37:
            return False
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

    def decode_cssr_st8(self, payload):
        ''' decode CSSR ST8 STEC message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < 44:
            return False
        stec_type = payload.read('u2')  # STEC correction type
        cnid      = payload.read('u5')  # compact network ID
        if cnid < 1 or N_CLASGRID < cnid:
            raise Exception(f"invalid compact network ID: {cnid}")
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if len_payload < payload.pos + ngsys:
                return False
            svmask[satsys] = payload.read(ngsys)
        msg1 = "ST8 SAT NID qual[TECU] c00[TECU]"
        if 1 <= stec_type:
            msg1 += " c01[TECU/deg] c10[TECU/deg]"
        if 2 <= stec_type:
            msg1 += " c11[TECU/deg^2]"
        if 3 <= stec_type:
            msg1 += " c02[TECU/deg^2] c20[TECU/deg^2]"
        for satsys in self.satsys:
            for i, gsys in enumerate(self.gsys[satsys]):
                if not svmask[satsys][i]:
                    continue
                if len_payload < payload.pos + 6 + 14:
                    return False
                qi   = payload.read(   6 )  # quality indicator
                c00  = payload.read('i14')
                if c00 != -8192:
                    msg1 += f"\nST8 {gsys}  {cnid:2d}     {ura2dist(qi):{FMT_TECU}}    {c00*0.05:{FMT_TECU}}"
                if 1 <= stec_type:
                    if len_payload < payload.pos + 12 + 12:
                        return False
                    c01  = payload.read('i12')
                    c10  = payload.read('i12')
                    if c01 != -2048 and c10 != -2048:
                        msg1 += f"        {c01*0.02:{FMT_TECU}}        {c10*0.02:{FMT_TECU}}"
                if 2 <= stec_type:
                    if len_payload < payload.pos + 10:
                        return False
                    c11  = payload.read('i10')
                    if c11 != -512:
                        msg1 += f"          {c11*0.02:{FMT_TECU}}"
                if 3 <= stec_type:
                    if len_payload < payload.pos + 8 + 8:
                        return False
                    c02  = payload.read('i8')
                    c20  = payload.read('i8')
                    if c02 != -128 and c20 != -128:
                        msg1 += f"          {c02*0.005:{FMT_TECU}}          {c20*0.005:{FMT_TECU}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos + 7
        self.stat_bsat += payload.pos - stat_pos - 7
        return True

    def decode_cssr_st9(self, payload):
        ''' decode CSSR ST9 trop correction message and returns True if success '''
        len_payload = len(payload)
        if len_payload < payload.pos + 2 + 1 + 5:
            return False
        tctype = payload.read('u2')  # Trop correction type
        srange = payload.read('u1')  # STEC correction range
        cnid   = payload.read('u5')  # compact network ID
        if cnid < 1 or N_CLASGRID < cnid:
            raise Exception(f"invalid compact network ID: {cnid}")
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if len_payload < payload.pos + ngsys:
                return False
            svmask[satsys] = payload.read(ngsys)
        if len_payload < payload.pos + 6 + 6:
            return False
        tqi   = payload.read(  6 )  # tropo quality indicator
        ngrid = payload.read('u6')  # number of grids
        if CLASGRID[cnid-1][1] != ngrid:
            raise Exception(f"ngrid={ngrid} != {CLASGRID[cnid-1][1]}")
        bw = 16 if srange else 7    # bit width of residual correction
        CSSR_TROP_CORR_TYPE = ['Not included', 'Neill mapping function', 'Reserved', 'Reserved',]
        msg1 = f"ST9 Trop Type: {CSSR_TROP_CORR_TYPE[tctype]} ({tctype}), resolution={bw}[bit] ({srange}), NID={cnid} ({CLASGRID[cnid-1][0]}), qual={ura2dist(tqi):{FMT_URA}}[mm], ngrid={ngrid}"
        if tctype != 1:
            self.trace.show(1, msg1)
            raise Exception(f"tctype={tctype}: we implicitly assume the tropospheric correction type (tctype) is 1. if tctype=0 (no topospheric correction), we don't know whether we read the following tropospheric correction data or not. Others are reserved.")
        for grid in range(ngrid):
            if len_payload < payload.pos + 9 + 8:
                return False
            msg1 += '\nST9 SAT NID grid residual[TECU]'
            vd_h = payload.read('i9')  # hydrostatic vertical delay
            vd_w = payload.read('i8')  # wet         vertical delay
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
                        msg1 += f'\nST9 {gsys}  {cnid}   {grid+1:2d}         {res*0.04:{FMT_TECU}}'
        self.trace.show(1, f"pos={payload.pos}, len_payload={len_payload}", fg='yellow')
        self.trace.show(1, msg1)
        self.stat_both += payload.pos
        return True

    def decode_cssr_st10(self, payload):
        ''' decode CSSR ST10 auxiliary message and returns True if success '''
        len_payload = len(payload)
        if len_payload < 5:
            return False
        counter = payload.read('u3')  # info message counter
        dsize   = payload.read('u2')  # data size
        size  = (dsize + 1) * 40
        if len_payload < payload.pos + size:
            return False
        aux_frame_data = payload.read(size)
        self.trace.show(1, f'ST10 {counter}:{aux_frame_data.hex}')
        self.stat_both += payload.pos
        return True

    def decode_cssr_st11(self, payload):
        ''' decode CSSR ST11 network correction message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < 40:
            return False
        f_o = payload.read('u1')  # orbit existing flag
        f_c = payload.read('u1')  # clock existing flag
        f_n = payload.read('u1')  # network correction
        msg1 = f"ST11 orbit_correction={'on' if f_o else 'off'} clock_correction={'on' if f_c else 'off'} network_correction={'on' if f_n else 'off'}"
        svmask = {}
        if f_n:
            if len_payload < payload.pos + 5:
                return False
            cnid = payload.read('u5')  # compact network ID
            if cnid < 1 or N_CLASGRID < cnid:
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
                if f_o:
                    bw = 10 if satsys == 'E' else 8  # IODE bit width
                    if len_payload < payload.pos + bw + 15 + 13 + 13:
                        return False
                    iode   = payload.read(f'u{bw}')  # IODE
                    radial = payload.read('i15')     # radial
                    along  = payload.read('i13')     # along
                    cross  = payload.read('i13')     # cross
                if f_c:
                    if len_payload < payload.pos + 15:
                        return False
                    c0  = payload.read('i15')
                f_o_ok = f_o and (radial != -16384 and along != -4096 and cross != -4096)
                f_c_ok = f_c and c0 != -16384
                if f_o_ok or f_c_ok:
                    msg1 += f"\nST11 {gsys}"
                if f_o_ok:
                    msg1 += f' {iode:{FMT_IODE}}   {radial*0.0016:{FMT_ORB}}  {along*0.0064:{FMT_ORB}}  {cross*0.0064:{FMT_ORB}}'
                if f_c_ok:
                    msg1 += f" {c0*1.6e-3:{FMT_CLK}}"
        self.trace.show(1, msg1)
        self.stat_both += stat_pos + 3
        self.stat_bsat += payload.pos - stat_pos - 3
        if f_n:  # correct bit number because because we count up bsat as NID
            self.stat_both += 5
            self.stat_bsat -= 5
        return True

    def decode_cssr_st12(self, payload):
        ''' decode CSSR ST12 network and troposphere corrections message and returns True if success '''
        len_payload = len(payload)
        if len_payload < 52:
            return False
        tavail = payload.read(  2 )  # troposhpere correction availability
        savail = payload.read(  2 )  # STEC        correction availability
        cnid   = payload.read('u5')  # compact network ID
        ngrid  = payload.read('u6')  # number of grids
        if cnid < 1 or N_CLASGRID < cnid:
            raise Exception(f"invalid compact network ID: {cnid}")
        msg1 = f"ST12 Trop NID={cnid} ({CLASGRID[cnid-1][0]})"
        if tavail[0]:  # bool object
            # 0 <= ttype (forward reference)
            if len_payload < payload.pos + 6 + 2 + 9:
                return False
            tqi   = payload.read(  6 )  # tropo quality indication
            ttype = payload.read('u2')  # tropo correction type
            t00   = payload.read('i9')  # tropo poly coeff
            msg1 += f" qual={ura2dist(tqi)}[mm]"
            if t00 != -256:
                msg1 += f" t00={t00*0.004:.3f}[m]"
            if 1 <= ttype:
                if len_payload < payload.pos + 7 + 7:
                    return False
                t01  = payload.read('i7')
                t10  = payload.read('i7')
                if t01 != -64 and t10 != -64:
                    msg1 += f" t01={t01*0.002:.3f}[m/deg] t10={t10*0.002:.3f}[m/deg]"
            if 2 <= ttype:
                if len_payload < payload.pos + 7:
                    return False
                t11  = payload.read('i7')
                if t11 != -64:
                    msg1 += f" t11={t11*0.001:.3f}[m/deg^2]"
        if tavail[1]:  # bool object
            if len_payload < payload.pos + 1 + 4:
                return False
            trs  = payload.read('u1')  # tropo residual size
            tro  = payload.read('u4')  # tropo residual offset
            bw   = 8 if trs else 6
            msg1 += f" offset={tro*0.02:.3f}[m]"
            if len_payload < payload.pos + bw * ngrid:
                return False
            msg1 += "\nST12 Trop NID grid residual[m]"
            for grid in range(ngrid):
                tr = payload.read(f'i{bw}')  # tropo residual
                if (bw == 6 and tr != -32) or (bw == 8 and tr != -128):
                    msg1 += f"\nST12 Trop  {cnid:2d}   {grid+1:2d} {tr*0.004:{FMT_TROP}}"
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
                    sqi = payload.read(   6 )  # STEC quality indication
                    sct = payload.read( 'u2')   # STEC correct type
                    c00 = payload.read('i14')
                    msg1 += f"\nST12 STEC {gsys} NID grid residual[TECU] qual={ura2dist(sqi):.3f}[TECU]"
                    if c00 != -8192:
                        msg1 += f" c00={c00*0.05:.3f}[TECU]"
                    if 1 <= sct:
                        if len_payload < payload.pos + 12 + 12:
                            return False
                        c01 = payload.read('i12')
                        c10 = payload.read('i12')
                        if c01 != -2048 and c10 != -2048:
                            msg1 += f" c01={c01*0.02:.3f}[TECU/deg] c10={c10*0.02:.3f}[TECU/deg]"
                    if 2 <= sct:
                        if len_payload < payload.pos + 10:
                            return False
                        c11 = payload.read('i10')
                        if c11 != -512:
                            msg1 += f" c11={c11* 0.02:.3f}[TECU/deg^2]"
                    if 3 <= sct:
                        if len_payload < payload.pos + 8 + 8:
                            return False
                        c02 = payload.read('i8')
                        c20 = payload.read('i8')
                        if c02 != -128 and c20 != -128:
                            msg1 += f" c02={c02*0.005:.3f}[TECU/deg^2] c20={c20*0.005:.3f}[TECU/deg^2]"
                    if len_payload < payload.pos + 2:
                        return False
                    srs = payload.read('u2')  # STEC residual size
                    bw  = [   4,    4,    5,    7][srs]
                    lsb = [0.04, 0.12, 0.16, 0.24][srs]
                    for grid in range(ngrid):
                        if len_payload < payload.pos + bw:
                            return False
                        sr  = payload.read(f'i{bw}')  # STEC residual
                        if (bw == 4 and sr !=  -8) or \
                           (bw == 5 and sr != -16) or \
                           (bw == 7 and sr != -64):
                            msg1 += f"\nST12 STEC {gsys}  {cnid:2d}   {grid+1:2d}         {sr*lsb:{FMT_TECU}}"
        if savail[1]:  # bool object
            pass  # the use of this bit is not defined in ref.[1]
        self.trace.show(1, msg1)
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

# EOF

