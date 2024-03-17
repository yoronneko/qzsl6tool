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

# format definitions
FMT_IODC = '<4d'  # format string for issue of data clock
FMT_IODE = '<4d'  # format string for issue of data ephemeris

# constants
PI = 3.1415926535898            # Ratio of a circle's circumference
MU = 3.986004418  * (10**14)    # Geocentric gravitational constant [m^3/s^2]
OE = 7.2921151467 * (10**(-5))  # Mean angular velocity of the Earth [rad/s]
C  = 299792458                  # Speed of light [m/s]

class EphRaw:
    ''' raw ephemeris data '''
    def __init__(self):
        self.clear()

    def clear(self):
        ''' clears ephemeris data except for IODE '''
        self.svid  = 0  # satellite id
        self.m0    = 0  # mean anomaly at reference time
        self.e     = 0  # eccentricity
        self.a12   = 0  # square root of the semi-major axis
        self.t0e   = 0  # ephemeris reference time
        self.omg0  = 0  # longitude of ascending node of orbital plane
        self.i0    = 0  # inclination angle at reference time
        self.omg   = 0  # argument of perigee
        self.idot  = 0  # rate of change of inclination angle
        self.dn    = 0  # mean motion difference from computed value
        self.omgd  = 0  # rate of change of right ascension
        self.cuc   = 0  # cos harmonic correction term to the argument of latitude
        self.cus   = 0  # sin harmonic correction term to the argument of latitude
        self.crc   = 0  # cos harmonic correction term to the orbit radius
        self.crs   = 0  # sin harmonic correction term to the orbit radius
        self.cic   = 0  # cos harmonic correction term to the angle of inclination
        self.cis   = 0  # sin harmonic correction term to the angle of inclination
        self.t0c   = 0  # clock correction data reference TOW
        self.af0   = 0  # SV clock bias correction coefficient
        self.af1   = 0  # SV clock drift correction coefficient
        self.af2   = 0  # SV clock drift rate correction coefficient
        self.be5a  = 0  # E1-E5a broadcast group delay
        self.be5b  = 0  # E1-E5b broadcast group delay
        self.ai0   = 0  # effective ionisation level 1st order parameter
        self.ai1   = 0  # effective ionisation level 2nd order parameter
        self.a0    = 0  # constant term of polynomial
        self.a1    = 0  # 1st order term of polynomial
        self.dtls  = 0  # leap Second count before leap second adjustment
        self.t0t   = 0  # UTC data reference TOW
        self.wn0t  = 0  # UTC data reference week number
        self.wnlsf = 0  # week number of leap second adjustment
        self.dn    = 0  # day number at the end of which a leap second adjustment becomes effective
        self.dtlsf = 0  # leap second count after leap second adjustment
        self.a0g   = 0  # constant term of the polynomial describing the offset
        self.a1g   = 0  # rate of change of the offset
        self.t0g   = 0  # reference time for GGTO data
        self.wn0g  = 0  # week number of GGTO reference

class EphData:
    ''' ephemeris data '''
    pass

