#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libnav.py: library for navigation message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2026 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.
# [2] Cabinet Office, Government of Japan, Quasi-Zenith Satellite System
#     Interface Specification Satellite Positioning, Navigation and Timing
#     Service, IS-QZSS-PNT-005, Oct. 2022.

# constants
PI      : float = 3.1415926535898            # Ratio of a circle's circumference
MU      : float = 3.986004418  * (10**14)    # Geocentric gravitational constant [m^3/s^2]
OE      : float = 7.2921151467 * (10**(-5))  # Mean angular velocity of the Earth [rad/s]
C       : int   = 299792458                  # Speed of light [m/s]
N_GPSSAT: int   = 63   # maximum number of GPS     satellites
N_GLOSAT: int   = 63   # maximum number of GLONASS satellites
N_GALSAT: int   = 63   # maximum number of Galileo satellites
N_QZSSAT: int   = 11   # maximum number of QZSS    satellites
N_BDSAT : int   = 63   # maximum number of BeiDou  satellites
N_IRNSAT: int   = 12   # maximum number of NavIC   satellites
# format definitions
FMT_IODC: str   = '<4d'  # format string for issue of data clock
FMT_IODE: str   = '<4d'  # format string for issue of data ephemeris

import os
import sys

sys.path.append(os.path.dirname(__file__))
import libtrace

try:
    from bitstring import BitStream
