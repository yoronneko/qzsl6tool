#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libeph.py: library for RTCM ephemeride message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2024 Satoshi Takahashi
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
PI = 3.1415926535898            # Ratio of a circle's circumference
MU = 3.986004418  * (10**14)    # Geocentric gravitational constant [m^3/s^2]
OE = 7.2921151467 * (10**(-5))  # Mean angular velocity of the Earth [rad/s]
C  = 299792458                  # Speed of light [m/s]
N_GPSSAT = 63   # maximum number of GPS     satellites
N_GLOSAT = 63   # maximum number of GLONASS satellites
N_GALSAT = 63   # maximum number of Galileo satellites
N_QZSSAT = 11   # maximum number of QZSS    satellites
N_BDSAT  = 63   # maximum number of BeiDou  satellites
N_IRNSAT = 9    # maximum number of NavIC   satellites

# format definitions
FMT_IODC = '<4d'  # format string for issue of data clock
FMT_IODE = '<4d'  # format string for issue of data ephemeris

class EphNull:
    pass

class EphGps:
    ''' GPS ephemeris data '''

    def __init__(self, trace):
        self.trace = trace
        self.eph   = [EphNull() for _ in range(N_GPSSAT)]
        self.alm   = [EphNull() for _ in range(N_GPSSAT)]

    def decode_rtcm(self, payload):
        ''' read and decode RTCM GPS ephemeris '''
        svid     = payload.read( 6).u  # satellite id, DF009
        eph      = self.eph[svid-1]
        eph.wn   = payload.read(10).u  # week number, DF076
        eph.sva  = payload.read( 4).u  # SV accuracy DF077
        eph.gpsc = payload.read( 2)    # GPS code L2, DF078
        eph.idot = payload.read(14).i  # IDOT, DF079
        eph.iode = payload.read( 8).u  # IODE, DF071
        eph.toc  = payload.read(16).u  # t_oc, DF081
        eph.af2  = payload.read( 8).i  # a_f2, DF082
        eph.af1  = payload.read(16).i  # a_f1, DF083
        eph.af0  = payload.read(22).i  # a_f0, DF084
        eph.iodc = payload.read(10).u  # IODC, DF085
        eph.crs  = payload.read(16).i  # C_rs, DF086
        eph.dn   = payload.read(16).i  # d_n,  DF087
        eph.m0   = payload.read(32).i  # M_0,  DF088
        eph.cuc  = payload.read(16).i  # C_uc, DF089
        eph.e    = payload.read(32).u  # e,    DF090
        eph.cus  = payload.read(16).i  # C_us, DF091
        eph.a12  = payload.read(32).u  # a12,  DF092
        eph.toe  = payload.read(16).u  # t_oe, DF093
        eph.cic  = payload.read(16).i  # C_ic, DF094
        eph.omg0 = payload.read(32).i  # Omg0, DF095
        eph.cis  = payload.read(16).i  # C_is, DF096
        eph.i0   = payload.read(32).i  # i_0,  DF097
        eph.crc  = payload.read(16).i  # C_rc, DF098
        eph.omg  = payload.read(32).i  # omg,  DF099
        eph.omgd = payload.read(24).i  # Omg-dot, DF100
        eph.tgd  = payload.read( 8).i  # t_GD, DF101
        eph.svh  = payload.read( 6).u  # SV health, DF102
        eph.l2p  = payload.read( 1).u  # P flag, DF103
        eph.fi   = payload.read( 1).u  # fit interval, DF137
        msg = f'G{svid:02d} WN={eph.wn} IODE={eph.iode:{FMT_IODE}} IODC={eph.iodc:{FMT_IODC}}'
        if   eph.gpsc == '0b01': msg += ' L2P'
        elif eph.gpsc == '0b10': msg += ' L2C/A'
        elif eph.gpsc == '0b11': msg += ' L2C'
        else: msg += f'unknown L2 code: {eph.gpsc}'
        if eph.svh:
            msg += self.trace.msg(0, f' unhealthy({eph.svh:02x})', fg='red')
        return msg

    def convert(self, svid):
        ''' decode GPS ephemeris '''
        eph   = self.eph[svid-1]
        m0    = eph.m0.i   * 2**(-31)*PI  # mean anomaly at reference time
        e     = eph.e.u    * 2**(-33)     # eccentricity
        a12   = eph.a12.u  * 2**(-19)     # square root of the semi-major axis
        t0e   = eph.t0e.u  * 60           # ephemeris reference time
        omg0  = eph.omg0.i * 2**(-31)*PI  # longitude of ascending node of orbital plane
        i0    = eph.i0.i   * 2**(-31)*PI  # inclination angle at reference time
        omg   = eph.omg.i  * 2**(-31)*PI  # argument of perigee
        idot  = eph.idot.i * 2**(-43)*PI  # rate of change of inclination angle
        dn    = eph.dn.i   * 2**(-43)*PI  # mean motion difference from computed value
        omgd  = eph.omgd.i * 2**(-43)*PI  # rate of change of right ascension
        cuc   = eph.cuc.i  * 2**(-29)     # cos harmonic correction term to the argument of latitude
        cus   = eph.cus.i  * 2**(-29)     # sin harmonic correction term to the argument of latitude
        crc   = eph.crc.i  * 2**(-5)      # cos harmonic correction term to the orbit radius
        crs   = eph.crs.i  * 2**(-5)      # sin harmonic correction term to the orbit radius
        cic   = eph.cic.i  * 2**(-29)     # cos harmonic correction term to the angle of inclination
        cis   = eph.cis.i  * 2**(-29)     # sin harmonic correction term to the angle of inclination
        t0c   = eph.t0c.u  * 60           # clock correction data reference TOW
        af0   = eph.af0.i  * 2**(-34)     # SV clock bias correction coefficient
        af1   = eph.af1.i  * 2**(-46)     # SV clock drift correction coefficient
        af2   = eph.af2.i  * 2**(-59)     # SV clock drift rate correction coefficient
        be5a  = eph.be5a.i * 2**(-32)     # E1-E5a broadcast group delay
        be5b  = eph.be5b.i * 2**(-32)     # E1-E5b broadcast group delay
        ai0   = eph.ai0.u  * 2**(-2)      # effective ionisation level 1st order parameter
        ai1   = eph.ai1.i  * 2**(-8)      # effective ionisation level 2nd order parameter
        a0    = eph.a0.i   * 2**(-30)     # constant term of polynomial
        a1    = eph.a1.i   * 2**(-50)     # 1st order term of polynomial
        dtls  = eph.dtls.i                # leap Second count before leap second adjustment
        t0t   = eph.t0t.u                 # UTC data reference TOW
        wn0t  = eph.wn0t.u                # UTC data reference week number
        wnlsf = eph.wnlsf.u               # week number of leap second adjustment
        dn    = eph.dn.u                  # day number at the end of which a leap second adjustment becomes effective
        dtlsf = eph.dtlsf.i               # leap second count after leap second adjustment
        a0g   = eph.a0g.i  * 2**(-35)     # constant term of the polynomial describing the offset
        a1g   = eph.a1g.i  * 2**(-51)     # rate of change of the offset
        t0g   = eph.t0g.u  * 3600         # reference time for GGTO data
        wn0g  = eph.wn0g.u                # week number of GGTO reference