def decode(ephraw, satsys):
    '''
    returns decoded ephemeris data
    '''
    ephdec = EphData()  # decoded ephemeris data
    ephdec.svid  = ephraw.svid.u                # satellite id
    ephdec.m0    = ephraw.m0.i   * 2**(-31)*PI  # mean anomaly at reference time
    ephdec.e     = ephraw.e.u    * 2**(-33)     # eccentricity
    ephdec.a12   = ephraw.a12.u  * 2**(-19)     # square root of the semi-major axis
    ephdec.t0e   = ephraw.t0e.u  * 60           # ephemeris reference time
    ephdec.omg0  = ephraw.omg0.i * 2**(-31)*PI  # longitude of ascending node of orbital plane
    ephdec.i0    = ephraw.i0.i   * 2**(-31)*PI  # inclination angle at reference time
    ephdec.omg   = ephraw.omg.i  * 2**(-31)*PI  # argument of perigee
    ephdec.idot  = ephraw.idot.i * 2**(-43)*PI  # rate of change of inclination angle
    ephdec.dn    = ephraw.dn.i   * 2**(-43)*PI  # mean motion difference from computed value
    ephdec.omgd  = ephraw.omgd.i * 2**(-43)*PI  # rate of change of right ascension
    ephdec.cuc   = ephraw.cuc.i  * 2**(-29)     # cos harmonic correction term to the argument of latitude
    ephdec.cus   = ephraw.cus.i  * 2**(-29)     # sin harmonic correction term to the argument of latitude
    ephdec.crc   = ephraw.crc.i  * 2**(-5)      # cos harmonic correction term to the orbit radius
    ephdec.crs   = ephraw.crs.i  * 2**(-5)      # sin harmonic correction term to the orbit radius
    ephdec.cic   = ephraw.cic.i  * 2**(-29)     # cos harmonic correction term to the angle of inclination
    ephdec.cis   = ephraw.cis.i  * 2**(-29)     # sin harmonic correction term to the angle of inclination
    ephdec.t0c   = ephraw.t0c.u  * 60           # clock correction data reference TOW
    ephdec.af0   = ephraw.af0.i  * 2**(-34)     # SV clock bias correction coefficient
    ephdec.af1   = ephraw.af1.i  * 2**(-46)     # SV clock drift correction coefficient
    ephdec.af2   = ephraw.af2.i  * 2**(-59)     # SV clock drift rate correction coefficient
    ephdec.be5a  = ephraw.be5a.i * 2**(-32)     # E1-E5a broadcast group delay
    ephdec.be5b  = ephraw.be5b.i * 2**(-32)     # E1-E5b broadcast group delay
    ephdec.ai0   = ephraw.ai0.u  * 2**(-2)      # effective ionisation level 1st order parameter
    ephdec.ai1   = ephraw.ai1.i  * 2**(-8)      # effective ionisation level 2nd order parameter
    ephdec.a0    = ephraw.a0.i   * 2**(-30)     # constant term of polynomial
    ephdec.a1    = ephraw.a1.i   * 2**(-50)     # 1st order term of polynomial
    ephdec.dtls  = ephraw.dtls.i                # leap Second count before leap second adjustment
    ephdec.t0t   = ephraw.t0t.u                 # UTC data reference TOW
    ephdec.wn0t  = ephraw.wn0t.u                # UTC data reference week number
    ephdec.wnlsf = ephraw.wnlsf.u               # week number of leap second adjustment
    ephdec.dn    = ephraw.dn.u                  # day number at the end of which a leap second adjustment becomes effective
    ephdec.dtlsf = ephraw.dtlsf.i               # leap second count after leap second adjustment
    ephdec.a0g   = ephraw.a0g.i  * 2**(-35)     # constant term of the polynomial describing the offset
    ephdec.a1g   = ephraw.a1g.i  * 2**(-51)     # rate of change of the offset
    ephdec.t0g   = ephraw.t0g.u  * 3600         # reference time for GGTO data
    ephdec.wn0g  = ephraw.wn0g.u                # week number of GGTO reference
    return ephdec