except ModuleNotFoundError:
    libtrace.err('''\
    The code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

class NavNull:
    pass

class NavGps:
    def __init__(self, trace: libtrace.Trace) -> None:
        self.trace = trace
        self.eph   = [NavNull() for _ in range(N_GPSSAT)]
        self.alm   = [NavNull() for _ in range(N_GPSSAT)]

    def decode_rtcm(self, payload: BitStream) -> str:
        ''' read and decode RTCM GPS navigation messages '''
        svid   = payload.read( 6)  # satellite id, DF009
        if svid.u < 1 or svid.u > N_GPSSAT:
            raise Exception(f'GPS satellite ID out of range: {svid.u}')
        e      = self.eph[svid.u-1]
        e.wn   = payload.read(10)  # week number, DF076
        e.sva  = payload.read( 4)  # SV accuracy, DF077
        e.gpsc = payload.read( 2)  # GPS code L2, DF078
        e.idot = payload.read(14)  # IDOT, DF079
        e.iode = payload.read( 8)  # IODE, DF071
        e.toc  = payload.read(16)  # t_oc, DF081
        e.af2  = payload.read( 8)  # a_f2, DF082
        e.af1  = payload.read(16)  # a_f1, DF083
        e.af0  = payload.read(22)  # a_f0, DF084
        e.iodc = payload.read(10)  # IODC, DF085
        e.crs  = payload.read(16)  # C_rs, DF086
        e.dn   = payload.read(16)  # d_n,  DF087
        e.m0   = payload.read(32)  # M_0,  DF088
        e.cuc  = payload.read(16)  # C_uc, DF089
        e.e    = payload.read(32)  # e,    DF090
        e.cus  = payload.read(16)  # C_us, DF091
        e.a12  = payload.read(32)  # a12,  DF092
        e.toe  = payload.read(16)  # t_oe, DF093
        e.cic  = payload.read(16)  # C_ic, DF094
        e.omg0 = payload.read(32)  # Omg0, DF095
        e.cis  = payload.read(16)  # C_is, DF096
        e.i0   = payload.read(32)  # i_0,  DF097
        e.crc  = payload.read(16)  # C_rc, DF098
        e.omg  = payload.read(32)  # omg,  DF099
        e.omgd = payload.read(24)  # Omg-dot, DF100
        e.tgd  = payload.read( 8)  # t_GD, DF101
        e.svh  = payload.read( 6)  # SV health, DF102
        e.l2p  = payload.read( 1)  # P flag, DF103
        e.fi   = payload.read( 1)  # fit interval, DF137
        msg = f'G{svid.u:02d} WN={e.wn.u} IODE={e.iode.u:{FMT_IODE}} IODC={e.iodc.u:{FMT_IODC}}'
        if   e.gpsc == '0b01': msg += ' L2P'
        elif e.gpsc == '0b10': msg += ' L2C/A'
        elif e.gpsc == '0b11': msg += ' L2C'
        else: msg += f'unknown L2 code: {e.gpsc}'
        if e.svh.u:
            msg += self.trace.msg(0, f' unhealthy({e.svh.u:02x})', fg='red')
        return msg

    def convert(self, svid: int) -> NavNull:
        ''' decode GPS ephemeris '''
        e       = self.eph[svid-1]
        d       = NavNull()
        d.m0    = e.m0.i   * 2**(-31)*PI  # mean anomaly at reference time
        d.e     = e.e.u    * 2**(-33)     # eccentricity
        d.a12   = e.a12.u  * 2**(-19)     # square root of the semi-major axis
        d.t0e   = e.t0e.u  * 60           # ephemeris reference time
        d.omg0  = e.omg0.i * 2**(-31)*PI  # longitude of ascending node of orbital plane
        d.i0    = e.i0.i   * 2**(-31)*PI  # inclination angle at reference time
        d.omg   = e.omg.i  * 2**(-31)*PI  # argument of perigee
        d.idot  = e.idot.i * 2**(-43)*PI  # rate of change of inclination angle
        d.dn    = e.dn.i   * 2**(-43)*PI  # mean motion difference from computed value
        d.omgd  = e.omgd.i * 2**(-43)*PI  # rate of change of right ascension
        d.cuc   = e.cuc.i  * 2**(-29)     # cos harmonic correction term to the argument of latitude
        d.cus   = e.cus.i  * 2**(-29)     # sin harmonic correction term to the argument of latitude
        d.crc   = e.crc.i  * 2**(-5)      # cos harmonic correction term to the orbit radius
        d.crs   = e.crs.i  * 2**(-5)      # sin harmonic correction term to the orbit radius
        d.cic   = e.cic.i  * 2**(-29)     # cos harmonic correction term to the angle of inclination
        d.cis   = e.cis.i  * 2**(-29)     # sin harmonic correction term to the angle of inclination
        d.t0c   = e.t0c.u  * 60           # clock correction data reference TOW
        d.af0   = e.af0.i  * 2**(-34)     # SV clock bias correction coefficient
        d.af1   = e.af1.i  * 2**(-46)     # SV clock drift correction coefficient
        d.af2   = e.af2.i  * 2**(-59)     # SV clock drift rate correction coefficient
        d.be5a  = e.be5a.i * 2**(-32)     # E1-E5a broadcast group delay
        d.be5b  = e.be5b.i * 2**(-32)     # E1-E5b broadcast group delay
        d.ai0   = e.ai0.u  * 2**(-2)      # effective ionisation level 1st order parameter
        d.ai1   = e.ai1.i  * 2**(-8)      # effective ionisation level 2nd order parameter
        d.a0    = e.a0.i   * 2**(-30)     # constant term of polynomial
        d.a1    = e.a1.i   * 2**(-50)     # 1st order term of polynomial
        d.dtls  = e.dtls.i                # leap Second count before leap second adjustment
        d.t0t   = e.t0t.u                 # UTC data reference TOW
        d.wn0t  = e.wn0t.u                # UTC data reference week number
        d.wnlsf = e.wnlsf.u               # week number of leap second adjustment
        d.dn    = e.dn.u                  # day number at the end of which a leap second adjustment becomes effective
        d.dtlsf = e.dtlsf.i               # leap second count after leap second adjustment
        d.a0g   = e.a0g.i  * 2**(-35)     # constant term of the polynomial describing the offset
        d.a1g   = e.a1g.i  * 2**(-51)     # rate of change of the offset
        d.t0g   = e.t0g.u  * 3600         # reference time for GGTO data
        d.wn0g  = e.wn0g.u                # week number of GGTO reference
        return d

class NavGlo:
    ''' GLONASS ephemeris data '''

    def __init__(self, trace: libtrace.Trace) -> None:
        self.trace = trace
        self.eph   = [NavNull() for _ in range(N_GLOSAT)]
        self.alm   = [NavNull() for _ in range(N_GLOSAT)]

    def decode_rtcm(self, payload: BitStream) -> str:
        ''' read and decode RTCM GLONASS ephemeris '''
        svid    = payload.read( 6)  # satellite id, DF038
        if svid.u < 1 or svid.u > N_GLOSAT:
            raise Exception(f'GLONASS satellite ID out of range: {svid.u}')
        e       = self.eph[svid.u-1]
        e.fcn   = payload.read( 5)  # freq ch, DF040
        e.svh   = payload.read( 1)  # alm health DF104
        e.aha   = payload.read( 1)  # alm health avail, DF105
        e.p1    = payload.read( 2)  # P1, DF106
        e.tk    = payload.read(12)  # t_k, DF107
        e.bn    = payload.read( 1)  # B_n word MSB, DF108
        e.p2    = payload.read( 1)  # P2, DF109
        e.tb    = payload.read( 7)  # t_b, DF110
        e.xnd   = payload.read(24)  # x_n dot, DF111
        e.xn    = payload.read(27)  # x_n, DF112
        e.xndd  = payload.read( 5)  # x_n dot^2, DF113
        e.ynd   = payload.read(24)  # y_n dot, DF114
        e.yn    = payload.read(27)  # y_n, DF115
        e.yndd  = payload.read( 5)  # y_n dot^2, DF116
        e.znd   = payload.read(24)  # z_n dot, DF117
        e.zn    = payload.read(27)  # z_n, DF118
        e.zndd  = payload.read( 5)  # z_n dot^2, DF119
        e.p3    = payload.read( 1)  # P3, DF120
        e.gmn   = payload.read(11)  # gamma_n, DF121
        e.p     = payload.read( 2)  # P, DF122
        e.in3   = payload.read( 1)  # I_n, DF123
        e.taun  = payload.read(22)  # tau_n, DF124
        e.dtaun = payload.read( 5)  # d_tau_n, DF125
        e.en    = payload.read( 5)  # E_n, DF126
        e.p4    = payload.read( 1)  # P4, DF127
        e.ft    = payload.read( 4)  # F_t, DF128
        e.nt    = payload.read(11)  # N_t, DF129
        e.m     = payload.read( 2)  # M, DF130
        e.add   = payload.read( 1)  # addition, DF131
        e.na    = payload.read(11)  # N^A, DF132
        e.tauc  = payload.read(32)  # tau_c, DF133
        e.n4    = payload.read( 5)  # N_4, DF134
        e.tgps  = payload.read(22)  # tau_GPS, DF135
        e.in5   = payload.read( 1)  # I_n, DF136
        payload.pos +=  7                   # reserved
        msg = f'R{svid.u:02d} f={e.fcn.i:02d} tk={e.tk[7:12].u:02d}:{e.tk[1:7].u:02d}:{e.tk[0:2].u*15:02d} tb={e.tb.u*15}min'
        if e.svh.u:
            msg += self.trace.msg(0, ' unhealthy', fg='red')
        return msg

class NavGal:
    def __init__(self, trace: libtrace.Trace) -> None:
        self.trace = trace
        self.eph   = [NavNull() for _ in range(N_GALSAT)]
        self.alm   = [NavNull() for _ in range(N_GALSAT)]
        self.svid1 = -1  # Galileo almanac for SV1
        self.svid2 = -1  # Galileo almanac for SV2
        self.svid3 = -1  # Galileo almanac for SV3

    def decode_rtcm(self, payload: BitStream, mtype: str) -> str:
        ''' read and decode RTCM Galileo ephemeris '''
        svid    = payload.read( 6)     # satellite id, DF252
        if svid.u < 1 or svid.u > N_GALSAT:
            raise Exception(f'Galileo satellite ID out of range: {svid.u}')
        e       = self.eph[svid.u-1]
        e.wn    = payload.read(12)     # week number, DF289
        e.iodn  = payload.read(10)     # IODnav, DF290
        e.sisa  = payload.read( 8)     # SIS Accuracy, DF291
        e.idot  = payload.read(14)     # IDOT, DF292
        e.toc   = payload.read(14)     # t_oc, DF293
        e.af2   = payload.read( 6)     # a_f2, DF294
        e.af1   = payload.read(21)     # a_f1, DF295
        e.af0   = payload.read(31)     # a_f0, DF296
        e.crs   = payload.read(16)     # C_rs, DF297
        e.dn    = payload.read(16)     # delta n, DF298
        e.m0    = payload.read(32)     # M_0, DF299
        e.cuc   = payload.read(16)     # C_uc, DF300
        e.e     = payload.read(32)     # e, DF301
        e.cus   = payload.read(16)     # C_us, DF302
        e.a12   = payload.read(32)     # sqrt_a, DF303
        e.toe   = payload.read(14)     # t_oe, DF304
        e.cic   = payload.read(16)     # C_ic, DF305
        e.omg0  = payload.read(32)     # Omega_0, DF306
        e.cis   = payload.read(16)     # C_is, DF307
        e.i0    = payload.read(32)     # i_0, DF308
        e.crc   = payload.read(16)     # C_rc, DF309
        e.omg   = payload.read(32)     # omega, DF310
        e.omgd0 = payload.read(24)     # Omega-dot0, DF311
        e.be5a  = payload.read(10)     # BGD_E5aE1, DF312
        msg = f'E{svid.u:02d} WN={e.wn.u} IODnav={e.iodn.u}'
        if   mtype == 'F/NAV':
            e.osh = payload.read(2)    # open signal health DF314
            e.osv = payload.read(1)    # open signal valid DF315
            payload.pos += 7           # reserved, DF001
            if e.osh.u:
                msg += self.trace.msg(0, f' unhealthy OS ({e.osh.u})', fg='red')
            if e.osv.u:
                msg += self.trace.msg(0, ' invalid OS', fg='red')
        elif mtype == 'I/NAV':
            e.be5b = payload.read(10)  # BGD_E5bE1 DF313
            e.e5h  = payload.read( 2)  # E5b signal health, DF316
            e.e5v  = payload.read( 1)  # E5b data validity, DF317
            e.e1h  = payload.read( 2)  # E1b signal health, DF287
            e.e1v  = payload.read( 1)  # E1b data validity, DF288
            payload.pos += 2           # reserved, DF001
            if e.e5h.u:
                msg += self.trace.msg(0, f' unhealthy E5b ({e.e5h.u})', fg='red')
            if e.e5v.u:
                msg += self.trace.msg(0, ' invalid E5b', fg='red')
            if e.e1h.u:
                msg += self.trace.msg(0, f' unhealthy E1b ({e.e1h.u})', fg='red')
            if e.e1v.u:
                msg += self.trace.msg(0, ' invalid E1b', fg='red')
        else:
            raise Exception(f'unknown Galileo nav message: {mtype}')
        return msg

class NavQzs(NavGps):
    def __init__(self, trace: libtrace.Trace) -> None:
        self.trace = trace
        self.eph   = [NavNull() for _ in range(N_QZSSAT)]
        self.alm   = [NavNull() for _ in range(N_QZSSAT)]

    def decode_rtcm(self, payload: BitStream) -> str:
        ''' read and decode RTCM QZSS ephemeris '''
        svid   = payload.read( 4)  # satellite id, DF429
        if svid.u < 1 or svid.u > N_QZSSAT:
            raise Exception(f'QZSS satellite ID out of range: {svid.u}')
        e      = self.eph[svid.u-1]
        e.toc  = payload.read(16)  # t_oc, DF430
        e.af2  = payload.read( 8)  # a_f2, DF431
        e.af1  = payload.read(16)  # a_f1, DF432
        e.af0  = payload.read(22)  # a_f0, DF433
        e.iode = payload.read( 8)  # IODE, DF434
        e.crs  = payload.read(16)  # C_rs, DF435
        e.dn0  = payload.read(16)  # delta n_0, DF436
        e.m0   = payload.read(32)  # M_0, DF437
        e.cuc  = payload.read(16)  # C_uc, DF438
        e.e    = payload.read(32)  # e, DF439
        e.cus  = payload.read(16)  # C_uc, DF440
        e.a12  = payload.read(32)  # sqrt_A, DF441
        e.toe  = payload.read(16)  # t_oe, DF442
        e.cic  = payload.read(16)  # C_ic, DF443
        e.omg0 = payload.read(32)  # Omg_0, DF444
        e.cis  = payload.read(16)  # C_is, DF445
        e.i0   = payload.read(32)  # i_0, DF446
        e.crc  = payload.read(16)  # C_rc, DF447
        e.omgn = payload.read(32)  # omg_n, DF448
        e.omgd = payload.read(24)  # Omg dot, DF449
        e.i0d  = payload.read(14)  # i0 dot, DF450
        e.l2   = payload.read( 2)  # L2 code, DF451
        e.wn   = payload.read(10)  # week number, DF452
        e.ura  = payload.read( 4)  # URA, DF453
        e.svh  = payload.read( 6)  # SVH, DF454
        e.tgd  = payload.read( 8)  # T_GD, DF455
        e.iodc = payload.read(10)  # IODC, DF456
        e.fi   = payload.read( 1)  # fit interval, DF457
        msg = f'J{svid.u:02d} WN={e.wn.u} IODE={e.iode.u:{FMT_IODE}} IODC={e.iodc.u:{FMT_IODC}}'
        if (e.svh[0:1]+e.svh[2:5]).u:  # determination of QZSS health including L1C/B is complex, self.f.[2], p.47, 4.1.2.3(4)
            unhealthy = ''
            if e.svh[1]: unhealthy += ' L1C/A'
            if e.svh[2]: unhealthy += ' L2C'
            if e.svh[3]: unhealthy += ' L5'
            if e.svh[4]: unhealthy += ' L1C'
            if e.svh[5]: unhealthy += ' L1C/B'
            msg += self.trace.msg(0, f' unhealthy ({unhealthy[1:]})', fg='red')
        elif not e.svh[0]:                # L1 signal is healthy
            if e.svh[1]: msg += ' L1C/B'  # transmitting L1C/B
            if e.svh[5]: msg += ' L1C/A'  # transmitting L1C/A
        return msg

class NavBds:
    def __init__(self, trace: libtrace.Trace) -> None:
        self.trace = trace
        self.eph   = [NavNull() for _ in range(N_BDSAT)]
        self.alm   = [NavNull() for _ in range(N_BDSAT)]

    def decode_rtcm(self, payload: BitStream) -> str:
        ''' read and decode RTCM BeiDou ephemeris '''
        svid   = payload.read( 6)  # satellite id, DF488
        if svid.u < 1 or svid.u > N_BDSAT:
            raise Exception(f'BeiDou satellite ID out of range: {svid.u}')
        e      = self.eph[svid.u-1]
        e.wn   = payload.read(13)  # week number, DF489
        e.urai = payload.read( 4)  # URA, DF490
        e.idot = payload.read(14)  # IDOT, DF491
        e.aode = payload.read( 5)  # AODE, DF492
        e.toc  = payload.read(17)  # t_oc, DF493
        e.a2   = payload.read(11)  # a_2, DF494
        e.a1   = payload.read(22)  # a_1, DF495
        e.a0   = payload.read(24)  # a_0, DF496
        e.aodc = payload.read( 5)  # AODC, DF497
        e.crs  = payload.read(18)  # C_rs, DF498
        e.dn   = payload.read(16)  # delta n, DF499
        e.m0   = payload.read(32)  # M_0, DF500
        e.cuc  = payload.read(18)  # C_uc, DF501
        e.e    = payload.read(32)  # e, DF502
        e.cus  = payload.read(18)  # C_us, DF503
        e.a12  = payload.read(32)  # sqrt_a, DF504
        e.toe  = payload.read(17)  # t_oe, DF505
        e.cic  = payload.read(18)  # C_ic, DF506
        e.omg0 = payload.read(32)  # Omg_0, DF507
        e.cis  = payload.read(18)  # C_is, DF508
        e.i0   = payload.read(32)  # i_0, DF509
        e.crc  = payload.read(18)  # C_rc, DF510
        e.omg  = payload.read(32)  # omg, DF511
        e.omgd = payload.read(24)  # Omg dot, DF512
        e.tgd1 = payload.read(10)  # T_GD1, DF513
        e.tgd2 = payload.read(10)  # T_GD2, DF514
        e.svh  = payload.read( 1)  # SVH, DF515
        msg =f'C{svid.u:02d} WN={e.wn.u} AODE={e.aode.u}'
        if e.svh.u:
            msg += self.trace.msg(0, ' unhealthy', fg='red')
        return msg

class NavIrn:
    def __init__(self, trace: libtrace.Trace) -> None:
        self.trace = trace
        self.eph = [NavNull() for _ in range(N_IRNSAT)]
        self.alm = [NavNull() for _ in range(N_IRNSAT)]

    def decode_rtcm(self, payload: BitStream) -> str:
        ''' read and decode RTCM IRNSS ephemeris '''
        svid    = payload.read( 6)  # satellite id, DF516
        if svid.u < 1 or svid.u > N_IRNSAT:
            raise Exception(f'IRNSS satellite ID out of range: {svid.u}')
        e       = self.eph[svid.u-1]
        e.wn    = payload.read(10)  # week number, DF517
        e.af0   = payload.read(22)  # a_f0, DF518
        e.af1   = payload.read(16)  # a_f1, DF519
        e.af2   = payload.read( 8)  # a_f2, DF520
        e.ura   = payload.read( 4)  # URA, DF521
        e.toc   = payload.read(16)  # t_oc, DF522
        e.tgd   = payload.read( 8)  # t_GD, DF523
        e.dn    = payload.read(22)  # delta n, DF524
        e.iodec = payload.read( 8)  # IODEC, DF525
        payload.pos += 10               # reserved, DF526
        e.hl5   = payload.read( 1)  # L5_flag, DF527
        e.hs    = payload.read( 1)  # S_flag, DF528
        e.cuc   = payload.read(15)  # C_uc, DF529
        e.cus   = payload.read(15)  # C_us, DF530
        e.cic   = payload.read(15)  # C_ic, DF531
        e.cis   = payload.read(15)  # C_is, DF532
        e.crc   = payload.read(15)  # C_rc, DF533
        e.crs   = payload.read(15)  # C_rs, DF534
        e.idot  = payload.read(14)  # IDOT, DF535
        e.m0    = payload.read(32)  # M_0, DF536
        e.toe   = payload.read(16)  # t_oe, DF537
        e.e     = payload.read(32)  # e, DF538
        e.a12   = payload.read(32)  # sqrt_A, DF539
        e.omg0  = payload.read(32)  # Omg0, DF540
        e.omg   = payload.read(32)  # omg, DF541
        e.omgd  = payload.read(22)  # Omg dot, DF542
        e.i0    = payload.read(32)  # i0, DF543
        payload.pos += 2              # spare, DF544
        payload.pos += 2              # spare, DF545
        msg = f'I{svid.u:02d} WN={e.wn.u} IODEC={e.iodec.u:{FMT_IODE}}'
        if e.hl5.u or e.hs.u:
            msg += self.trace.msg(0, ' unhealthy', fg='red')
            if e.hl5.u:
                msg += self.trace.msg(0, ' L5', fg='red')
            if e.hs.u:
                msg += self.trace.msg(0, ' S', fg='red')
        return msg

# EOF