class EphGlo:
    ''' GLONASS ephemeris data '''

    def __init__(self, trace):
        self.trace = trace
        self.eph   = [EphNull() for _ in range(N_GLOSAT)]
        self.alm   = [EphNull() for _ in range(N_GLOSAT)]

    def decode_rtcm(self, payload):
        ''' read and decode RTCM GLONASS ephemeris '''
        svid      =       payload.read( 6).u        # satellite id, DF038
        eph       =       self.eph[svid-1]
        eph.fcn   =       payload.read( 5).u        # freq ch, DF040
        eph.svh   =       payload.read( 1).u        # alm health DF104
        eph.aha   =       payload.read( 1).u        # alm health avail, DF105
        eph.p1    =       payload.read( 2).u        # P1, DF106
        eph.tk    =       payload.read(12)          # t_k, DF107
        eph.bn    =       payload.read( 1).u        # B_n word MSB, DF108
        eph.p2    =       payload.read( 1).u        # P2, DF109
        eph.tb    =       payload.read( 7).u        # t_b, DF110
        eph.xnd   = -1 if payload.read( 1).u else 1 # x_n dot, DF111
        eph.xnd   *=      payload.read(23).u
        eph.xn    = -1 if payload.read( 1).u else 1 # x_n, DF112
        eph.xn    *=      payload.read(26).u
        eph.xndd  = -1 if payload.read( 1).u else 1 # x_n dot^2, DF113
        eph.xndd  *=      payload.read( 4).u
        eph.ynd   = -1 if payload.read( 1).u else 1 # y_n dot, DF114
        eph.ynd   *=      payload.read(23).u
        eph.yn    = -1 if payload.read( 1).u  else 1 # y_n, DF115
        eph.yn    *=      payload.read(26).u
        eph.yndd  = -1 if payload.read( 1).u  else 1 # y_n dot^2, DF116
        eph.yndd  *=      payload.read( 4).u
        eph.znd   = -1 if payload.read( 1).u  else 1 # z_n dot, DF117
        eph.znd   *=      payload.read(23).u
        eph.zn    = -1 if payload.read( 1).u  else 1 # z_n, DF118
        eph.zn    *=      payload.read(26).u
        eph.zndd  = -1 if payload.read( 1).u  else 1 # z_n dot^2, DF119
        eph.zndd  *=      payload.read( 4).u
        eph.p3    =       payload.read( 1).u         # P3, DF120
        eph.gmn   = -1 if payload.read( 1).u  else 1 # gamma_n, DF121
        eph.gmn   *=      payload.read(10).u
        eph.p     =       payload.read( 2)           # P, DF122
        eph.in3   =       payload.read( 1).u         # I_n, DF123
        eph.taun  = -1 if payload.read( 1).u  else 1 # tau_n, DF124
        eph.taun  *=      payload.read(21).u
        eph.dtaun = -1 if payload.read( 1).u  else 1 # d_tau_n, DF125
        eph.dtaun *=      payload.read( 4).u
        eph.en    =       payload.read( 5).u         # E_n, DF126
        eph.p4    =       payload.read( 1).u         # P4, DF127
        eph.ft    =       payload.read( 4).u         # F_t, DF128
        eph.nt    =       payload.read(11).u         # N_t, DF129
        eph.m     =       payload.read( 2)           # M, DF130
        eph.add   =       payload.read( 1).u         # addition, DF131
        eph.na    =       payload.read(11).u         # N^A, DF132
        eph.tauc  = -1 if payload.read( 1).u  else 1 # tau_c, DF133
        eph.tauc  *=      payload.read(31).u
        eph.n4    =       payload.read( 5).u         # N_4, DF134
        eph.tgps  = -1 if payload.read( 1).u  else 1 # tau_GPS, DF135
        eph.tgps  *=      payload.read(21).u
        eph.in5   =       payload.read( 1).u         # I_n, DF136
        payload.pos +=  7                             # reserved
        msg = f'R{svid:02d} f={eph.fcn:02d} tk={eph.tk[7:12].u:02d}:{eph.tk[1:7].u:02d}:{eph.tk[0:2].u*15:02d} tb={eph.tb*15}min'
        if eph.svh:
            msg += self.trace.msg(0, ' unhealthy', fg='red')
        return msg