class Eph:
    ''' Ephemeris class '''
    def __init__(self, fp_disp, t_level, msg_color):
        self.fp_disp   = fp_disp
        self.t_level   = t_level
        self.msg_color = msg_color

    def trace(self, level, *args):
        if self.t_level < level or not self.fp_disp:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_disp)
            except (BrokenPipeError, IOError):
                sys.exit()

    def decode_ephemerides(self, payload, satsys, mtype):
        ''' returns decoded ephemeris data '''
        r = EphRaw()
        string = ''
        if satsys == 'G':  # GPS ephemerides
            r.svid = payload.read( 'u6')  # satellite id, DF009
            r.wn   = payload.read('u10')  # week number, DF076
            r.sva  = payload.read( 'u4')  # SV accuracy DF077
            r.gpsc = payload.read(   2 )  # GPS code L2, DF078
            r.idot = payload.read('i14')  # IDOT, DF079
            r.iode = payload.read( 'u8')  # IODE, DF071
            r.toc  = payload.read('u16')  # t_oc, DF081
            r.af2  = payload.read( 'i8')  # a_f2, DF082
            r.af1  = payload.read('i16')  # a_f1, DF083
            r.af0  = payload.read('i22')  # a_f0, DF084
            r.iodc = payload.read('u10')  # IODC, DF085
            r.crs  = payload.read('i16')  # C_rs, DF086
            r.dn   = payload.read('i16')  # d_n,  DF087
            r.m0   = payload.read('i32')  # M_0,  DF088
            r.cuc  = payload.read('i16')  # C_uc, DF089
            r.e    = payload.read('u32')  # e,    DF090
            r.cus  = payload.read('i16')  # C_us, DF091
            r.a12  = payload.read('u32')  # a12,  DF092
            r.toe  = payload.read('u16')  # t_oe, DF093
            r.cic  = payload.read('i16')  # C_ic, DF094
            r.omg0 = payload.read('i32')  # Omg0, DF095
            r.cis  = payload.read('i16')  # C_is, DF096
            r.i0   = payload.read('i32')  # i_0,  DF097
            r.crc  = payload.read('i16')  # C_rc, DF098
            r.omg  = payload.read('i32')  # omg,  DF099
            r.omgd = payload.read('i24')  # Omg-dot, DF100
            r.tgd  = payload.read( 'i8')  # t_GD, DF101
            r.svh  = payload.read( 'u6')  # SV health, DF102
            r.l2p  = payload.read( 'u1')  # P flag, DF103
            r.fi   = payload.read( 'u1')  # fit interval, DF137
            string += f'G{r.svid:02d} WN={r.wn} IODE={r.iode:{FMT_IODE}} IODC={r.iodc:{FMT_IODC}}'
            if   r.gpsc == '0b01': string += ' L2P'
            elif r.gpsc == '0b10': string += ' L2C/A'
            elif r.gpsc == '0b11': string += ' L2C'
            else: string += f'unknown L2 code: {r.gpsc}'
            if r.svh:
                string += self.msg_color.fg('red') + \
                    f' unhealthy({r.svh:02x})' + self.msg_color.fg()
        elif satsys == 'R':  # GLONASS ephemerides
            r.svid  = payload.read( 'u6')  # satellite id, DF038
            r.fcn   = payload.read( 'u5')  # freq ch, DF040
            r.svh   = payload.read( 'u1')  # alm health DF104
            r.aha   = payload.read( 'u1')  # alm health avail, DF105
            r.p1    = payload.read( 'u2')  # P1, DF106
            r.tk    = payload.read(  12 )  # t_k, DF107
            r.bn    = payload.read( 'u1')  # B_n word MSB, DF108
            r.p2    = payload.read( 'u1')  # P2, DF109
            r.tb    = payload.read( 'u7')  # t_b, DF110
            _sgn    = payload.read( 'u1')  # x_n dot, DF111
            r.xnd   = payload.read('u23')
            if _sgn: r.xnd = -r.xnd
            _sgn    = payload.read( 'u1')  # x_n, DF112
            r.xn    = payload.read('u26')
            if _sgn: r.xn = -r.xn
            _sgn    = payload.read( 'u1')  # x_n dot^2, DF113
            r.xndd  = payload.read( 'u4')
            if _sgn: r.xndd = -r.xndd
            _sgn    = payload.read( 'u1')  # y_n dot, DF114
            r.ynd   = payload.read('u23')
            if _sgn: r.ynd = -r.ynd
            _sgn    = payload.read( 'u1')  # y_n, DF115
            r.yn    = payload.read('u26')
            if _sgn: r.yn = -r.yn
            _sgn    = payload.read( 'u1')  # y_n dot^2, DF116
            r.yndd  = payload.read( 'u4')
            if _sgn: r.yndd = -r.yndd
            _sgn    = payload.read( 'u1')  # z_n dot, DF117
            r.znd   = payload.read('u23')
            if _sgn: r.znd = -r.znd
            _sgn    = payload.read( 'u1')  # z_n, DF118
            r.zn    = payload.read('u26')
            if _sgn: r.zn = -r.zn
            _sgn    = payload.read( 'u1')  # z_n dot^2, DF119
            r.zndd  = payload.read( 'u4')
            if _sgn: r.zndd = -r.zndd
            r.p3    = payload.read( 'u1')  # P3, DF120
            _sgn    = payload.read( 'u1')  # gamma_n, DF121
            r.gmn   = payload.read('u10')
            if _sgn: r.gmn = -r.gmn
            r.p     = payload.read(   2 )  # P, DF122
            r.in3   = payload.read( 'u1')  # I_n, DF123
            _sgn    = payload.read( 'u1')  # tau_n, DF124
            r.taun  = payload.read('u21')
            if _sgn: r.taun = -r.taun
            _sgn    = payload.read( 'u1')  # d_tau_n, DF125
            r.dtaun = payload.read( 'u4')
            if _sgn: r.dtaun = -r.dtaun
            r.en    = payload.read( 'u5')  # E_n, DF126
            r.p4    = payload.read( 'u1')  # P4, DF127
            r.ft    = payload.read( 'u4')  # F_t, DF128
            r.nt    = payload.read('u11')  # N_t, DF129
            r.m     = payload.read(   2 )  # M, DF130
            r.add   = payload.read( 'u1')  # addition, DF131
            r.na    = payload.read('u11')  # N^A, DF132
            _sgn    = payload.read( 'u1')  # tau_c, DF133
            r.tauc  = payload.read('u31')
            if _sgn: r.tauc = -r.tauc
            r.n4    = payload.read( 'u5')  # N_4, DF134
            _sgn    = payload.read( 'u1')  # tau_GPS, DF135
            r.tgps  = payload.read('u21')
            if _sgn: r.tgps = -r.tgps
            r.in5   = payload.read( 'u1')  # I_n, DF136
            payload.pos +=  7              # reserved
            string += f'R{r.svid:02d} f={r.fcn:02d} tk={r.tk[7:12].u:02d}:{r.tk[1:7].u:02d}:{r.tk[0:2].u*15:02d} tb={r.tb*15}min'
            if r.svh:
                string += self.msg_color.fg('red') + \
                    ' unhealthy' + self.msg_color.fg()
        elif satsys == 'E':  # Galileo ephemerides
            r.svid  = payload.read( 'u6')  # satellite id, DF252
            r.wn    = payload.read('u12')  # week number, DF289
            r.iodn  = payload.read('u10')  # IODnav, DF290
            r.sisa  = payload.read( 'u8')  # SIS Accracy, DF291
            r.idot  = payload.read('i14')  # IDOT, DF292
            r.toc   = payload.read('u14')  # t_oc, DF293
            r.af2   = payload.read( 'i6')  # a_f2, DF294
            r.af1   = payload.read('i21')  # a_f1, DF295
            r.af0   = payload.read('i31')  # a_f0, DF296
            r.crs   = payload.read('i16')  # C_rs, DF297
            r.dn    = payload.read('i16')  # delta n, DF298
            r.m0    = payload.read('i32')  # M_0, DF299
            r.cuc   = payload.read('i16')  # C_uc, DF300
            r.e     = payload.read('u32')  # e, DF301
            r.cus   = payload.read('i16')  # C_us, DF302
            r.a12   = payload.read('u32')  # sqrt_a, DF303
            r.toe   = payload.read('u14')  # t_oe, DF304
            r.cic   = payload.read('i16')  # C_ic, DF305
            r.omg0  = payload.read('i32')  # Omega_0, DF306
            r.cis   = payload.read('i16')  # C_is, DF307
            r.i0    = payload.read('i32')  # i_0, DF308
            r.crc   = payload.read('i16')  # C_rc, DF309
            r.omg   = payload.read('i32')  # omega, DF310
            r.omgd0 = payload.read('i24')  # Omega-dot0, DF311
            r.be5a  = payload.read('i10')  # BGD_E5aE1, DF312
            if   mtype == 'F/NAV':
                r.osh = payload.read('u2')  # open signal health DF314
                r.osv = payload.read('u1')  # open signal valid DF315
                payload.pos += 7            # reserved, DF001
            elif mtype == 'I/NAV':
                r.be5b = payload.read('i10')  # BGD_E5bE1 DF313
                r.e5h  = payload.read( 'u2')  # E5b signal health, DF316
                r.e5v  = payload.read( 'u1')  # E5b data validity, DF317
                r.e1h  = payload.read( 'u2')  # E1b signal health, DF287
                r.e1v  = payload.read( 'u1')  # E1b data validity, DF288
                payload.pos += 2              # reserved, DF001
            else:
                raise Exception(f'unknown Galileo nav message: {mtype}')
            string += f'E{r.svid:02d} WN={r.wn} IODnav={r.iodn}'
            if   mtype == 'F/NAV':
                if r.osh:
                    string += self.msg_color.fg('red') + \
                        f' unhealthy OS ({r.osh.uint})' + self.msg_color.fg()
                if r.osv:
                    string += self.msg_color.fg('red') + \
                        ' invalid OS' + self.msg_color.fg()
            elif mtype == 'I/NAV':
                if r.e5h:
                    string += self.msg_color.fg('red') + \
                        f' unhealthy E5b ({r.e5h.uint})' + self.msg_color.fg()
                if r.e5v:
                    string += self.msg_color.fg('red') + \
                        ' invalid E5b' + self.msg_color.fg()
                if r.e1h:
                    string += self.msg_color.fg('red') + \
                        f' unhealthy E1b ({r.e1h.uint})' + self.msg_color.fg()
                if r.e1v:
                    string += self.msg_color.fg('red') + \
                        ' invalid E1b' + self.msg_color.fg()
            else:
                raise Exception(f'unknown Galileo nav message: {mtype}')
        elif satsys == 'J':  # QZSS ephemerides
            r.svid = payload.read( 'u4')  # satellite id, DF429
            r.toc  = payload.read('u16')  # t_oc, DF430
            r.af2  = payload.read( 'i8')  # a_f2, DF431
            r.af1  = payload.read('i16')  # a_f1, DF432
            r.af0  = payload.read('i22')  # a_f0, DF433
            r.iode = payload.read( 'u8')  # IODE, DF434
            r.crs  = payload.read('i16')  # C_rs, DF435
            r.dn0  = payload.read('i16')  # delta n_0, DF436
            r.m0   = payload.read('i32')  # M_0, DF437
            r.cuc  = payload.read('i16')  # C_uc, DF438
            r.e    = payload.read('u32')  # e, DF439
            r.cus  = payload.read('i16')  # C_uc, DF440
            r.a12  = payload.read('u32')  # sqrt_A, DF441
            r.toe  = payload.read('u16')  # t_oe, DF442
            r.cic  = payload.read('i16')  # C_ic, DF443
            r.omg0 = payload.read('i32')  # Omg_0, DF444
            r.cis  = payload.read('i16')  # C_is, DF445
            r.i0   = payload.read('i32')  # i_0, DF446
            r.crc  = payload.read('i16')  # C_rc, DF447
            r.omgn = payload.read('i32')  # omg_n, DF448
            r.omgd = payload.read('i24')  # Omg dot, DF449
            r.i0d  = payload.read('i14')  # i0 dot, DF450
            r.l2   = payload.read( 'u2')  # L2 code, DF451
            r.wn   = payload.read('u10')  # week number, DF452
            r.ura  = payload.read( 'u4')  # URA, DF453
            r.svh  = payload.read( 'u6')  # SVH, DF454
            r.tgd  = payload.read( 'i8')  # T_GD, DF455
            r.iodc = payload.read('u10')  # IODC, DF456
            r.fi   = payload.read( 'u1')  # fit interval, DF457
            string += f'J{r.svid:02d} WN={r.wn} IODE={r.iode:{FMT_IODE}} IODC={r.iodc:{FMT_IODC}}'
            if r.svh:  # to be determined: L1 C/B operation
                string += self.msg_color.fg('red') + \
                    f' unhealthy ({r.svh:02x})' + self.msg_color.fg()
        elif satsys == 'C':  # BeiDou ephemerides
            r.svid = payload.read( 'u6')  # satellite id, DF488
            r.wn   = payload.read('u13')  # week number, DF489
            r.urai = payload.read( 'u4')  # URA, DF490
            r.idot = payload.read('i14')  # IDOT, DF491
            r.aode = payload.read( 'u5')  # AODE, DF492
            r.toc  = payload.read('u17')  # t_oc, DF493
            r.a2   = payload.read('i11')  # a_2, DF494
            r.a1   = payload.read('i22')  # a_1, DF495
            r.a0   = payload.read('i24')  # a_0, DF496
            r.aodc = payload.read( 'u5')  # AODC, DF497
            r.crs  = payload.read('i18')  # C_rs, DF498
            r.dn   = payload.read('i16')  # delta n, DF499
            r.m0   = payload.read('i32')  # M_0, DF500
            r.cuc  = payload.read('i18')  # C_uc, DF501
            r.e    = payload.read('u32')  # e, DF502
            r.cus  = payload.read('i18')  # C_us, DF503
            r.a12  = payload.read('u32')  # sqrt_a, DF504
            r.toe  = payload.read('u17')  # t_oe, DF505
            r.cic  = payload.read('u18')  # C_ic, DF506
            r.omg0 = payload.read('i32')  # Omg_0, DF507
            r.cis  = payload.read('i18')  # C_is, DF508
            r.i0   = payload.read('i32')  # i_0, DF509
            r.crc  = payload.read('i18')  # C_rc, DF510
            r.omg  = payload.read('i32')  # omg, DF511
            r.omgd = payload.read('i24')  # Omg dot, DF512
            r.tgd1 = payload.read('i10')  # T_GD1, DF513
            r.tgd2 = payload.read('i10')  # T_GD2, DF514
            r.svh  = payload.read( 'u1')  # SVH, DF515
            string +=f'C{r.svid:02d} WN={r.wn} AODE={r.aode}'
            if r.svh:
                string += self.msg_color.fg('red') + \
                    ' unhealthy' + self.msg_color.fg()
        elif satsys == 'I':  # NavIC ephemerides
            r.svid  = payload.read( 'u6')  # satellite id, DF516
            r.wn    = payload.read('u10')  # week number, DF517
            r.af0   = payload.read('i22')  # a_f0, DF518
            r.af1   = payload.read('i16')  # a_f1, DF519
            r.af2   = payload.read( 'i8')  # a_f2, DF520
            r.ura   = payload.read( 'u4')  # URA, DF521
            r.toc   = payload.read('u16')  # t_oc, DF522
            r.tgd   = payload.read( 'i8')  # t_GD, DF523
            r.dn    = payload.read('i22')  # delta n, DF524
            r.iodec = payload.read( 'u8')  # IODEC, DF525
            payload.pos += 10              # reserved, DF526
            r.hl5   = payload.read( 'u1')  # L5_flag, DF527
            r.hs    = payload.read( 'u1')  # S_flag, DF528
            r.cuc   = payload.read('i15')  # C_uc, DF529
            r.cus   = payload.read('i15')  # C_us, DF530
            r.cic   = payload.read('i15')  # C_ic, DF531
            r.cis   = payload.read('i15')  # C_is, DF532
            r.crc   = payload.read('i15')  # C_rc, DF533
            r.crs   = payload.read('i15')  # C_rs, DF534
            r.idot  = payload.read('i14')  # IDOT, DF535
            r.m0    = payload.read('i32')  # M_0, DF536
            r.toe   = payload.read('u16')  # t_oe, DF537
            r.e     = payload.read('u32')  # e, DF538
            r.a12   = payload.read('u32')  # sqrt_A, DF539
            r.omg0  = payload.read('i32')  # Omg0, DF540
            r.omg   = payload.read('i32')  # omg, DF541
            r.omgd  = payload.read('i22')  # Omg dot, DF542
            r.i0    = payload.read('i32')  # i0, DF543
            payload.pos += 2               # spare, DF544
            payload.pos += 2               # spare, DF545
            string += f'I{r.svid:02d} WN={r.wn} IODEC={r.iodec:{FMT_IODE}}'
            if r.hl5 or r.hs:
                string += self.msg_color.fg('red') + ' unhealthy'
                if r.hl5: string += ' L5'
                if r.hs : string += ' S'
                string += self.msg_color.fg()
        else:
            raise Exception(f'unknown satsys({satsys})')
        return string

# EOF