class EphGal:
    def __init__(self, trace):
        self.trace = trace
        self.eph   = [EphNull() for _ in range(N_GALSAT)]
        self.alm   = [EphNull() for _ in range(N_GALSAT)]
        self.svid1 = -1  # Galileo almanac for SV1
        self.svid2 = -1  # Galileo almanac for SV2
        self.svid3 = -1  # Galileo almanac for SV3

    def decode_rtcm(self, payload, mtype):
        ''' read and decode RTCM Galileo ephemeris '''
        svid      = payload.read( 6).u     # satellite id, DF252
        eph       = self.eph[svid-1]
        eph.wn    = payload.read(12).u     # week number, DF289
        eph.iodn  = payload.read(10).u     # IODnav, DF290
        eph.sisa  = payload.read( 8).u     # SIS Accuracy, DF291
        eph.idot  = payload.read(14).i     # IDOT, DF292
        eph.toc   = payload.read(14).u     # t_oc, DF293
        eph.af2   = payload.read( 6).i     # a_f2, DF294
        eph.af1   = payload.read(21).i     # a_f1, DF295
        eph.af0   = payload.read(31).i     # a_f0, DF296
        eph.crs   = payload.read(16).i     # C_rs, DF297
        eph.dn    = payload.read(16).i     # delta n, DF298
        eph.m0    = payload.read(32).i     # M_0, DF299
        eph.cuc   = payload.read(16).i     # C_uc, DF300
        eph.e     = payload.read(32).u     # e, DF301
        eph.cus   = payload.read(16).i     # C_us, DF302
        eph.a12   = payload.read(32).u     # sqrt_a, DF303
        eph.toe   = payload.read(14).u     # t_oe, DF304
        eph.cic   = payload.read(16).i     # C_ic, DF305
        eph.omg0  = payload.read(32).i     # Omega_0, DF306
        eph.cis   = payload.read(16).i     # C_is, DF307
        eph.i0    = payload.read(32).i     # i_0, DF308
        eph.crc   = payload.read(16).i     # C_rc, DF309
        eph.omg   = payload.read(32).i     # omega, DF310
        eph.omgd0 = payload.read(24).i     # Omega-dot0, DF311
        eph.be5a  = payload.read(10).i     # BGD_E5aE1, DF312
        if   mtype == 'F/NAV':
            eph.osh = payload.read(2).u    # open signal health DF314
            eph.osv = payload.read(1).u    # open signal valid DF315
            payload.pos += 7               # reserved, DF001
        elif mtype == 'I/NAV':
            eph.be5b = payload.read(10).i  # BGD_E5bE1 DF313
            eph.e5h  = payload.read( 2).u  # E5b signal health, DF316
            eph.e5v  = payload.read( 1).u  # E5b data validity, DF317
            eph.e1h  = payload.read( 2).u  # E1b signal health, DF287
            eph.e1v  = payload.read( 1).u  # E1b data validity, DF288
            payload.pos += 2               # reserved, DF001
        else:
            raise Exception(f'unknown Galileo nav message: {mtype}')
        msg = f'E{svid:02d} WN={eph.wn} IODnav={eph.iodn}'
        if   mtype == 'F/NAV':
            if eph.osh:
                msg += self.trace.msg(0, f' unhealthy OS ({eph.osh})', fg='red')
            if eph.osv:
                msg += self.trace.msg(0, ' invalid OS', fg='red')
        elif mtype == 'I/NAV':
            if eph.e5h:
                msg += self.trace.msg(0, f' unhealthy E5b ({eph.e5h})', fg='red')
            if eph.e5v:
                msg += self.trace.msg(0, ' invalid E5b', fg='red')
            if eph.e1h:
                msg += self.trace.msg(0, f' unhealthy E1b ({eph.e1h})', fg='red')
            if eph.e1v:
                msg += self.trace.msg(0, ' invalid E1b', fg='red')
        else:
            raise Exception(f'unknown Galileo nav message: {mtype}')
        return msg

class EphQzs:
    def __init__(self, trace):
        self.trace = trace
        self.eph   = [EphNull() for _ in range(N_QZSSAT)]
        self.alm   = [EphNull() for _ in range(N_QZSSAT)]

    def decode_rtcm(self, payload):
        ''' read and decode RTCM QZSS ephemeris '''
        svid     = payload.read( 4).u  # satellite id, DF429
        eph      = self.eph[svid-1]
        eph.toc  = payload.read(16).u  # t_oc, DF430
        eph.af2  = payload.read( 8).i  # a_f2, DF431
        eph.af1  = payload.read(16).i  # a_f1, DF432
        eph.af0  = payload.read(22).i  # a_f0, DF433
        eph.iode = payload.read( 8).u  # IODE, DF434
        eph.crs  = payload.read(16).i  # C_rs, DF435
        eph.dn0  = payload.read(16).i  # delta n_0, DF436
        eph.m0   = payload.read(32).i  # M_0, DF437
        eph.cuc  = payload.read(16).i  # C_uc, DF438
        eph.e    = payload.read(32).u  # e, DF439
        eph.cus  = payload.read(16).i  # C_uc, DF440
        eph.a12  = payload.read(32).u  # sqrt_A, DF441
        eph.toe  = payload.read(16).u  # t_oe, DF442
        eph.cic  = payload.read(16).i  # C_ic, DF443
        eph.omg0 = payload.read(32).i  # Omg_0, DF444
        eph.cis  = payload.read(16).i  # C_is, DF445
        eph.i0   = payload.read(32).i  # i_0, DF446
        eph.crc  = payload.read(16).i  # C_rc, DF447
        eph.omgn = payload.read(32).i  # omg_n, DF448
        eph.omgd = payload.read(24).i  # Omg dot, DF449
        eph.i0d  = payload.read(14).i  # i0 dot, DF450
        eph.l2   = payload.read( 2).u  # L2 code, DF451
        eph.wn   = payload.read(10).u  # week number, DF452
        eph.ura  = payload.read( 4).u  # URA, DF453
        eph.svh  = payload.read( 6)    # SVH, DF454
        eph.tgd  = payload.read( 8).i  # T_GD, DF455
        eph.iodc = payload.read(10).u  # IODC, DF456
        eph.fi   = payload.read( 1).u  # fit interval, DF457
        msg = f'J{svid:02d} WN={eph.wn} IODE={eph.iode:{FMT_IODE}} IODC={eph.iodc:{FMT_IODC}}'
        if (eph.svh[0:1]+eph.svh[2:5]).u:  # determination of QZSS health including L1C/B is complex, self.f.[2], p.47, 4.1.2.3(4)
            unhealthy = ''
            if eph.svh[1]: unhealthy += ' L1C/A'
            if eph.svh[2]: unhealthy += ' L2C'
            if eph.svh[3]: unhealthy += ' L5'
            if eph.svh[4]: unhealthy += ' L1C'
            if eph.svh[5]: unhealthy += ' L1C/B'
            msg += self.trace.msg(0, f' unhealthy ({unhealthy[1:]})', fg='red')
        elif not eph.svh[0]:                # L1 signal is healthy
            if eph.svh[1]: msg += ' L1C/B'  # transmitting L1C/B
            if eph.svh[5]: msg += ' L1C/A'  # transmitting L1C/A
        return msg

class EphBds:
    def __init__(self, trace):
        self.trace = trace
        self.eph   = [EphNull() for _ in range(N_BDSAT)]
        self.alm   = [EphNull() for _ in range(N_BDSAT)]

    def decode_rtcm(self, payload):
        ''' read and decode RTCM BeiDou ephemeris '''
        svid     = payload.read( 6).u  # satellite id, DF488
        eph      = self.eph[svid-1]
        eph.wn   = payload.read(13).u  # week number, DF489
        eph.urai = payload.read( 4).u  # URA, DF490
        eph.idot = payload.read(14).i  # IDOT, DF491
        eph.aode = payload.read( 5).u  # AODE, DF492
        eph.toc  = payload.read(17).u  # t_oc, DF493
        eph.a2   = payload.read(11).i  # a_2, DF494
        eph.a1   = payload.read(22).i  # a_1, DF495
        eph.a0   = payload.read(24).i  # a_0, DF496
        eph.aodc = payload.read( 5).u  # AODC, DF497
        eph.crs  = payload.read(18).i  # C_rs, DF498
        eph.dn   = payload.read(16).i  # delta n, DF499
        eph.m0   = payload.read(32).i  # M_0, DF500
        eph.cuc  = payload.read(18).i  # C_uc, DF501
        eph.e    = payload.read(32).u  # e, DF502
        eph.cus  = payload.read(18).i  # C_us, DF503
        eph.a12  = payload.read(32).u  # sqrt_a, DF504
        eph.toe  = payload.read(17).u  # t_oe, DF505
        eph.cic  = payload.read(18).u  # C_ic, DF506
        eph.omg0 = payload.read(32).i  # Omg_0, DF507
        eph.cis  = payload.read(18).i  # C_is, DF508
        eph.i0   = payload.read(32).i  # i_0, DF509
        eph.crc  = payload.read(18).i  # C_rc, DF510
        eph.omg  = payload.read(32).i  # omg, DF511
        eph.omgd = payload.read(24).i  # Omg dot, DF512
        eph.tgd1 = payload.read(10).i  # T_GD1, DF513
        eph.tgd2 = payload.read(10).i  # T_GD2, DF514
        eph.svh  = payload.read( 1).u  # SVH, DF515
        msg =f'C{svid:02d} WN={eph.wn} AODE={eph.aode}'
        if eph.svh:
            msg += self.trace.msg(0, ' unhealthy', fg='red')
        return msg

class EphIrn:
    def __init__(self, trace):
        self.trace = trace
        self.eph = [EphNull() for _ in range(N_IRNSAT)]
        self.alm = [EphNull() for _ in range(N_IRNSAT)]

    def decode_rtcm(self, payload):
        ''' read and decode RTCM IRNSS ephemeris '''
        svid      = payload.read( 6).u  # satellite id, DF516
        eph       = self.eph[svid-1]
        eph.wn    = payload.read(10).u  # week number, DF517
        eph.af0   = payload.read(22).i  # a_f0, DF518
        eph.af1   = payload.read(16).i  # a_f1, DF519
        eph.af2   = payload.read( 8).i  # a_f2, DF520
        eph.ura   = payload.read( 4).u  # URA, DF521
        eph.toc   = payload.read(16).u  # t_oc, DF522
        eph.tgd   = payload.read( 8).i  # t_GD, DF523
        eph.dn    = payload.read(22).i  # delta n, DF524
        eph.iodec = payload.read( 8).u  # IODEC, DF525
        payload.pos += 10               # reserved, DF526
        eph.hl5   = payload.read( 1).u  # L5_flag, DF527
        eph.hs    = payload.read( 1).u  # S_flag, DF528
        eph.cuc   = payload.read(15).i  # C_uc, DF529
        eph.cus   = payload.read(15).i  # C_us, DF530
        eph.cic   = payload.read(15).i  # C_ic, DF531
        eph.cis   = payload.read(15).i  # C_is, DF532
        eph.crc   = payload.read(15).i  # C_rc, DF533
        eph.crs   = payload.read(15).i  # C_rs, DF534
        eph.idot  = payload.read(14).i  # IDOT, DF535
        eph.m0    = payload.read(32).i  # M_0, DF536
        eph.toe   = payload.read(16).u  # t_oe, DF537
        eph.e     = payload.read(32).u  # e, DF538
        eph.a12   = payload.read(32).u  # sqrt_A, DF539
        eph.omg0  = payload.read(32).i  # Omg0, DF540
        eph.omg   = payload.read(32).i  # omg, DF541
        eph.omgd  = payload.read(22).i  # Omg dot, DF542
        eph.i0    = payload.read(32).i  # i0, DF543
        payload.pos += 2                # spare, DF544
        payload.pos += 2                # spare, DF545
        msg = f'I{svid:02d} WN={eph.wn} IODEC={eph.iodec:{FMT_IODE}}'
        if eph.hl5 or eph.hs:
            msg += self.trace.msg(0, f" unhealthy{' L5' if eph.hl5 else ''}{' S' if eph.hs else ''}", fg='red')
        return msg

# EOF
